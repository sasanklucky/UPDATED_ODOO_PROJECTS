from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ARSCatalogInvoice(models.Model):
    _inherit = 'account.invoice'

    ars_type = fields.Selection([('general', 'General Bill'), ('vehicle', 'Vehicle Bill'),
                                 ('after_sales', 'After Sales Bill')], string='Bill Type')

    ars_invoice_type = fields.Selection([('general', 'General Invoice'), ('vehicle', 'Vehicle Invoice'),
                                         ('after_sales', 'After Sales Invoice')], string='Invoice Type')

    # @api.model
    # def create(self, values):
    #     print(values)
    #     res = super(ARSCatalogInvoice, self).create(values)
    #     return res

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if self.purchase_id:
            self.ars_type = self.purchase_id.purchase_type
        domain = super(ARSCatalogInvoice, self).purchase_order_change()
        return domain


class ARSaccount_journal(models.Model):
    _inherit = "account.journal"

    ars_type = fields.Selection([('general', 'General'), ('vehicle', 'Vehicle'),
                                 ('after_sales', 'Parts/After Sales')], string='Journal Type')





