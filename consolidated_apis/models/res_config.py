from odoo import models, fields, api, registry, SUPERUSER_ID, sql_db
import re
import contextlib
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
    
    def button_view(self):
#         print('hello baby i am called')
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('consolidated_apis.company_type')
        check_pipeline_sync = param.get_param('consolidated_apis.enable_pipeline_sync')
        child_database = self._cr.dbname
        if child == 'is_child_company' and check_pipeline_sync == 'yes':
            database = param.get_param('consolidated_apis.db_name')
            # child_database = param.get_param('consolidated_apis.child_db_name')
            reference_ids = []
            db = sql_db.db_connect(f"{database}")
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                exist_in_parent = env['crm.lead'].sudo().search([('child_db','=',child_database)])
                if exist_in_parent:
                    reference_ids = exist_in_parent.mapped('child_id_ref')
            pipelines = self.env['crm.lead'].sudo().search([('id','not in',reference_ids)]).mapped('id')
        view_id = self.env.ref('consolidated_apis.crm_wizard')
#         print('action called again',pipelines)
        action = {
            'name': 'Sync Data',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'crm_wizard',
            'target': 'self',
            'context': {'crm_ids': pipelines, }
        }
        return action


class crm_wizard(models.TransientModel):
    _name = "crm_wizard"
    _description = "Pipeline Records"

    @api.model
    def default_get(self, fields):
        res = super(crm_wizard, self).default_get(fields)
        crm_records = self.env.context.get('crm_ids', [])
        # print(self.env.context)

        res.update({
            'crm_ids': crm_records,
        })

        return res


    crm_ids = fields.Many2many(
        string='Crm Ids',
        comodel_name='crm.lead',
        relation='crm_wizard_rel',
        column1='process_id',
        column2='crm_id',
    )



    def sync_data(self):
        if not self.crm_ids:
            raise ValidationError('No records for manual sync')
        else:
            self.env['crm.lead'].sudo()._cron_update_pipe_line_to_parent(self.crm_ids)
            action_id = self.env.ref("base_setup.action_general_configuration").id
            return {
                    'type': 'ir.actions.act_url',
                    'target': 'self',
                    'url': f'/web#action={action_id}&model=res.config.settings',
                }
            
