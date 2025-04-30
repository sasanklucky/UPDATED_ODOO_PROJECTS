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
    # parent_id = fields.Many2one('branch.master.company', string='Parent Branch', index=True)
    # child_ids = fields.One2many('branch.master.company', 'parent_id', string='Child Branches')


#
# class BranchUserCompany(models.Model):
#     _inherit = 'res.users'
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch')
#


class ResUserList(models.Model):
    _inherit = 'res.users'

    branch_id = fields.Many2one(
        'branch.master.company',
        string='Branch'
    )

    allowed_branch_ids = fields.Many2many(
        'branch.master.company',
        'branch_user_rel',
        'user_id',
        'branch_id',
        string='Allowed Branches', ondelete='cascade'
    )

    @api.model
    def default_get(self, fields_list):
        res = super(ResUserList, self).default_get(fields_list)
        if self.env.user.exists() and self.env.user.branch_id:
            res['allowed_branch_ids'] = [(6, 0, self.env.user.allowed_branch_ids.ids)]
        return res

    @api.onchange('company_ids')
    def _onchange_company_id(self):
        if self.company_ids:
            selected_company_ids = self.company_ids.ids

            user_branch_allowed = self.allowed_branch_ids.filtered(lambda b: b.company_id.id in selected_company_ids)
            user_branch = self.branch_id if self.branch_id.company_id.id in selected_company_ids else False

            self.allowed_branch_ids = user_branch_allowed if user_branch_allowed else False
            self.branch_id = user_branch if user_branch else False
        else:
            self.allowed_branch_ids = False
            self.branch_id = False

    @api.onchange('allowed_branch_ids')
    def _onchange_allowed_branch_ids(self):
        if self.branch_id and self.branch_id not in self.allowed_branch_ids:
            self.branch_id = False

    @api.multi
    def write(self, vals):
        if 'company_id' in vals and len(vals) == 1:
            vals['branch_id'] = False
        return super(ResUserList, self).write(vals)

