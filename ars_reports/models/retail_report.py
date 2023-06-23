from odoo import models, fields, api, tools, _

class RetailReport(models.Model):
    _name = 'retail.report'
    _description = 'Retail Report'
    _auto = False
    
    def get_color(self):
        for record in self:
            color = record.product_id.attribute_value_ids.filtered(lambda x: x.attribute_id.name == 'color').ids
            if color:
                attribute = self.env['product.attribute.value'].sudo().search([('id', 'in', color)])
                record.color = attribute.name
    dealer_code = fields.Char(string="Dealer Code")
    dealer_city = fields.Char(string="City", related="outlet.city")
    dealer_state = fields.Many2one('res.country.state',string="State",related="outlet.state_id")
    date_of_invoice = fields.Date(string="Date of Invoice")
    invoice_number = fields.Char(string="Invoice Number")
    vin_no = fields.Many2one('stock.production.lot',string="VIN")
    customer_name = fields.Many2one('res.partner',string="Customer Name")
    product_template_id = fields.Many2one('product.template',string="Model")
    product_id = fields.Many2one('product.product',string="Product")
    color = fields.Char(string="Color",compute="get_color")
    outlet = fields.Many2one('res.company',string="Outlet")
    date_of_booking = fields.Date(string="Date of Booking")
    billing_address = fields.Text(string="Billing Address",compute="_compute_billing_address")
    contact_person = fields.Char(string="Contact Person")
    contact_no = fields.Char(string="Contact No")
    email = fields.Char(string="Email")
    city = fields.Char(string="City")
    state = fields.Many2one('res.country.state',string="State")
    source = fields.Many2one('utm.source',string="Enquiry Source")
    salesperson = fields.Many2one('res.users',string="SalesPerson")
    finance_bank = fields.Many2one('res.bank','Finance Bank')
    basic_price = fields.Float(string="Basic Price")
    gst = fields.Float(string="GST")
    total = fields.Float(String="Total")

    @api.multi
    @api.depends('customer_name')
    def _compute_billing_address(self):
        for record in self:
            record.billing_address = ((record.customer_name.street + ',') if record.customer_name.street else '') + \
                    ((record.customer_name.street2 + ',') if record.customer_name.street2 else '') + \
                    ((record.customer_name.city + ',') if record.customer_name.city else '') + \
                    ((record.customer_name.state_id.name + ',') if record.customer_name.state_id else '') + \
                    ((record.customer_name.country_id.name + ',') if record.customer_name.country_id else '') + \
                    ((record.customer_name.zip) if record.customer_name.zip else '')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over(order by ai.id desc) as id,
            ai.company_id as dealer_id,
            rc.dealer_code as dealer_code,
            ai.date_invoice as date_of_invoice,
            ai.number as invoice_number,
            ail.product_template_id as product_template_id,
            ail.product_id as product_id,
            ail.vin_no as vin_no,
            ai.partner_id as customer_name,
            (select name from res_partner where parent_id= ai.partner_id order by id desc limit 1) as contact_person,
			(select mobile from res_partner where parent_id= ai.partner_id order by id desc limit 1) as contact_no,
			(select email from res_partner where parent_id= ai.partner_id order by id desc limit 1) as email,
			(select city from res_partner where parent_id= ai.partner_id order by id desc limit 1) as city,
			(select state_id from res_partner where parent_id= ai.partner_id order by id desc limit 1) as state,
            so.company_id as outlet,
            DATE(so.confirmation_date) as date_of_booking,
            so.source_id as source,
			ai.user_id as salesperson,
			so.bank_account as finance_bank,
			ail.price_subtotal_signed as basic_price,
			(ail.price_total - ail.price_subtotal) as gst,
			ail.price_total as total

            from account_invoice_line ail 
            left join account_invoice ai on ai.id = ail.invoice_id
            left join res_company rc on rc.id = ai.company_id
            left join sale_order so on so.id = ai.order_id
            left join crm_team ct on ct.id = ai.team_id
            where ai.type = 'out_invoice' and ct.team_type = 'sales'
           
        )""" % (self._table))