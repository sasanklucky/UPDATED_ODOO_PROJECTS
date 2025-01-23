import re

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
from odoo.exceptions import UserError
from lxml import etree
from openerp.osv.orm import setup_modifiers
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm
import json

# CRM LEAD
class BranchCrmLead(models.Model):
    _inherit = 'crm.lead'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchCrmLead, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )



    # @api.onchange('user_id')
    # def _onchange_user_id(self):
    #     if self.user_id and self.user_id.branch_id:
    #         self.branch_id = self.user_id.branch_id
    #     else:
    #         self.branch_id = False
    #
    #         print(self.user_id, 'user_id', self.branch_id)
    #
    # @api.onchange('company_id')
    # def _onchange_company_id(self):
    #     self.branch_id = self._get_branch_based_on_company(self.company_id)
    #
    # def _get_branch_based_on_company(self, company):
    #     branch = self.env['branch.master.company'].search([('company_id', '=', company.id)], limit=1)
    #     return branch.id if branch else False
    #
    # @api.model
    # def create(self, vals):
    #     if 'company_id' in vals and 'branch_id' not in vals:
    #         # Automatically set branch_id based on company_id if it's not provided
    #         company = self.env['res.company'].browse(vals['company_id'])
    #         vals['branch_id'] = self._get_branch_based_on_company(company)
    #
    #     if vals.get('user_id'):
    #         user = self.env['res.users'].browse(vals['user_id'])
    #         vals['branch_id'] = user.branch_id.id if user.branch_id else False
    #
    #     return super(BranchCrmLead, self).create(vals)
    #
    # # def write(self, vals):
    # #     if 'user_id' in vals:
    # #         user = self.env['res.users'].browse(vals['user_id'])
    # #         vals['branch_id'] = user.branch_id.id if user.branch_id else False
    # #         print(vals['branch_id'], 'vals11111111')
    # #     return super(BranchCrmLead, self).write(vals)
    #
    # def write(self, vals):
    #     if 'company_id' in vals and 'branch_id' not in vals:
    #         company = self.env['res.company'].browse(vals['company_id'])
    #         vals['branch_id'] = self._get_branch_based_on_company(company)
    #
    #     if 'user_id' in vals:
    #         user = self.env['res.users'].browse(vals['user_id'])
    #         vals['branch_id'] = user.branch_id.id if user.branch_id else False
    #     return super(BranchCrmLead, self).write(vals)


# SALE
class BranchSaleOrder(models.Model):
    _inherit = 'sale.order'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchSaleOrder, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    def action_confirm(self):
        res = super(BranchSaleOrder, self).action_confirm()

        for order in self:
            user_branch = self.env.user.branch_id
            if user_branch:
                order.picking_ids.write({'branch_id': user_branch.id})
            else:
                raise UserError("The current user does not have a branch assigned. Please set a branch for the user.")
        return res


    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )



# RES PARTNER BANK
class BranchRESPartner(models.Model):
    _inherit = 'res.partner.bank'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchRESPartner, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )


# Product Template
class BranchProductTemp(models.Model):
    _inherit = 'product.template'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchProductTemp, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )


#CRM Team
class CRMTeam(models.Model):
    _inherit = 'crm.team'

    branch_id = fields.Many2one('branch.master.company', 'Branch', domain="[('company_id', '=', company_id)]")

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(CRMTeam, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )
    #

#Vehicle
class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(FleetVehicle, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(ResPartner, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )


class StockProduction(models.Model):
    _inherit = 'stock.production.lot'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(StockProduction, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(AccountInvoice, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(ProductPricelist, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )
    #

class WebsitePage(models.Model):
    _inherit = 'website.page'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(WebsitePage, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )

#
# class Instructions(models.Model):
#     _inherit = 'instructions'
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch based on the logged-in user."""
#         res = super(Instructions, self).default_get(fields_list)
#         if self.env.user.branch_id:
#             res['branch_id'] = self.env.user.branch_id.id
#         return res
#
#     @api.onchange('company_id')
#     def _onchange_company_id(self):
#         """Update branch based on the company."""
#         if self.company_id:
#             # Set branch based on user's branch filtered by company
#             user_branch = self.env.user.branch_id
#             if user_branch and user_branch.company_id == self.company_id:
#                 self.branch_id = user_branch
#             else:
#                 self.branch_id = False
#         else:
#             # Clear the branch if no company is selected
#             self.branch_id = False
#
#     @api.constrains('branch_id')
#     def _check_branch_id(self):
#         """
#         Validate that the selected branch belongs to the logged-in user.
#         """
#         for record in self:
#             if record.branch_id and record.branch_id != self.env.user.branch_id:
#                 raise ValidationError(
#                     "You can only select your assigned branch. "
#                     "The branch you selected is not allowed for this user."
#                 )


class ResUserList(models.Model):
    _inherit = 'res.users'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(ResUserList, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False
    #
    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(MailActivity, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )

#
# class LeadsAnalysis(models.Model):
#     _inherit = 'crm.opportunity.report'
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)


#
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(HelpdeskTicket, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )

#
# class Estimation(models.Model):
#     _inherit = 'sale.order'
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)
#
#     @api.onchange('user_id')
#     def _onchange_user_id(self):
#         if self.user_id and self.user_id.branch_id:
#             self.branch_id = self.user_id.branch_id
#         else:
#             self.branch_id = False
#
#             print(self.user_id, 'user_id', self.branch_id)
#
#     @api.onchange('company_id')
#     def _onchange_company_id(self):
#         self.branch_id = self._get_branch_based_on_company(self.company_id)
#
#     def _get_branch_based_on_company(self, company):
#         branch = self.env['branch.master.company'].search([('company_id', '=', company.id)], limit=1)
#         return branch.id if branch else False
#
#     @api.model
#     def create(self, vals):
#         if 'company_id' in vals and 'branch_id' not in vals:
#             # Automatically set branch_id based on company_id if it's not provided
#             company = self.env['res.company'].browse(vals['company_id'])
#             vals['branch_id'] = self._get_branch_based_on_company(company)
#
#         if vals.get('user_id'):
#             user = self.env['res.users'].browse(vals['user_id'])
#             vals['branch_id'] = user.branch_id.id if user.branch_id else False
#
#         return super(Estimation, self).create(vals)
#
#
#     def write(self, vals):
#         if 'company_id' in vals and 'branch_id' not in vals:
#             company = self.env['res.company'].browse(vals['company_id'])
#             vals['branch_id'] = self._get_branch_based_on_company(company)
#
#         if 'user_id' in vals:
#             user = self.env['res.users'].browse(vals['user_id'])
#             vals['branch_id'] = user.branch_id.id if user.branch_id else False
#         return super(Estimation, self).write(vals)



class ChannelSales(models.Model):
    _inherit = 'report.all.channels.sales'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(ChannelSales, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class Website(models.Model):
    _inherit = 'website'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(Website, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

class WebPage(models.Model):
    _inherit = 'website.page'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(WebPage, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(PurchaseOrder, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(PurchaseOrderLine, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['company_id'] = self.env.user.company_id.id
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(PurchaseRequisition, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(ProductSupplierInfo, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class AccountMove(models.Model):
    _inherit = 'account.move'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(AccountMove, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


#
# class FleetVehicle(models.Model):
#     _inherit = 'fleet.vehicle'
#
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch based on the logged-in user."""
#         res = super(FleetVehicle, self).default_get(fields_list)
#         if self.env.user.branch_id:
#             res['branch_id'] = self.env.user.branch_id.id
#         return res
#
#     @api.onchange('company_id')
#     def _onchange_company_id(self):
#         """Update branch based on the company."""
#         if self.company_id:
#             # Set branch based on user's branch filtered by company
#             user_branch = self.env.user.branch_id
#             if user_branch and user_branch.company_id == self.company_id:
#                 self.branch_id = user_branch
#             else:
#                 self.branch_id = False
#         else:
#             # Clear the branch if no company is selected
#             self.branch_id = False


#
# class BranchAccountInvoice(models.Model):
#     _inherit = 'account.invoice'
#
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch based on the logged-in user."""
#         res = super(BranchAccountInvoice, self).default_get(fields_list)
#         if self.env.user.branch_id:
#             res['branch_id'] = self.env.user.branch_id.id
#         return res
#
#     @api.onchange('company_id')
#     def _onchange_company_id(self):
#         """Update branch based on the company."""
#         if self.company_id:
#             # Set branch based on user's branch filtered by company
#             user_branch = self.env.user.branch_id
#             if user_branch and user_branch.company_id == self.company_id:
#                 self.branch_id = user_branch
#             else:
#                 self.branch_id = False
#         else:
#             # Clear the branch if no company is selected
#             self.branch_id = False



class BranchStockPicking(models.Model):
    _inherit = 'stock.picking'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchStockPicking, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )


class BranchStockInventory(models.Model):
    _inherit = 'stock.inventory'


    branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchStockInventory, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchStockProduction(models.Model):
    _inherit = 'stock.production.lot'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchStockProduction, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class BranchWarehouse(models.Model):
    _inherit = 'stock.warehouse'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchWarehouse, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class BranchWarehouseLocation(models.Model):
    _inherit = 'stock.location'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchWarehouseLocation, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class BranchLocationRoute(models.Model):
    _inherit = 'stock.location.route'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchLocationRoute, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False



class BranchProcurement(models.Model):
    _inherit = 'procurement.rule'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchProcurement, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchProductProduct(models.Model):
    _inherit = 'product.product'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchProductProduct, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchMoveLine(models.Model):
    _inherit = 'account.move.line'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchMoveLine, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchAccountPayment(models.Model):
    _inherit = 'account.payment'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchAccountPayment, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchStockQuant(models.Model):
    _inherit = 'stock.quant'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchStockQuant, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


# class BranchAccountasset(models.Model):
#     _inherit = 'account.asset.asset'
#
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch based on the logged-in user."""
#         res = super(BranchAccountasset, self).default_get(fields_list)
#         if self.env.user.branch_id:
#             res['branch_id'] = self.env.user.branch_id.id
#         return res
#
#     @api.onchange('company_id')
#     def _onchange_company_id(self):
#         """Update branch based on the company."""
#         if self.company_id:
#             # Set branch based on user's branch filtered by company
#             user_branch = self.env.user.branch_id
#             if user_branch and user_branch.company_id == self.company_id:
#                 self.branch_id = user_branch
#             else:
#                 self.branch_id = False
#         else:
#             # Clear the branch if no company is selected
#             self.branch_id = False
#

#
# class BranchAssetCategory(models.Model):
#     _inherit = 'account.asset.category'
#
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch based on the logged-in user."""
#         res = super(BranchAssetCategory, self).default_get(fields_list)
#         if self.env.user.branch_id:
#             res['branch_id'] = self.env.user.branch_id.id
#         return res
#
#     @api.onchange('company_id')
#     def _onchange_company_id(self):
#         """Update branch based on the company."""
#         if self.company_id:
#             # Set branch based on user's branch filtered by company
#             user_branch = self.env.user.branch_id
#             if user_branch and user_branch.company_id == self.company_id:
#                 self.branch_id = user_branch
#             else:
#                 self.branch_id = False
#         else:
#             # Clear the branch if no company is selected
#             self.branch_id = False


class BranchAccountAccount(models.Model):
    _inherit = 'account.account'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchAccountAccount, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchAccountTax(models.Model):
    _inherit = 'account.tax'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchAccountTax, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchAccountFiscal(models.Model):
    _inherit = 'account.fiscal.position'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchAccountFiscal, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchAccountJournal(models.Model):
    _inherit = 'account.journal'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchAccountJournal, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchAccountFinancial(models.Model):
    _inherit = 'account.financial.html.report'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchAccountFinancial, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchHrPayslip(models.Model):
    _inherit = 'hr.payslip'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchHrPayslip, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchHrPayroll(models.Model):
    _inherit = 'hr.payroll.structure'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchHrPayroll, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchHrSalary(models.Model):
    _inherit = 'hr.salary.rule'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchHrSalary, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchHrReg(models.Model):
    _inherit = 'hr.contribution.register'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchHrReg, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchProjectTask(models.Model):
    _inherit = 'project.task'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchProjectTask, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchProjectTaskUser(models.Model):
    _inherit = 'report.project.task.user'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchProjectTaskUser, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchIrAttachment(models.Model):
    _inherit = 'ir.attachment'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchIrAttachment, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchAnalytic(models.Model):
    _inherit = 'account.analytic.line'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchAnalytic, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchHrEmployee(models.Model):
    _inherit = 'hr.employee'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchHrEmployee, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchHrContract(models.Model):
    _inherit = 'hr.contract'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchHrContract, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchHrDepartment(models.Model):
    _inherit = 'hr.department'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchHrDepartment, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchLabour(models.Model):
    _inherit = 'labour.group'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchLabour, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchApplicant(models.Model):
    _inherit = 'hr.applicant'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchApplicant, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class BranchHrJob(models.Model):
    _inherit = 'hr.job'


    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(BranchHrJob, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False


class AccountInvoiceAC(models.Model):
    _inherit = 'account.invoice'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(AccountInvoiceAC, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            self.branch_id = False

    # @api.constrains('branch_id')
    # def _check_branch_id(self):
    #     """
    #     Validate that the selected branch belongs to the logged-in user.
    #     """
    #     for record in self:
    #         if record.branch_id and record.branch_id != self.env.user.branch_id:
    #             raise ValidationError(
    #                 "You can only select your assigned branch. "
    #                 "The branch you selected is not allowed for this user."
    #             )



class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    branch_id = fields.Many2one('branch.master.company', 'Branch')

    @api.model
    def default_get(self, fields_list):
        """Set default branch based on the logged-in user."""
        res = super(StockWarehouse, self).default_get(fields_list)
        if self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Update branch based on the company."""
        if self.company_id:
            # Set branch based on user's branch filtered by company
            user_branch = self.env.user.branch_id
            if user_branch and user_branch.company_id == self.company_id:
                self.branch_id = user_branch
            else:
                self.branch_id = False
        else:
            # Clear the branch if no company is selected
            self.branch_id = False
