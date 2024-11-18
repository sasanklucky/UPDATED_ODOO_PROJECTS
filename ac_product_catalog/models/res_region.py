from odoo import fields, models


class ResRegion(models.Model):
    _name = 'res.region'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    region = fields.Many2one('res.region', string="Region")
    _sql_constraints = [
        ('unique_mobile', 'UNIQUE(mobile)', "The mobile number must be unique."),
    ]


class EcbRegions(models.Model):
    _name = 'zone.zone'
    _rec_name = 'zone_name'

    zone_name = fields.Selection([
        ('east', 'EAST'),
        ('west', 'WEST'),
        ('north', 'NORTH'),
        ('south', 'SOUTH')
    ], 'Zone Name')

    responsible_person = fields.Many2one('res.partner', string='Responsible Person')
