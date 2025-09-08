from odoo import models, fields,api


class VehicleMessage(models.TransientModel):
    _name = 'vehicle.message'

    @api.model
    def default_get(self, fields):
        res = super(VehicleMessage, self).default_get(fields)
        # Fetch the custom message from the configuration parameter
        custom_message = "Vehicle Card Created Successfully"
        res['vehicle_message'] = custom_message
        return res

    vehicle_message = fields.Text(string='Message',readonly=True)

    def vehicle_message_define(self):
        return {'type': 'ir.actions.act_window_close'}