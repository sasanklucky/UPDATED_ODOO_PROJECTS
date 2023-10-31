from odoo import models, fields, api, tools, _


class WholesaleReport(models.Model):
    _name = 'wholesale.report'
    _description = 'Wholesale Report'
    _auto = False

    def get_color(self):
        for record in self:
            color = record.product_id.attribute_value_ids.filtered(lambda x: x.attribute_id.name == 'color').ids
            if color:
                attribute = self.env['product.attribute.value'].sudo().search([('id', 'in', color)])
                record.color = attribute.name
    dealer_code = fields.Char(string="Dealer Code")
    dealer_city = fields.Char(string="City", related="outlet.city")
    dealer_state = fields.Many2one('res.country.state', string="State", related="outlet.state_id")
    date_of_invoice = fields.Date(string="Date of Invoice")
    invoice_number = fields.Char(string="Invoice Number")
    vin_no = fields.Many2one('stock.production.lot', string="Vin No")
    product_template_id = fields.Many2one('product.template', string="Model")
    product_id = fields.Many2one('product.product', string="Product")
    color = fields.Char(string="Color", compute="get_color")
    outlet = fields.Many2one('res.company', string="Outlet")
    basic_price = fields.Float(string="Basic Price")
    gst = fields.Float(string="GST")
    total = fields.Float(string="Total")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over(order by ai.id desc) as id,
            ai.number as invoice_number,
            ail.product_template_id as product_template_id,
            ai.date_invoice as date_of_invoice,
            ail.vin_no as vin_no,
            ail.product_id as product_id,
            ail.price_subtotal_signed as basic_price,
			(ail.price_total - ail.price_subtotal) as gst,
			ail.price_total as total,
            ai.company_id as outlet,
            rc.dealer_code as dealer_code
            from account_invoice_line ail 
            left join account_invoice ai on ai.id = ail.invoice_id
            left join res_company rc on rc.id = ai.company_id
            left join sale_order so on so.id = ai.order_id
            where ai.type = 'in_invoice' and ai.ars_invoice_type = 'vehicle'
        )""" % (self._table))
