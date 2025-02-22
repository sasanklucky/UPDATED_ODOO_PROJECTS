from odoo import models, api
from odoo.tools import float_is_zero


class ARSAfterSaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Extend `action_invoice_create` to handle separate invoices for warranty cases
        with adjusted prices for split amounts and correct tax calculations.
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        for order in self:
            if order.sale_aftersales == 'after_sales' and not order.counter_parts:
                for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                    if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue

                    # Handle warranty split logic
                    if line.category.name.lower() == "warranty" and line.warranty_split_partner_ids:
                        for split in line.warranty_split_partner_ids:
                            split_partner = split.customer_split_id
                            split_amount = split.price_unit

                            price = line.price_unit * (split_amount / line.price_subtotal if line.price_subtotal else 1)

                            # Search for an existing invoice for the same category type
                            invoice = inv_obj.search([
                                ('origin', '=', order.name),
                                ('partner_id', '=', split_partner.id),
                                ('cust_invoice_type', '=', split.category.name.lower()),
                                ('state', '=', 'draft')
                            ], limit=1)

                            if not invoice:
                                invoice_vals = {
                                    'type': 'out_invoice',
                                    'partner_id': split_partner.id,
                                    'origin': order.name,
                                    'cust_invoice_type': split.category.name.lower(),
                                }
                                invoice = inv_obj.create(invoice_vals)
                                invoices[invoice.id] = invoice

                            # Ensure product line is created per invoice type
                            invoice_line = invoice.invoice_line_ids.filtered(
                                lambda x: x.product_id.id == line.product_id.id
                            )

                            if not invoice_line or invoice.cust_invoice_type != split.category.name.lower():
                                self._create_invoice_line(invoice, line, price)

                            # Add additional fields to the invoice
                            invoice.write({
                                'mobile': order.mobile,
                                'email': order.email,
                                'reg_no': order.regn_no.id,
                                'vin': order.vin_no,
                                'model': order.model.id,
                                'kilometer': order.mileage_in,
                                'doc_type': order.doc_type,
                                'appointment_date': order.appointment_date,
                                'delivery_service_advisor': order.delivery_service_advisor.id,
                                'delivery_date': order.delivery_date,
                                'service_options': order.service_options.id,
                                'service_type': order.service_type.id
                            })

                            # If invoice amount is negative, adjust for refund
                            if invoice.amount_untaxed < 0:
                                invoice.type = 'out_refund'
                                for inv_line in invoice.invoice_line_ids:
                                    inv_line.quantity = -inv_line.quantity

                            # Ensure additional fields are set correctly for each line
                            for inv_line in invoice.invoice_line_ids:
                                inv_line._set_additional_fields(invoice)

                            # Force computation of taxes
                            invoice.compute_taxes()

                            order.invoice_status = "invoiced"
                            continue

            # Process other orders (non-after-sales, or with counter_parts)
            res = super(ARSAfterSaleOrder, self).action_invoice_create(grouped=False, final=False)
            invoices.update({inv.id: inv for inv in inv_obj.browse(res)})

        return [inv.id for inv in invoices.values()]

    def _create_invoice_line(self, invoice, line, price):
        """Helper function to create invoice line."""
        tax_ids = line.tax_id.ids if line.tax_id else []
        print(tax_ids, 'tax_idstax_ids')
        invoice_line = self.env['account.invoice.line'].create({
            'invoice_id': invoice.id,
            'product_catalog_id':line.product_catalog_id.id,
            'product_template_id':line.product_template_id.id,
            'product_id': line.product_id.id,
            'uom_id':line.product_uom.id,
            'quantity': line.qty_delivered,
            'price_unit': price,
            'name': line.name,
            'split_type': 'split',
            'invoice_line_tax_ids':[(6, 0, tax_ids)],
            'account_id': line.product_id.property_account_income_id.id or
                          line.product_id.categ_id.property_account_income_categ_id.id,
            'sale_line_ids': [(6, 0, [line.id])]
        })

        return invoice_line