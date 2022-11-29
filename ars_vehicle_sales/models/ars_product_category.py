# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ARS_Product_category(models.Model):
    _inherit = 'product.category'

    active = fields.Boolean(default=True)





