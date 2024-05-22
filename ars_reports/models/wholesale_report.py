from odoo import models, fields, api, tools, _


class WholesaleReport(models.Model):
    _name = 'wholesale.report'
    _description = 'Wholesale Report'
    _auto = False

    def get_color(self):
        for record in self:
            color = record.product_id.attribute_value_ids.filtered(
                lambda x: x.attribute_id.name == 'colour' or x.attribute_id.name == 'Ext. colour').ids
            if color:
                color_list = []
                for i in color:
                    attribute = self.env['product.attribute.value'].sudo().search([('id', '=', i)])
                    color_list.append(attribute.name)
                record.color = ', '.join(str(attribute) for attribute in color_list)

    sl_no = fields.Integer()
    dealer_code = fields.Char(string="Dealer Code")
    dealer_city = fields.Char(string="City", related="outlet.city")
    dealer_state = fields.Many2one('res.country.state', string="State", related="outlet.state_id")
    date_of_invoice = fields.Date(string="Date of Invoice")
    invoice_number = fields.Char(string="Invoice Number")
    vin_no = fields.Char(string="Vin No")
    product_template_id = fields.Many2one('product.template', string="Model")
    product_id = fields.Many2one('product.product', string="Product")
    color = fields.Char(string="Color", compute="get_color")
    outlet = fields.Many2one('res.company', string="Outlet")
    basic_price = fields.Float(string="Basic Price")
    gst = fields.Float(string="GST")
    total = fields.Float(string="Total")
    motor_number = fields.Char(string="Motor Number")
    vendor = fields.Char(string="Vendor")
    vendor_reference_no = fields.Char(string="Vendor Reference No")
    description = fields.Char(string="Description")


    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over(order by mvl.id ASC) as id,
            mvl.id AS sl_no,
            ai.number as invoice_number,
            ai.date_invoice as date_of_invoice,
            mvl.lot_name as vin_no,
			mvl.motor_number as motor_number,
            pp.product_tmpl_id as product_template_id,
            ail.product_id as product_id,
            ail.price_subtotal_signed as basic_price,
			(ail.price_total - ail.price_subtotal) as gst,
			ail.price_total as total,
            ai.company_id as outlet,
            rc.dealer_code as dealer_code,
            ai.reference as vendor_reference_no,
			rp.name as vendor,
			ail.name as description
            from account_invoice_line ail 
            left join account_invoice ai on ai.id = ail.invoice_id
            left join purchase_order_line pol on ail.purchase_line_id = pol.id
            left join stock_move mv on mv.purchase_line_id = pol.id
			left join stock_move_line mvl on mvl.move_id = mv.id
			left join res_company rc on rc.id = ai.company_id
            left join sale_order so on so.id = ai.order_id
            left join product_product pp on ail.product_id = pp.id
			left join res_partner rp on ai.partner_id = rp.id
            where ai.type = 'in_invoice' and ai.ars_type = 'vehicle'
        )""" % (self._table))
