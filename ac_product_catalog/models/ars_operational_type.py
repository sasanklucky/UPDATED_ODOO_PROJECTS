from odoo import models, fields, _
from odoo.tools import format_date


class ARSPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_type = fields.Selection([('general', 'General Sales'), ('vehicle', 'Vehicle Sales'),
                                      ('after_sales', 'After Sales')], string='Type')

    # @api.depends('purchase_type')
    # def _get_default_product_catalog(self):
    #     print("product_catalog")
    #     # if self.lead_order_id.team_id.team_type == 'sales':
    #     product_catalog = []
    #     if self.purchase_type == 'vehicle':
    #         product_catalog = self.env['product.catalog'].search([('name', '=', 'Vehicle')], limit=1)
    #     elif self.purchase_type == 'after_sales':
    #         product_catalog = self.env['product.catalog'].search([('name', '=', 'Parts')], limit=1)
    #     # else:
    #     #     product_catalog = self.env['product.catalog'].search([], limit=1)
    #     self.product_catalog_id = product_catalog.id
    #
    # product_catalog_id = fields.Many2one('product.catalog', string='Catalog Type',
    #                                      compute='_get_default_product_catalog')


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    purchase_type = fields.Selection([('general', 'General Sales'), ('vehicle', 'Vehicle Sales'),
                                      ('after_sales', 'After Sales')], string='Type')


class ARSInvoice(models.Model):
    _inherit = 'account.invoice'

    ars_type = fields.Selection([('general', 'General Sales'), ('vehicle', 'Vehicle Sales'),
                                 ('after_sales', 'After Sales')], string='Type')


class ARSStockPicking(models.Model):
    _inherit = 'stock.picking'

    ars_type = fields.Selection([('general', 'General Sales'), ('vehicle', 'Vehicle Sales'),
                                 ('after_sales', 'After Sales')], string='Type')
