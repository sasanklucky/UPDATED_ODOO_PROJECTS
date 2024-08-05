from odoo import models, fields, api, tools, _


class AfterSlaesRetailReport(models.Model):
    _name = 'retail.report.after.sales'
    _description = 'Retail Report'
    _auto = False

    dealer_code = fields.Char(string="Dealer Code")
    dealer_id = fields.Many2one('res.company', 'Dealer Name')
    dealer_state_id = fields.Many2one('res.country.state', string="State", related="dealer_id.state_id")
    dealer_city_id = fields.Char(string="City", related="dealer_id.city")
    order_id = fields.Many2one('sale.order', string="Order")
    customer_name = fields.Many2one('res.partner', related='order_id.partner_id')
    line_item_id = fields.Many2one('account.invoice.line', string="Invoice Line")
    vin = fields.Char(string="VIN")
    registration_no = fields.Many2one('fleet.vehicle', string="Registration No")
    model = fields.Many2one('product.product', string="Model")
    last_service_dealer = fields.Char(string="Last Service Dealer")
    last_service_date = fields.Date(string="Last Service Date")
    ro_number = fields.Char(string="RO Number")
    ro_open_date = fields.Datetime(string="RO Open Date")
    ro_close_date = fields.Date(string="RO Close Date")
    invoice_id = fields.Many2one('account.invoice', string="Invoice Number")
    invoice_date = fields.Date(string="Invoice Date", related="invoice_id.date_invoice")
    service_type = fields.Many2one('service.type', string="Service Type")
    ro_type = fields.Char(string="RO Type")
    last_ro_close_date = fields.Datetime(string="Last RO Close Date")
    odoometer = fields.Integer(string="Odometer Reading")
    price_unit = fields.Float(string="Price Unit")
    discount = fields.Float(string="Discount")
    part_id = fields.Many2one('product.product', string="Parts Replace")
    part_description = fields.Text(string="Product Description")
    default_code = fields.Char(related='part_id.default_code')
    l10n_in_hsn_code = fields.Char(related='part_id.l10n_in_hsn_code', string='HSN/SAC Code')
    part_price = fields.Float(string="Product price(W/O Tax)")
    total_part_price = fields.Float(string="Total amount")
    customer_voc = fields.Text(string="Customer VOC", compute="_compute_customer_voc")
    cgst_per = fields.Float(string="CGST %", compute="_compute_tax_percentage")
    sgst_per = fields.Float(string="SGST %", compute="_compute_tax_percentage")
    igst_per = fields.Float(string="IGST %", compute="_compute_tax_percentage")
    dealer_gst = fields.Char(string='Dealer GST Number', related='dealer_id.vat')
    customer_gst = fields.Char('Customer GST Number', related='customer_name.vat')
    customer_ph = fields.Char(string='Customer Mobile No', related='customer_name.mobile')
    customer_city = fields.Char(string='Customer City', related='customer_name.city')
    customer_state = fields.Many2one(string='Customer State', related='customer_name.state_id')
    cgst_amt = fields.Float('CGST Amount', compute='_compute_tax_percentage')
    sgst_amt = fields.Float(string='SGST Amount', compute='_compute_tax_percentage')
    igst_amt = fields.Float(string='IGST Amount', compute='_compute_tax_percentage')
    product_uom_qty = fields.Float('Ordered Quantity')
    product_catalog_id = fields.Many2one('product.catalog', 'Catalog Type')
    bill_to_customer = fields.Char()
    cust_invoice_type = fields.Char(string="Invoice Type")
    work_type = fields.Selection([('mechanical', 'Mechanical'), ('body_paint', 'Body & Paint'), ('labour', 'Labour')])
    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ],string="Invoice Category")
    invoice_reference = fields.Char('Invoice Reference')
    origin = fields.Char('Invoice Origin')
    pincode = fields.Char(string="Pincode")
    bill_to_customer_gst = fields.Char(string="Bill to Customer GST")
    e_invoice_generated = fields.Char(string="E-Invoice Generated")
    irn_no = fields.Char(string="IRN Number")


    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over(order by inli.id desc) as id,
            so.id as order_id,
            inli.id as line_item_id,
            rs.dealer_code as dealer_code,
            so.company_id as dealer_id,
            so.vin_no as vin,
            so.regn_no as registration_no,
            so.model as model,
            inv.id as invoice_id,
            inv.date_invoice as ro_close_date,
            inv.cust_invoice_type as cust_invoice_type,
            inv.type as invoice_type,
            inv.origin as origin,
            inv.reference as invoice_reference,
            (select rs.dealer_code from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc limit 1) as last_service_dealer,
            (select date from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as last_service_date,
            (select so.name from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc  limit 1) as ro_number,
            (select so.appointment_date from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc limit 1) as ro_open_date,
            so.service_type as service_type,
            (select servicetype from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as ro_type,
            (select date from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as last_ro_close_date,
            so.mileage_in as odoometer,
            inli.product_id as part_id,
            inli.name as part_description,
            inli.price_unit as price_unit,
            inli.discount as discount,
            inli.price_subtotal as part_price,
            inli.price_total as total_part_price,
            inli.quantity as product_uom_qty,
            inli.product_catalog_id as product_catalog_id,
            rp.name as bill_to_customer,
			so.work_type as work_type,
			rp.zip as pincode,
            rp.vat as bill_to_customer_gst,
            (select 
                case when inv.irn_no is not null then 'Yes' 
                else 'No' 
                end as e_invoice_generated from account_invoice ai where ai.id = inv.id) AS e_invoice_generated,
            inv.irn_no as irn_no
            from account_invoice_line inli
			left join account_invoice inv on inv.id = inli.invoice_id
            left join sale_order so on so.id = inv.order_id
            left join res_company rs on rs.id = so.company_id
			left join res_partner rp on inv.partner_id = rp.id
            where so.state not in ('draft', 'sent', 'cancel') and so.sale_aftersales = 'after_sales'
        )""" % (self._table))

    @api.multi
    def _compute_customer_voc(self):
        for rec in self:
            rec.customer_voc = ','.join(str(v.name if v.name else 'None') for v in rec.order_id.customer_voice_sale)

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
