# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ACStockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    ars_type = fields.Selection([('general', 'General'), ('vehicle', 'Vehicle'),
                                 ('after_sales', 'Parts')], string='Warehouse Type')


