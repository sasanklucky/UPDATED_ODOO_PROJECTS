from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from datetime import datetime

class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    is_dealer = fields.Boolean()
    dealer_code = fields.Char()