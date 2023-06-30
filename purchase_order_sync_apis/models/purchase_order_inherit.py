from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm

class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    sync_po  = fields.Boolean(string='Sync')
    child_id_ref = fields.Char(string='Child Reference')
    # child_partner_ref = fields.Many2one('res.partner', string='Child Reference')
    child_db = fields.Char()

    @api.multi
    def unlink(self):
        for record in self:
            param = self.env['ir.config_parameter'].sudo()
            database = param.get_param('purchase_order_sync_apis.parent_db_name')
            self.unlink_purchase_order_from_parent(database,record.id)
        return super(PurchaseOrderInherit, self).unlink()
    
    @api.multi
    def write(self, vals):
        if 'sync_po' not in vals:
            vals['sync_po'] = False
        res =  super(PurchaseOrderInherit, self).write(vals)
        return res


    @api.multi
    def unlink_purchase_order_from_parent(self,parent_db_name,child_id):
        # unlink po from parent db
        try:
            param = self.env['ir.config_parameter'].sudo()
            child = param.get_param('purchase_order_sync_apis.po_company_type')
            check_enable_po_sync = param.get_param('purchase_order_sync_apis.enable_po_sync')
            if child == 'is_child_company' and check_enable_po_sync == 'yes':
                # print("database=====",parent_db_name)
                db = sql_db.db_connect(f"{parent_db_name}")
                # child_database = param.get_param('purchase_order_sync_apis.child_parent_db_name')
                child_database = self._cr.dbname
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    exist_in_parent = env['purchase.order'].sudo().search([('child_id_ref','=',str(child_id)),('child_db','=',child_database)])
                    # print("exist_in_parent=====",exist_in_parent)
                    if exist_in_parent:
                        exist_in_parent.unlink()
        except Exception as e:
            raise ValidationError(e)


    @api.model
    def _cron_update_purchase_order_to_parent(self):
        """ connect to parent db set up in general settings """
        try:
            param = self.env['ir.config_parameter'].sudo()
            child = param.get_param('purchase_order_sync_apis.po_company_type')
            check_po_sync = param.get_param('purchase_order_sync_apis.enable_po_sync')
            print("child---",child,check_po_sync)
            if child == 'is_child_company' and check_po_sync == 'yes':
                database = param.get_param('purchase_order_sync_apis.parent_db_name')
                print("database=====",database)
                db = sql_db.db_connect(f"{database}")
                # child_database = param.get_param('purchase_order_sync_apis.child_parent_db_name')
                child_database = self._cr.dbname
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    #getting child data as sellf represent child db env
                    po_records = self.env['purchase.order'].sudo().search([('sync_po','=',False),('state','=','purchase')],order='id asc')
                    print("==1==",po_records)
                    
                    # looped child po datas
                    for rec in po_records:
                        print("rec=====",rec)

                        # parent record env
                        po_quotation = env['purchase.order'].sudo()
                        exist_in_parent = po_quotation.search([('child_id_ref','=',str(rec.id)),('child_db','=',child_database)],limit=1, order='id desc')
                        if not exist_in_parent:
                            print("purchase order=====",exist_in_parent)
                            customer = False
                            user= False
                            payment_term_id= False
                            country= False
                            currency= False
                            fiscal_position_id= False
                            picking_type_id= False
                            payment_term_id= False
                            incoterm_id= False
                            requisition_id= False
                            # # if exist_in_parent:
                            company = env['res.company'].sudo().search([('dealer_code','=',rec.company_id.dealer_code)],order='id desc',limit=1)
                            
                            if rec.partner_id:
                                customer = env['res.partner'].sudo().search([('mobile','=',rec.partner_id.mobile),('company_id','=',rec.company_id.id)],order='id desc',limit=1)
                            
                                if not customer:
                                    data_dict = {
                                        'name':rec.partner_id.name if rec.partner_id else '',
                                        'mobile':rec.partner_id.mobile if rec.partner_id.mobile else '',
                                        'email':rec.partner_id.email if rec.partner_id.email else '',
                                        'street':rec.partner_id.street if rec.partner_id.street else '',
                                        'street2':rec.partner_id.street2 if rec.partner_id.street2 else '',
                                        'city':rec.partner_id.city if rec.partner_id.city else '',
                                        'state_id':country.state if country else False,
                                        'zip':rec.partner_id.zip if rec.partner_id.zip else '',
                                        'country_id':country if country else False,
                                        'pan_no':rec.partner_id.pan_no if rec.partner_id.pan_no else '',
                                        'vat':rec.partner_id.vat if rec.partner_id.vat else '',
                                        'function':rec.partner_id.function if rec.partner_id.function else '',
                                        'phone':rec.partner_id.phone if rec.partner_id.phone else '',
                                        'website':rec.partner_id.website if rec.partner_id.website else '',
                                        # 'title':title.id if title else False,
                                        'lang':rec.partner_id.lang if rec.partner_id.lang else '',
                                    }
                                    customer = env['res.partner'].sudo().create(data_dict)
                            
                            if rec.dest_address_id:
                                dest_address_id = env['res.partner'].sudo().search([('mobile','=',rec.dest_address_id.mobile),('company_id','=',rec.company_id.id)],order='id desc',limit=1)
                                if not dest_address_id:
                                    data_dict = {
                                        'name':rec.dest_address_id.name if rec.dest_address_id else '',
                                        'mobile':rec.dest_address_id.mobile if rec.dest_address_id.mobile else '',
                                        'email':rec.dest_address_id.email if rec.dest_address_id.email else '',
                                        'street':rec.dest_address_id.street if rec.dest_address_id.street else '',
                                        'street2':rec.dest_address_id.street2 if rec.dest_address_id.street2 else '',
                                        'city':rec.dest_address_id.city if rec.dest_address_id.city else '',
                                        'state_id':country if country.state else False,
                                        'zip':rec.dest_address_id.zip if rec.dest_address_id.zip else '',
                                        'country_id':country if country else False,
                                        'pan_no':rec.dest_address_id.pan_no if rec.dest_address_id.pan_no else '',
                                        'vat':rec.dest_address_id.vat if rec.dest_address_id.vat else '',
                                        'function':rec.dest_address_id.function if rec.dest_address_id.function else '',
                                        'phone':rec.dest_address_id.phone if rec.dest_address_id.phone else '',
                                        'website':rec.dest_address_id.website if rec.dest_address_id.website else '',
                                        # 'title':title.id if title else False,
                                        'lang':rec.dest_address_id.lang if rec.dest_address_id.lang else '',
                                    }
                                    dest_addres_id = env['res.partner'].sudo().create(data_dict)
                        

                            if rec.fiscal_position_id:
                                fiscal_position_id = env['account.fiscal.position'].sudo().search([('name','=',rec.fiscal_position_id.name)],order='id desc',limit=1)
                                if not fiscal_position_id:
                                    data_dict = {
                                        'name':rec.fiscal_position_id.name if rec.fiscal_position_id else '',
                                        'active':rec.fiscal_position_id.active,
                                        'company_id':company.id if company else rec.company_id.id,
                                        'currency_id':currency.id if currency else False,
                                        'country_id':country.id if country else False,
                                        'auto_apply':rec.fiscal_position_id.auto_apply,
                                        'vat_required':rec.fiscal_position_id.vat_required,
                                        'zip_from':rec.fiscal_position_id.zip_from,
                                        'zip_to':rec.fiscal_position_id.zip_to,
                                        'note':rec.fiscal_position_id.note,
                                    }
                                    fiscal_position_id = env['account.fiscal.position'].sudo().create(data_dict)
                            
                            # picking type id
                            if rec.picking_type_id:
                                picking_type_id = env['stock.picking.type'].sudo().search([('name','=',rec.picking_type_id.name),('code','=',rec.picking_type_id.code),('active','=',rec.picking_type_id.active)],order='id desc',limit=1)
                                if not picking_type_id:
                                    data_dict = {
                                        'name':rec.picking_type_id.name if rec.picking_type_id else '',
                                        'active':rec.picking_type_id.active if rec.picking_type_id else False,
                                        'color':rec.picking_type_id.color if rec.picking_type_id.color else '',
                                        'sequence':rec.picking_type_id.sequence if rec.picking_type_id else '',
                                        'sequence_id':rec.picking_type_id.sequence_id.id if rec.picking_type_id.sequence_id else False,
                                        'default_location_src_id':rec.picking_type_id.default_location_src_id if rec.picking_type_id.default_location_src_id else False,
                                        'default_location_dest_id':rec.picking_type_id.default_location_dest_id if rec.picking_type_id.default_location_dest_id else False,
                                        'code':rec.picking_type_id.code if rec.picking_type_id else '',
                                        "return_picking_type_id":rec.picking_type_id.return_picking_type_id.id if rec.picking_type_id.return_picking_type_id else False,
                                        "show_entire_packs":rec.picking_type_id.show_entire_packs if rec.picking_type_id.show_entire_packs else False,
                                        "warehouse_id":rec.picking_type_id.warehouse_id.id if rec.picking_type_id.warehouse_id else False,
                                        "use_create_lots":rec.picking_type_id.use_create_lots if rec.picking_type_id.use_create_lots else False,
                                        "use_existing_lots":rec.picking_type_id.use_existing_lots if rec.picking_type_id.use_existing_lots else False,
                                        "show_reserved":rec.picking_type_id.show_reserved if rec.picking_type_id.show_reserved else 'False',
                                                                    }
                                    picking_type_id = env['stock.picking.type'].sudo().create(data_dict)
                            
                            # payment terms
                            if rec.payment_term_id:
                                payment_term_id = env['account.payment.term'].sudo().search([('name','=',rec.payment_term_id.name),('company_id','=',rec.payment_term_id.company_id.id),('active','=',rec.payment_term_id.active)],order='id desc',limit=1)
                                if not payment_term_id:
                                    data_dict = {
                                        'name':rec.payment_term_id.name if rec.payment_term_id else '',
                                        'active':rec.payment_term_id.active if rec.payment_term_id else False,
                                        'note':rec.payment_term_id.note if rec.payment_term_id.note else '',
                                        'company_id':rec.payment_term_id.company_id.id if rec.payment_term_id.company_id else rec.company_id.id,
                                        'sequence':rec.payment_term_id.sequence.id if rec.payment_term_id.sequence else False,
                                        }
                                    payment_term_id = env['account.payment.term'].sudo().create(data_dict)
                            # incoterms
                            if rec.incoterm_id:
                                incoterm_id = env['stock.incoterms'].sudo().search([('name','=',rec.incoterm_id.name),('code','=',rec.incoterm_id.code),('active','=',rec.incoterm_id.active)],order='id desc',limit=1)
                                if not incoterm_id:
                                    data_dict = {
                                        'name':rec.incoterm_id.name if rec.incoterm_id else '',
                                        'active':rec.incoterm_id.active if rec.incoterm_id else False,
                                        'code':rec.incoterm_id.code if rec.incoterm_id.code else '',
                                        }
                                    incoterm_id = env['stock.incoterms'].sudo().create(data_dict)
                            
                            #
                            if rec.requisition_id:
                                requisition_id = env['purchase.requisition'].sudo().search([('name','=',rec.requisition_id.name),('company_id','=',rec.requisition_id.company_id.id)],order='id desc',limit=1)
                                if not requisition_id:
                                    if not rec.requisition_id.type_id:
                                        type_id = False
                                        data_dict = {
                                            'name':rec.requisition_id.type_id.name if rec.requisition_id.type_id.name else '',
                                            'exclusive':rec.requisition_id.type_id.exclusive if rec.requisition_id.type_id.exclusive else '',
                                            'quantity_copy':rec.requisition_id.type_id.quantity_copy if rec.requisition_id.type_id.quantity_copy else '',
                                            'line_copy':rec.requisition_id.type_id.line_copy if rec.requisition_id.type_id.line_copy else '',
                                            }
                                        print("----------------data_dict-----",data_dict)
                                        type_id = env['purchase.requisition.type'].sudo().create(data_dict)
                                        print("type_id=========",type_id)
                                    if not rec.requisition_id.picking_type_id:
                                        if not rec.requisition_id.picking_type_id.sequence_id:
                                            sequence_id = False
                                            data_dict = {
                                                'name':rec.requisition_id.sequence_id.name if rec.requisition_id.sequence_id.name else '',
                                                'exclusive':rec.requisition_id.sequence_id.exclusive if rec.requisition_id.sequence_id.exclusive else '',
                                                'quantity_copy':rec.requisition_id.sequence_id.quantity_copy if rec.requisition_id.sequence_id.quantity_copy else '',
                                                'line_copy':rec.requisition_id.sequence_id.line_copy if rec.requisition_id.sequence_id.line_copy else '',
                                                }
                                            print("----------------data_dict-----",data_dict)
                                            sequence_id = env['purchase.requisition.type'].sudo().create(data_dict)
                                            print("sequence_id=========",sequence_id)
                                        data_dict = {
                                            'name':rec.requisition_id.picking_type_id.name if rec.requisition_id.picking_type_id else '',
                                            'active':rec.requisition_id.picking_type_id.active if rec.requisition_id.picking_type_id else False,
                                            'color':rec.requisition_id.picking_type_id.color if rec.requisition_id.picking_type_id.color else '',
                                            'sequence':rec.requisition_id.picking_type_id.sequence if rec.requisition_id.picking_type_id else '',
                                            'sequence_id':sequence_id.id if sequence_id else rec.requisition_id.picking_type_id.sequence_id.id,
                                            'default_location_src_id':rec.requisition_id.picking_type_id.default_location_src_id if rec.requisition_id.picking_type_id.default_location_src_id else False,
                                            'default_location_dest_id':rec.requisition_id.picking_type_id.default_location_dest_id if rec.requisition_id.picking_type_id.default_location_dest_id else False,
                                            'code':rec.requisition_id.picking_type_id.code if rec.requisition_id.picking_type_id else '',
                                            "return_picking_type_id":rec.requisition_id.picking_type_id.return_picking_type_id.id if rec.requisition_id.picking_type_id.return_picking_type_id else False,
                                            "show_entire_packs":rec.requisition_id.picking_type_id.show_entire_packs if rec.requisition_id.picking_type_id.show_entire_packs else False,
                                            "warehouse_id":rec.requisition_id.picking_type_id.warehouse_id.id if rec.requisition_id.picking_type_id.warehouse_id else False,
                                            "use_create_lots":rec.requisition_id.picking_type_id.use_create_lots if rec.requisition_id.picking_type_id.use_create_lots else False,
                                            "use_existing_lots":rec.requisition_id.picking_type_id.use_existing_lots if rec.requisition_id.picking_type_id.use_existing_lots else False,
                                            "show_reserved":rec.requisition_id.picking_type_id.show_reserved if rec.requisition_id.picking_type_id.show_reserved else 'False',
                                                                        }
                                        picking_type_id = env['stock.picking.type'].sudo().create(data_dict)
                                    
                                    data_dict = {
                                        "message_last_post":rec.requisition_id.message_last_post if rec.requisition_id.message_last_post else '',
                                        "name":rec.requisition_id.name if rec.requisition_id.name else '',
                                        "origin":rec.requisition_id.origin if rec.requisition_id.origin else '',
                                        "vendor_id":rec.requisition_id.vendor_id.id if rec.requisition_id.vendor_id else False,
                                        "type_id":type_id.id if type_id else rec.requisition_id.type_id.id,
                                        "ordering_date":rec.requisition_id.ordering_date if rec.requisition_id.ordering_date else False,
                                        "date_end":rec.requisition_id.date_end if rec.requisition_id.date_end else False,
                                        "schedule_date":rec.requisition_id.schedule_date if rec.requisition_id.schedule_date else False,
                                        "user_id":rec.requisition_id.user_id.id if rec.requisition_id.user_id else False,
                                        "description":rec.requisition_id.description if rec.requisition_id.description else False,
                                        "company_id":rec.requisition_id.company_id.id if rec.requisition_id.company_id else rec.company_id.id,
                                        "warehouse_id":rec.requisition_id.warehouse_id.id if rec.requisition_id.warehouse_id else False,
                                        "state":rec.requisition_id.state if rec.requisition_id.state else 'done',
                                        "account_analytic_id":rec.requisition_id.account_analytic_id.id if rec.requisition_id.account_analytic_id else False,
                                        "picking_type_id":picking_type_id.id if picking_type_id else rec.requisition_id.picking_type_id.id,
                                        }
                                    print("data_dict==req=====",data_dict,rec.requisition_id.type_id,rec.requisition_id)
                                    requisition_id = env['purchase.requisition'].sudo().create(data_dict)
                                    print("requisition_id=====",requisition_id)
                            #-------------------------------------------------------------------------------
                            # "currency_id"                    
                            order_line_list = []
                            data = {
                                "name":rec.name if rec.name else '',
                                "partner_id":customer.id if customer else rec.partner_id.id,
                                "partner_ref":rec.partner_ref if rec.partner_ref else '',
                                "requisition_id":requisition_id.id if requisition_id else rec.requisition_id.id,
                                "currency_id":rec.currency_id.id if rec.currency_id else '',
                                "date_order":rec.date_order if rec.date_order else '',
                                "company_id":company.id if company else rec.company_id.id,
                                "date_planned":rec.date_planned if rec.date_planned else '',
                                "fiscal_position_id":fiscal_position_id.id if fiscal_position_id else rec.fiscal_position_id.id,
                                "payment_term_id":payment_term_id.id if payment_term_id else rec.payment_term_id.id,
                                "incoterm_id":incoterm_id.id if incoterm_id else rec.incoterm_id.id,
                                "picking_type_id":picking_type_id.id if picking_type_id else rec.picking_type_id.id,
                                "date_approve":rec.date_approve if rec.date_approve else False,
                                "invoice_status":rec.invoice_status if rec.invoice_status else '',
                                "message_last_post":rec.message_last_post if rec.message_last_post else '',
                                "activity_date_deadline":rec.activity_date_deadline if rec.activity_date_deadline else False,
                                "origin":rec.origin if rec.origin else '',
                                "dest_address_id":rec.dest_address_id if rec.dest_address_id else False,
                                "state":rec.state if rec.state else '',
                                "notes":rec.notes if rec.notes else '',
                                "invoice_count":rec.invoice_count if rec.invoice_count else 0,
                                "picking_count":rec.picking_count if rec.picking_count else 0,
                                "amount_untaxed":rec.amount_untaxed if rec.amount_untaxed else 0,
                                "amount_tax":rec.amount_tax if rec.amount_tax else 0,   
                                "amount_total":rec.amount_total if rec.amount_total else 0,
                                'child_id_ref':rec.id,
                                'sync_po':rec.sync_po,
                                'child_db':database,
                            }
                            for line_data in rec.order_line:
                                if line_data:
                                    order_line_list.append((0,0,{
                                        'name':line_data.name if line_data.name else '',
                                        'sequence':line_data.sequence if line_data.sequence else '',
                                        'state':line_data.state if line_data.state else '',
                                        'product_id':line_data.product_id.id if line_data.product_id else False,
                                        'date_planned':line_data.date_planned if line_data.date_planned else '',
                                        'company_id':line_data.company_id.id if line_data.company_id else rec.company_id.id,
                                        'product_qty':line_data.product_qty if line_data.product_qty else 0,
                                        'qty_received':line_data.qty_received if line_data.qty_received else 0,
                                        'qty_invoiced':line_data.qty_invoiced if line_data.qty_invoiced else 0,
                                        'product_uom':line_data.product_uom.id if line_data.product_uom else '',
                                        'price_unit':line_data.price_unit if line_data.price_unit else 0,
                                        # 'taxes_id':line_data.product_catalog_id.activity_date_deadline if line_data.product_catalog_id.activity_date_deadline else '',
                                        'price_subtotal':line_data.price_subtotal if line_data.price_subtotal else '',
                                    }))
                            if order_line_list:
                                data['order_line'] = order_line_list
                            print("----data prepared-------",data)
                            """ Insert new records """
                            if data:
                                print("--------------------Create----------------------------")
                                new_recordds = env['purchase.order'].sudo().create(data)
                                if new_recordds:
                                    rec.sudo().write({'sync_po':  True,'state':'done'})
                                print("Created new records-----",new_recordds)
                        else:
                            print("Record already present in parent DB.")
                            
        
        except Exception as e:
            raise ValidationError(e)

