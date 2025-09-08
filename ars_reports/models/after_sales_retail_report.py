from odoo import models, fields, api, tools, _


class AfterSlaesRetailReport(models.Model):
    _name = 'retail.report.after.sales'
    _description = 'Retail Report'
    _auto = False

    dealer_code = fields.Char(string="Dealer Code")
    dealer_id = fields.Many2one('res.company', 'Dealer Name')
    dealer_state_id = fields.Many2one('res.country.state', string="State")
    dealer_city_id = fields.Char(string="City")
    order_id = fields.Many2one('sale.order', string="Order")
    customer_name = fields.Many2one('res.partner')
    line_item_id = fields.Many2one('account.invoice.line', string="Invoice Line")
    vin = fields.Char(string="VIN")
    registration_no = fields.Many2one('fleet.vehicle', string="Registration No")

    master_name = fields.Char(string='Model Group ')
    model = fields.Many2one('product.product', string="Model")
    last_service_dealer = fields.Char(string="Last Service Dealer")
    last_service_date = fields.Date(string="Last Service Date")
    ro_number = fields.Char(string="RO Number")
    ro_open_date = fields.Datetime(string="RO Open Date")
    ro_close_date = fields.Date(string="RO Close Date")
    invoice_id = fields.Many2one('account.invoice', string="Invoice Number")
    invoice_date = fields.Date(string="Invoice Date")
    service_type = fields.Many2one('service.type', string="Service Type")
    ro_type = fields.Char(string="RO Type")
    last_ro_close_date = fields.Datetime(string="Last RO Close Date")
    odoometer = fields.Integer(string="Odometer Reading")
    price_unit = fields.Float(string="Price Unit")
    discount = fields.Float(string="Discount")
    part_id = fields.Many2one('product.product', string="Parts Replace")
    part_description = fields.Text(string="Product Description")
    default_code = fields.Char( )
    l10n_in_hsn_code = fields.Char(string='HSN/SAC Code')
    part_price = fields.Float(string="Product price(W/O Tax)")
    total_part_price = fields.Float(string="Total amount")
    customer_voc = fields.Text(string="Customer VOC", compute="_compute_customer_voc")
    cgst_per = fields.Float(string="CGST %", compute="_compute_tax_percentage")
    sgst_per = fields.Float(string="SGST %", compute="_compute_tax_percentage")
    igst_per = fields.Float(string="IGST %", compute="_compute_tax_percentage")
    dealer_gst = fields.Char(string='Dealer GST Number')
    customer_gst = fields.Char('Customer GST Number')
    customer_ph = fields.Char(string='Customer Mobile No')
    customer_city = fields.Char(string='Customer City')
    customer_state = fields.Many2one('res.country.state',string='Customer State')
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
    selling_dealer = fields.Char(string="Selling Dealer")
    service_advisor = fields.Many2one('res.users', 'Service Advisor')

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
                select row_number() over(order by inli.id desc) as id,
                so.id as order_id,
                inli.id as line_item_id,
                rs.dealer_code as dealer_code,
                so.company_id as dealer_id,
                so.vin_no as vin,
                so.regn_no as registration_no,
                so.model as model,
                rp2.name as selling_dealer,
                inv.id as invoice_id,
                inv.date_invoice as invoice_date,
                inv.create_date as ro_close_date,
                inv.cust_invoice_type as cust_invoice_type,
                inv.type as invoice_type,
                inv.origin as origin,
                inv.reference as invoice_reference,
                mg.name as master_name,
                (select rs.dealer_code from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc limit 1) as last_service_dealer,
                (select date from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as last_service_date,
                (select so.name from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc  limit 1) as ro_number,
                (select so.confirmation_date from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc limit 1) as ro_open_date,
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
                
                res_par.state_id as dealer_state_id,
                res_par.city as dealer_city_id,
                res_par.vat as dealer_gst,
                sale_res_par.id as customer_name,
                res_user.id as service_advisor,
                sale_res_par.vat as customer_gst,
                sale_res_par.mobile as customer_ph,
                sale_res_par.city as customer_city,
                sale_res_par.state_id as customer_state,
                prod_temp.default_code as default_code,
                prod_temp.l10n_in_hsn_code as l10n_in_hsn_code,
                
                
                (select 
                    case when inv.irn_no is not null then 'Yes' 
                    else 'No' 
                    end as e_invoice_generated from account_invoice ai where ai.id = inv.id) AS e_invoice_generated,
                inv.irn_no as irn_no
                from account_invoice_line inli
    			left join account_invoice inv on inv.id = inli.invoice_id
                left join sale_order so on so.id = inv.order_id
                left join res_company rs on rs.id = so.company_id
                left join res_partner res_par on res_par.id = rs.id
    			left join res_partner rp on inv.partner_id = rp.id
    			left join res_partner rp2 on so.sold_by = rp2.id
    			left join res_partner sale_res_par on sale_res_par.id = so.partner_id
    			left join res_users res_user on res_user.id = so.user_id
    			left join fleet_vehicle fv on fv.id = inv.reg_no
                left join product_template pt on pt.id = fv.model_id
                left join product_product prod_prod on prod_prod.id = inli.product_id
                left join product_template prod_temp on prod_temp.id = prod_prod.product_tmpl_id
                
                left join model_groups mg on mg.id = pt.master_id
                where so.state not in ('draft', 'sent', 'cancel') and so.sale_aftersales = 'after_sales'
                AND rs.id IN {company_ids}
                  {date_filter}
            )
        """)



            # format(table_name=self._table, company_ids=company_ids,start_date=start_date_str, end_date=end_date_str))


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


class AfterSalesRetailWizard(models.TransientModel):
    _name = 'retail.report.after.sales.wizard'

    company_id = fields.Many2many('res.company', default=lambda self: self.env.user.company_ids)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    def retrieve_stock_qty(self):
        self.ensure_one()
        comp_ids = []
        for rec in self.company_id:
            comp_ids.append(rec.id)
        query = self.env['retail.report.after.sales']
        query.sudo().sql_query(companys=comp_ids,start_date=self.start_date, end_date=self.end_date)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Retail Report',
            'res_model': 'retail.report.after.sales',
            'view_mode': 'tree',
            'view_type': 'form',
            'context': self.env.context,
            'target': 'current',
        }
