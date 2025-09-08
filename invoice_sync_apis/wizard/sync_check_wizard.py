from odoo import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class InvoiceSyncCheckWizard(models.Model):
    _name = 'invoice_sync_check_wizard'

    def _get_default_invoice_status(self):
        ids = self.env['account.invoice'].search([
            ('state', 'in', ['open','paid']),('sync_invoice', '=', False)])
        return ids

    sync_status_ids = fields.Many2many('account.invoice', string="Records Status",default=lambda self: self._get_default_invoice_status())


    @api.multi
    def invoice_sync_now(self):
        print("wiz called now---")
        if self.sync_status_ids:
            self.env['account.invoice']._cron_sync_invoice_to_parent()
        else:
            raise ValidationError(_('No Data (Invoice) found in Draft state.'))
