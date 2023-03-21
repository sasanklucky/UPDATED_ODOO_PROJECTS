from odoo import models, fields, tools, api, _
from datetime import datetime


class report_epv_sales_enquiry(models.Model):
    _name = 'report_epv_sales_enquiry'
    _description = 'Report EPV Sales Enquiry  '
    _auto = False

    def get_address(self):
        address = ''
        for record in self:
            record.address2 = f'{record.address} {record.address1}'

    def get_color(self):
        for record in self:
            color = record.product_id.attribute_value_ids.filtered(lambda x: x.attribute_id.name == 'color').ids
            if color:
                attribute = self.env['product.attribute.value'].sudo().search([('id', 'in', color)])
                record.color = attribute.name

    def get_invoice(self):
        for record in self:
            sales_order = self.env['sale.order'].sudo().search(
                [('opportunity_id', '=', record.record_id), ('state', '=', 'draft')])
            if sales_order:
                record.invoice = 'YES'
            else:
                record.invoice = 'NO'

            # if sales_order:
            #     invoice = self.env['account.invoice'].sudo().search([('order_id','in',sales_order)])
            #     if invoice:
            #         record.invoice = 'YES'
            #     else:
            #         record.invoice = 'NO'
            # else:
            #     record.invoice = 'NO'

    def get_existing_customer(self):
        for record in self:
            invoice = self.env['account.invoice'].sudo().search(
                [('partner_id', '=', record.partner_id.id), ('state', '=', 'paid')])
            if invoice:
                record.existing_customer = 'YES'
            else:
                record.existing_customer = 'NO'

    def get_test_drive_date(self):
        for record in self:
            if record.test_drive == 'yes':
                test_drive = self.env['ars.test.drive'].search([('opportunity_id', '=', record.record_id)],
                                                               order="id desc", limit=1)
                if test_drive:
                    record.test_drive_date = test_drive.test_drive_date

    def get_booking_details(self):
        for record in self:
            if record.sale_order_id:
                record.booking = 'yes'
                print(record.sale_order_id.create_date)
                booking_date = datetime.strptime(record.sale_order_id.create_date, "%Y-%m-%d %H:%M:%S").date()
                record.booking_date = booking_date
                record.booking_token = record.sale_order_id.amount_total
            else:
                record.booking = 'no'
                record.booking_date = False
                record.booking_token = 0.0

    def get_invoice_details(self):
        for record in self:
            if record.invoice_id:
                record.retail = 'yes'
                record.retail_date = datetime.strptime(record.invoice_id.create_date, "%Y-%m-%d %H:%M:%S").date()
            else:
                record.retail = 'no'
                record.retail_date = False

    def get_invoice_cancel_reason(self):
        for record in self:
            if record.invoice_id:
                record.retail_reason = ''

    def get_loan_details(self):
        for record in self:
            record.loan = ''
            record.loan_bank = ''

    record_id = fields.Integer()
    company_id = fields.Many2one('res.company', 'Dealer Name')
    dealer_zone = fields.Selection(related="company_id.dealer_zone")
    dealer_code = fields.Char(related="company_id.dealer_code")
    dealer_state = fields.Many2one('res.country.state', related="company_id.state_id")
    dealer_city = fields.Char(related="company_id.city", string='Dealer City')
    enquiry_date = fields.Char('Enquiry Creation Date')
    purchase_date = fields.Char('Expected Purchase Date')
    no_of_days = fields.Char('Intension To Purchase Days')
    enquiry_category = fields.Char('Enquiry Category')
    user_id = fields.Many2one('res.users', 'Sales Consultant')
    partner_id = fields.Many2one('res.partner', 'Partner')
    city = fields.Char(related="partner_id.city")
    address = fields.Char(related="partner_id.street")
    address1 = fields.Char(related="partner_id.street2")
    address2 = fields.Char(compute="get_address")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('transgender', 'Transgender')],
                              related="partner_id.gender")
    age = fields.Integer(related="partner_id.age")
    function = fields.Char(related="partner_id.function")
    annual_income = fields.Many2one('annual.income', related='partner_id.annual_income')
    title = fields.Many2one('res.partner.title', 'Salutation')
    contact_name = fields.Char('Contact Name')
    phone = fields.Char('Phone')
    email = fields.Char('Email ID')
    product_id = fields.Many2one('product.product', 'Variant')
    make = fields.Char(related="product_id.product_tmpl_id.brand_id.name")
    model = fields.Char(related="product_id.product_tmpl_id.name")
    color = fields.Char(compute="get_color")
    source_id = fields.Many2one('utm.source', 'Source')
    medium_id = fields.Many2one('utm.medium', 'First Enquiry Mode')
    invoice = fields.Char(compute="get_invoice")
    stage_id = fields.Many2one('crm.stage')
    lost_reason = fields.Many2one('crm.lost.reason')
    existing_customer = fields.Char(compute="get_existing_customer")
    referred = fields.Char()
    test_drive = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    test_drive_date = fields.Date('TD Date', compute='get_test_drive_date')
    sale_order_id = fields.Many2one('sale.order')
    booking = fields.Selection([('yes', 'Yes'), ('no', 'No')], compute="get_booking_details")
    booking_date = fields.Date('Booking Date', compute="get_booking_details")
    booking_token = fields.Float('Booking amount Token', compute="get_booking_details")
    sale_cancel_reason = fields.Many2one('sale.order.cancel.reason', related='sale_order_id.cancel_reason_id')
    invoice_id = fields.Many2one('account.invoice')
    retail = fields.Selection([('yes', 'Yes'), ('no', 'No')],compute="get_invoice_details")
    retail_date = fields.Date('Retail Date',compute="get_invoice_details")
    retail_reason = fields.Char(compute="get_invoice_cancel_reason")
    loan = fields.Selection([('yes', 'Yes'), ('no', 'No')],compute="get_loan_details")
    loan_bank = fields.Char(compute="get_loan_details")
    delivery_date = fields.Char('Delivery Date')
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        print("table name", self._table);
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over() as id,a.id as record_id,a.company_id,a.create_date::Date as enquiry_date,a.date_deadline 
            as purchase_date,a.date_deadline - a.create_date::Date as no_of_days,so.id as sale_order_id,
            case
            when a.date_deadline - a.create_date::Date <= 30 then 'HOT'
            when a.date_deadline - a.create_date::Date > 30 and a.date_deadline - a.create_date::Date <= 60 then 'WARM'
            when a.date_deadline - a.create_date::Date > 60 then 'COLD'
            else ''
            end as enquiry_category,
            case
                when a.is_test_drive = true then 'yes'
                when a.is_test_drive = false then 'no'
            else 'no'
            end as test_drive,inv.id as invoice_id,
            a.user_id,a.partner_id,a.title,a.contact_name,
            a.phone,a.email_from as email,a.source_id,a.medium_id,a.stage_id,a.lost_reason,b.product_id,
            a.referred as referred,pic.date_done::Date as delivery_date
            from crm_lead a join crm_lead_line b on a.id = b.lead_order_id
            left join sale_order so on so.opportunity_id = a.id
            left join account_invoice inv on inv.order_id = so.id
            left join stock_picking pic on pic.sale_id = so.id
            where a.type = 'opportunity'

        )""" % (self._table))
