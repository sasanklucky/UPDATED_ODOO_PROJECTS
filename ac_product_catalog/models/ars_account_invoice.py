from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ARSCatalogInvoice(models.Model):
    _inherit = 'account.invoice'

    ars_type = fields.Selection([('general', 'General Bill'), ('vehicle', 'Vehicle Bill'),
                                 ('after_sales', 'After Sales Bill')], string='Bill Type')

    ars_invoice_type = fields.Selection([('general', 'General Invoice'), ('vehicle', 'Vehicle Invoice'),
                                         ('after_sales', 'After Sales Invoice')], string='Invoice Type')
    kilometer = fields.Float(string="Kilometer")
    kilometer_out = fields.Float(string="Kilometer Out")
    cust_invoice_type = fields.Selection([('warranty', 'Warranty Invoice'),
                                          ('customer', 'Customer Invoice'),
                                          ('insurance', 'Insurance Invoice')], string='Type')

    @api.onchange('ars_invoice_type','ars_type')
    def default_invoice_type(self):
        if self.ars_invoice_type:
            domain = [('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale'], 'in_refund': ['purchase'],
                                      'in_invoice': ['purchase']}.get(self.type, [])),
                      ('company_id', '=', self.company_id.id), ('ars_type', '=', self.ars_invoice_type)]
            journal = self.env['account.journal'].search(domain, limit=1)
            self.journal_id = journal.id
        if self.ars_type:
            domain = [('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale'], 'in_refund': ['purchase'],
                                      'in_invoice': ['purchase']}.get(self.type, [])),
                      ('company_id', '=', self.company_id.id), ('ars_type', '=', self.ars_type)]
            journal = self.env['account.journal'].search(domain, limit=1)
            self.journal_id = journal.id


    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if self.purchase_id:
            self.ars_type = self.purchase_id.purchase_type
            self.default_invoice_type()
        domain = super(ARSCatalogInvoice, self).purchase_order_change()
        return domain

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(ARSCatalogInvoice, self)._onchange_partner_id()
        if not self.env.context.get('default_journal_id') and self.partner_id and self.currency_id and\
                self.type in ['in_invoice', 'in_refund'] and\
                self.currency_id != self.partner_id.property_purchase_currency_id:
            journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.company_id.id),
                ('currency_id', '=', self.partner_id.property_purchase_currency_id.id),
                ('ars_type', '=', self.ars_type),
            ]
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
            if default_journal_id:
                self.journal_id = default_journal_id
        return res

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(ARSCatalogInvoice, self)._prepare_invoice_line_from_po_line(line)
        print(res)
        if 'name' in res:
            po_line = self.env['purchase.order.line'].search([('id', '=', res['purchase_line_id'])])
            if po_line.product_id.default_code:
                description = '[' + po_line.product_id.default_code + '] ' + po_line.name
            else:
                description = po_line.name
            res['name'] = description
        res['product_template_id'] = line.product_template_id
        res['product_catalog_id'] = line.product_catalog_id
        return res


class ARSaccount_journal(models.Model):
    _inherit = "account.journal"

    ars_type = fields.Selection([('general', 'General'), ('vehicle', 'Vehicle'),
                                 ('after_sales', 'Parts/After Sales')], string='Journal Type')


class UtmSource(models.Model):
    _inherit = "utm.source"

    active = fields.Boolean(default=True)

