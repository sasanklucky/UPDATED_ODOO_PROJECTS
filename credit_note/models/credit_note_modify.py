from odoo import api, fields, models, _

class AccountInvoiceLineModify(models.Model):
    _inherit = 'account.invoice.line'

    origin_invoice_line_id = fields.Many2one('account.invoice.line', string="Origin Invoice Line")


class Accounting(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        values = super(Accounting, self)._prepare_refund(invoice, date_invoice, date, description, journal_id)

        # Maintain origin reference for each invoice line
        new_invoice_lines = []
        for line in invoice.invoice_line_ids:
            line_data = line.copy_data()[0]
            line_data['origin_invoice_line_id'] = line.id
            new_invoice_lines.append((0, 0, line_data))
        values['invoice_line_ids'] = new_invoice_lines

        return values

    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None):
        new_invoices = super(Accounting, self).refund(date_invoice, date, description, journal_id)
        for refund_invoice in new_invoices:
            for credit_line in refund_invoice.invoice_line_ids:
                origin_line = credit_line.origin_invoice_line_id
                if origin_line:
                    # Find the sale order line linked to the original invoice line
                    sale_order_lines = self.env['sale.order.line'].search([('invoice_lines', 'in', origin_line.id)])
                    for sale_order_line in sale_order_lines:
                        # Link the credit note line to the sale order line
                        sale_order_line.invoice_lines = [(4, credit_line.id)]
        return new_invoices
