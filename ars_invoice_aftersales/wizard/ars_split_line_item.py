from odoo import models, fields,api


class ARS_split_lineitem(models.TransientModel):
    _name = "split.lineitem"

    product_name = fields.Char()







