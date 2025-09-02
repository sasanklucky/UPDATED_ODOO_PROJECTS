from odoo import models, fields, api, _
from datetime import datetime, timedelta, date

class GatePassButtonWizard(models.TransientModel):
    _name = 'ars.gate.pass.wizard'
    _description = 'Gate Pass Wizard'

    invoice_id = fields.Many2one('account.invoice', string="Invoice", required=True)
    remarks = fields.Text(string="Remarks")

    def action_print_gate_pass(self):
        invoice = self.invoice_id

        invoice.write({
            'gate_pass_remarks': self.remarks,
        })

        param = self.env['ir.config_parameter'].sudo()
        sale_days = int(param.get_param('ars_mail_survey.sale_followup_days') or '0')
        postsale_days = int(param.get_param('ars_mail_survey.postsale_followup_days') or '0')

        gate_pass = invoice.gate_pass_date
        if isinstance(gate_pass, str):
            gate_pass = datetime.strptime(gate_pass, "%Y-%m-%d").date()

        activity = self.env['mail.activity'].search([
            ('invoice_id', '=', invoice.id),
            ('invoice_type', 'in', ['sales', 'after_sales'])
        ], limit=1)

        if activity:
            days = sale_days if activity.invoice_type == 'sales' else postsale_days
            exact_due_date = gate_pass + timedelta(days=days)
            activity.write({'exact_psf_due_date': exact_due_date})

        return self.env.ref('ars_vehicle_sales.gatepass_report') \
            .with_context(doc=invoice).report_action(invoice)