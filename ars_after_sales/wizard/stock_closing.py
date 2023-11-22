from odoo import models, fields, tools, api, _

class StockClosingReport(models.TransientModel):
    _name = 'stock.closing.report'

    dealer_code = fields.Char(string="Dealer Code",default=lambda self : self.env.user.company_id.dealer_code)
    date = fields.Date('Date')
    categ_id = fields.Many2one('product.category')
    catalog_type = fields.Many2one('product.catalog')

    compute_at_date = fields.Selection([
        (0, 'Current Inventory'),
        (1, 'At a Specific Date')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")
    date = fields.Datetime('Inventory at Date', help="Choose a date to get the inventory at that date",
                           default=fields.Datetime.now)

    def open_table(self):
        self.ensure_one()

        if self.compute_at_date:
            tree_view_id = self.env.ref('ars_after_sales.view_parts_product_tree').id,
            form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
            # We pass `to_date` in the context so that `qty_available` will be computed across
            # moves until date.
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Products'),
                'res_model': 'product.product',
                'context': dict(self.env.context, to_date=self.date),
                'domain': [('catalog_type.name', '=','Parts')]
            }
            return action
        else:
            self.env['stock.quant']._merge_quants()
            self.env['stock.quant']._unlink_zero_quants()
            return self.env.ref('stock.quantsact').read()[0]


class ProductProductInherit(models.Model):

    _inherit = 'product.product'

    catalog_type = fields.Many2one('product.catalog')
    parts_value = fields.Float('Value',compute='total_value_parts')
    total_value_stock = fields.Float('Total Value')

    def total_value_parts(self):

        for price in self:
            price.parts_value = price.standard_price * price.qty_available

