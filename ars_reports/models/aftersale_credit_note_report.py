from odoo import models, fields, api, tools, _


class AfterSlaesRetailReport(models.Model):
    _name = 'credit.report.after.sales'
    _description = 'Credit Note Report'
    _auto = False

    dealer_code = fields.Char(string="Dealer Code")
    dealer_id = fields.Many2one('res.company', 'Dealer Name')
    dealer_state_id = fields.Many2one('res.country.state', string="State", related="dealer_id.state_id")
    dealer_city_id = fields.Char(string="City", related="dealer_id.city")
    order_id = fields.Many2one('sale.order', string="Order")
    customer_name = fields.Many2one('res.partner', related='credit_note_id.partner_id')
    line_item_id = fields.Many2one('sale.order.line', string="Order Line")
    vin = fields.Char(string="VIN")
    registration_no = fields.Many2one('fleet.vehicle', string="Registration No")

    master_name = fields.Char(string='Model Group ')
    model = fields.Many2one('product.product', string="Model")
    last_service_dealer = fields.Char(string="Last Service Dealer")
    last_service_date = fields.Date(string="Last Service Date")
    ro_number = fields.Char(string="RO Number")
    ro_open_date = fields.Datetime(string="RO Open Date")
    ro_close_date = fields.Datetime(string="RO Close Date")
    invoice_id = fields.Many2one('account.invoice', string="Invoice Number")
    credit_note_id = fields.Many2one('account.invoice')
    credit_note_number = fields.Char(string="Credit Number Number")
    credit_note_date = fields.Date()
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
    e_invoice_generated = fields.Char(string="E-Invoice Generated")
    irn_no = fields.Char(string="IRN Number")

    # product_uom_qty = fields.Float('Ordered Quantity')
    # product_catalog_id = fields.Many2one('product.catalog', 'Catalog Type')
    # bill_to_customer = fields.Char()

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
                    select row_number() over(order by sol.id desc) as id,
                    so.id as order_id,
                    sol.id as line_item_id,
                    rs.dealer_code as dealer_code,
                    so.company_id as dealer_id,
                    so.vin_no as vin,
                    so.regn_no as registration_no,
                    so.model as model,
                    inv.id as invoice_id,
                    cn.id as credit_note_id,
                    cn.number as credit_note_number,
                    cn.date_invoice as credit_note_date,
                    inv.create_date as ro_close_date,
                    mg.name as master_name,
                    (select rs.dealer_code from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc limit 1) as last_service_dealer,
                    (select date from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as last_service_date,
                    (select so.name from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc  limit 1) as ro_number,
                    (select so.confirmation_date from service_history sh where sh.vehicle_id = so.regn_no and sh.order = so.id order by id desc limit 1) as ro_open_date,
        
                    so.service_type as service_type,
                    (select servicetype from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as ro_type,
                    (select date from service_history where vehicle_id = so.regn_no order by id desc  limit 1) as last_ro_close_date,
                    so.mileage_in as odoometer,
                    cnl.product_id as part_id,
                    cnl.name as part_description,
                    cnl.price_unit as price_unit,
                    cnl.discount as discount,
                    cnl.price_subtotal as part_price,
                    cnl.price_total as total_part_price,
                    (select 
                        case when inv.irn_no is not null then 'Yes' 
                        else 'No' 
                        end as e_invoice_generated from account_invoice ai where ai.id = inv.id) AS e_invoice_generated,
                    inv.irn_no as irn_no
                    --sol.product_uom_qty as product_uom_qty,
                    --sol.product_catalog_id as product_catalog_id
        
                    from account_invoice_line cnl
                    left join account_invoice cn on cnl.invoice_id = cn.id
                    left join account_invoice inv on cn.origin = inv.number
                    left join account_invoice_line inli on inli.invoice_id = inv.id
                    left join sale_order_line_invoice_rel invl on invl.invoice_line_id = inli.id
                    left join sale_order_line sol on sol.id = invl.order_line_id
                    left join sale_order so on so.id = sol.order_id
                    left join res_company rs on rs.id = so.company_id
                    left join fleet_vehicle fv on fv.id = inv.reg_no
                    left join product_template pt on pt.id = fv.model_id
                    left join model_groups mg on mg.id = pt.master_id
                    where so.state not in ('draft', 'sent', 'cancel') and so.sale_aftersales = 'after_sales'
                AND rs.id IN {company_ids}
                  {date_filter}
            )
        """)



        #     from sale_order_line sol
        #     left join sale_order so on so.id = sol.order_id
        #     left join res_company rs on rs.id = so.company_id
        #     join sale_order_line_invoice_rel invl on invl.order_line_id = sol.id
		# 	left join account_invoice_line inli on inli.id = invl.invoice_line_id
		# 	left join account_invoice inv on inv.id = inli.invoice_id
		# 	left join res_partner rp on inv.partner_id = rp.id
		# 	left join account_invoice cn on cn.origin = inv.number
		# 	left join account_invoice_line cnl on cnl.invoice_id = cn.id
        #     where so.state not in ('draft', 'sent', 'cancel') and so.sale_aftersales = 'after_sales'
        # )""" % (self._table))

    # @api.multi
    # def _compute_credit_number(self):
    #     for rec in self:
    #         credit_note = self.env['account.invoice'].search([('type', '=', 'out_refund'),('origin','=', str(rec.invoice_id))])
    #         if credit_note:
    #             rec.credit_note_number = credit_note
    @api.multi
    def _compute_customer_voc(self):
        for rec in self:
            rec.customer_voc = ','.join(str(v.name if v.name else 'None') for v in rec.order_id.customer_voice_sale)

    @api.multi
    def _compute_tax_percentage(self):
        for rec in self:
            price = rec.price_unit * (1 - (rec.discount or 0.0) / 100.0)
            taxes = rec.line_item_id.tax_id.compute_all(price, rec.line_item_id.order_id.currency_id,
                                                        rec.line_item_id.product_uom_qty,
                                                        product=rec.line_item_id.product_id,
                                                        partner=rec.line_item_id.order_id.partner_shipping_id)
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




# customer name---> from credit note
# cus gst num-----> inside customer
# bill to customer ---no need
# ro number, open date, close date ---no need
# inv number, inv date, service type,




class AfterSalesCreditNoteWizard(models.TransientModel):
    _name = 'credit.report.after.sales.wizard'

    company_id = fields.Many2many('res.company', default=lambda self: self.env.user.company_ids)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    def credit_stock_qty(self):
        self.ensure_one()
        comp_ids = []
        for rec in self.company_id:
            comp_ids.append(rec.id)
        query = self.env['credit.report.after.sales']
        query.sudo().sql_query(companys=comp_ids, start_date=self.start_date, end_date=self.end_date)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Credit Note Report',
            'res_model': 'credit.report.after.sales',
            'view_mode': 'tree',
            'view_type': 'form',
            'context': self.env.context,
            'target': 'current',
        }
