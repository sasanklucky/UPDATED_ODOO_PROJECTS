from odoo import fields, models


class ResRegion(models.Model):
    _name = 'res.region'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    region = fields.Many2one('res.region', string="Region")
    customer_code = fields.Char('Customer Code', store=True)
    is_dealer = fields.Boolean('Is Dealer')
    dealer_code = fields.Char('Dealer Code')

    def generate_customer_code(self):
        for rec in self:
            if rec.id and not rec.customer_code:
                db = rec._cr.dbname
                rec.customer_code = f"{db}_{rec.id}"


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
