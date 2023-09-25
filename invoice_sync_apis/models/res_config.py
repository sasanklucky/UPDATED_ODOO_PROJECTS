from odoo import models, fields, api
import re
from openerp.exceptions import UserError, ValidationError
from ast import literal_eval


class InvoiceSyncDbConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_company_type = fields.Selection([('is_child_company', 'Child Company'),('is_parent_company', 'Parent Company')])
    enable_invoice_sync = fields.Selection([('yes', 'Yes'),('no', 'No')])
    invoice_parent_db = fields.Char(string='Parent DB')
    

    @api.multi
    def invoice_sync_check(self):
        form_view = self.env.ref('invoice_sync_apis.invoice_sync_check_wizard_view')
        result = {
                    'name': 'Invoice Sync Check',
                    'res_model': 'invoice_sync_check_wizard',
                    'view_id': form_view.id,
                    'views': [(form_view.id, 'form'),],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }
        return result
    

    @api.multi
    def set_values(self):
        super(InvoiceSyncDbConfiguration, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('invoice_sync_apis.invoice_company_type', self.invoice_company_type),
        set_param('invoice_sync_apis.enable_invoice_sync', self.enable_invoice_sync),
        set_param('invoice_sync_apis.invoice_parent_db', self.invoice_parent_db)
        
    
    @api.model
    def get_values(self):
        res = super(InvoiceSyncDbConfiguration, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            invoice_company_type='is_child_company' if get_param('invoice_sync_apis.invoice_company_type') == 'is_child_company' else 'is_parent_company',
            enable_invoice_sync='yes' if get_param('invoice_sync_apis.enable_invoice_sync') == 'yes' else 'no',
            invoice_parent_db=get_param('invoice_sync_apis.invoice_parent_db', ''),
        )
        return res
