from odoo import models, fields, api, tools, _


class PartsPurchaseReport(models.Model):
    _name = 'parts.purchase.report'
    _description = 'Parts Purchase Report'
    _auto = False

    dealer_code = fields.Char(string="Dealer Code")
    dealer_id = fields.Many2one('res.company', 'Dealer Name')
    dealer_state_id = fields.Many2one('res.country.state', string="State", related="dealer_id.state_id")
    dealer_city_id = fields.Char(string="City", related="dealer_id.city")
    invoice_no = fields.Many2one('account.invoice', string='Invoice No')
    invoice_line_id = fields.Many2one('account.invoice.line', string="Invoice Line")
    invoice_date = fields.Date(string="Invoice Date")
    po_id = fields.Many2one('purchase.order', string="PO No")
    po_date = fields.Datetime(string="PO Date")
    part_id = fields.Many2one('product.product', 'Part Replace')
    part_description = fields.Char(string="Parts Description",related='part_id.name')
    part_category = fields.Many2one(string="Parts Category", related='part_id.categ_id')
    hsn_code = fields.Char(related="part_id.l10n_in_hsn_code", string="HSN Code")
    default_code = fields.Char(related="part_id.default_code", string="Parts Number")
    quantity = fields.Float(string='Quantity')
    unit_price = fields.Float(string="Unit Price")
    discount = fields.Float(string="Discount")
    cgst_per = fields.Float(string="CGST %", compute="_compute_tax_percentage")
    sgst_per = fields.Float(string="SGST %", compute="_compute_tax_percentage")
    igst_per = fields.Float(string="IGST %", compute="_compute_tax_percentage")
    net_dealer_price = fields.Float(string="Net Dealer Price")
    vendor = fields.Char(string="Vendor")
    vendor_ref = fields.Char(string="Vendor Reference")

    @api.multi
    def sql_query(self, companys, start_date, end_date):
        tools.drop_view_if_exists(self.env.cr, self._table)
        if len(companys) == 1:
            company_ids = f"({companys[0]})"
        else:
            company_ids = str(tuple(companys))

        date_filter = ""
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = fields.Datetime.from_string(start_date)
            if isinstance(end_date, str):
                end_date = fields.Datetime.from_string(end_date)
            start_date_str = "'{}'".format(start_date.strftime('%Y-%m-%d %H:%M:%S'))
            end_date_str = "'{}'".format(end_date.strftime('%Y-%m-%d %H:%M:%S'))
            date_filter = f"AND ai.date_invoice::date BETWEEN {start_date_str} AND {end_date_str}"

        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                select row_number() over(order by ail.id desc) as id,
                ail.id as invoice_line_id,
                rs.dealer_code as dealer_code,
                po.company_id as dealer_id,
                ai.id as invoice_no,
                ai.date_invoice as invoice_date,
                po.id as po_id,
                po.date_order as po_date,
                ail.product_id as part_id,
                ail.quantity as quantity,
                ail.price_unit as unit_price,
                ail.discount as discount,
                ail.price_total as net_dealer_price,
                rp.name as vendor,
                ai.reference as vendor_ref
                from account_invoice_line ail
                left join account_invoice ai on ai.id = ail.invoice_id
                left join product_product pp on pp.id = ail.product_id
                left join res_company rs on rs.id = ai.company_id
                left join purchase_order po on po.name = ai.origin
                left join res_partner rp on rp.id = ai.partner_id
                where ai.type = 'in_invoice' and ai.ars_type = 'after_sales'
                AND ai.company_id IN {company_ids}
                        {date_filter}
            )
        """)



    @api.multi
    def _compute_tax_percentage(self):
        for rec in self:
            price = rec.unit_price * (1 - (rec.discount or 0.0) / 100.0)
            taxes = rec.invoice_line_id.invoice_line_tax_ids.compute_all(price, rec.invoice_no.currency_id,
                                                                         rec.invoice_line_id.quantity,
                                                                         product=rec.invoice_line_id.product_id,
                                                                         partner=rec.invoice_no.partner_id)
            for t in taxes.get('taxes', []):
                tax_id = self.env['account.tax'].browse(t.get('id', False))
                if tax_id:
                    if 'cgst' in tax_id.name.lower():
                        rec.cgst_per = round(tax_id.amount, 1)
                    if 'sgst' in tax_id.name.lower():
                        rec.sgst_per = round(tax_id.amount, 1)
                    if 'igst' in tax_id.name.lower():
                        rec.igst_per = round(tax_id.amount, 1)


class PartPurchaseWizard(models.TransientModel):
    _name = 'parts.purchase.report.wizard'

    company_id = fields.Many2many('res.company', default=lambda self: self.env.user.company_ids)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    def part_purchase_report_qty(self):
        self.ensure_one()
        comp_ids = []
        for rec in self.company_id:
            comp_ids.append(rec.id)
        query = self.env['parts.purchase.report']
        query.sudo().sql_query(companys=comp_ids,start_date=self.start_date, end_date=self.end_date)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Parts Purchase Report',
            'res_model': 'parts.purchase.report',
            'view_mode': 'tree',
            'view_type': 'form',
            'context': self.env.context,
            'target': 'current',
        }
