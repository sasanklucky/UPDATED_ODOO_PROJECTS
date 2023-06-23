from odoo import models, fields, api, tools, _

class PartsPurchaseReport(models.Model):
    _name = 'parts.purchase.report'
    _description = 'Parts Purchase Report'
    _auto = False

    dealer_code = fields.Char(string="Dealer Code")
    dealer_id = fields.Many2one('res.company','Dealer Name')
    dealer_state_id = fields.Many2one('res.country.state',string="State",related="dealer_id.state_id")
    dealer_city_id = fields.Char(string="City",related="dealer_id.city")
    invoice_no = fields.Many2one('account.invoice',string='Invoice No')
    invoice_line_id = fields.Many2one('account.invoice.line',string="Invoice Line")
    invoice_date = fields.Date(string="Invoice Date")
    po_id = fields.Many2one('purchase.order',string="PO No")
    po_date = fields.Datetime(string="PO Date")
    part_id = fields.Many2one('product.product','Part Replace')
    part_description = fields.Text(string="Parts Description")
    hsn_code = fields.Char(related="part_id.l10n_in_hsn_code",string="HSN Code")
    quantity = fields.Float(string='Quantity')
    unit_price = fields.Float(string="Unit Price")
    discount = fields.Float(string="Discount")
    cgst_per = fields.Float(string="CGST %", compute="_compute_tax_percentage")
    sgst_per = fields.Float(string="SGST %", compute="_compute_tax_percentage")
    igst_per  = fields.Float(string="IGST %", compute="_compute_tax_percentage")
    net_dealer_price = fields.Float(string="Net Dealer Price")
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over(order by ail.id desc) as id,
            ail.id as invoice_line_id,
            rs.dealer_code as dealer_code,
            po.company_id as dealer_id,
            ai.id as invoice_no,
            ai.date_invoice as invoice_date,
            po.id as po_id,
            po.date_order as po_date,
            ail.product_id as part_id,
            ail.name as part_description,
            ail.quantity as quantity,
            ail.price_unit as unit_price,
            ail.discount as discount,
            ail.price_total as net_dealer_price
            from account_invoice_line ail
            left join account_invoice ai on ai.id = ail.invoice_id
            left join product_product pp on pp.id = ail.product_id
            left join res_company rs on rs.id = ai.company_id
            left join purchase_order po on po.name = ai.origin
            where ai.type = 'in_invoice' and ai.ars_type = 'after_sales'
        )""" % (self._table))

    @api.multi
    def _compute_tax_percentage(self):
        for rec in self:
            price = rec.unit_price * (1 - (rec.discount or 0.0) / 100.0)
            taxes = rec.invoice_line_id.invoice_line_tax_ids.compute_all(price, rec.invoice_no.currency_id, rec.invoice_line_id.quantity, product=rec.invoice_line_id.product_id, partner=rec.invoice_no.partner_id)
            for t in taxes.get('taxes', []):
                tax_id = self.env['account.tax'].browse(t.get('id',False))
                if tax_id:
                    if 'cgst' in tax_id.name.lower():
                        rec.cgst_per = round(tax_id.amount,1)
                    if 'sgst' in tax_id.name.lower():
                        rec.sgst_per = round(tax_id.amount,1)
                    if 'igst' in tax_id.name.lower():
                        rec.igst_per = round(tax_id.amount,1)
    