from odoo import models, fields, api, _



class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'


    product_enabled = fields.Boolean(string='Enabled', default=False)



