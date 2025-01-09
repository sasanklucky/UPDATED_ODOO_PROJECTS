from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class BranchMasterCompany(models.Model):
    _name = 'branch.master.company'
    _description = 'Location Master'
    _rec_name = 'name'

    name = fields.Char('Branch')
    company_id = fields.Many2one('res.company', 'Company', required=True)
    partner_id = fields.Many2one('res.partner', string="User")



class BranchUserCompany(models.Model):
    _inherit = 'res.users'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

