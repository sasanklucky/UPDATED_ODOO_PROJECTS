from odoo import models, fields, api
import re
from openerp.exceptions import UserError, ValidationError
from ast import literal_eval


class POSyncDbConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    po_company_type = fields.Selection([('is_child_company', 'Child Company'),('is_parent_company', 'Parent Company')])
    child_db_name = fields.Char(string='Parent DB')
    parent_db_name = fields.Char(string='Parent DB')
    enable_po_sync = fields.Selection([('yes', 'Yes'),('no', 'No')])
    enable_sale_sync = fields.Selection([('yes', 'Yes'),('no', 'No')])

    @api.multi
    def po_sync_check(self):
        form_view = self.env.ref('purchase_order_sync_apis.posync_check_wizard_view')
        result = {
                    'name': 'PO Sync Check',
                    'res_model': 'po_sync_check_wizard',
                    'view_id': form_view.id,
                    'views': [(form_view.id, 'form'),],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }
        return result
    
    @api.multi
    def so_sync_check(self):
        form_view = self.env.ref('purchase_order_sync_apis.sosync_check_wizard_view')
        result = {
                    'name': 'SO Sync Check',
                    'res_model': 'so_sync_check_wizard',
                    'view_id': form_view.id,
                    'views': [(form_view.id, 'form'),],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }
        return result

    @api.multi
    def set_values(self):
        super(POSyncDbConfiguration, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('purchase_order_sync_apis.po_company_type', self.po_company_type)
        set_param('purchase_order_sync_apis.child_db_name', self.child_db_name)
        set_param('purchase_order_sync_apis.parent_db_name', self.parent_db_name)
        set_param('purchase_order_sync_apis.enable_po_sync', self.enable_po_sync),
        set_param('purchase_order_sync_apis.enable_sale_sync', self.enable_sale_sync),
    
    @api.model
    def get_values(self):
        res = super(POSyncDbConfiguration, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            po_company_type='is_child_company' if get_param('purchase_order_sync_apis.po_company_type') == 'is_child_company' else 'is_parent_company',
            parent_db_name=get_param('purchase_order_sync_apis.parent_db_name', ''),
            child_db_name=get_param('purchase_order_sync_apis.child_db_name', ''),
            enable_po_sync='yes' if get_param('purchase_order_sync_apis.enable_po_sync') == 'yes' else 'no',
            enable_sale_sync='yes' if get_param('purchase_order_sync_apis.enable_sale_sync') == 'yes' else 'no',
        )
        return res
