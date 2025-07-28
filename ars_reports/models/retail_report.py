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
    master_group = fields.Char(string="Model Group")

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
    # gst = fields.Float(string="GST")
    line_item_id = fields.Many2one('account.invoice.line', string="Invoice Line")
    total = fields.Float(String="Total")
    price_unit = fields.Float(string="Price Unit")
    discount = fields.Float(string="Discount")
    cgst_per = fields.Float(string="CGST %", compute="_compute_tax_percentage")
    sgst_per = fields.Float(string="SGST %", compute="_compute_tax_percentage")
    igst_per = fields.Float(string="IGST %", compute="_compute_tax_percentage")
    cgst_amt = fields.Float('CGST Amount', compute='_compute_tax_percentage')
    sgst_amt = fields.Float(string='SGST Amount', compute='_compute_tax_percentage')
    igst_amt = fields.Float(string='IGST Amount', compute='_compute_tax_percentage')
    pincode = fields.Char(string='Pincode', related="customer_name.zip")
    bill_to_customer_gstn = fields.Char(string='Bill to Customer GSTIN', related="customer_name.vat")

    @api.multi
    def _compute_tax_percentage(self):
        for rec in self:
            price = rec.line_item_id.price_unit * (1 - (rec.discount or 0.0) / 100.0)
            taxes = rec.line_item_id.invoice_line_tax_ids.compute_all(price, rec.line_item_id.company_id.currency_id,
                                                                      rec.line_item_id.quantity,
                                                                      product=rec.line_item_id.product_id,
                                                                      partner=rec.line_item_id.invoice_id.partner_shipping_id)
            for t in taxes.get('taxes', []):
                tax_id = self.env['account.tax'].browse(t.get('id', False))
                if tax_id:
                    if 'cgst' in tax_id['name'].lower() and t['amount']:
                        rec.cgst_per = round(tax_id.amount, 1)
                        rec.cgst_amt = t['amount']
                    if 'sgst' in tax_id['name'].lower():
                        rec.sgst_per = round(tax_id.amount, 1)
                        rec.sgst_amt = t['amount']
                    if 'igst' in tax_id['name'].lower():
                        rec.igst_per = round(tax_id.amount, 1)
                        rec.igst_amt = t['amount']

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

    @api.multi
    def sql_query(self, companys, start_date, end_date):
        tools.drop_view_if_exists(self.env.cr, self._table)
        if len(companys) == 1:
            company_ids = f"({companys[0]})"
        else:
            company_ids = str(tuple(companys))

        date_filter = ""
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = fields.Datetime.from_string(start_date)
            if isinstance(end_date, str):
                end_date = fields.Datetime.from_string(end_date)
            start_date_str = "'{}'".format(start_date.strftime('%Y-%m-%d %H:%M:%S'))
            end_date_str = "'{}'".format(end_date.strftime('%Y-%m-%d %H:%M:%S'))
            date_filter = f"AND ai.date_invoice::date BETWEEN {start_date_str} AND {end_date_str}"

        self.env.cr.execute(f"""
                    CREATE OR REPLACE VIEW {self._table} AS (
            select row_number() over(order by ai.id desc) as id,
            ai.company_id as dealer_id,
            rc.dealer_code as dealer_code,
            ai.date_invoice as date_of_invoice,
            ai.number as invoice_number,
            ail.product_template_id as product_template_id,
            ail.product_id as product_id,
            sml.lot_id as vin_no,
            ail.id as line_item_id,
            ail.price_unit as price_unit,
            ail.discount as discount,
            mg.name AS master_group,

            ai.partner_id as customer_name,
            rsp.mobile as contact_no,
            rsp.email as email,
            rsp.city as city,
            rsp.state_id as state,
            (select name from res_partner where parent_id= ai.partner_id order by id desc limit 1) as contact_person,
			--(select mobile from res_partner where parent_id= ai.partner_id order by id desc limit 1) as contact_no,
			--(select email from res_partner where parent_id= ai.partner_id order by id desc limit 1) as email,
			--(select city from res_partner where parent_id= ai.partner_id order by id desc limit 1) as city,
			--(select state_id from res_partner where parent_id= ai.partner_id order by id desc limit 1) as state,
            so.company_id as outlet,
            DATE(so.confirmation_date) as date_of_booking,
            so.source_id as source,
			ai.user_id as salesperson,
			so.bank_account as finance_bank,
			ail.price_subtotal_signed as basic_price,
			--(ail.price_total - ail.price_subtotal) as gst,
			ail.price_total as total
            from account_invoice_line ail 
            left join account_invoice ai on ai.id = ail.invoice_id
            left join res_company rc on rc.id = ai.company_id
            left join sale_order so on so.id = ai.order_id
            left join crm_team ct on ct.id = ai.team_id
            left join sale_order_line_invoice_rel solir on solir.invoice_line_id = ail.id
            left join sale_order_line sol on solir.order_line_id = sol.id
            left join stock_move sm on sm.sale_line_id = sol.id
            left join stock_move_line sml on sml.move_id = sm.id
            left join res_partner rsp on rsp.id = ai.partner_id   
            left join product_template pt on pt.id = ail.product_template_id
            left join model_groups mg on mg.id = pt.master_id       
            where ai.type = 'out_invoice' and ct.team_type = 'sales' and ai.ars_invoice_type = 'vehicle'
                    AND ai.company_id IN {company_ids}
                        {date_filter}
            )
        """)

# from lxml import etree
class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _add_tracking_to_fields(self):
        excluded_fields = {"__last_update", "write_date"} #if you don't want to display modification and update
        field_def = self._fields
        for field_name, field in field_def.items():
            if field_name in excluded_fields:
                continue
            if getattr(field, 'track_visibility', None):
                continue
            field.track_visibility = 'onchange'
    @api.model
    def _register_hook(self):
        self._add_tracking_to_fields()
        return super(ResPartner, self)._register_hook()


class RetailReportPSFWizard(models.TransientModel):
    _name = 'retail.report.wizard'

    company_id = fields.Many2many('res.company', default=lambda self: self.env.user.company_ids)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    def retail_report_qty(self):
        self.ensure_one()
        comp_ids = []
        for rec in self.company_id:
            comp_ids.append(rec.id)
        query = self.env['retail.report']
        query.sudo().sql_query(companys=comp_ids,start_date=self.start_date, end_date=self.end_date)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Retail Report',
            'res_model': 'retail.report',
            'view_mode': 'tree',
            'view_type': 'form',
            'context': self.env.context,
            'target': 'current',
        }
