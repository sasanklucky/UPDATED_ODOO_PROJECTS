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
            with company as
            (
                select id,dealer_zone,dealer_code,name from res_company
            ),
            partner as
            (
                select rp.id,rp.name,rp.phone, rp.title,rp.mobile,
                CONCAT(rp.street,',',rp.street2,',',rp.city,',',rcs.name,',',rc.name,',',zip) as address
                from res_partner rp
                left join res_country_state rcs on rcs.id = rp.state_id
                left join res_country rc on rc.id = rp.country_id
            ),
            lead as
            (
                select id, name, date_deadline, description, referred,medium_id,source_id,create_uid,create_date from crm_lead
            ),
            vehicle as 
            (
                select sol.order_id,sol.product_id,fvmb.id as make, pt.id as model 
                from sale_order_line sol 
                left join product_catalog pc on pc.id = sol.product_catalog_id
                left join product_template pt on pt.id = sol.product_template_id
                left join product_product pp on pp.id = sol.product_id
                left join fleet_vehicle_model_brand fvmb on fvmb.id = pt.brand_id
                where pc.name='Vehicle'
            )

            select row_number() over() as id, 
            c.dealer_zone as dealer_zone, 
            c.dealer_code as dealer_code,
            so.company_id as company_id,
            so.id as contract_id, 
            so.create_date as order_date,
            p.title as salutation_id, 
            p.id as partner_id, 
            p.phone as phone, 
            p.mobile as mobile,
            p.address as address,
            so.commitment_date as expected_delivery_date, 
            l.create_date as enquiry_creation_date, 
            l.date_deadline as expected_purchase_date,
            so.user_id as sales_executive_id, 
            l.description as commitments_offers_to_customer,
            l.referred as referred_by,
            l.source_id as source_id,
            l.medium_id as medium_id,
            v.product_id as product_id,
            v.make as vehicle_make,
            v.model as vehicle_model,
            l.create_uid as created_by,
            case when so.state='cancel' then so.write_date else null end as cancel_date,
            {booking_amount} as booking_amount,
            {no_of_cars_purchased} as no_of_cars_purchased
            from sale_order so
            left join company c on c.id = so.company_id
            left join partner p on p.id = so.partner_id
            left join lead l on l.id = so.opportunity_id
            left join vehicle v on v.order_id = so.id
            where so.invoice_status = 'to invoice' and so.sale_aftersales = 'sales'
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
