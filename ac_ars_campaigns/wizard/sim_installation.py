from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import re


class SimInstallation(models.TransientModel):
    _name = 'sim.installation'

    sim_numbers = fields.Char(string='Sim Number', tracking=True)
    sim_installation_date = fields.Date(string='SIM Assignment Date', default=fields.Date.context_today,tracking=True)
    vehicle = fields.Integer('Vehicle id')
    sale_id = fields.Integer('Sale id')

    @api.constrains('sim_numbers')
    def _check_sim_number_format(self):
        for record in self:
            sim = record.sim_numbers
            if sim:
                if len(sim) != 20:
                    raise ValidationError("Sim Number must be exactly 20 characters.")
                if not re.fullmatch(r'[A-Z0-9]{20}', sim):
                    raise ValidationError("Sim Number must contain only uppercase letters and digits (A-Z, 0-9).")

    def updation_sim(self):
        for rec in self:
            vehicle_id = self.env['fleet.vehicle'].search([('id', '=', rec.vehicle)], limit=1)
            sale_id = self.env['sale.order'].search([('id', '=', rec.sale_id)], limit=1)
            campaign_his_id = self.env['campaign.history'].search([('id', '=', sale_id.campaign_his_id.id)])
            if vehicle_id:
                vehicle_id.write({'sim_number': rec.sim_numbers,
                                  'sim_installation_date': rec.sim_installation_date})

            campaign_his_id.write({'state': 'done',
                                   'camp_cancel_reasons': ''
                                   })
