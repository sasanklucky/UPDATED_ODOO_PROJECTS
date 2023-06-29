from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db, _
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm


class SaleOrderLineInheritSync(models.Model):
    _inherit = "stock.picking"

    sync_picking  = fields.Boolean(string='Sync',default=False)

    @api.multi
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some lines to move'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if you have not processed any quantity. You should rather cancel the transfer.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a lot/serial number for %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        # update sync false in sale order for re sync of shipment if backorder
        self.sale_id.sync_so = False
        return


class SaleOrderLineInheritSync(models.Model):
    _inherit = "sale.order.line"
    _description = "Sale Order Line"

    child_po_id_ref = fields.Char(string='Child Reference')
    child_db = fields.Char()
    ready_for_sync  = fields.Boolean(string='Ready for Sync')
    sync_so_order_line  = fields.Boolean(string='Sync')
    modified_fields = fields.Char()

    @api.multi
    def update_tax_and_price(self):
        # print("view called0-----",self.state)
        if self.state not in ['done','cancel']:
            print("inside")
            form_view = self.env.ref('purchase_order_sync_apis.sale_order_line_froms')
            # print("form_view===",form_view)
            action = {
                'name': 'Update Tax/Unit Price',
                'type': 'ir.actions.act_window',
                'res_model': 'update_sale_order_line',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': form_view.id,
                'target': 'new',
                'context':{'tax_ids':self.tax_id.ids,'default_order_line_id':self.id,'default_price_unit':self.price_unit}
            }
            # print("action====",action)
            return action
        else:
            raise ValidationError('You cannot update Price/Tax details.')
    


    @api.multi
    def write(self, vals):
        # print("vals---",vals)
        if vals and self.sync_so_order_line==False:
            # print("--------4444444444---------",self.modified_fields if self.modified_fields else '' +  ','.join(vals))
            vals['modified_fields'] = (self.modified_fields +  ',' + ','.join(vals)) if self.modified_fields else '' +  ','.join(vals)
            if self.child_po_id_ref or 'child_po_id_ref' in vals:
                vals['ready_for_sync']=True
        if vals and self.sync_so_order_line==True:
            # print("--------99999999---------",','.join(vals))
            vals['modified_fields'] = ','.join(vals)
            if self.child_po_id_ref or 'child_po_id_ref' in vals:
                vals['ready_for_sync']=True
        if vals:
            vals['sync_so_order_line'] = True
        else:
            vals['sync_so_order_line'] = False
        res =  super(SaleOrderLineInheritSync, self).write(vals)
        return res


class SaleOrderInheritSync(models.Model):
    _inherit = "sale.order"
    _description = "Sale Order"

    sync_so  = fields.Boolean(string='Sync')
    check_picking_status  = fields.Boolean(string='Sync', compute='get_pick_status')
    ready_for_sync  = fields.Boolean(string='Ready for Sync')
    child_po_id_ref = fields.Char(string='Child Reference')
    child_po_ref = fields.Char(string='Child Reference')
    child_db = fields.Char()
    parent_db = fields.Char()
    modified_fields = fields.Char()
    test_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)

    @api.depends('child_po_ref')
    def get_pick_status(self):
        for rec in self:
            picking_id = self.env['stock.picking'].sudo().search([('sale_id','=',rec.id),('state','=','done'),('sync_picking','=',False)],order='id desc',limit=1)
            param = self.env['ir.config_parameter'].sudo()
            parent = param.get_param('purchase_order_sync_apis.po_company_type')
            if picking_id or rec.child_po_id_ref ==False or rec.ready_for_sync==False or parent == 'is_parent_company':
                rec.check_picking_status =True
            else:
                rec.check_picking_status =False
    
    @api.depends('state')
    def _compute_css(self):
        for record in self:
            print('state------------caupdate_tax_unit_pricelled',record.state)
            if record.child_po_id_ref != '':
                print("csss----------")
                record.test_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                record.test_css = False

    # update False value to sync_so if no value is passed
    @api.multi
    def write(self, vals):
        print("valueeee---",vals)
        if vals and self.sync_so==False:
            print("--------4444444444---------",self.modified_fields if self.modified_fields else '' +  ','.join(vals))
            vals['modified_fields'] = (self.modified_fields + ',' + ','.join(vals)) if self.modified_fields else '' +  ','.join(vals)
            vals['ready_for_sync']=True
        if vals and self.sync_so==True:
            print("--------99999999---------",','.join(vals))
            vals['modified_fields'] = ','.join(vals)
            vals['ready_for_sync']=True

        if 'sync_so' not in vals:
            vals['sync_so'] = False
        res =  super(SaleOrderInheritSync, self).write(vals)
        return res

    # @api.multi
    # def unlink(self):
    #     for record in self:
    #         param = self.env['ir.config_parameter'].sudo()
    #         database = record.child_db
    #         self.unlink_so_from_parent(database,int(record.child_po_id_ref))
    #     return super(SaleOrderInheritSync, self).unlink()
    

    # Delete Sale order from parent if purchase order is deleted from child
    @api.multi
    def unlink_so_from_parent(self,parent_db_name,child_id):
        # unlink po from parent db
        try:
            param = self.env['ir.config_parameter'].sudo()
            child = param.get_param('purchase_order_sync_apis.po_company_type')
            check_enable_po_sync = param.get_param('purchase_order_sync_apis.enable_po_sync')
            if child == 'is_parent_company' and check_enable_po_sync == 'yes':
                db = sql_db.db_connect(f"{parent_db_name}")
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    exist_in_parent = env['purchase.order'].sudo().search([('id','=',str(child_id))])
                    print("exist_in_parent=====",exist_in_parent)
                    if exist_in_parent:
                        exist_in_parent.unlink()
        except Exception as e:
            raise ValidationError(e)



# ----------------------- ADD ir.sequence for quotation nno in purchase order  -------------------------
    def call_so_sync(self):
        self.sync_so_to_parent(self)

    @api.model
    def _cron_sync_so_to_po_in_child(self):
        call = self.env['sale.order'].sync_so_to_parent(False)
    
    @api.model
    def sync_so_to_parent(self,current_po_record=False):
        """ connect to parent db set up in general settings """
        # return
        try:
            param = self.env['ir.config_parameter'].sudo()
            child = param.get_param('purchase_order_sync_apis.po_company_type')
            check_sale_sync = param.get_param('purchase_order_sync_apis.enable_sale_sync')
            print("child---",child,check_sale_sync)
            so_records = self.env['sale.order'].sudo().search([('ready_for_sync','=',True),('child_po_id_ref','!=',False)],order='id asc')
            if child == 'is_parent_company' and check_sale_sync == 'yes' and so_records:
                database = self._cr.dbname
                print("database=====",database)
                # child_database = param.get_param('purchase_order_sync_apis.child_parent_db_name')
                db = sql_db.db_connect(f"{so_records[0].child_db}")
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    #getting child data as sellf represent child db env
                    print("==1==",so_records)
                    
                    # looped child po datas
                    for rec in so_records:
                        #fetching child model ids and mapping with parent model ids
                        company = env['res.company'].sudo().search([('dealer_code','=',rec.company_id.dealer_code)],order='id desc',limit=1)
                        partner_id = env['res.partner'].sudo().search([('mobile','=',rec.partner_id.mobile)],order='id desc',limit=1)
                        # ('company_id','=',company.id)
                        # prepare dynamic data for sync sale sync to purchase
                        child_database = rec.child_db
                        order_datas = env['purchase.order'].sudo().browse(int(rec.child_po_id_ref))
                        if rec.ready_for_sync and rec.modified_fields != '' and order_datas:
                            values = rec.modified_fields.split(',')
                            print("order values=====",values)
                            # sale_dict = {}
                            # if 'partner_id' in values:
                            #     sale_dict['partner_id'] = partner_id.id
                            # if 'requisition_id' in values:
                            #     requisition_id = env['purchase.requisition'].sudo().search([('name','=',rec.requisition_id.name),('company_id','=',company.id)],order='id desc',limit=1)
                            #     sale_dict['requisition_id'] = requisition_id.id if requisition_id else False
                            # if 'currency_id' in values:
                            #     currency_id = env['res.currency'].sudo().search([('mobile','=',partner_id.mobile),('company_id','=',company.id)],order='id desc',limit=1)
                            #     sale_dict['currency_id'] = currency_id.id if currency_id else False
                            # if 'date_order' in values:
                            #     sale_dict['date_order'] = rec.date_order
                            # if 'company_id' in values:
                            #     sale_dict['company_id'] = company.id
                            # if 'date_planned' in values:
                            #     sale_dict['date_planned'] = rec.date_planned
                            # if 'fiscal_position_id' in values:
                            #     fiscal_position_id = env['account.fiscal.position'].sudo().search([('name','=',rec.fiscal_position_id.name)],order='id desc',limit=1)
                            #     sale_dict['fiscal_position_id'] = fiscal_position_id.id if fiscal_position_id else False
                            # if 'payment_term_id' in values:
                            #     payment_term_id = env['account.payment.term'].sudo().search([('name','=',rec.payment_term_id.name),('company_id','=',company.id),('active','=',rec.payment_term_id.active)],order='id desc',limit=1)
                            #     sale_dict['payment_term_id'] = payment_term_id.id if payment_term_id else False
                            # if 'incoterm_id' in values:
                            #     incoterm_id = env['stock.incoterms'].sudo().search([('name','=',rec.incoterm_id.name),('code','=',rec.incoterm_id.code),('active','=',rec.incoterm_id.active)],order='id desc',limit=1)
                            #     sale_dict['incoterm_id'] = incoterm_id.id
                            # if 'picking_type_id' in values:
                            #     picking_type_id = env['stock.picking.type'].sudo().search([('name','=',rec.picking_type_id.name),('code','=',rec.picking_type_id.code),('active','=',rec.picking_type_id.active)],order='id desc',limit=1)
                            #     sale_dict['picking_type_id'] = picking_type_id.id if picking_type_id else False
                            # if 'date_approve' in values:
                            #     sale_dict['date_approve'] = rec.date_approve
                            # if 'invoice_status' in values:
                            #     sale_dict['invoice_status'] = rec.invoice_status
                            # if 'note' in values:
                            #     sale_dict['notes'] = rec.note
                        # order_line_list = []
                        # print("sale_dict====",sale_dict)
                        for line_data in rec.order_line:
                            print("rec----",rec)
                            dic_data = {}
                            if line_data.ready_for_sync and line_data.child_po_id_ref and line_data.modified_fields != '':
                                # value_list = line_data.modified_fields.split(',')
                                value_list = ['price_unit','price_subtotal','tax_id']
                                print("order line values====",value_list)
                                # if 'name' in value_list:
                                #     dic_data['name']=line_data.name if line_data.name else ''
                                # if 'state' in value_list:
                                #     dic_data['state']=line_data.state if line_data.state else ''
                                order_line_datas = env['purchase.order.line'].sudo().browse(int(line_data.child_po_id_ref))
                                if order_line_datas:
                                    # if 'product_id' in value_list:
                                    #     product_data = env['product.product'].sudo().search([('name','=',line_data.product_id.name),('default_code','=',line_data.product_id.default_code)],order='id desc',limit=1)
                                    #     dic_data['product_id']=product_data.id if product_data else line_data.product_id.id
                                    # 'date_planned':line_data.date_planned if line_data.date_planned else ''
                                    # 'company_id':line_data.company_id.id if line_data.company_id else rec.company_id.id
                                    # if 'product_uom_qty' in value_list:
                                    #     dic_data['product_qty']=line_data.product_uom_qty if line_data.product_uom_qty else 0
                                    # if 'qty_received' in value_list:
                                        # dic_data['qty_received']=line_data.product_uom_qty if line_data.product_uom_qty else 0
                                    # if 'qty_invoiced' in value_list:
                                        # dic_data['qty_invoiced']=line_data.product_uom_qty if line_data.product_uom_qty else 0
                                    # if 'product_uom' in value_list:
                                    #     product_uom = env['product.uom'].sudo().search([('name','=',line_data.product_uom.name)],order='id desc',limit=1)
                                    #     dic_data['product_uom']=product_uom.id if product_uom else line_data.product_uom.id
                                    if 'price_unit' in value_list:
                                        dic_data['price_unit']=line_data.price_unit if line_data.price_unit else 0
                                    if 'tax_id' in value_list:
                                        dic_data['taxes_id']=line_data.tax_id.ids if line_data.tax_id else ''
                                    if 'price_subtotal' in value_list:
                                        dic_data['price_subtotal']=line_data.price_subtotal if line_data.price_subtotal else ''
                                print("--------------------Updated-------1---------------------",order_line_datas,dic_data)
                                if dic_data and order_line_datas:
                                    """ Insert new records """
                                    line_record=order_line_datas.sudo().write(dic_data)
                                else:
                                    print("Record already present in parent DB.")
                        if order_datas:
                            # print("--------------------Updated-------2---------------------",order_datas,sale_dict)
                            # record = order_datas.sudo().write(sale_dict)
                            rec.sync_so=True
                            rec.ready_for_sync=False
                            rec.modified_fields=''
                            #update shipping and receive quantity
                            picking_id = self.env['stock.picking'].sudo().search([('sale_id','=',rec.id),('state','=','done'),('sync_picking','=',False)],order='id desc',limit=1)
                            print("picking_id====",picking_id)
                            if picking_id:
                                move_id = self.env['stock.move'].sudo().search([('picking_id','=',picking_id.id)],order='id desc',limit=1)
                                print("move_id====",move_id)
                                update_val = False
                                if move_id:
                                    move_line_ids = self.env['stock.move.line'].sudo().search([('move_id','=',move_id.id)])
                                    print("move_line_ids====",move_line_ids)
                                    origin = env['purchase.order'].sudo().search([('id','=',int(rec.child_po_id_ref))],order='id desc',limit=1)
                                    print("origin===",origin)
                                    po_picking_id = env['stock.picking'].sudo().search([('origin','=',origin.name)],order='id desc',limit=1)
                                    print("po_picking_id===",po_picking_id,rec.child_po_id_ref)
                                    po_move_id = env['stock.move'].sudo().search([('picking_id','=',po_picking_id.id)],order='id desc',limit=1)
                                    print("po_move_id===",po_move_id,po_picking_id)
                                    for data in move_line_ids:
                                        unvalidated_rec = po_move_id.move_line_ids.filtered(lambda x:x.qty_done == 0.0 and x.state not in ['done','cancel'])
                                        print("unvalidated_recvv===",unvalidated_rec)
                                        if unvalidated_rec.ids:
                                            unvalidated_rec[0].sudo().write({
                                                'qty_done':data.qty_done if data.qty_done  else 0,
                                                'lot_name':data.lot_id.name if data.lot_id else '',
                                                'owner_id':partner_id.id if partner_id else False,
                                            })
                                            print("-----------------picking updated---------------")
                                        update_val = True
                                if update_val:
                                    print("-----------------sync updated---------------")
                                    picking_id.sync_picking = True
                       
        except Exception as e:
            raise ValidationError(e)