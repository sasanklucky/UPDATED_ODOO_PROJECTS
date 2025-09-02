from odoo import models, fields, api,exceptions, _

class Customerfieldrestrict(models.Model):
    _inherit = 'crm.lead'

    has_quotation = fields.Boolean(
        string="Has Quotation", compute="_compute_has_quotation"
    )




    def _compute_has_quotation(self):
        for lead in self:
            count = self.env['sale.order'].search_count([
                ('opportunity_id', '=', lead.id),
                ('state', 'in', ['draft', 'sent','sale','done'])
            ])
            lead.has_quotation = bool(count)

    def write(self, vals):
        for lead in self:
            if lead.type == 'opportunity' and 'mobile' in vals:
                raise exceptions.UserError(_("You cannot change the mobile number for an opportunity."))
        return super(Customerfieldrestrict, self).write(vals)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_has_opportunities = fields.Boolean(
        string="Has Opportunity",
        compute="_compute_has_opportunity",
        store=False
    )

    def _compute_has_opportunity(self):
        for order in self:
            order.sale_has_opportunities = bool(order.opportunity_id)


class AccountInvoiceCustomerRestrict(models.Model):
    _inherit = 'account.invoice'

    has_invoice_lines = fields.Boolean(
        string="Has Invoice Lines",
        compute="_compute_has_invoice_lines",
        store=False
    )

    def _compute_has_opportunity_origin(self):
        for invoice in self:
            # Check if invoice is linked to a sale order that comes from an opportunity
            opportunity_origin = False
            if invoice.origin:
                # Check if origin is a sale order
                sale_orders = self.env['sale.order'].search([('name', '=', invoice.origin)])
                if sale_orders:
                    # Check if sale order has an opportunity
                    opportunity_origin = bool(sale_orders[0].opportunity_id)

            invoice.has_opportunity_origin = opportunity_origin

    def write(self, vals):
        # Prevent partner_id change if invoice has opportunity origin
        if 'partner_id' in vals:
            for invoice in self:
                if invoice.has_opportunity_origin:
                    raise exceptions.UserError(
                        _("You cannot change the customer for an invoice that originates from an opportunity.")
                    )
        return super(AccountInvoiceCustomerRestrict, self).write(vals)





