from odoo import models, fields, tools, api, _


class SalesReportFormat(models.Model):
    _name = 'sales.report.format'
    _description = 'Sales Report Format'
    _auto = False

    def get_gst(self):
        for rec in self:
            total_tax_percent = 0
            for tax_id in rec.invoice_line_id.invoice_line_tax_ids:
                if tax_id.tax_group_id.name == 'Taxes':
                    for tax_groups in tax_id.children_tax_ids:
                        total_tax_percent += tax_groups.amount
                else:
                    total_tax_percent = tax_id.amount
            rec.gst = total_tax_percent

    def get_gst_amount(self):
        for record in self:
            record.gst_amount = round((record.amount / 100) * record.gst)

    def get_cgst_amount(self):
        for record in self:
            for tax_id in record.invoice_line_id.invoice_line_tax_ids:
                if tax_id.tax_group_id.name == 'Taxes':
                    for tax_groups in tax_id.children_tax_ids:
                        if tax_groups.tax_group_id.name == 'CGST':
                            record.cgst_amount = round((record.amount / 100) * tax_groups.amount)

    def get_sgst_amount(self):
        for record in self:
            for tax_id in record.invoice_line_id.invoice_line_tax_ids:
                if tax_id.tax_group_id.name == 'Taxes':
                    for tax_groups in tax_id.children_tax_ids:
                        if tax_groups.tax_group_id.name == 'SGST':
                            record.sgst_amount = round((record.amount / 100) * tax_groups.amount)

    def get_igst_amount(self):
        for record in self:
            for tax_id in record.invoice_line_id.invoice_line_tax_ids:
                if tax_id.tax_group_id.name == 'IGST':
                    record.igst_amount = round((record.amount / 100) * tax_id.amount)

    def get_utgst_amount(self):
        for record in self:
            tax_group = self.env['account.tax.group'].sudo().search([('name', '=', 'UTGST')], limit=1)
            list_tax = record.invoice_line_id.invoice_line_tax_ids.mapped('id')
            tax_records = self.env['account.tax'].sudo().search(
                [('id', 'in', list_tax), ('tax_group_id', '=', tax_group.id)])
            if tax_records:
                percent = 0
                for rec in tax_records:
                    percent += rec.amount
                record.utgst_amount = round((record.amount / 100) * percent)
            else:
                record.utgst_amount = 0

    def get_vat_amount(self):
        for record in self:
            tax_group = self.env['account.tax.group'].sudo().search([('name', '=', 'VAT')], limit=1)
            list_tax = record.invoice_line_id.invoice_line_tax_ids.mapped('id')
            tax_records = self.env['account.tax'].sudo().search(
                [('id', 'in', list_tax), ('tax_group_id', '=', tax_group.id)])
            if tax_records:
                percent = 0
                for rec in tax_records:
                    percent += rec.amount
                record.vat_amount = round((record.amount / 100) * percent)
            else:
                record.vat_amount = 0

    def get_total_amount(self):
        for record in self:
            record.total_amount = record.amount + record.cgst_amount + record.sgst_amount + record.igst_amount + record.utgst_amount + record.vat_amount

    invoice_id = fields.Many2one('account.invoice', 'Invoice Id')
    invoice_state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status')
    company_id = fields.Many2one('res.company', 'Dealer name')
    # dealer_zone = fields.Char(related="company_id.dealer_zone",string="Region")
    dealer_zone = fields.Selection([
        ('east', 'East'),
        ('west', 'West'), ('north', 'North'), ('south', 'South')
    ], string='Region', related="company_id.dealer_zone")
    dealer_code = fields.Char(related="company_id.dealer_code", string="Dealer No_")
    warehouse_id = fields.Many2one('stock.warehouse', 'Location Code')
    product_id = fields.Many2one('product.product', 'Product Id')
    category_id = fields.Char('Category')
    part_number = fields.Char(related="product_id.default_code", string="Part Number")
    part_description = fields.Char(related="product_id.product_tmpl_id.name", string="Part Description")
    hsn_code = fields.Char(related="product_id.product_tmpl_id.l10n_in_hsn_code", string="HSN / SAC")
    part_type = fields.Many2one('product.category', related="product_id.product_tmpl_id.categ_id", string="Part Type")
    invoice_no = fields.Char(related="invoice_id.number", string="Customer Invoice No")
    # invoice_date = fields.Date(related="invoice_id.date_invoice", string="Customer Invoice Date")
    invoice_date = fields.Date(string="Customer Invoice Date")
    bill_to_customer = fields.Many2one('res.partner', related="invoice_id.partner_id", string="Bill to Customer Name")
    repair_no = fields.Char(related="invoice_id.origin", string="Repair Order No")
    vin = fields.Char(related="invoice_id.vin", string="VIN")
    model_code = fields.Char(related="invoice_id.model.default_code", string="Model Code")
    master_name = fields.Char(string='Model Group')
    model_description = fields.Char(related="invoice_id.model.name", string="Model Desc")
    issue_date = fields.Date(string="Issue Date")
    issue_quantity = fields.Float(string="Issue Quantity")
    standard_price = fields.Float(related="product_id.standard_price", string="Avg Unit Cost / NDP")
    amount = fields.Float(string="Amount")
    invoice_line_id = fields.Many2one('account.invoice.line', 'Invoice Line')
    gst = fields.Integer(compute="get_gst", string='GST %')
    gst_amount = fields.Float(compute="get_gst_amount", string='Total GST')
    cgst_amount = fields.Float(compute="get_cgst_amount", string='CGST')
    sgst_amount = fields.Float(compute="get_sgst_amount", string='SGST')
    igst_amount = fields.Float(compute="get_igst_amount", string='IGST')
    utgst_amount = fields.Float(compute="get_utgst_amount", string='UTGST')
    vat_amount = fields.Float(compute="get_vat_amount", string='VAT')
    total_amount = fields.Float(compute="get_total_amount", string='Total')
    service_advisor = fields.Many2one('res.users', 'Sales Person', related="invoice_id.user_id")

    repair_date = fields.Date('Repair Order Date')
    doc_type = fields.Selection([
        ('appointment', 'Appointment'),
        ('walkin', 'Walkin'),
    ], string='Service Order Type')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        print("table name", self._table);
        self.env.cr.execute(f"""  CREATE or REPLACE VIEW %s as (
                    select row_number() over() as id,a.id as invoice_id,a.company_id,a.state as invoice_state,
                    a.date_invoice::Date as invoice_date,mg.name as master_name,
                    (select warehouse_id from sale_order where name = a.origin order by id desc limit 1 OFFSET 0) as warehouse_id,al.product_id,
                    (select confirmation_date::Date from sale_order where name = a.origin order by id desc limit 1 OFFSET 0) as repair_date,
                    (select doc_type from sale_order where name = a.origin order by id desc limit 1 OFFSET 0) as doc_type,a.delivery_date::Date as issue_date,
                    al.quantity as issue_quantity,al.price_subtotal as amount,al.id as invoice_line_id,
                    CASE 
                    WHEN al.category IS NOT NULL THEN 
                        (SELECT name FROM order_line_category WHERE id = al.category)
                    ELSE 
                        a.cust_invoice_type
                    END as category_id
                    from account_invoice a join account_invoice_line al on a.id = al.invoice_id
                    left join fleet_vehicle fv on fv.id = a.reg_no
                    left join product_template pt on pt.id = fv.model_id
                    left join model_groups mg on mg.id = pt.master_id
                    where a.type = 'out_invoice' 
                    and a.team_id in (select id from crm_team where team_type = 'after_sales' order by id desc OFFSET 0)
        )""" % (self._table))
