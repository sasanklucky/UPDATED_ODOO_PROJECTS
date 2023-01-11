from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm



class CrmLeadIherit(models.Model):
    _inherit = "crm.lead"
    _description = "CRM Lead"

    sync_pipeline  = fields.Boolean(string='Sync',default='False')
    child_id_ref = fields.Char(string='Child Reference')
    # child_partner_ref = fields.Many2one('res.partner', string='Child Reference')
    child_db = fields.Char()

    @api.multi
    def unlink(self):
        param = self.env['ir.config_parameter'].sudo()
        database = param.get_param('consolidated_apis.db_name')
        self.unlink_pipeline_from_parent(database,self.id)
        return super(CrmLeadIherit, self).unlink()

    @api.multi
    def write(self, vals):
        if 'sync_pipeline' not in vals:
            vals['sync_pipeline'] = False
        res =  super(CrmLeadIherit, self).write(vals)
        return res

    @api.multi
    def unlink_pipeline_from_parent(self,db_name,child_id):
        try:
            param = self.env['ir.config_parameter'].sudo()
            child = param.get_param('consolidated_apis.company_type')
            check_quotation_sync = param.get_param('consolidated_apis.enable_quotation_sync')
            if child == 'is_child_company' and check_quotation_sync == 'yes':
                print("database=====",db_name)
                db = sql_db.db_connect(f"{db_name}")
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    exist_in_parent = env['crm.lead'].sudo().search([('child_id_ref','=',str(child_id))])
                    print("exist_in_parent=====",exist_in_parent)
                    if exist_in_parent:
                        exist_in_parent.unlink()
        except Exception as e:
            raise ValidationError(e)


    @api.model
    def _cron_update_pipe_line_to_parent(self):
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
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    pipelines = self.env['crm.lead'].sudo().search([('sync_pipeline','=',False)],order='id asc')
                    # print("===",pipelines)
                    for rec in pipelines:
                        # print("rec=====",rec)
                        # import pdb
                        # pdb.set_trace()
                        lead = env['crm.lead'].sudo()
                        exist_in_parent = lead.search([('child_id_ref','=',str(rec.id))],limit=1, order='id desc')
                        # print("sale_order=====",exist_in_parent)
                        customer = False
                        user= False
                        state= False
                        country= False
                        title= False
                        campaign= False
                        medium= False
                        source= False
                        tag= False
                        tag= False
                        # if exist_in_parent:
                        user_partner_created = False
                        new_partner_id = False
                        # print("rec.user_id.login===",rec.user_id.login)
                        company = env['res.company'].sudo().search([('dealer_code','=',rec.company_id.dealer_code)],order='id desc',limit=1)
                        
                        user = env['res.users'].sudo().search([('login','=',rec.user_id.login)])
                        if not user and rec.user_id:
                            # print("company.name=====",company.name)
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

                        customer = env['res.partner'].sudo().search([('mobile','=',rec.partner_id.mobile),('company_id','=',company.id)],order='id desc',limit=1)
                        # if new_partner_id:
                        #     customer = new_partner_id
                        
                        title = env['res.partner.title'].sudo().search([('name','=',rec.title.name)],order='id desc',limit=1)
                        if not title and rec.title:
                            data_dict = {
                                'name':rec.title.name if rec.title.name else '',
                                'shortcut':rec.title.shortcut if rec.title.shortcut else '',
                            }
                            title = env['res.partner.title'].sudo().create(data_dict)
                        
                        country = env['res.country'].sudo().search([('name','=',rec.country_id.name)],order='id desc',limit=1)
                        if not country and rec.country_id:
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
                    
                        state = env['res.country.state'].sudo().search([('name','=',rec.state_id.name)],limit=1,order='id desc')
                        if not state and rec.state_id:
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
                                'state_id':state.id if state else False,
                                'zip':rec.partner_id.zip if rec.partner_id.zip else '',
                                'country_id':country.id if country else False,
                                'pan_no':rec.partner_id.pan_no if rec.partner_id.pan_no else '',
                                'vat':rec.partner_id.vat if rec.partner_id.vat else '',
                                'function':rec.partner_id.function if rec.partner_id.function else '',
                                'phone':rec.partner_id.phone if rec.partner_id.phone else '',
                                'website':rec.partner_id.website if rec.partner_id.website else '',
                                'title':title.id if title else False,
                                'lang':rec.partner_id.lang if rec.partner_id.lang else '',
                                'company_id':company.id if company else False,
                            }
                            # print("=====data_dict===",data_dict)
                            customer = env['res.partner'].sudo().create(data_dict)
                            # print("====customer====",customer.company_id)
                    
                        tag = env['crm.lead.tag'].sudo().search([('name','in',rec.tag_ids.mapped('name'))],order='id desc',limit=1)
                        if not tag and rec.tag_ids:
                            tag_list = []
                            for rec in rec.tag_ids:
                                tag_list.append({
                                    'name':rec.name if rec.name else '',
                                    'color':rec.color if rec.color else '',
                                })
                            if tag_list:
                                tag = env['crm.lead.tag'].sudo().create(tag_list)
                    


                        campaign = env['utm.campaign'].sudo().search([('name','=',rec.campaign_id.name)],order='id desc',limit=1)
                        if not campaign and rec.campaign_id.name:
                            data_dict = {
                                'name':rec.campaign_id.name,
                            }
                            campaign = env['utm.campaign'].sudo().create(data_dict)
                    
                        medium = env['utm.medium'].sudo().search([('name','=',rec.medium_id.name)],order='id desc',limit=1)
                        if not medium and rec.medium_id.name:
                            data_dict = {
                                'name':rec.medium_id.name,
                            }
                            medium =env['utm.medium'].sudo().create(data_dict)
                    
                        source = env['utm.source'].sudo().search([('name','=',rec.source_id.name)],order='id desc',limit=1)
                        if not source and rec.source_id.name:
                            data_dict = {
                                'name':rec.source_id.name,
                            }
                            source = env['utm.source'].sudo().create(data_dict)
                        
                        stage_id = env['crm.stage'].sudo().search([('name','=',rec.stage_id.name)],order='id desc',limit=1)
                        if not stage_id and rec.stage_id.name:
                            data_dict = {
                                'name':rec.stage_id.name,
                            }
                            stage_id = env['crm.stage'].sudo().create(data_dict)
                    
                        vehicle_line_list = []
                        data = {
                            'planned_revenue':rec.planned_revenue if rec.planned_revenue else '',
                            'probability':rec.probability if rec.probability else '',
                            'company_type':rec.company_type if rec.company_type else '',
                            'partner_id':customer.id if customer else False,
                            'email_from':rec.email_from if rec.email_from else '',
                            'mobile':rec.mobile if rec.mobile else '',
                            'priority':rec.priority if rec.priority else '',
                            'date_closed':rec.date_closed if rec.date_closed else '',
                            'user_id':user.id if user else False,
                            'tag_ids':[(6,0,tag.ids if tag else [])],
                            'description':rec.description if rec.description else '',
                            'partner_name':rec.partner_name if rec.partner_name else '',
                            'street':rec.street if rec.street else '',
                            'street2':rec.street2 if rec.street2 else '',
                            'city':rec.city if rec.city else '',
                            'state_id':state.id if state else False,
                            'zip':rec.zip if rec.zip else '',
                            'country_id':country.id if country else False,
                            'website':rec.website if rec.website else '',
                            'contact_name':rec.contact_name if rec.contact_name else '',
                            'title':title.id if title else False,
                            'phone':rec.phone if rec.phone else '',
                            'function':rec.function if rec.function else '',
                            'opt_out':rec.opt_out if rec.opt_out else '',
                            'campaign_id':campaign.id if campaign else False,
                            'medium_id':medium.id if medium else False,
                            'source_id':source.id if source else False,
                            'day_open':rec.day_open if rec.day_open else '',
                            'day_close':rec.day_close if rec.day_close else '',
                            'referred':rec.referred if rec.referred else '',
                            'type':rec.type if rec.type else '',
                            'company_id':company.id if company else False,
                            'child_id_ref':rec.id,
                            'stage_id':stage_id.id,
                            'date_deadline':rec.date_deadline,
                        }
                        for line_data in rec.vehicle_line:
                            if line_data:
                                template_data = env['product.template'].sudo().search([('name','=',line_data.product_template_id.name),('default_code','=',line_data.product_template_id.default_code)],order='id desc',limit=1)
                                product_data = env['product.product'].sudo().search([('name','=',line_data.product_id.name),('default_code','=',line_data.product_id.default_code)],order='id desc',limit=1)
                                catalog_data = env['product.catalog'].sudo().search([('name','=',line_data.product_catalog_id.name)],order='id desc',limit=1)
                                if not catalog_data and line_data.product_catalog_id.name:
                                    data_dict = {
                                        'name':line_data.product_catalog_id.name if line_data.product_catalog_id else '',
                                    }
                                    catalog_data = env['product.catalog'].sudo().create(data_dict)
                                # categ_id =  env['product.template'].sudo().search([('name','=',line_data.product_catalog_id.name)],order='id desc',limit=1)
                                # uom_id = env['product.template'].sudo().search([('name','=',line_data.product_catalog_id.uom_id.name)],order='id desc',limit=1)
                                # uom_po_id = env['product.template'].sudo().search([('name','=',line_data.product_catalog_id.uom_po_id.name)],order='id desc',limit=1)
                                if not template_data and line_data.product_template_id.name:
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
                                        'responsible_id':line_data.product_catalog_id.responsible_id.id if line_data.product_catalog_id.responsible_id else False,
                                        'sale_delay':line_data.product_catalog_id.sale_delay if line_data.product_catalog_id.sale_delay else '',
                                        'tracking':line_data.product_catalog_id.tracking if line_data.product_catalog_id.tracking else '',
                                    }
                                    template_data = env['product.template'].sudo().create(data_dict)


                                if not product_data and line_data.product_id.name:
                                    data_dict = {
                                        'default_code':line_data.product_id.default_code if line_data.product_id.default_code else '',
                                        'active':line_data.product_id.active if line_data.product_id.active else '',
                                        'product_tmpl_id':line_data.product_id.product_tmpl_id.id if line_data.product_id.product_tmpl_id else False,
                                        'barcode':line_data.product_id.barcode if line_data.product_id.barcode else '',
                                        'volume':line_data.product_id.volume if line_data.product_id.volume else '',
                                        'weight':line_data.product_id.weight if line_data.product_id.weight else '',
                                        'activity_date_deadline':line_data.product_id.activity_date_deadline if line_data.product_id.activity_date_deadline else '',
                                        'lot_id':line_data.product_id.lot_id.id if line_data.product_id.lot_id else False,
                                    }
                                    product_data = env['product.product'].sudo().create(data_dict)
                            vehicle_line_list.append((0,0,{
                                'name':line_data.name,
                                'product_catalog_id':catalog_data.id,
                                'product_template_id':template_data.id,
                                'product_id':product_data.id,
                                'lead_order_id':rec.id,
                                'create_uid':line_data.create_uid.id,
                            }))
                            if vehicle_line_list:
                                data['vehicle_line'] = vehicle_line_list
                            # print("----data prepared-------",data,lead)
                            if exist_in_parent:
                                """ Update existing records after unlinking the vehcile lines"""
                                # line_data.unlink()
                                if data:
                                    rec.sudo().write({'sync_pipeline': True})
                                    # self.update_sync(rec)
                                    # print("-------------------update----------------------------",rec,rec.sync_pipeline)
                                    exist_in_parent.vehicle_line.unlink()
                                    exist_in_parent.sudo().write(data)
                                print("update the record------")
                            else:
                                """ Insert new records """
                                # print("--------------------Create----------------------------")
                                if data:
                                    rec.sudo().write({'sync_pipeline':  True})
                                    # self.update_sync(rec)
                                    new_recordds = env['crm.lead'].sudo().create(data)
                                    print("insert the records-----",new_recordds)

        except Exception as e:
            raise ValidationError(e)

    # @api.multi
    # def update_sync(self, rec):
    #     if rec:
    #         """ connect to the child db and update the sync value """
    #         param = self.env['ir.config_parameter'].sudo()
    #         child = param.get_param('consolidated_apis.company_type')
    #         print("child---",child)
    #         if child == 'is_child_company':
    #             database = param.get_param('consolidated_apis.child_db_name')
    #             print("database=====",database)
    #             db = sql_db.db_connect(f"{database}")
    #             with contextlib.closing(db.cursor()) as cr:
    #                 cr.autocommit(True)
    #                 my_env = api.Environment(cr, SUPERUSER_ID, {})
    #                 record_id = my_env['crm.lead'].sudo().browse(rec.id)
    #                 if record_id:
    #                     record_id.sudo().write({'sync_pipeline':True, 'website':'vish.com'})

