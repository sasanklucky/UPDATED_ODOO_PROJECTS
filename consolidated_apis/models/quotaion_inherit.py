from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"
    _description = "Sale Order"

    sync_pipeline  = fields.Boolean(string='Sync')
    child_id_ref = fields.Char(string='Child Reference')
    # child_partner_ref = fields.Many2one('res.partner', string='Child Reference')
    child_db = fields.Char()

    @api.multi
    def unlink(self):
        for record in self:
            param = self.env['ir.config_parameter'].sudo()
            database = param.get_param('consolidated_apis.db_name')
            self.unlink_quotation_from_parent(database,record.id)
        return super(SaleOrderInherit, self).unlink()
    
    @api.multi
    def write(self, vals):
        if 'sync_pipeline' not in vals:
            vals['sync_pipeline'] = False
        res =  super(SaleOrderInherit, self).write(vals)
        return res


    @api.multi
    def unlink_quotation_from_parent(self,db_name,child_id):
        try:
            param = self.env['ir.config_parameter'].sudo()
            child = param.get_param('consolidated_apis.company_type')
            check_quotation_sync = param.get_param('consolidated_apis.enable_quotation_sync')
            if child == 'is_child_company' and check_quotation_sync == 'yes':
                # print("database=====",db_name)
                db = sql_db.db_connect(f"{db_name}")
                # child_database = param.get_param('consolidated_apis.child_db_name')
                child_database = self._cr.dbname
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    exist_in_parent = env['sale.order'].sudo().search([('child_id_ref','=',str(child_id)),('child_db','=',child_database)])
                    # print("exist_in_parent=====",exist_in_parent)
                    if exist_in_parent:
                        exist_in_parent.unlink()
        except Exception as e:
            raise ValidationError(e)


    @api.model
    def _cron_update_quotation_to_parent(self):
        """ connect to parent db set up in general settings """
        try:
            param = self.env['ir.config_parameter'].sudo()
            child = param.get_param('consolidated_apis.company_type')
            check_pipeline_sync = param.get_param('consolidated_apis.enable_pipeline_sync')
            # print("child---",child,check_pipeline_sync)
            if child == 'is_child_company' and check_pipeline_sync == 'yes':
                database = param.get_param('consolidated_apis.db_name')
                # print("database=====",database)
                db = sql_db.db_connect(f"{database}")
                # child_database = param.get_param('consolidated_apis.child_db_name')
                child_database = self._cr.dbname
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    orders = self.env['sale.order'].sudo().search([('sync_pipeline','=',False)],order='id asc')
                    # print("==1==",orders)
                    # orders = env['sale.order'].sudo().search([],order='id asc')
                    # print("==2==",orders)
                    # return
                    for rec in orders:
                        # print("rec=====",rec)
                        # import pdb
                        # pdb.set_trace()
                        quotation = env['sale.order'].sudo()
                        exist_in_parent = quotation.search([('child_id_ref','=',str(rec.id)),('child_db','=',child_database)],limit=1, order='id desc')

                        # print("sale_order=====",exist_in_parent)
                        customer = False
                        user= False
                        payment_term_id= False
                        pricelist_id= False
                        title= False
                        campaign= False
                        medium= False
                        source= False
                        tag= False
                        # # if exist_in_parent:
                        user_partner_created = False
                        new_partner_id = False
                        # print("rec.user_id.login===",rec.user_id.login)
                        company = env['res.company'].sudo().search([('dealer_code','=',rec.company_id.dealer_code)],order='id desc',limit=1)
                        user = env['res.users'].sudo().search([('login','=',rec.user_id.login)])
                        if not user and rec.user_id:
                            # print("rec.user_id.company_id.name=====",rec.user_id.company_id.name)
                            # company = env['res.company'].sudo().search([('name','=',rec.user_id.company_id.name),('company_id','=',company.id)],order='id desc',limit=1)
                            # print("====company===",company,self.env.user)
                            data_dict = {
                                'name':rec.user_id.name if rec.user_id.name else '',
                                'mobile':rec.user_id.mobile if rec.user_id.mobile else '',
                                'phone':rec.user_id.phone if rec.user_id.phone else '',
                                'login':rec.user_id.login if rec.user_id.login else '',
                                'company_id':company.id if company else False,
                                'salesperson':True if rec.user_id.salesperson else False,
                                'company_ids': [(6, 0, company.ids if company else [])],
                            }
                            # print("====data_dict====",data_dict)
                            user = env['res.users'].sudo().create(data_dict)
                            if user:
                                user_partner_created = True
                        # print("===user_partner_created===",user_partner_created)
                        if user_partner_created:
                            if user.login == rec.user_id.login:
                                new_partner_id = user.partner_id
                        
                        if rec.partner_id:
                            customer = env['res.partner'].sudo().search([('mobile','=',rec.partner_id.mobile),('company_id','=',company.id)],order='id desc',limit=1)
                        # # if new_partner_id:
                        # #     customer = new_partner_id
                        
                        # title = env['res.partner.title'].sudo().search([('name','=',rec.title.name)],order='id desc',limit=1)
                        # if not title and rec.title:
                        #     data_dict = {
                        #         'name':rec.title.name if rec.title.name else '',
                        #         'shortcut':rec.title.shortcut if rec.title.shortcut else '',
                        #     }
                        #     title = env['res.partner.title'].sudo().create(data_dict)
                        
                        country = env['res.country'].sudo().search([('name','=',rec.partner_id.country_id.name)],order='id desc',limit=1)
                        if not country and rec.partner_id.country_id:
                            data_dict = {
                                'name':rec.country_id.name if rec.country_id.name else '',
                                'code':rec.country_id.code if rec.country_id.code else '',
                                'address_format':rec.country_id.address_format if rec.country_id.address_format else '',
                                'address_view_id':rec.country_id.address_view_id.id if rec.country_id.address_view_id else False,
                                'currency_id':rec.country_id.currency_id.id if rec.country_id.currency_id else False,
                                'phone_code':rec.country_id.phone_code if rec.country_id.phone_code else '',
                                'name_position':rec.country_id.name_position if rec.country_id.name_position else '',
                                'vat_label':rec.country_id.vat_label if rec.country_id.vat_label else '',
                            }
                            country = env['res.country'].sudo().create(data_dict)
                        currency = country.currency_id

                        state = env['res.country.state'].sudo().search([('name','=',rec.partner_id.state_id.name)],order='id desc',limit=1)
                        if not state and rec.partner_id.state_id:
                            data_dict = {
                                'name':rec.state_id.name if rec.state_id.name else '',
                                'code':rec.state_id.code if rec.state_id.code else '',
                                'country_id':country.id if country else False,
                            }
                            state = env['res.country.state'].sudo().create(data_dict)

                        if not customer and rec.partner_id:
                            data_dict = {
                                'name':rec.partner_id.name if rec.partner_id else '',
                                'mobile':rec.partner_id.mobile if rec.partner_id.mobile else '',
                                'email':rec.partner_id.email if rec.partner_id.email else '',
                                'street':rec.partner_id.street if rec.partner_id.street else '',
                                'street2':rec.partner_id.street2 if rec.partner_id.street2 else '',
                                'city':rec.partner_id.city if rec.partner_id.city else '',
                                'state_id':state if state else False,
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
                    
                        tag = env['crm.lead.tag'].sudo().search([('name','in',rec.tag_ids.mapped('name'))],order='id desc',limit=1)
                        if not tag and rec.tag_ids:
                            tag_list = []
                            for tag_data in rec.tag_ids:
                                tag_list.append({
                                    'name':tag_data.name if tag_data.name else '',
                                    'color':tag_data.color if tag_data.color else '',
                                })
                            if tag_list:
                                tag = env['crm.lead.tag'].sudo().create(tag_list)
                    


                        campaign = env['utm.campaign'].sudo().search([('name','=',rec.campaign_id.name)],order='id desc',limit=1)
                        if not campaign and rec.campaign_id:
                            data_dict = {
                                'name':rec.campaign_id.name,
                            }
                            campaign = env['utm.campaign'].sudo().create(data_dict)
                    
                        medium = env['utm.medium'].sudo().search([('name','=',rec.medium_id.name)],order='id desc',limit=1)
                        if not medium and rec.medium_id:
                            data_dict = {
                                'name':rec.medium_id.name,
                            }
                            medium =env['utm.medium'].sudo().create(data_dict)
                    
                        source = env['utm.source'].sudo().search([('name','=',rec.source_id.name)],order='id desc',limit=1)
                        if not source and rec.source_id:
                            data_dict = {
                                'name':rec.source_id.name,
                            }
                            source = env['utm.source'].sudo().create(data_dict)
                        
                        pricelist_id = env['product.pricelist'].sudo().search([('name','=',rec.pricelist_id.name)],order='id desc',limit=1)
                        if not pricelist_id and rec.pricelist_id:
                            data_dict = {
                                'name':rec.pricelist_id.name if rec.pricelist_id else '',
                                'active':True,
                                'company_id':company.id if company else False,
                                'currency_id':currency.id if currency else False,
                            }
                            pricelist_id = env['product.pricelist'].sudo().create(data_dict)

                        payment_term_id = env['account.payment.term'].sudo().search([('name','=',rec.payment_term_id.name)],order='id desc',limit=1)
                        if not payment_term_id and rec.payment_term_id:
                            data_dict = {
                                'name':rec.payment_term_id.name if rec.payment_term_id else '',
                                'active':True,
                                'company_id':company.id if company else False,
                                'note':rec.note if rec.note else False,
                                'sequence':rec.sequence if rec.sequence else False,
                            }
                            payment_term_id = env['account.payment.term'].sudo().create(data_dict)
                        
                        fiscal_position_id = env['account.fiscal.position'].sudo().search([('name','=',rec.fiscal_position_id.name)],order='id desc',limit=1)
                        if not fiscal_position_id and rec.fiscal_position_id:
                            data_dict = {
                                'name':rec.fiscal_position_id.name if rec.fiscal_position_id else '',
                                'active':rec.fiscal_position_id.active,
                                'company_id':company.id if company else False,
                                'currency_id':currency.id if currency else False,
                                'country_id':country.id if country else False,
                                'auto_apply':rec.fiscal_position_id.auto_apply,
                                'vat_required':rec.fiscal_position_id.vat_required,
                                'zip_from':rec.fiscal_position_id.zip_from,
                                'zip_to':rec.fiscal_position_id.zip_to,
                                'note':rec.fiscal_position_id.note,
                            }
                            fiscal_position_id = env['account.fiscal.position'].sudo().create(data_dict)
                        
                        team_id = env['crm.team'].sudo().search([('name','=',rec.team_id.name)],order='id desc',limit=1)
                        if not team_id and rec.team_id:
                            data_dict = {
                                'name':rec.team_id.name,
                                'active':rec.team_id.active,
                                'company_id':company.id if company else False,
                                'user_id':user.id if user else False,
                                'reply_to':rec.team_id.reply_to,
                                'color':rec.team_id.color,
                                'team_type':rec.team_id.team_type,
                                'dashboard_graph_model':rec.team_id.dashboard_graph_model,
                                'dashboard_graph_group':rec.team_id.dashboard_graph_group,
                                'dashboard_graph_period':rec.team_id.dashboard_graph_period,
                                'use_quotations':rec.team_id.use_quotations,
                                'use_invoices':rec.team_id.use_invoices,
                                # 'invoice_target':rec.team_id.invoice_target,
                                # 'user_leads':rec.team_id.user_leads,
                                # 'user_opportunities':rec.team_id.user_opportunities,
                                'dashboard_graph_group_pipeline':rec.team_id.dashboard_graph_group_pipeline,
                            }
                            team_id = env['crm.team'].sudo().create(data_dict)
                        
                        warehouse = env['stock.warehouse'].sudo().search([('name','=',rec.warehouse_id.name),('code','=',rec.warehouse_id.code)],order='id desc',limit=1)
                        if not warehouse and rec.warehouse_id:
                            partner_id =  env['res.partner'].sudo().search([('name','=',rec.warehouse_id.partner_id.name)],order='id desc',limit=1)
                            data_dict = {
                                'name':rec.warehouse_id.name,
                                'active':rec.warehouse_id.active,
                                'company_id':company.id if company else False,
                                'partner_id':partner_id.id if partner_id else False,
                                'code':rec.warehouse_id.reply_to,
                                'reception_steps':rec.warehouse_id.color,
                                'delivery_steps':rec.warehouse_id.team_type,
                            }
                            warehouse = env['stock.warehouse'].sudo().create(data_dict)
                        
                        opportunity_id = env['crm.lead'].sudo().search([('child_id_ref','=',rec.opportunity_id.id)],order='id desc',limit=1) if rec.opportunity_id else False
                        order_line_list = []
                        data = {
                            'name':rec.name,
                            'partner_id':customer.id if customer else False,
                            'mobile':rec.mobile if rec.mobile else '',
                            'email':rec.email if rec.email else '',
                            'partner_invoice_id':customer.id if customer else False,
                            'partner_shipping_id':customer.id if customer else False,
                            'validity_date':rec.validity_date if rec.validity_date else '',
                            'pricelist_id':pricelist_id.id if pricelist_id else False,
                            'user_id':user.id if user else False,
                            'payment_term_id':payment_term_id.id if payment_term_id else False,
                            'tag_ids':[(6,0,tag.ids if tag else [])],
                            'warehouse_id':warehouse.id if warehouse else False,
                            'picking_policy':rec.picking_policy if rec.picking_policy else '',
                            'requested_date':rec.requested_date if rec.requested_date else '',
                            'commitment_date':rec.commitment_date if rec.commitment_date else '',
                            'effective_date':rec.effective_date if rec.effective_date else '',
                            'team_id':team_id.id if team_id else '',
                            # 'safe_type':rec.safe_type if rec.safe_type else False,
                            'client_order_ref':rec.client_order_ref if rec.client_order_ref else '',
                            'company_id':company.id if company else False,
                            'campaign_id':campaign.id if campaign else False,
                            'medium_id':medium.id if medium else False,
                            'source_id':source.id if source else False,
                            'opportunity_id':opportunity_id.id if opportunity_id else False,
                            'origin':rec.origin if rec.origin else '',
                            'date_order':rec.date_order if rec.date_order else '',
                            'fiscal_position_id':fiscal_position_id.id if fiscal_position_id else False,
                            'child_id_ref':rec.id,
                            'state':rec.state,
                            'child_db':child_database,
                            
                        }
                        for line_data in rec.order_line:
                            if line_data:
                                template_data = env['product.template'].sudo().search([('name','=',line_data.product_template_id.name)],order='id desc',limit=1)
                                product_data = env['product.product'].sudo().search([('name','=',line_data.product_id.name),('default_code','=',line_data.product_id.default_code)],order='id desc',limit=1)
                                product_uom = env['product.uom'].sudo().search([('name','=',line_data.product_uom.name)],order='id desc',limit=1)
                                catalog_data = env['product.catalog'].sudo().search([('name','=',line_data.product_catalog_id.name)],order='id desc',limit=1)
                                if not catalog_data:
                                    data_dict = {
                                        'name':line_data.product_catalog_id.name if line_data.product_catalog_id else '',
                                    }
                                    catalog = env['product.catalog'].sudo().create(data_dict)
                                
                                if not template_data and line_data.product_template_id.name:
                                    # categ_id =  env['product.template'].sudo().search([('name','=',line_data.product_catalog_id.categ_id.name)],order='id desc',limit=1)
                                    # uom_id = env['product.template'].sudo().search([('name','=',line_data.product_catalog_id.uom_id.name)],order='id desc',limit=1)
                                    # uom_po_id = env['product.template'].sudo().search([('name','=',line_data.product_catalog_id.uom_po_id.name)],order='id desc',limit=1)
                                    data_dict = {
                                        'name':line_data.product_catalog_id.name if line_data.product_catalog_id.name else '',
                                        'sequence':line_data.product_catalog_id.sequence if line_data.product_catalog_id.sequence else '',
                                        'description':line_data.product_catalog_id.description if line_data.product_catalog_id.description else '',
                                        'description_purchase':line_data.product_catalog_id.description_purchase if line_data.product_catalog_id.description_purchase else '',
                                        'description_sale':line_data.product_catalog_id.description_sale if line_data.product_catalog_id.description_sale else '',
                                        'type':line_data.product_catalog_id.type if line_data.product_catalog_id.type else '',
                                        'rental':line_data.product_catalog_id.rental if line_data.product_catalog_id.rental else '',
                                        # 'categ_id':categ_id.id if categ_id else False,
                                        'list_price':line_data.product_catalog_id.list_price if line_data.product_catalog_id.list_price else '',
                                        'volume':line_data.product_catalog_id.volume if line_data.product_catalog_id.volume else '',
                                        'weight':line_data.product_catalog_id.weight if line_data.product_catalog_id.weight else '',
                                        'sale_ok':line_data.product_catalog_id.sale_ok if line_data.product_catalog_id.sale_ok else '',
                                        'purchase_ok':line_data.product_catalog_id.purchase_ok if line_data.product_catalog_id.purchase_ok else '',
                                        # 'uom_id':uom_id.id if uom_id else False,
                                        # 'uom_po_id':uom_po_id.id if uom_po_id else False,   
                                        'company_id':company.id if company else False,
                                        'active':line_data.product_catalog_id.active if line_data.product_catalog_id.active else '',
                                        'default_code':line_data.product_catalog_id.default_code if line_data.product_catalog_id.default_code else '',
                                        'activity_date_deadline':line_data.product_catalog_id.activity_date_deadline if line_data.product_catalog_id.activity_date_deadline else '',
                                        # 'responsible_id':line_data.product_catalog_id.responsible_id.id if line_data.product_catalog_id.responsible_id else False,
                                        'sale_delay':line_data.product_catalog_id.sale_delay if line_data.product_catalog_id.sale_delay else '',
                                        'tracking':line_data.product_catalog_id.tracking if line_data.product_catalog_id.tracking else '',
                                        'list_price':line_data.product_catalog_id.list_price if line_data.product_catalog_id.list_price else 0,

                                    }
                                    template_data = env['product.template'].sudo().create(data_dict)

                                if not product_data and line_data.product_id.name:
                                    data_dict = {
                                        'default_code':line_data.product_id.default_code if line_data.product_id.default_code else '',
                                        'active':line_data.product_id.active if line_data.product_id.active else '',
                                        'product_tmpl_id':line_data.product_id.product_tmpl_id.id if line_data.product_id.product_tmpl_id else False,
                                        'barcode':line_data.product_id.barcode if line_data.product_id.barcode else False,
                                        'volume':line_data.product_id.volume if line_data.product_id.volume else '',
                                        'weight':line_data.product_id.weight if line_data.product_id.weight else '',
                                        'activity_date_deadline':line_data.product_id.activity_date_deadline if line_data.product_id.activity_date_deadline else '',
                                        # 'lot_id':line_data.product_id.lot_id.id if line_data.product_id.lot_id else False,
                                    }
                                    product_data = env['product.product'].sudo().create(data_dict)
                                
                                if not product_uom and line_data.product_uom.name:
                                    # category_id = env['product.product'].sudo().search([('name','=',line_data.product_uom.name),('default_code','=',line_data.product_id.default_code)],order='id desc',limit=1)
                                    # if not category_id and line_data.product_uom.name and line_data.product_id.default_code:
                                    #     data_dict = {
                                    #         'name':line_data.product_uom.name if line_data.product_uom.name else '',
                                    #     }
                                    #     category_id = env['product.product'].sudo().create(data_dict)
                                    data_dict = {
                                        'name':line_data.product_uom.name if line_data.product_uom.name else '',
                                        # 'category_id':category_id.id if category_id else False,
                                        'factor':line_data.product_id.product_tmpl_id.id if line_data.product_id.product_tmpl_id else False,
                                        'rounding':line_data.product_id.barcode if line_data.product_id.barcode else '',
                                        'active':line_data.product_id.volume if line_data.product_id.volume else '',
                                        'uom_type':line_data.product_id.weight if line_data.product_id.weight else '',
                                    }
                                    product_uom = env['product.uom'].sudo().create(data_dict)

                                order_line_list.append((0,0,{
                                    'name':line_data.name,
                                    'product_catalog_id':catalog_data.id if catalog_data else catalog_data,
                                    'product_template_id':template_data.id if template_data else template_data,
                                    'product_id':product_data.id if product_data else False,
                                    'order_id':rec.id,
                                    'product_uom_qty':line_data.product_uom_qty,
                                    'product_uom':product_uom.id if product_uom else product_uom,
                                    'price_unit':line_data.price_unit,
                                    'tax_id':[(6, 0, line_data.tax_id.ids if line_data.tax_id else [])],
                                    'discount':line_data.discount,
                                }))
                        if order_line_list:
                            data['order_line'] = order_line_list
                        # print("----data prepared-------",data,quotation)
                        if exist_in_parent:
                            """ Update existing records after unlinking the vehcile lines"""
                            # line_data.unlink()
                            if data:
                                exist_in_parent.order_line.unlink()
                                result = exist_in_parent.sudo().write(data)
                                # print("-------------------update----------------------------")
                                if result:
                                    rec.sudo().write({'sync_pipeline':  True})
                            # print("update the record------")
                        else:
                            """ Insert new records """
                            # print("--------------------Create----------------------------")
                            if data:
                                new_recordds = env['sale.order'].sudo().create(data)
                                if new_recordds:
                                    rec.sudo().write({'sync_pipeline':  True})
                                # print("insert the records-----",new_recordds)
        
        except Exception as e:
            raise ValidationError(e)

