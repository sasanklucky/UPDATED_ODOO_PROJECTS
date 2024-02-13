from odoo import models, fields


class ResCompanyTan(models.Model):
    _inherit = "res.company"
    _description = "Res Company Tan"

    tan_no = fields.Char(string='Tan No.')
