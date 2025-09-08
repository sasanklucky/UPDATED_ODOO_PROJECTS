from odoo import models, fields, api
from odoo import http
from odoo.http import request
import asyncio


class stockPickingTax(models.Model):
    _inherit = 'stock.picking'

    amount_untaxed = fields.Float(string='Untaxed Amount', compute='_compute_amounts')
    amount_tax = fields.Float(string='Tax', compute='_compute_amounts')
    amount_total = fields.Float(string='Total', compute='_compute_amounts')

    @api.depends('amount_untaxed', 'amount_tax', 'amount_total')
    def _compute_amounts(self):
        for rec in self:
            print('STOCK PICKING')
            total_tax_included = total_tax_excluded = 0.0
            print(rec.id)
            for product in rec.move_lines:
                for tax in product.product_id.taxes_id:
                    taxes = tax.compute_all(price_unit=product.product_id.standard_price, product=product.product_id,
                                            quantity=product.product_uom_qty, partner=rec.partner_id)
                    total_tax_included += taxes['total_included']
                    total_tax_excluded += taxes['total_excluded']
                    # print(taxes)
            print(total_tax_included, total_tax_excluded, "compute_all()")
            rec.amount_total = total_tax_included
            rec.amount_tax = total_tax_included - total_tax_excluded
            rec.amount_untaxed = total_tax_excluded

    def tax_percentage(self, taxes):
        if taxes:
            percentage_se = self.env['account.tax'].search([('id', '=', taxes.id)])
            percentage = 0
            for tax in percentage_se:
                if tax.amount_type == 'group' and tax.children_tax_ids:
                    for child_tax in tax.children_tax_ids:
                        percentage += child_tax.amount
                    return percentage
                elif tax.amount_type == 'percent':
                    percentage = tax.amount
                    return percentage
        else:
            return 0.0

