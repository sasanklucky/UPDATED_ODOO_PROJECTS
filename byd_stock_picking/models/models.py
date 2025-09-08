# -*- coding: utf-8 -*-

from odoo import models, fields, api


class byd_stock_picking_purchase(models.Model):
    _inherit = 'purchase.order'

    def set_origin_for_picking(self):
        purchase_orders = self.env['purchase.order'].search([])
        for po in purchase_orders:
            for picking in po.picking_ids:
                if picking.origin != po.name:
                    picking.origin = po.name


class byd_stock_picking_sales(models.Model):
    _inherit = 'sale.order'

    def set_origin_for_picking(self):
        sale_orders = self.env['sale.order'].search([])
        for so in sale_orders:
            for picking in so.picking_ids:
                if picking.origin != so.name:
                    picking.origin = so.name
