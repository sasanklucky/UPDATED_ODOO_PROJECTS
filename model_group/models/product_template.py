# models/product_template.py
from odoo import models, fields,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    master_id = fields.Many2one(
        'model.groups',
        string='Model Group',
        index=True
    )

