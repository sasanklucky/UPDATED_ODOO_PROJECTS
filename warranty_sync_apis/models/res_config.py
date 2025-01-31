from odoo import models, fields, api
import re
from openerp.exceptions import UserError, ValidationError
from ast import literal_eval


class WarrentySyncDbConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    warrenty_company_type = fields.Selection([('is_child_company', 'Child Company'),('is_parent_company', 'Parent Company')])
    warrenty_sync_db = fields.Char(string='Parent DB')
    enable_sync_to_parent = fields.Selection([('yes', 'Yes'),('no', 'No')])
    enable_sync_to_child = fields.Selection([('yes', 'Yes'),('no', 'No')])

    @api.multi
    def redirect_sync_warranty_to_parent(self):
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('warranty_sync_apis.warrenty_company_type')
        if child == 'is_child_company':
            form_view = self.env.ref('warranty_sync_apis.warranty_sync_check_wizard_view')
            result = {
                        'name': 'Warranty Sync To Parent',
                        'res_model': 'warranty_sync_check_wizard',
                        'view_id': form_view.id,
                        'views': [(form_view.id, 'form'),],
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                    }
            return result
        else:
            raise ValidationError("Current company is not child company.Please change the company type to 'Child Company' and Try again.")
    
    @api.multi
    def redirect_sync_warranty_to_child(self):
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('warranty_sync_apis.warrenty_company_type')
        if child == 'is_parent_company':
            form_view = self.env.ref('warranty_sync_apis.warranty_sync_checkparent_to_child_wizard_froms')
            result = {
                        'name': 'Warranty Sync To Child',
                        'res_model': 'warranty_sync_checkparent_to_child_wizard',
                        'view_id': form_view.id,
                        'views': [(form_view.id, 'form'),],
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                    }
            return result
        else:
            raise ValidationError("Current company is child company.Please change the company type to 'Parent Company' and Try again.")

    @api.multi
    def set_values(self):
        super(WarrentySyncDbConfiguration, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('warranty_sync_apis.warrenty_company_type', self.warrenty_company_type)
        set_param('warranty_sync_apis.warrenty_sync_db', self.warrenty_sync_db)
        set_param('warranty_sync_apis.enable_sync_to_parent', self.enable_sync_to_parent),
        set_param('warranty_sync_apis.enable_sync_to_child', self.enable_sync_to_child),
    
    @api.model
    def get_values(self):
        res = super(WarrentySyncDbConfiguration, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            warrenty_company_type='is_child_company' if get_param('warranty_sync_apis.warrenty_company_type') == 'is_child_company' else 'is_parent_company',
            warrenty_sync_db=get_param('warranty_sync_apis.warrenty_sync_db', ''),
            enable_sync_to_parent='yes' if get_param('warranty_sync_apis.enable_sync_to_parent') == 'yes' else 'no',
            enable_sync_to_child='yes' if get_param('warranty_sync_apis.enable_sync_to_child') == 'yes' else 'no',
        )
        return res
