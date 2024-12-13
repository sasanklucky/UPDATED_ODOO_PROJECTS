from odoo import fields,models


class ResBank(models.Model):
    _inherit = 'res.bank'

    beneficiary_name = fields.Char('Beneficiary Name')
    account_number = fields.Char('Account Number')
    ifsc_code = fields.Char('IFSC Code')
    branch_code = fields.Char('Branch Code')
    bank_code = fields.Char('Bank Code')


class ResCompany(models.Model):
    _inherit = 'res.company'

    bank_account_id = fields.Many2one('res.bank')
