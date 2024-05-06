from odoo import fields, models


class ResRegion(models.Model):
    _name = 'res.region'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    region = fields.Many2one('res.region', string="Region")



