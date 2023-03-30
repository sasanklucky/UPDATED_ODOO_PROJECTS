from odoo import models, fields, tools, api, _


class customer_dump_mis_report(models.Model):
    _name = 'customer_dump_mis_report'
    _description = 'Customer Enquiry Dump Mis Report'
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

    record_id = fields.Integer()
    company_id = fields.Many2one('res.company', 'Dealer Name')
    dealer_zone = fields.Selection(related="company_id.dealer_zone")
    dealer_code = fields.Char(related="company_id.dealer_code")
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
    title = fields.Many2one('res.partner.title', 'Salutation')
    contact_name = fields.Char('Contact Name')
    phone = fields.Char('Phone')
    mobile = fields.Char("Mobile")
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

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        print("table name", self._table);
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over() as id,a.id as record_id,a.company_id,a.create_date::Date as enquiry_date,a.date_deadline 
            as purchase_date,a.date_deadline - a.create_date::Date as no_of_days,
            case
            when a.date_deadline - a.create_date::Date <= 30 then 'HOT'
            when a.date_deadline - a.create_date::Date > 30 and a.date_deadline - a.create_date::Date <= 60 then 'WARM'
            when a.date_deadline - a.create_date::Date > 60 then 'COLD'
            else ''
            end as enquiry_category,a.user_id,a.partner_id,a.title,a.contact_name,
            a.phone,a.mobile,a.email_from as email,a.source_id,a.medium_id,a.stage_id,a.lost_reason,b.product_id,
            a.referred as referred
            from crm_lead a join crm_lead_line b on a.id = b.lead_order_id
            where a.type = 'opportunity'
           
        )""" % (self._table))
