from odoo import models, fields, api, _
from datetime import datetime
import logging
import json

_logger = logging.getLogger(__name__)


class ARS_sale_order_line(models.Model):
    _inherit = "sale.order.line"

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'ars_warranty_price')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            wrn_price = line.ars_warranty_price * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            wrntaxes = line.tax_id.compute_all(wrn_price, line.order_id.currency_id, line.product_uom_qty,
                                               product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'wrn_price_tax': sum(t.get('amount', 0.0) for t in wrntaxes.get('taxes', [])),
                'wrn_price_total': wrntaxes['total_included'],
                'wrn_price_subtotal': wrntaxes['total_excluded'],
            })

    ars_warranty_price = fields.Float('Warranty Price')
    ars_std_price = fields.Float('Base Price')
    apr_action = fields.Selection(
        [('approved', 'Approved'), ('reject', 'Reject'), ('hold', 'Hold'), ('re_submission', 'Re Submission')],
        string='Action')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    wrn_price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    wrn_price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    wrn_price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    product_catalog_id = fields.Many2one('product.catalog', string='Catalog Type')
    product_id_domain = fields.Char(compute="_compute_product_id_domain", readonly=True, store=False)
    # product_temp_id = fields.Many2one('product.template', string="Product Template")?

    @api.multi
    @api.depends('product_catalog_id')
    def _compute_product_id_domain(self):
        for this in self:
            if not this.product_catalog_id:
                this.product_catalog_id = this.order_id.product_catalog_id.id
            domain = ([('catalog_type', '=', this.product_catalog_id.id)] if this.product_catalog_id else [])
            this.product_id_domain = json.dumps(domain)

    @api.multi
    @api.onchange('category')
    def category_change(self):
        res = {}
        print('warranty onchange')
        _logger.info('Category Change start === %s' % datetime.now().strftime("%H:%M:%S.%f"))
        if self.category and self.category.name.lower() == 'warranty':
            seller_ids = [sl.name.id for sl in self.product_id.seller_ids]
            print('seller_ids', seller_ids)
            if len(seller_ids) == 1:
                self.customer_split = seller_ids and seller_ids[0]
            else:
                self.customer_split = False
                res = {'domain': {'customer_split': [('id', 'in', seller_ids)]}}

        elif self.category and self.category.name.lower() == 'customer':
            self.customer_split = self.order_id.partner_id.id
            res = {'domain': {'customer_split': []}}
        # self.update({'ars_warranty_price': self.price_unit,
        #              'ars_std_price': self.price_unit})
        _logger.info('Category Change end === %s' % datetime.now().strftime("%H:%M:%S.%f"))
        return res

    @api.multi
    @api.onchange('customer_split')
    def CustomerSplit_Change(self):
        res = {}
        self.ensure_one()
        print('customer onchange', self.customer_split)
        if self.customer_split and self.product_id:
            res = self.customer_split.property_product_pricelist.with_context().get_product_price_rule(self.product_id,
                                                                                                       1.0,
                                                                                                       self.customer_split)
            self.price_unit = res[0]
            self.ars_warranty_price = res[0]
            self.ars_std_price = res[0]

    @api.model
    def write(self, values):
        priceUnit = 0
        msg = ''
        priceDict = {}
        context = self._context
        print('order line context', self._context)
        for ol in self:
            priceDict[ol.id] = ol.price_unit
        if 'apr_action' in values and values.get('apr_action') == 'reject':
            values.update({'customer_split': False})
        if 'apr_action' in values and not self.customer_split and values.get('apr_action') == 'approved':
            params = context.get('params')
            if params.get('model') == 'ars.sale.warranty':
                warranty = self.env['ars.sale.warranty'].search_read([('id', '=', params.get('id'))],
                                                                     fields=['partner_id'])
                if warranty:
                    values.update({'customer_split': warranty[0].get('partner_id')[0]})

        if 'category' in values and values.get('category'):
            category = self.env['order.line.category'].browse(values.get('category'))
            if category.name.lower() == 'customer':
                values['apr_action'] = ''
        line = super(ARS_sale_order_line, self).write(values)
        for ol in self:
            order_id = ol.order_id
            if 'price_unit' in values and priceDict.get(ol.id) != values.get('price_unit'):
                msg += _("Price changed for %s : %s - %s \n") % (
                    ol.product_id.display_name, priceDict.get(ol.id), values.get('price_unit'))

        msg and order_id.message_post(body=msg)
        return line
