from odoo import models, fields, api, _


class VehicleServiceSetup(models.Model):
    _name = 'service.setup.manual'
    _rec_name = 'service_type'

    service_type = fields.Many2one('service.type',string='Service Type')
    model_id = fields.Many2one('product.template')
    days = fields.Integer('Total Days')
    kms = fields.Integer('Kilometers')
    labor_hrs = fields.Integer('Labor Hours')


