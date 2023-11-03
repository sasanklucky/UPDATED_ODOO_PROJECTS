from odoo import models, fields, api, tools, _

class RepairOrderReport(models.Model):
    _name = 'repair.order.report'
    _description = 'Repair Order Report'
    _auto = False

    dealer_code = fields.Char(string="Dealer Code")
    dealer_id = fields.Many2one('res.company','Dealer Name')
    dealer_state_id = fields.Many2one('res.country.state',string="State",related="dealer_id.state_id")
    dealer_city_id = fields.Char(string="City", related="dealer_id.city")
    customer_state_id = fields.Many2one('res.country.state',string="State",related="customer_id.state_id")
    customer_city_id = fields.Char(string="City",related="customer_id.city")
    order_id = fields.Many2one('sale.order',string="Order")
    line_item_id = fields.Many2one('sale.order.line',string="Order Line")
    vin = fields.Char(string="VIN")
    registration_no = fields.Many2one('fleet.vehicle',string="Registration No")
    model = fields.Many2one('product.product',string="Model")
    last_service_dealer = fields.Char(string="Last Service Dealer")
    last_service_date = fields.Date(string="Last Service Date")
    ro_number = fields.Char(string="RO Number")
    ro_open_date = fields.Datetime(string="RO Open Date")
    ro_close_date = fields.Datetime(string="RO Close Date")
    service_type = fields.Many2one('service.type',string="Service Type")
    ro_type = fields.Char(string="RO Type")
    last_ro_close_date = fields.Datetime(string="Last RO Close Date")
    odoometer = fields.Integer(string="Odometer Reading")
    price_unit = fields.Float(string="Price Unit")
    discount = fields.Float(string="Discount")
    part_id = fields.Many2one('product.product',string="Product Number ")
    part_description = fields.Text(string="Part/Labor Description")
    part_price = fields.Float(string="Part/Labor price(W/O Tax)")
    total_part_price = fields.Float(string="Total Bill amount")
    customer_voc = fields.Text(string="Customer VOC",compute="_compute_customer_voc")
    cgst_per = fields.Float(string="CGST %", compute="_compute_tax_percentage")
    sgst_per = fields.Float(string="SGST %", compute="_compute_tax_percentage")
    igst_per  = fields.Float(string="IGST %", compute="_compute_tax_percentage")
    dealer_gst = fields.Char(string='Dealer Gst',related='dealer_id.vat')
    product_varient_id = fields.Many2one(string='Product Variant',related='registration_no.mvariant_id')
    vehiclesale_dt = fields.Date(string='Vehicle Sale Date')
    last_service_km = fields.Integer(string='Last Odometer Reading')
    repair_type = fields.Many2one('service.type',string='Repair Type')
    product_catalog = fields.Many2one('product.catalog',string='Product Catalog')
    part_ref = fields.Char('Part Number',related='part_id.default_code')
    customer_id = fields.Many2one('res.partner',string='Customer Name')
    customer_contact = fields.Char('Contact Detail',related='customer_id.mobile')
    stages = fields.Selection(
        [('pending', 'Pending'), ('survey_done', 'Survey Done'), ('ticket_created', 'Ticket Created'),
         ('completed', 'Completed')], string="PSF Status",compute='psf_status_crm')

    def psf_status_crm(self):
        for record in self:
            # print('record',record)
            order = record.order_id.invoice_ids
            for sale_order in order:
                if sale_order:
                    invoice_number = sale_order.number
                # print('sale Order',sale_order)
                crm_state = self.env['mail.activity'].search([('invoice_id','=',invoice_number),('invoice_type','=','after_sales')])
                for state in crm_state:
                    if state:
                        record.stages = state.stages

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over(order by sol.id desc) as id,
            so.id as order_id,
            so.partner_id as customer_id,
            sol.id as line_item_id,
            rs.dealer_code as dealer_code,
            so.company_id as dealer_id,
            so.vin_no as vin,
            so.service_type as repair_type,
            so.regn_no as registration_no,
            so.model as model,
            (select rs.dealer_code from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc limit 1) as last_service_dealer,
            (select date from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as last_service_date,
            (select mileage from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as last_service_km,
            (select date_of_ownership from ownership_history where vehicle_id = so.regn_no order by id desc  limit 1) as vehiclesale_dt,
            (select so.name from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc  limit 1) as ro_number,
            (select so.create_date from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc limit 1) as ro_open_date,
            (select so.confirmation_date from service_history sh where vehicle_id = so.regn_no order by id desc  limit 1) as last_ro_close_date,
            so.service_type as service_type,
            (select servicetype from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as ro_type,
            inv.create_date as ro_close_date,
            so.mileage_in as odoometer,
            sol.product_id as part_id,
            sol.name as part_description,
            sol.price_unit as price_unit,
            sol.discount as discount,
            sol.price_subtotal as part_price,
            sol.price_total as total_part_price,
            sol.product_catalog_id as product_catalog
            from sale_order_line sol
            left join sale_order so on so.id = sol.order_id
            left join res_company rs on rs.id = so.company_id
            left join account_invoice inv on inv.origin = so.name
            where so.state not in ('draft', 'sent', 'cancel') and so.sale_aftersales = 'after_sales'
        )""" % (self._table))


    @api.multi
    def _compute_customer_voc(self):
        for rec in self:
            rec.customer_voc = ','.join(str(v.name if v.name else 'None') for v in rec.order_id.customer_voice_sale)

    @api.multi
    def _compute_tax_percentage(self):
        for rec in self:
            price = rec.price_unit * (1 - (rec.discount or 0.0) / 100.0)
            taxes = rec.line_item_id.tax_id.compute_all(price, rec.line_item_id.order_id.currency_id, rec.line_item_id.product_uom_qty, product=rec.line_item_id.product_id, partner=rec.line_item_id.order_id.partner_shipping_id)
            for t in taxes.get('taxes', []):
                tax_id = self.env['account.tax'].browse(t.get('id',False))
                if tax_id:
                    if 'cgst' in tax_id.name.lower():
                        rec.cgst_per = round(tax_id.amount,1)
                    if 'sgst' in tax_id.name.lower():
                        rec.sgst_per = round(tax_id.amount,1)
                    if 'igst' in tax_id.name.lower():
                        rec.igst_per = round(tax_id.amount,1)
