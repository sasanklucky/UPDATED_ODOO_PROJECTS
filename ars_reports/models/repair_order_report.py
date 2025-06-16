from odoo import models, fields, api, tools, _
from odoo.tools import datetime


class RepairOrderReport(models.Model):
    _name = 'repair.order.report'
    _description = 'Repair Order Report'
    _auto = False

    dealer_code = fields.Char(string="Dealer Code")
    invoice_number = fields.Char(string="Invoice Number")
    dealer_id = fields.Many2one('res.company','Dealer Name')
    dealer_state_id = fields.Many2one('res.country.state',string="State",related="dealer_id.state_id")
    dealer_city_id = fields.Char(string="City", related="dealer_id.city")
    customer_state_id = fields.Many2one('res.country.state',string="State",related="customer_id.state_id")
    customer_city_id = fields.Char(string="City",related="customer_id.city")
    order_id = fields.Many2one('sale.order',string="Order")
    line_item_id = fields.Many2one('sale.order.line',string="Order Line")
    vin = fields.Char(string="VIN")
    registration_no = fields.Many2one('fleet.vehicle',string="Registration No")
    model = fields.Many2one('product.product',string="Product Varient")
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

    master_id = fields.Many2one('model.group', string='Model Group')
    master_name = fields.Char(string='Model Group')

    product_varient_id = fields.Many2one(string='Product Name',related='registration_no.model_id')
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
    product_uom_qty = fields.Float(string='Ordered Quantity')
    ro_ageing = fields.Integer('Ro Ageing',compute='ro_ageing_compute')


    @api.depends('ro_close_date', 'ro_open_date')
    def ro_ageing_compute(self):
        for record in self:
            if record.ro_open_date and record.ro_close_date:
                start_date = fields.Datetime.from_string(record.ro_open_date)
                end_date = fields.Datetime.from_string(record.ro_close_date)

                # Calculate the difference in days
                delta = end_date - start_date
                record.ro_ageing = delta.days
            else:
                record.ro_ageing = 0
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

    @api.multi
    def sql_query(self, companys, start_date, end_date):
        tools.drop_view_if_exists(self.env.cr, self._table)
        if len(companys) == 1:
            company_ids = f"({companys[0]})"
        else:
            company_ids = tuple(companys)

        date_filter = ""
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = fields.Datetime.from_string(start_date)
            if isinstance(end_date, str):
                end_date = fields.Datetime.from_string(end_date)
            start_date_str = "'{}'".format(start_date.strftime('%Y-%m-%d %H:%M:%S'))
            end_date_str = "'{}'".format(end_date.strftime('%Y-%m-%d %H:%M:%S'))
            date_filter = f"AND inv.create_date::date BETWEEN {start_date_str} AND {end_date_str}"
        self.env.cr.execute(f"""
                CREATE OR REPLACE VIEW {self._table} AS (
                    WITH last_service AS (
                            SELECT 
                                vehicle_id,
                                MAX(id) AS last_service_id,
                                MAX(date) AS last_service_date,
                                MAX(mileage) AS last_service_km,
                                MAX(servicetype) AS ro_type
                            FROM service_history
                            GROUP BY vehicle_id
                        ),
                        last_ownership AS (
                            SELECT 
                                vehicle_id,
                                MAX(date_of_ownership) AS vehiclesale_dt
                            FROM ownership_history
                            GROUP BY vehicle_id
                        )
                        SELECT 
                            ROW_NUMBER() OVER (ORDER BY sol.id DESC) AS id,
                            so.id AS order_id,
                            inv.number as invoice_number,
                            so.partner_id AS customer_id,
                            sol.id AS line_item_id,
                            rs.dealer_code AS dealer_code,
                            so.company_id AS dealer_id,
                            so.vin_no AS vin,
                            so.service_type AS repair_type,
                            so.service_type AS service_type,
                            so.regn_no AS registration_no,
                            so.model AS model,
                            pt.master_id as master_id,
                            last_service.last_service_id,
                            last_service.last_service_date,
                            last_service.last_service_km,
                            last_ownership.vehiclesale_dt,
                            last_service.ro_type as ro_type,
                            rs.dealer_code AS last_service_dealer, 
                            so.name AS ro_number,  -- Fetching 'name' from 'sale_order' instead
                            mg.name AS master_name,
                            so.confirmation_date AS ro_open_date,
                            so.confirmation_date AS last_ro_close_date,
                            inv.create_date AS ro_close_date,
                            so.mileage_in AS odoometer,
                            sol.product_id AS part_id,
                            sol.name AS part_description,
                            sol.price_unit AS price_unit,
                            sol.discount AS discount,
                            sol.product_uom_qty AS product_uom_qty,
                            sol.price_subtotal AS part_price,
                            sol.price_total AS total_part_price,
                            sol.product_catalog_id AS product_catalog
                            FROM sale_order_line sol
                            LEFT JOIN sale_order so ON so.id = sol.order_id
                            LEFT JOIN res_company rs ON rs.id = so.company_id
                            LEFT JOIN account_invoice inv ON inv.origin = so.name
                            LEFT JOIN last_service ON last_service.vehicle_id = so.regn_no
                            LEFT JOIN service_history sh_last ON sh_last.id = last_service.last_service_id
                            LEFT JOIN last_ownership ON last_ownership.vehicle_id = so.regn_no
                            LEFT JOIN fleet_vehicle ftv ON ftv.id = so.regn_no
                            LEFt JOIN product_template pt ON pt.id = ftv.model_id
                            LEFT JOIN model_groups mg ON mg.id = pt.master_id
        
                            WHERE so.state NOT IN ('draft', 'sent', 'cancel') 
                              AND so.sale_aftersales = 'after_sales'
                          AND rs.id IN {company_ids}
                  {date_filter}
            )
        """)


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



class AfterSalesRepairOrderWizard(models.TransientModel):
    _name = 'repair.order.report.wizard'

    company_id = fields.Many2many('res.company', default=lambda self: self.env.user.company_ids)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    def repair_order_stock_qty(self):
        self.ensure_one()
        comp_ids = []
        for rec in self.company_id:
            comp_ids.append(rec.id)
        query = self.env['repair.order.report']
        query.sudo().sql_query(companys=comp_ids, start_date=self.start_date, end_date=self.end_date)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repair Order Report',
            'res_model': 'repair.order.report',
            'view_mode': 'tree',
            'view_type': 'form',
            'context': self.env.context,
            'target': 'current',
        }
