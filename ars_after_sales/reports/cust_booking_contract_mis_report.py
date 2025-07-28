from odoo import tools
from odoo import models, fields, api

class CustBookingContractMISReport(models.Model):
    _name           = "cust_booking_contract_mis_report"
    _description    = "Cust Booking Contract MIS Report"
    _auto           = False

    dealer_zone = fields.Selection([
        ('east', 'EAST'),
        ('west', 'WEST'),
        ('north', 'NORTH'),
        ('south', 'SOUTH')
        ], 'Dealer Zone')
    dealer_code = fields.Char(string="Dealer Code")
    company_id = fields.Many2one('res.company',string="Dealer")
    contract_id = fields.Many2one('sale.order',string="Contract Id")
    order_date = fields.Datetime(string="Order Date")
    salutation_id = fields.Many2one('res.partner.title',string="Salutation")
    partner_id = fields.Many2one('res.partner',string="Customer")
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    address = fields.Text(string="Address")
    expected_delivery_date = fields.Datetime(string="Expected Delivery Date")
    enquiry_creation_date = fields.Datetime(string="Enquiry Creation Date")
    expected_purchase_date = fields.Datetime(string="Expected Purchase Date")
    sales_executive_id = fields.Many2one('res.users',string="Sales Executive")
    commitments_offers_to_customer = fields.Text(string="Commitments/Offers to Customer")
    referred_by = fields.Char(string="Referred By")
    source_id = fields.Many2one('utm.source',string="Source")
    medium_id = fields.Many2one('utm.medium',string="First Capture Mode")
    created_by = fields.Many2one('res.users',string="Created By")
    booking_amount = fields.Float(string="Booking Amount")
    cancel_date = fields.Datetime(string="Cancel Date")
    no_of_cars_purchased = fields.Integer(string="No of Cars Purchased",compute="_get_no_of_cars_purchased")
    product_id = fields.Many2one('product.product',string="Product")

    model_group = fields.Char(string="Model Group")

    product_name = fields.Char(related="product_id.name",string="Variant")
    vehicle_colour = fields.Char(string="Vehicle Colour",compute="_get_vehicle_colour")
    vehicle_make = fields.Many2one('fleet.vehicle.model.brand',string="Vehicle Make")
    vehicle_model = fields.Many2one('product.template',string="Vehicle Model")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        booking_amount = 0.0
        no_of_cars_purchased = 0
        query = f""" CREATE or REPLACE VIEW %s as (
            WITH company AS (
                SELECT id, dealer_zone, dealer_code, name FROM res_company
            ),
            partner AS (
                SELECT rp.id, rp.name, rp.phone, rp.title, rp.mobile,
                    CONCAT(rp.street, ',', rp.street2, ',', rp.city, ',', rcs.name, ',', rc.name, ',', zip) AS address
                FROM res_partner rp
                LEFT JOIN res_country_state rcs ON rcs.id = rp.state_id
                LEFT JOIN res_country rc ON rc.id = rp.country_id
            ),
            lead AS (
                SELECT id, name, date_deadline, description, referred, medium_id, source_id, create_uid, create_date
                FROM crm_lead
            ),
            vehicle AS (
                SELECT 
                    sol.order_id,
                    sol.product_id,
                    fvmb.id AS make,
                    pt.id AS model,
                    mg.name AS model_group
                FROM sale_order_line sol
                LEFT JOIN product_catalog pc ON pc.id = sol.product_catalog_id
                LEFT JOIN product_template pt ON pt.id = sol.product_template_id
                LEFT JOIN product_product pp ON pp.id = sol.product_id
                LEFT JOIN model_groups mg ON mg.id = pt.master_id
                LEFT JOIN fleet_vehicle_model_brand fvmb ON fvmb.id = pt.brand_id
                WHERE pc.name = 'Vehicle'
            )
            SELECT 
                row_number() OVER() AS id,
                c.dealer_zone AS dealer_zone,
                c.dealer_code AS dealer_code,
                so.company_id AS company_id,
                so.id AS contract_id,
                so.create_date AS order_date,
                p.title AS salutation_id,
                p.id AS partner_id,
                p.phone AS phone,
                p.mobile AS mobile,
                p.address AS address,
                so.commitment_date AS expected_delivery_date,
                l.create_date AS enquiry_creation_date,
                l.date_deadline AS expected_purchase_date,
                so.user_id AS sales_executive_id,
                l.description AS commitments_offers_to_customer,
                l.referred AS referred_by,
                l.source_id AS source_id,
                l.medium_id AS medium_id,
                v.product_id AS product_id,
                v.make AS vehicle_make,
                v.model AS vehicle_model,
                v.model_group AS model_group,
                l.create_uid AS created_by,
                CASE WHEN so.state = 'cancel' THEN so.write_date ELSE NULL END AS cancel_date,
                {booking_amount} AS booking_amount,
                {no_of_cars_purchased} AS no_of_cars_purchased
            FROM sale_order so
            LEFT JOIN company c ON c.id = so.company_id
            LEFT JOIN partner p ON p.id = so.partner_id
            LEFT JOIN lead l ON l.id = so.opportunity_id
            LEFT JOIN vehicle v ON v.order_id = so.id
            WHERE so.invoice_status = 'to invoice' AND so.sale_aftersales = 'sales'
        )""" % (self._table)
        self.env.cr.execute(query)

    @api.multi
    @api.depends('partner_id')
    def _get_no_of_cars_purchased(self):
        for rec in self:
            no_of_cars_purchased = self.env['fleet.vehicle'].search_count([('driver_id','=',rec.partner_id.id),('vehicle_status','=','customer'),('categ_id.name','=','Vehicle')])
            rec.no_of_cars_purchased = no_of_cars_purchased

    @api.multi
    @api.depends('product_id')
    def _get_vehicle_colour(self):
        for rec in self:
            vehicle_colour = ', '.join(map(lambda x: (x.name), rec.product_id.attribute_value_ids))
            rec.vehicle_colour = vehicle_colour
