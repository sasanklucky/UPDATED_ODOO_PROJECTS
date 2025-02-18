from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db, _
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm
import logging

_logger = logging.getLogger(__name__)


class WarrentySaleOrderLineInheritSyncParent(models.Model):
    _inherit = "sale.order.line"

    parent_warrenty_id_ref = fields.Char(string='Parent Reference')
    parent_sync  = fields.Boolean(string='Sync Parent',default=False)
    check_parent_sync  = fields.Boolean(string='Sync', compute='check_parent_sync_status')
    
    @api.depends('state')
    def check_parent_sync_status(self):
        param = self.env['ir.config_parameter'].sudo()
        parent = param.get_param('warranty_sync_apis.warrenty_company_type')
        print("parent====",parent)
        for record in self:
            if parent == 'is_parent_company':
                record.check_parent_sync = True
            else:
                record.check_parent_sync = False
    
    # update False value to sync_warranty if no value is passed
    @api.multi
    def write(self, vals):
        parent = self.env['ir.config_parameter'].sudo().get_param('warranty_sync_apis.warrenty_company_type')
        if parent == 'is_parent_company' and ('ars_warranty_price' in vals or 'apr_action' in vals):
            vals['parent_sync'] = True
            # warranty_rec = self.env['warranty_order_line_rel'].sudo().search(['sale_order_line_id','=',self.id],limit=1)
            # print("warranty_rec===",warranty_rec,warranty_rec.ars_sale_warranty_id)
            # if warranty_rec:
                # warranty_rec.parent_sync = True
        res = super(WarrentySaleOrderLineInheritSyncParent, self).write(vals)
        return res


class WarrantyOrderLine(models.Model):
    _name = "warranty.order.line"
    _description = "Warranty Order Line"

    warranty_id = fields.Many2one('ars.sale.warranty')
    product_catalog_id = fields.Many2one('product.catalog', string='Catalog Type')
    product_id = fields.Many2one('product.product', string="Product")
    name = fields.Char(string='Description')
    product_uom_qty = fields.Float(string='Ordered Quantity')
    product_uom = fields.Many2one('product.uom', string='Unit of Measure')
    ars_std_price = fields.Float('Base Price')
    ars_warranty_price = fields.Float('Warranty Price')
    reject_reason = fields.Char('Rejected Reason')
    reject_date = fields.Date(string="Rejected Date")
    reject_by = fields.Many2one('res.partner', string="Rejected By")
    reject_by_name = fields.Char('Rejected By', store=True, related='reject_by.name')
    apr_action = fields.Char()


class ArsSaleWarrentySyncParent(models.Model):
    _inherit = "ars.sale.warranty"

    parent_warrenty_id_ref = fields.Char(string='Child ID Reference')
    parent_warrenty_ref = fields.Char(string='Child Reference')
    check_parent_sync  = fields.Boolean(string='Sync', compute='check_parent_sync_status')
    parent_sync  = fields.Boolean(string='Sync Parent',default=False)
    hide_parent_sync_button = fields.Boolean(compute='compute_hide_unhide_sync_button')
    hide_warranty_sync_button = fields.Boolean(compute='compute_hide_unhide_sync_button')
    warranty_order_lines = fields.One2many('warranty.order.line', 'warranty_id', string='Warranty Order Lines')
    order_lines = fields.Many2many('sale.order.line', 'warranty_order_line_rel', string='Order Lines')


    @api.depends('state')
    def compute_hide_unhide_sync_button(self):
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('warranty_sync_apis.warrenty_company_type')
        print("child==compute-------------==",child)
        for record in self:
            if child == 'is_child_company':
                record.hide_warranty_sync_button = True
                record.hide_parent_sync_button = False
            if child == 'is_parent_company':
                record.hide_warranty_sync_button = False
                record.hide_parent_sync_button = True
                
    
    @api.depends('state')
    def check_parent_sync_status(self):
        param = self.env['ir.config_parameter'].sudo()
        parent = param.get_param('warranty_sync_apis.warrenty_company_type')
        print("parent====",parent)
        for record in self:
            if parent == 'is_parent_company' and record.parent_sync:
                record.check_parent_sync = True
            else:
                record.check_parent_sync = False

    @api.multi
    def call_warrenty_sync_to_child(self):
        self.sync_warranty_to_child(self)

    # update False value to sync_warranty if no value is passed
    # @api.multi
    # def write(self, vals):
    #     print("vals-----------------------------------",vals)
    #     # import pdb
    #     # pdb.set_trace()
    #     if 'sync_warranty' not in vals:
    #         vals['sync_warranty'] = False
    #     param = self.env['ir.config_parameter'].sudo()
    #     parent = param.get_param('warranty_sync_apis.warrenty_company_type')
    #     if 'order_lines' in vals and parent == 'is_parent_company':
    #         vals['parent_sync'] = True
    #     res =  super(ArsSaleWarrentySyncParent, self).write(vals)
    #     return res

    @api.model
    def _cron_warrenty_sync_to_child(self):
        call = self.env['ars.sale.warranty'].sync_warranty_to_child(False)
    
    @api.model
    def sync_warranty_to_child(self,current_warrenty_record):
        """ connect to parent db set up in general settings """
        # try:
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('warranty_sync_apis.warrenty_company_type')
        check_warrenty_sync = param.get_param('warranty_sync_apis.enable_sync_to_child')
        print("child---",child, check_warrenty_sync)
        print(current_warrenty_record,'current_warrenty_recordcurrent_warrenty_record')

        #getting child data as self represent child db env
        warrenty_records = False
        if current_warrenty_record:
            warrenty_records = current_warrenty_record
        else:
            warrenty_records = self.env['ars.sale.warranty'].sudo().search([('parent_sync','=',True),('state','=','draft')],order='id asc')
            print("==1==",warrenty_records)

        if child == 'is_parent_company' and check_warrenty_sync == 'yes':
            db_list = warrenty_records.mapped('child_db')
            print("dab list-----------")
            for database in list(set(db_list)):
                # database = param.get_param('warranty_sync_apis.warrenty_sync_db')
                print("database=====",database)
                db = sql_db.db_connect(f"{database}")
                print(db,'dbdbdbdbdbdb')
                # child_database = param.get_param('warranty_sync_apis.child_warrenty_sync_db')
                # child_database = self._cr.dbname
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                
                # looped child po datas
                    for rec in warrenty_records:
                        print("rec=====",rec,rec.child_warrenty_id_ref)
                        stop_sync = False
                        sync_log_dict = {
                            'warrenty_record':rec.id,
                            'warrenty_sequence':rec.name,
                            'status':200,
                        }
                        # parent record env
                        warranty_data = env['ars.sale.warranty'].sudo()
                        exist_in_child = warranty_data.search([('id','=',int(rec.child_warrenty_id_ref))],limit=1, order='id desc')
                        print("purchase order=====",exist_in_child)
                        data = {'parent_sync':True}
                        order_line_list =[]
                        one2many_data={}
                        if exist_in_child:
                            for line in rec.order_lines:
                                child_line_rec = env['sale.order.line'].sudo().search([('id','=',int(line.child_warrenty_id_ref))])
                                if child_line_rec:
                                    one2many_data ={'parent_sync':True,
                                                    'ars_warranty_price':line.ars_warranty_price if line.ars_warranty_price else 0,
                                                    'apr_action':line.apr_action if line.apr_action else False,
                                                    }
                                    child_line_rec.write(one2many_data)
                                    order_line_list.append(one2many_data)
                            #     one2many_data['tax_id'] = [(6, 0, rec.order_lines.tax_id.ids)]
                            
                                # if one2many_data:
                                #     data['order_lines'] = one2many_data
                                #     print("----data     -------",data)
                                #     print("----stop sync-------",stop_sync)
                                    """ Insert new records """
                            if data and order_line_list and not stop_sync:
                                data['order_lines']=order_line_list
                                print("--------------------Update----------------------------")
                                exist_in_child.write({'parent_sync': True,
                                                      'reject_reason': rec.reject_reason,
                                                      'reject_date': rec.reject_date,
                                                      'hide_sync': True,
                                                      })
                                print("new_recordds===",exist_in_child)
                                # seq.number_next_actual = seq.number_next_actual+1
                                sync_log_dict['sync_message'] = 'Success.Warrenty synced from Parent to child.'
                                sync_log_dict['payload'] = {'warrenty_sequence':rec.name,'db':self._cr.dbname,'values':data}
                                print("sync_log_dict====",sync_log_dict)
                                record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                                print("record_set===",record_set)
                                rec.sudo().write({'parent_sync':  False})
                        else:
                            print("Record does not present in parent DB.")
                            sync_log_dict['status'] = 500
                            sync_log_dict['sync_message'] = 'Failure.Record does not present in child.'
                            sync_log_dict['payload'] = {'warrenty_sequence':rec.name,'db':self._cr.dbname,}
                            record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                            stop_sync =True
                            print("log updated0----",record_set)
                            
        
            # except Exception as e:
            #     raise ValidationError(e)



class WarrantyClaimConfig(models.Model):
    _name = 'warranty.claim.config'
    _description = 'Warranty Claim Configuration'
    _rec_name = 'warranty_claim_list'


    warranty_claim_list = fields.Char('Warranty Claim Type')


class RejectReasonConfiguration(models.Model):
    _name = 'reject.reason.config'
    _description = 'Reject Reason Configuration'
    _rec_name = 'reject_reason_list'


    reject_reason_list = fields.Char('Reject Reason')


class RejectLinesWizard(models.TransientModel):
    _name = 'reject.lines.wizard'
    _description = 'Wizard for Rejection Reason'

    reject_reason = fields.Text('Reject Reason')

    def action_reject(self):
        active_ids = self._context.get('active_ids', [])
        warranties = self.env['ars.sale.warranty'].browse(active_ids)

        for warranty in warranties:
            _logger.info("Processing warranty ID: %s", warranty.id)
            warranty.write({
                'reject_reason': self.reject_reason,
                'apr_action': 'reject',
                'state': 'inprocess',
                'parent_sync': True,
                'reject_date': fields.Date.context_today(self),
            })

            if warranty.sync_count == 1:
                warranty.write({'state': 're_submit'})
                for line in warranty.order_lines:
                    line.write({'apr_action': 'reject'})

            elif warranty.sync_count == 2:
                warranty.write({'state': 'inprocess'})
                for line in warranty.order_lines:
                    line.write({'apr_action': 'reject'})

            _logger.info("Processed warranty ID %s with sync_count %d", warranty.id, warranty.sync_count)

            for line in warranty.order_lines:
                if line.apr_action != 'approved':
                    line.write({'apr_action': 'reject'})

            if all(line.apr_action == False for line in warranty.order_lines):
                warranty.sudo().write({'state': 'draft'})

        return {'type': 'ir.actions.act_window_close'}
    #     warranty.write({
        #         'reject_reason': self.reject_reason,
        #         'apr_action': 'reject',
        #         'state': 'inprocess',
        #         'parent_sync': True,
        #         'reject_date': fields.Date.context_today(self),
        #     })
        #
        #     for line in warranty.order_lines:
        #         if line.apr_action != 'approved':
        #             line.write({'apr_action': 'reject'})
        #
        #     if warranty.sync_warranty:
        #         _logger.info("Sync warranty is True for warranty ID: %s", warranty.id)
        #         warranty.write({
        #             'any_line_rejected': False,
        #             'Warranty_sync_reject': False,
        #             'apr_action': False,
        #             'reject_date': False,
        #             # 'state': 'draft'
        #         })
        #
        #
                # for line in warranty.order_lines:
                #     if line.apr_action != 'approved':
                #         line.write({'apr_action': 'reject'})
                #
                # if all(line.apr_action == False for line in warranty.order_lines):
                #     warranty.sudo().write({'state': 'draft'})
        #
        # return {'type': 'ir.actions.act_window_close'}

