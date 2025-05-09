from odoo import models, fields, api, _
class AcVehicleConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    consolidate_db_name = fields.Char('Consolidate Database Name', required=1)
    # ims_db_name = fields.Char('IMS Database Name', required=1)
    is_consolidation = fields.Boolean(string="Consolidation Setup", default=False)
    is_vehicle_create = fields.Boolean(related="company_id.is_vehicle_create", string="Vehicle Card Creation", default=False)

    @api.multi
    def set_values(self):
        super(AcVehicleConfigSetting, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('ac_vehicle_history.consolidate_db_name', self.consolidate_db_name)
        # set_param('ac_vehicle_history.ims_db_name', self.ims_db_name)
        set_param('ac_vehicle_history.is_consolidation', self.is_consolidation)
        set_param('ac_vehicle_history.is_vehicle_create', self.is_vehicle_create)


    @api.model
    def get_values(self):
        res = super(AcVehicleConfigSetting, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            consolidate_db_name=get_param('ac_vehicle_history.consolidate_db_name', ''),
            # ims_db_name=get_param('ac_vehicle_history.ims_db_name', '')
            is_consolidation=get_param('ac_vehicle_history.is_consolidation', ''),
            is_vehicle_create=get_param('ac_vehicle_history.is_vehicle_create', ''),
        )
        return res


class ResCompany(models.Model):
    _inherit ='res.company'

    is_vehicle_create = fields.Boolean()