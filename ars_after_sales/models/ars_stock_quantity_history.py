from odoo import fields, models, _


class ArsStockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'
    _description = 'Stock Quantity History'

    def open_table(self):
        self.ensure_one()
        if self.compute_at_date:
            tree_view_id = self.env.ref('stock.view_stock_product_tree').id
            form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
            # We pass `to_date` in the context so that `qty_available` will be computed across
            # moves until date.
            if self._context.get('vehicle_inventory') == True:
                action = {
                    'type': 'ir.actions.act_window',
                    'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                    'view_mode': 'tree,form',
                    'name': _('Products'),
                    'res_model': 'product.product',
                    'context': dict(self.env.context, to_date=self.date),
                    'domain': [('catalog_type.name', '=', 'Vehicle')]
                }
                return action
            elif self._context.get('parts_inventory') == True:
                action = {
                    'type': 'ir.actions.act_window',
                    'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                    'view_mode': 'tree,form',
                    'name': _('Products'),
                    'res_model': 'product.product',
                    'context': dict(self.env.context, to_date=self.date),
                    'domain': [('catalog_type.name', '=', 'Parts')]
                }
                return action
            else:
                action = {
                    'type': 'ir.actions.act_window',
                    'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                    'view_mode': 'tree,form',
                    'name': _('Products'),
                    'res_model': 'product.product',
                    'context': dict(self.env.context, to_date=self.date),
                }
                return action
        else:
            if self._context.get('vehicle_inventory') == True:
                self.env['stock.quant'].search([('product_tmpl_id.catalog_type.name', '=', 'Vehicle')])._merge_quants()
                self.env['stock.quant'].search(
                    [('product_tmpl_id.catalog_type.name', '=', 'Vehicle')])._unlink_zero_quants()
                return self.env.ref('ars_after_sales.quantsact1').read()[0]
            elif self._context.get('parts_inventory') == True:
                self.env['stock.quant'].search([('product_tmpl_id.catalog_type.name', '=', 'Parts')])._merge_quants()
                self.env['stock.quant'].search(
                    [('product_tmpl_id.catalog_type.name', '=', 'Vehicle')])._unlink_zero_quants()
                return self.env.ref('ars_after_sales.quantsact2').read()[0]
            else:
                self.env['stock.quant']._merge_quants()
                self.env['stock.quant']._unlink_zero_quants()
                return self.env.ref('stock.quantsact').read()[0]
