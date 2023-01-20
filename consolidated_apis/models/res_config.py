from odoo import models, fields, api
import re
from openerp.exceptions import UserError, ValidationError
from ast import literal_eval


class ConsolidatedDbConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    company_type = fields.Selection([('is_child_company', 'Child Company'),('is_parent_company', 'Parent Company')])
    child_connection_type = fields.Selection([('internal', 'Internal'),('external', 'External')])
    parent_pconnection_type = fields.Selection([('internal', 'Internal'),('external', 'External')])
    external_url = fields.Char()
    db_name = fields.Char(string='Parent DB')
    # child_db_name = fields.Char(string='Parent DB')
    days_between_two_followups = fields.Char()
    child_ids = fields.Many2many('parent.child.configuration', 'res_config_parent_child_cnfig_rel','res_id','parent_child_id', string='Set up Childs')
    is_child = fields.Boolean()
    is_parent = fields.Boolean()
    enable_pipeline_sync = fields.Selection([('yes', 'Yes'),('no', 'No')])
    enable_quotation_sync = fields.Selection([('yes', 'Yes'),('no', 'No')])
    connection_type = fields.Selection([('internal', 'Internal'),('external', 'External')])
    # port = fields.Char()
    # host = fields.Char()
    # db_user_name = fields.Char()
    # db_password = fields.Char()

    @api.multi
    def set_values(self):
        super(ConsolidatedDbConfiguration, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        # we store the repr of the values, since the value of the parameter is a required string
        set_param('consolidated_apis.company_type', self.company_type)
        set_param('consolidated_apis.child_connection_type', self.child_connection_type)
        set_param('consolidated_apis.parent_pconnection_type', self.parent_pconnection_type)
        set_param('consolidated_apis.external_url', self.external_url)
        set_param('consolidated_apis.db_name', self.db_name)
        # set_param('consolidated_apis.child_db_name', self.child_db_name)
        set_param('consolidated_apis.child_ids', self.child_ids.ids)
        set_param('consolidated_apis.enable_pipeline_sync', self.enable_pipeline_sync),
        set_param('consolidated_apis.enable_quotation_sync', self.enable_quotation_sync),
    
    @api.model
    def get_values(self):
        res = super(ConsolidatedDbConfiguration, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        # the value of the parameter is a nonempty string
        childs = get_param('consolidated_apis.child_ids')
        flines = False
        if childs:
            flines = [(6, 0, literal_eval(childs))]
        res.update(
            company_type='is_child_company' if get_param('consolidated_apis.company_type') == 'is_child_company' else 'is_parent_company',
            child_connection_type='internal' if get_param('consolidated_apis.child_connection_type') == 'internal' else 'external',
            parent_pconnection_type='internal' if get_param('consolidated_apis.parent_pconnection_type') == 'internal' else 'external',
            external_url=get_param('consolidated_apis.external_url', ''),
            db_name=get_param('consolidated_apis.db_name', ''),
            # child_db_name=get_param('consolidated_apis.child_db_name', ''),
            enable_pipeline_sync='yes' if get_param('consolidated_apis.enable_pipeline_sync') == 'yes' else 'no',
            enable_quotation_sync='yes' if get_param('consolidated_apis.enable_quotation_sync') == 'yes' else 'no',
            child_ids=flines,
        )
        return res
