# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ACProductCatalog(models.Model):
    _name = 'product.catalog'

    name = fields.Char()
    code = fields.Char(required=True)
    type = fields.Selection([('consu', 'Consumable'), ('service', 'Service'), ('product', 'Stockable Product')])
