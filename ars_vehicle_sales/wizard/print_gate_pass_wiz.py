from datetime import date

from odoo import models, fields, api, _


class GatePassWizard(models.TransientModel):
    _name = 'gate.pass.wiz'

    @api.model
    def default_get(self, fields):
        defaults = super(GatePassWizard, self).default_get(fields)

        # Retrieve active invoice
        invoice_id = self.env.context.get('active_id')
        if invoice_id:
            # Read existing custom field values from the active invoice
            invoice = self.env['account.invoice'].browse(invoice_id)
            if 'delivery_type' in fields:
                defaults['delivery_type'] = invoice.delivery_type
            if 'after_sale_intro' in fields:
                defaults['after_sale_intro'] = invoice.after_sale_intro

        return defaults

    delivery_type = fields.Selection([('home_delivery', 'Home Delivery'), ('showroom', 'Showroom')])
    after_sale_intro = fields.Selection([('yes', 'Yes'), ('no', 'No')])

    @api.multi
    def action_print_gate_pass_wiz(self):
        invoice_id = self.env.context.get('active_id')
        if invoice_id:
            # Update the invoice with the custom field values
            invoice = self.env['account.invoice'].browse(invoice_id)
            invoice.write({
                'delivery_type': self.delivery_type,
                'after_sale_intro': self.after_sale_intro,
            })
        # if not self.gate_pass_date:
        # #     self.gate_pass_date = date.today()
        # data = self.env.ref('ars_vehicle_sales.gatepass_report').with_context(doc=invoice_id).report_action(invoice_id)
        return invoice
