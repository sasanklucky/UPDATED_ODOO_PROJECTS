from odoo import models, fields,api



class ARS_check_regn(models.TransientModel):
    _name = "check.regn"


    filter_regn = fields.Many2one('fleet.vehicle')
    regi_no = fields.Char()
    vin = fields.Char()
    model = fields.Char()

    #Select/Save the Regn No in crm.lead
    @api.multi
    def select_regn(self):
        crm_ids = self.env.context.get('active_ids')
        crm_id = self.env['crm.lead'].browse(crm_ids)
        crm_id.regn_no = self.regi_no
        crm_id.vin_no = self.vin
        crm_id.vehicle_model = self.model
        return True

