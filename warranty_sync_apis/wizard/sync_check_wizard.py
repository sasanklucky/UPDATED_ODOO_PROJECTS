from odoo import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class WarrantySyncCheckWizard(models.Model):
    _name = 'warranty_sync_check_wizard'

    def _get_default_warranty_status(self):
        ids = self.env['ars.sale.warranty'].search([
            ('state', '=', 'draft'),('sync_warranty', '=', False)])
        return ids

    sync_status_ids = fields.Many2many('ars.sale.warranty', string="Records Status",default=lambda self: self._get_default_warranty_status())


    @api.multi
    def warranty_sync_now(self):
        print("wiz called now---")
        if self.sync_status_ids:
            self.env['ars.sale.warranty']._cron_warrenty_sync_to_child()
        else:
            raise ValidationError(_('No Data (Warranty) found.'))

class WarrantySyncCheckParentToChild(models.Model):
    _name = 'warranty_sync_checkparent_to_child_wizard'

    def _get_default_warranty_status(self):
        ids = self.env['ars.sale.warranty'].search([
            ('state', '=', 'draft'),('sync_warranty', '=', False)])
        return ids

    sync_status_ids = fields.Many2many('ars.sale.warranty', string="Records Status",default=lambda self: self._get_default_warranty_status())


    @api.multi
    def warranty_sync_now(self):
        print("wiz called now---")
        if self.sync_status_ids:
            self.env['ars.sale.warranty']._cron_warrenty_sync_to_child()
        else:
            raise ValidationError(_('No Data (Warranty) found.'))
