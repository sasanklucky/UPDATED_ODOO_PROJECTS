# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ACProductCatalog(models.Model):
    _name = 'product.catalog'

    name = fields.Char()
    code = fields.Char(required=True)
    type = fields.Selection([('consu', 'Consumable'), ('service', 'Service'), ('product', 'Stockable Product')])


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        print(values)
        return values


class ARSProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ARSProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom,
                                                                        location_id, name, origin, values, group_id)
        if values.get('sale_line_id', False):
            result['sale_line_id'] = values['sale_line_id']
        return result
