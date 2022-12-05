from odoo import tools
from odoo import models, fields, api

class CustBookingContractMISReport(models.Model):
    _name           = "cust_booking_contract_mis_report"
    _description    = "Cust Booking Contract MIS Report"
    _auto           = False

    company_id = fields.Many2one('res.company',string="Dealer")
    dealer_code = fields.Char(string="Dealer Code")
    partner_id = fields.Many2one('res.partner',string="Customer")
    phone = fields.Char(string="Phone")
    address = fields.Text(string="Address")
    expected_delivery_date = fields.Datetime(string="Expected Delivery Date")
    proforma_invoice_id = fields.Char(string="Pro-forma Invoice Id")
    sales_executive_id = fields.Many2one('res.users',string="Sales Executive")
    crm_lead_id = fields.Many2one('crm.lead',string="Enquiry Id")
    enquiry_creation_date = fields.Datetime(string="Enquiry Creation Date")



    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = f""" CREATE or REPLACE VIEW %s as (
            with company as
            (
                select id,dealer_code,name from res_company
            ),
            partner as
            (
                select rp.id,rp.name,rp.phone, CONCAT(rp.street,',',rp.street2,',',rp.city,',',rcs.name,',',rc.name,',',zip) as address
                from res_partner rp
                left join res_country_state rcs on rcs.id = rp.state_id
                left join res_country rc on rc.id = rp.country_id
            )
            select row_number() over() as id, so.invoice_status, so.company_id as company_id,c.dealer_code as dealer_code,
            p.id as partner_id,p.name as contact_name, p.phone as phone, p.address as address,
            so.commitment_date as expected_delivery_date,
            so.name as proforma_invoice_id, so.user_id as sales_executive_id,
            cl.id as crm_lead_id, cl.name as enquiry_id, cl.create_date as enquiry_creation_date
            from sale_order so
            left join company c on c.id = so.company_id
            left join partner p on p.id = so.partner_id
            left join crm_lead cl on cl.id = so.opportunity_id
            where so.invoice_status = 'to invoice' and so.sale_aftersales = 'sales'
        )""" % (self._table)
        self.env.cr.execute(query)
