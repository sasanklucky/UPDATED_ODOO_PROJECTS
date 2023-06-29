from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm

class PurchaseOrderLineInheritSync(models.Model):
    _inherit = "purchase.order.line"
    _description = "Purchase Order Line"

    parent_db = fields.Char()
    parent_sale_id_ref = fields.Char(string='Parent Reference')


class PurchaseOrderInheritSync(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    sync_po  = fields.Boolean(string='Sync')
    parent_sale_id_ref = fields.Char(string='Parent Reference')
    child_db = fields.Char()
    parent_db = fields.Char()
    test_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)
    hide_sync  = fields.Boolean(string='Sync', compute='hide_sync_status')

    @api.depends('state')
    def hide_sync_status(self):
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('purchase_order_sync_apis.po_company_type')
        print("child====",child)
        for record in self:
            if child == 'is_child_company' and record.state == 'purchase':
                record.hide_sync = False
            else:
                record.hide_sync = True

    @api.multi
    def call_po_sync(self):
        self.sync_po_to_parent(self)

    @api.depends('state')
    def _compute_css(self):
        for record in self:
            print('state------------called',record.state)
            if record.state == 'done':
                record.test_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                record.test_css = False


    @api.multi
    def unlink(self):
        for record in self:
            param = self.env['ir.config_parameter'].sudo()
            database = param.get_param('purchase_order_sync_apis.parent_db_name')
            self.unlink_so_from_parent(database,record.id)
        return super(PurchaseOrderInheritSync, self).unlink()
    
    # update False value to sync_po if no value is passed
    @api.multi
    def write(self, vals):
        if 'sync_po' not in vals:
            vals['sync_po'] = False
        res =  super(PurchaseOrderInheritSync, self).write(vals)
        return res

    # Delete Sale order from parent if purchase order is deleted from child
    @api.multi
    def unlink_so_from_parent(self,parent_db_name,child_id):
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
                    exist_in_parent = env['sale.order'].sudo().search([('child_po_id_ref','=',str(child_id)),('child_db','=',child_database)])
                    print("exist_in_parent=====",exist_in_parent)
                    if exist_in_parent:
                        exist_in_parent.unlink()
        except Exception as e:
            raise ValidationError(e)



    @api.model
    def _cron_sync_po_to_so_in_parent(self):
        call = self.env['purchase.order'].sync_po_to_parent(False)
    
    @api.model
    def sync_po_to_parent(self,current_po_record):
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
                    po_records = False
                    if current_po_record:
                        po_records = current_po_record
                    else:
                        po_records = self.env['purchase.order'].sudo().search([('sync_po','=',False),('state','=','purchase')],order='id asc')
                        print("==1==",po_records)
                    
                    # looped child po datas
                    for rec in po_records:
                        print("rec=====",rec)

                        # parent record env
                        sale_quotation = env['sale.order'].sudo()
                        exist_in_parent = sale_quotation.search([('child_po_id_ref','=',str(rec.id)),('child_db','=',child_database)],limit=1, order='id desc')
                        if not exist_in_parent:
                            print("purchase order=====",exist_in_parent)
                            customer = False
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
                            print("company===",company,rec.company_id.partner_id.mobile)
                            if rec.company_id.partner_id:
                                customer = env['res.partner'].sudo().search([('mobile','=',rec.company_id.partner_id.mobile),('company_id','=',company.id)],order='id desc',limit=1)
                            
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
                                                                        
                            print("customer===",customer)
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
                            
                            #-------------------------------------------------------------------------------
                            team_id = env['crm.team'].sudo().search([('name','ilike','Sales')],order='id desc',limit=1)
                            pricelist_id = env['product.pricelist'].sudo().search([('name','ilike','Warranty')],order='id desc',limit=1)
                            warehouse = env['stock.warehouse'].sudo().sudo().search([('code','=','VEH')],limit=1)
                            print("---------------------data--------",team_id,pricelist_id,warehouse,rec.company_id.partner_id,company,env.user.company_id,env.user.company_id)                            # "currency_id"
                            order_line_list = []
                            # import pdb
                            # pdb.set_trace()
                            # Sale order data formatted with minimum required fields
                            seq = env['ir.sequence'].sudo().search([('code','=','sale.order'),('active','=',True)],limit=1)
                            code = f"{seq.prefix}" + f"{seq.number_next_actual}"
                            print("seq===================",seq,code)
                            data = {
                                # ///////////////////////////////////////////////
                            'name':code,
                            'partner_id':customer.id if customer else False,
                            'mobile':customer.mobile if customer.mobile else '',
                            'email':customer.email if customer.email else '',
                            'partner_invoice_id':customer.id if customer else False,
                            'partner_shipping_id':customer.id if customer else False,
                            # 'validity_date':rec.validity_date if rec.validity_date else '',
                            'pricelist_id':customer.property_product_pricelist.id if customer.property_product_pricelist else pricelist_id.id,
                            'user_id':customer.user_id.id if customer.user_id else False,
                            'payment_term_id':payment_term_id.id if payment_term_id else False,
                            # 'tag_ids':[(6,0,tag.ids if tag else [])],
                            'warehouse_id':warehouse.id if warehouse else False,
                            'user_id':customer.user_id.id if customer.user_id else False,
                            'picking_policy':'direct',
                            # 'requested_date':rec.requested_date if rec.requested_date else '',
                            # 'commitment_date':rec.commitment_date if rec.commitment_date else '',
                            # 'effective_date':rec.effective_date if rec.effective_date else '',
                            'team_id':customer.team_id.id if customer.team_id else team_id.id,
                            # 'safe_type':rec.safe_type if rec.safe_type else False,
                            # 'client_order_ref':rec.client_order_ref if rec.client_order_ref else '',
                            # 'company_id':company.id if company else False,--------------------------------
                            # 'campaign_id':campaign.id if campaign else False,
                            # 'medium_id':medium.id if medium else False,
                            # 'source_id':source.id if source else False,
                            # 'opportunity_id':opportunity_id.id if opportunity_id else False,
                            # 'origin':rec.origin if rec.origin else '',
                            'date_order':rec.date_order if rec.date_order else '',
                            'fiscal_position_id':fiscal_position_id.id if fiscal_position_id else False,
                            'child_po_id_ref':rec.id,
                            'child_db':child_database,
                            "parent_db":database,
                            'child_po_ref':f"{rec.company_id.name}-{rec.name}",
                            "note":rec.notes,
                                
                            }
                            for line_data in rec.order_line:
                                print("line_data=====",line_data)
                                template_data = env['product.template'].sudo().search([('name','=',line_data.product_id.product_tmpl_id.name)],order='id desc',limit=1)
                                product_data = env['product.product'].sudo().search([('name','=',line_data.product_id.name),('default_code','=',line_data.product_id.default_code)],order='id desc',limit=1)
                                product_uom = env['product.uom'].sudo().search([('name','=',line_data.product_uom.name)],order='id desc',limit=1)
                                catalog_data = env['product.catalog'].sudo().search([('code','=',line_data.product_catalog_id.code)],order='id desc',limit=1)
                               
                                if not template_data:
                                    data_dict = {
                                        'name':line_data.product_id.product_tmpl_id.name if line_data.product_id.product_tmpl_id.name else '',
                                        'sequence':line_data.product_id.product_tmpl_id.sequence if line_data.product_id.product_tmpl_id.sequence else '',
                                        'description':line_data.product_id.product_tmpl_id.description if line_data.product_id.product_tmpl_id.description else '',
                                        'description_purchase':line_data.product_id.product_tmpl_id.description_purchase if line_data.product_id.product_tmpl_id.description_purchase else '',
                                        'description_sale':line_data.product_id.product_tmpl_id.description_sale if line_data.product_id.product_tmpl_id.description_sale else '',
                                        'type':line_data.product_id.product_tmpl_id.type if line_data.product_id.product_tmpl_id.type else '',
                                        'rental':line_data.product_id.product_tmpl_id.rental if line_data.product_id.product_tmpl_id.rental else '',
                                        'list_price':line_data.product_id.product_tmpl_id.list_price if line_data.product_id.product_tmpl_id.list_price else '',
                                        'volume':line_data.product_id.product_tmpl_id.volume if line_data.product_id.product_tmpl_id.volume else '',
                                        'weight':line_data.product_id.product_tmpl_id.weight if line_data.product_id.product_tmpl_id.weight else '',
                                        'sale_ok':line_data.product_id.product_tmpl_id.sale_ok if line_data.product_id.product_tmpl_id.sale_ok else '',
                                        'purchase_ok':line_data.product_id.product_tmpl_id.purchase_ok if line_data.product_id.product_tmpl_id.purchase_ok else '',
                                        'company_id':company.id if company else False,
                                        'active':line_data.product_id.product_tmpl_id.active if line_data.product_id.product_tmpl_id.active else '',
                                        'default_code':line_data.product_id.product_tmpl_id.default_code if line_data.product_id.product_tmpl_id.default_code else '',
                                        'activity_date_deadline':line_data.product_id.product_tmpl_id.activity_date_deadline if line_data.product_id.product_tmpl_id.activity_date_deadline else '',
                                        'sale_delay':line_data.product_id.product_tmpl_id.sale_delay if line_data.product_id.product_tmpl_id.sale_delay else '',
                                        'tracking':line_data.product_id.product_tmpl_id.tracking if line_data.product_id.product_tmpl_id.tracking else '',
                                        'list_price':line_data.product_id.product_tmpl_id.list_price if line_data.product_id.product_tmpl_id.list_price else 0,

                                    }
                                    template_data = env['product.template'].sudo().create(data_dict)

                                if not product_data:
                                    data_dict = {
                                        'default_code':line_data.product_id.default_code if line_data.product_id.default_code else '',
                                        'active':line_data.product_id.active if line_data.product_id.active else '',
                                        'product_tmpl_id':line_data.product_id.product_tmpl_id.id if line_data.product_id.product_tmpl_id else False,
                                        'barcode':line_data.product_id.barcode if line_data.product_id.barcode else False,
                                        'volume':line_data.product_id.volume if line_data.product_id.volume else '',
                                        'weight':line_data.product_id.weight if line_data.product_id.weight else '',
                                        'activity_date_deadline':line_data.product_id.activity_date_deadline if line_data.product_id.activity_date_deadline else '',
                                    }
                                    product_data = env['product.product'].sudo().create(data_dict)
                                
                                if not product_uom and line_data.product_uom.name:
                                    data_dict = {
                                        'name':line_data.product_uom.name if line_data.product_uom.name else '',
                                        'factor':line_data.product_uom.factor.id if line_data.product_uom.factor else False,
                                        'rounding':line_data.product_uom.rounding if line_data.product_uom.rounding else '',
                                        'active':line_data.product_uom.active if line_data.product_uom.active else '',
                                        'uom_type':line_data.product_uom.uom_type if line_data.product_uom.uom_type else '',
                                    }
                                    product_uom = env['product.uom'].sudo().create(data_dict)

                                order_line_list.append((0,0,{
                                    'name':line_data.name,
                                    'product_catalog_id':catalog_data.id if catalog_data else False,
                                    'product_template_id':template_data.id if template_data else False,
                                    'product_id':product_data.id if product_data else line_data.product_id.id,
                                    'order_id':rec.id,
                                    'product_uom_qty':line_data.product_qty,
                                    'product_uom':product_uom.id if product_uom else line_data.product_uom.id,
                                    'price_unit':line_data.price_unit,
                                    'tax_id':[(6, 0, line_data.taxes_id.ids if line_data.taxes_id else [])],
                                    'child_po_id_ref':line_data.id,
                                    'child_db':child_database
                                }))
                            if order_line_list:
                                data['order_line'] = order_line_list
                            print("----data prepared-------",data)
                            """ Insert new records """
                            if data:
                                print("--------------------Create----------------------------")
                                new_recordds = env['sale.order'].sudo().create(data)
                                seq.number_next_actual = seq.number_next_actual+1
                                if new_recordds:
                                    rec.sudo().write({'sync_po':  True,'state':'done'})
                                print("Created new records-----",new_recordds)
                        else:
                            print("Record already present in parent DB.")
                            
        
        except Exception as e:
            raise ValidationError(e)

