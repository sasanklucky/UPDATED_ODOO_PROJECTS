from odoo import api, fields, models
from datetime import datetime

class ResPartnerModelInherit(models.Model):
    _inherit = 'res.partner'
    _description = "Res partner Inherit"

    customer_code = fields.Char()