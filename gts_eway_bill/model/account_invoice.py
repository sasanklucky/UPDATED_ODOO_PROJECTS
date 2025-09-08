from odoo import fields, api, _,models

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for invoice in self:
    #         name = invoice.sequence_number_next_prefix + invoice.sequence_number_next
    #         result.append((invoice.id, name))
    #     return result