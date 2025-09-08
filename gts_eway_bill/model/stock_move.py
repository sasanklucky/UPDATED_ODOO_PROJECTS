from odoo import fields, models, api, _, tools
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_price = fields.Float('Product Price', help="Product Price for Eway Bill")
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    cess_non_advol = fields.Selection([('0', '0'), ('400', '400'), ('2076', '2076'),
                                       ('2747', '2747'), ('3668', '3668'), ('4006', '4006'),
                                       ('4170', '4170')], string='CESS Non Advol Amount')

    @api.model
    def create(self, vals):
        if 'sale_line_id' in vals:
            line_id = self.env['sale.order.line'].browse(vals.get('sale_line_id'))
            vals['tax_id'] = [(6, 0, line_id.tax_id.ids)]
            vals['product_price'] = line_id.price_unit
        return super(StockMove, self).create(vals)

    # @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if 'state' in vals:
            for data in self:
                if data.sale_line_id:
                    data.tax_id = [(6, 0, data.sale_line_id.tax_id.ids)]
                    data.product_price = data.sale_line_id.price_unit
        return res
