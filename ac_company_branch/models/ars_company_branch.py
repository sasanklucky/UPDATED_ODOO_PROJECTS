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
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_lead_rel', 'lead_id', 'branch_id', compute='_compute_user_allowed_branch_ids', string='Allowed Branches', ondelete='cascade')

    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            # Set the allowed branches for the lead to the allowed branches of the current user
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        res = super(BranchCrmLead, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
        return res

    @api.onchange('company_ids')
    def _onchange_company_id(self):
        if self.company_ids:
            selected_company_ids = self.company_ids.ids

            # Get the allowed branches for the selected companies
            user_branch_allowed = self.allowed_branch_ids.filtered(lambda b: b.company_id.id in selected_company_ids)
            user_branch = self.branch_id if self.branch_id.company_id.id in selected_company_ids else False

            # Update allowed branches and branch based on selected companies
            self.allowed_branch_ids = user_branch_allowed if user_branch_allowed else False
            self.branch_id = user_branch if user_branch else False
        else:
            self.allowed_branch_ids = False
            self.branch_id = False

    @api.onchange('allowed_branch_ids')
    def _onchange_allowed_branch_ids(self):
        # If branch_id is not in allowed_branch_ids, set it to False
        if self.branch_id and self.branch_id not in self.allowed_branch_ids:
            self.branch_id = False

    @api.model
    def create(self, vals):
        # Ensure the correct allowed branch_ids are set when creating the lead
        lead = super(BranchCrmLead, self).create(vals)

        if lead.branch_id:
            message = _(" A New Lead has been added in '%s'. '%s' branch.") % (lead.company_id.name, lead.branch_id.name)
        else:
            message = _(" A New Lead has been added in '%s'. Without branch.") % (lead.company_id.name)

        lead.env.user.notify_info(message)

        return lead



# class BranchCrmLead(models.Model):
#     _inherit = 'crm.lead'
#
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch')
#     allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_lead_rel', 'lead_id', 'branch_id', compute='_compute_user_allowed_branch_ids', string='Allowed Branches' , ondelete='cascade', store=True)
#
#     # @api.depends('user_id')
#     def _compute_user_allowed_branch_ids(self):
#         for rec in self:
#             rec.allowed_branch_ids = self.env.user.allowed_branch_ids
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch and allowed branches based on the logged-in user."""
#         res = super(BranchCrmLead, self).default_get(fields_list)
#         user = self.env.user
#         if user.branch_id:
#             res['branch_id'] = user.branch_id.id
#         if user.allowed_branch_ids:
#             res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
#
#         return res
#
#
#     @api.onchange('company_ids')
#     def _onchange_company_id(self):
#         if self.company_ids:
#             selected_company_ids = self.company_ids.ids
#
#             user_branch_allowed = self.allowed_branch_ids.filtered(lambda b: b.company_id.id in selected_company_ids)
#             user_branch = self.branch_id if self.branch_id.company_id.id in selected_company_ids else False
#
#             self.allowed_branch_ids = user_branch_allowed if user_branch_allowed else False
#             self.branch_id = user_branch    if user_branch else False
#         else:
#             self.allowed_branch_ids = False
#             self.branch_id = False
#
#     @api.onchange('allowed_branch_ids')
#     def _onchange_allowed_branch_ids(self):
#         if self.branch_id and self.branch_id not in self.allowed_branch_ids:
#             self.branch_id = False
#
#     @api.model
#     def create(self, vals):
#         lead = super(BranchCrmLead, self).create(vals)
#
#         if lead.branch_id:
#             message = _(" A New Lead has been added in '%s'. '%s' branch.") % (lead.company_id.name, lead.branch_id.name)
#         else:
#             message = _(" A New Lead has been added in '%s'. Without branch.") % (lead.company_id.name)
#
#         lead.env.user.notify_info(message)
#
#         return lead


# SALE
class BranchSaleOrder(models.Model):
    _inherit = 'sale.order'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_sale_rel', 'order_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids


    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchSaleOrder, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        current_user_branch = self.env.user.branch_id

        # Check if linked to a CRM Lead (usually via 'opportunity_id')
        if vals.get('opportunity_id'):
            lead = self.env['crm.lead'].browse(vals['opportunity_id'])

            if lead.branch_id and lead.branch_id.id != current_user_branch.id:
                raise ValidationError(_(
                    "Access Denied: Your current branch is '%s' does not match, the transaction's branch is '%s'."
                ) % (current_user_branch.name or 'N/A', lead.branch_id.name or 'N/A'))

        # Create the Sale Order
        order = super(BranchSaleOrder, self).create(vals)

        # Notification
        if order.branch_id:
            message = _("A new Sale Order has been added in '%s' (%s branch).") % (
                order.company_id.name, order.branch_id.name)
        else:
            message = _("A new Sale Order has been added in '%s' without a branch.") % order.company_id.name

        order.env.user.notify_info(message)

        return order

    # @api.model
    # def create(self, vals):
    #     order = super(BranchSaleOrder, self).create(vals)
    #
    #     if order.branch_id:
    #         message = _(" A New Sale Order has been added in '%s'. '%s' branch.") % (order.company_id.name, order.branch_id.name)
    #     else:
    #         message = _(" A New Sale Order has been added in '%s'. Without branch.") % (order.company_id.name)
    #
    #     order.env.user.notify_info(message)
    #
    #     return order

    # Validation error on suppose branch value didnt have in current company
    # @api.constrains('branch_id', 'allowed_branch_ids', 'company_id')
    # def _check_branch_allowed_and_company(self):
    #     for record in self:
    #         if record.branch_id:
    #
    #             if record.company_id and record.branch_id.company_id != record.company_id:
    #                 raise ValidationError("That branch value didn't map in current company.")


# RES PARTNER BANK
class BranchRESPartner(models.Model):
    _inherit = 'res.partner.bank'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_bank_rel', 'bank_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchRESPartner, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        bank = super(BranchRESPartner, self).create(vals)

        if bank.branch_id:
            message = _(" A New Res Partner Bank has been added in '%s'. '%s' branch.") % (
            bank.company_id.name, bank.branch_id.name)
        else:
            message = _(" A New Res Partner Bank has been added in '%s'. Without branch.") % (bank.company_id.name)

        bank.env.user.notify_info(message)

        return bank


# Product Template
class BranchProductTemp(models.Model):
    _inherit = 'product.template'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_template_rel', 'template_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchProductTemp, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        product = super(BranchProductTemp, self).create(vals)

        if product.branch_id:
            message = _(" A New Product Template has been added in '%s'. '%s' branch.") % (
                product.company_id.name, product.branch_id.name)
        else:
            message = _(" A New Product Template has been added in '%s'. Without branch.") % (product.company_id.name)

        product.env.user.notify_info(message)

        return product

#CRM Team
class CRMTeam(models.Model):
    _inherit = 'crm.team'

    branch_id = fields.Many2one('branch.master.company', 'Branch', domain="[('company_id', '=', company_id)]")
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_team_rel', 'team_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(CRMTeam, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        team = super(CRMTeam, self).create(vals)

        if team.branch_id:
            message = _(" A New CRM Team has been added in '%s'. '%s' branch.") % (
                team.company_id.name, team.branch_id.name)
        else:
            message = _(" A New CRM Team has been added in '%s'. Without branch.") % (team.company_id.name)

        team.env.user.notify_info(message)

        return team


#Vehicle
# class FleetVehicle(models.Model):
#     _inherit = 'fleet.vehicle'
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch')
#     allowed_branch_ids = fields.Many2many(
#         'branch.master.company',
#         'branch_fleet_vehicle_rel',
#         'vehicle_id',
#         'branch_id',
#         compute='_compute_user_allowed_branch_ids',
#         string='Allowed Branches',
#         ondelete='cascade', store=False
#     )
#
#     # @api.depends('user_id')
#     def _compute_user_allowed_branch_ids(self):
#         for rec in self:
#             rec.allowed_branch_ids = self.env.user.allowed_branch_ids
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch and allowed branches based on the logged-in user."""
#         res = super(FleetVehicle, self).default_get(fields_list)
#         user = self.env.user
#         if user.branch_id:
#             res['branch_id'] = user.branch_id.id
#         if user.allowed_branch_ids:
#             res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
#         return res
#
#     @api.onchange('company_ids')
#     def _onchange_company_id(self):
#         if self.company_ids:
#             selected_company_ids = self.company_ids.ids
#
#             user_branch_allowed = self.allowed_branch_ids.filtered(lambda b: b.company_id.id in selected_company_ids)
#             user_branch = self.branch_id if self.branch_id.company_id.id in selected_company_ids else False
#
#             self.allowed_branch_ids = user_branch_allowed if user_branch_allowed else False
#             self.branch_id = user_branch if user_branch else False
#         else:
#             self.allowed_branch_ids = False
#             self.branch_id = False
#
#     @api.onchange('allowed_branch_ids')
#     def _onchange_allowed_branch_ids(self):
#         if self.branch_id and self.branch_id not in self.allowed_branch_ids:
#             self.branch_id = False
#
#     # @api.model
#     def create(self, vals):
#         vehicle = super(FleetVehicle, self).create(vals)
#
#         if vehicle.branch_id:
#             message = _(" A New Fleet Vehicle has been added in '%s'. '%s' branch.") % (
#                 vehicle.company_id.name, vehicle.branch_id.name)
#         else:
#             message = _(" A New Fleet Vehicle has been added in '%s'. Without branch.") % (vehicle.company_id.name)
#
#         vehicle.env.user.notify_info(message)
#
#         return vehicle

class ResPartner(models.Model):
    _inherit = 'res.partner'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_partner_rel', 'partner_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(ResPartner, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)

        if partner.branch_id:
            message = _(" A New Partner has been added in '%s'. '%s' branch.") % (
                partner.company_id.name, partner.branch_id.name)
        else:
            message = _(" A New Partner has been added in '%s'. Without branch.") % (partner.company_id.name)

        partner.env.user.notify_info(message)

        return partner


class StockProduction(models.Model):
    _inherit = 'stock.production.lot'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_stock_rel', 'stock_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids


    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(StockProduction, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        stock = super(StockProduction, self).create(vals)

        if stock.branch_id:
            message = _(" A New Stock Production Lot has been added in '%s'. '%s' branch.") % (
                stock.company_id.name, stock.branch_id.name)
        else:
            message = _(" A New Stock Production Lot has been added in '%s'. Without branch.") % (stock.company_id.name)

        stock.env.user.notify_info(message)

        return stock
#
# class AccountInvoice(models.Model):
#     _inherit = 'account.invoice'
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch')
#     allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_invoice_rel', 'invoice_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
#                                           string='Allowed Branches', ondelete='cascade', store=True)
#
#     # @api.depends('user_id')
#     def _compute_user_allowed_branch_ids(self):
#         for rec in self:
#             rec.allowed_branch_ids = self.env.user.allowed_branch_ids
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch and allowed branches based on the logged-in user."""
#         res = super(AccountInvoice, self).default_get(fields_list)
#         user = self.env.user
#         if user.branch_id:
#             res['branch_id'] = user.branch_id.id
#         if user.allowed_branch_ids:
#             res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
#         return res
#
#     @api.onchange('company_ids')
#     def _onchange_company_id(self):
#         if self.company_ids:
#             selected_company_ids = self.company_ids.ids
#
#             user_branch_allowed = self.allowed_branch_ids.filtered(lambda b: b.company_id.id in selected_company_ids)
#             user_branch = self.branch_id if self.branch_id.company_id.id in selected_company_ids else False
#
#             self.allowed_branch_ids = user_branch_allowed if user_branch_allowed else False
#             self.branch_id = user_branch if user_branch else False
#         else:
#             self.allowed_branch_ids = False
#             self.branch_id = False
#
#     @api.onchange('allowed_branch_ids')
#     def _onchange_allowed_branch_ids(self):
#         if self.branch_id and self.branch_id not in self.allowed_branch_ids:
#             self.branch_id = False
#
#     @api.model
#     def create(self, vals):
#         invoice = super(AccountInvoice, self).create(vals)
#
#         if invoice.branch_id:
#             message = _(" A New Invoice has been added in '%s'. '%s' branch.") % (
#                 invoice.company_id.name, invoice.branch_id.name)
#         else:
#             message = _(" A New Invoice has been added in '%s'. Without branch.") % (invoice.company_id.name)
#
#         invoice.env.user.notify_info(message)
#
#         return invoice


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many(
        'branch.master.company',
        'branch_invoice_rel',
        'invoice_id',
        'branch_id',
        compute='_compute_user_allowed_branch_ids',
        string='Allowed Branches'
    )

    @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def create(self, vals):
        # Current user's branch
        current_user_branch = self.env.user.branch_id

        # Get or fallback to user's branch if not passed in
        invoice_branch_id = vals.get('branch_id') or current_user_branch.id

        # Get related sale order (from invoice 'origin' field)
        sale_order = None
        if vals.get('origin'):
            sale_order = self.env['sale.order'].search([
                ('name', '=', vals['origin'])
            ], limit=1)

        # Validate branch if sale order found
        if sale_order:
            order_branch_id = sale_order.branch_id.id
            if current_user_branch.id != order_branch_id:
                raise ValidationError(_(
                    "Your branch does not match the transaction branch: '%s'."
                ) % sale_order.branch_id.name)

            # Ensure invoice gets the correct branch_id from the order if missing
            if not vals.get('branch_id'):
                vals['branch_id'] = order_branch_id

        # Create the invoice using super
        invoice = super(AccountInvoice, self).create(vals)

        # Notify after creation
        if invoice.branch_id:
            message = _("A new invoice has been added in '%s' (%s branch).") % (
                invoice.company_id.name, invoice.branch_id.name)
        else:
            message = _("A new invoice has been added in '%s' without a branch.") % (
                invoice.company_id.name)

        self.env.user.notify_info(message)

        return invoice


    # @api.model
    # def create(self, vals):
    #     # Current user's branch
    #     current_user_branch = self.env.user.branch_id
    #
    #     # Get or fallback to user's branch if not passed in
    #     invoice_branch_id = vals.get('branch_id') or current_user_branch.id
    #
    #     # Get related sale order (from invoice 'origin' field)
    #     sale_order = None
    #     if vals.get('origin'):
    #         sale_order = self.env['sale.order'].search([
    #             ('name', '=', vals['origin'])
    #         ], limit=1)
    #
    #     # Validate branch if sale order found
    #     if sale_order:
    #         order_branch_id = sale_order.branch_id.id
    #         if current_user_branch.id != order_branch_id:
    #             raise ValidationError(_(
    #                 "Your branch does not match the transaction branch: '%s'."
    #             ) % sale_order.branch_id.name)
    #
    #         # Ensure invoice gets the correct branch_id from the order if missing
    #         if not vals.get('branch_id'):
    #             vals['branch_id'] = order_branch_id
    #
    #     return super(AccountInvoice, self).create(vals)

    # def write(self, vals):
    #     current_user_branch = self.env.user.branch_id
    #
    #     for invoice in self:
    #         # Use new or existing branch value
    #         new_branch_id = vals.get('branch_id', invoice.branch_id.id)
    #
    #         # Try to get linked sale order from origin
    #         sale_order = None
    #         if invoice.origin:
    #             sale_order = self.env['sale.order'].search([
    #                 ('name', '=', invoice.origin)
    #             ], limit=1)
    #
    #         if sale_order:
    #             if current_user_branch.id != sale_order.branch_id.id:
    #                 raise ValidationError(_(
    #                     "Your branch does not match the transaction branch: '%s'."
    #                 ) % sale_order.branch_id.name)
    #
    #     return super(AccountInvoice, self).write(vals)


    def write(self, vals):
        # active_model = self.env.context['params']
        uid = self.env.context['uid'] if 'uid' in self.env.context else False
        # user =current_user_branch= False
        # if active_model['active_model'] == 'sale.order' and uid:
        user = self.env['res.users'].browse(uid)
        current_user_branch = user.branch_id
        for invoice in self:
            print(self.env.context)
            # current_user_branch = self.env.user.branch_id
            new_branch_id = vals.get('branch_id', invoice.branch_id.id)

            # Try to get linked sale or purchase order from origin
            sale_order = purchase_order = None
            if invoice.origin:
                sale_order = self.env['sale.order'].search([('name', '=', invoice.origin)], limit=1)
                purchase_order = self.env['purchase.order'].search([('name', '=', invoice.origin)], limit=1)

            if sale_order:
                transaction_branch = sale_order.branch_id
                if current_user_branch.id != transaction_branch.id:
                    raise ValidationError(_(
                        "Access Denied: Your current branch '%s' does not match the Sale Order's branch '%s'."
                    ) % (current_user_branch.name or 'N/A', transaction_branch.name or 'N/A'))

            elif purchase_order:
                transaction_branch = purchase_order.branch_id
                if current_user_branch.id != transaction_branch.id:
                    raise ValidationError(_(
                        "Access Denied: Your current branch '%s' does not match the Purchase Order's branch '%s'."
                    ) % (current_user_branch.name or 'N/A', transaction_branch.name or 'N/A'))

        return super(AccountInvoice, self).write(vals)



class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_price_rel', 'list_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(ProductPricelist, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        productprice = super(ProductPricelist, self).create(vals)

        if productprice.branch_id:
            message = _(" A New Product PriceList has been added in '%s'. '%s' branch.") % (
                productprice.company_id.name, productprice.branch_id.name)
        else:
            message = _(" A New Product PriceList has been added in '%s'. Without branch.") % (productprice.company_id.name)

        productprice.env.user.notify_info(message)

        return productprice


class WebsitePage(models.Model):
    _inherit = 'website.page'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_page_rel', 'page_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(WebsitePage, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        websitepage = super(WebsitePage, self).create(vals)

        if websitepage.branch_id:
            message = _(" A New Website Page has been added in '%s'. '%s' branch.") % (
                websitepage.company_id.name, websitepage.branch_id.name)
        else:
            message = _(" A New Website Page has been added in '%s'. Without branch.") % (websitepage.company_id.name)

        websitepage.env.user.notify_info(message)

        return websitepage

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_mail_rel', 'mail_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(MailActivity, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        mailactivity = super(MailActivity, self).create(vals)

        if mailactivity.branch_id:
            message = _(" A New Mail Activity has been added in '%s'. '%s' branch.") % (
                mailactivity.company_id.name, mailactivity.branch_id.name)
        else:
            message = _(" A New Mail Activity has been added in '%s'. Without branch.") % (mailactivity.company_id.name)

        mailactivity.env.user.notify_info(message)

        return mailactivity

#
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_ticket_rel', 'ticket_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(HelpdeskTicket, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        halpdek = super(HelpdeskTicket, self).create(vals)

        if halpdek.branch_id:
            message = _(" A New Helpdesk Ticket has been added in '%s'. '%s' branch.") % (
                halpdek.company_id.name, halpdek.branch_id.name)
        else:
            message = _(" A New Helpdesk Ticket has been added in '%s'. Without branch.") % (halpdek.company_id.name)

        halpdek.env.user.notify_info(message)

        return halpdek


class ChannelSales(models.Model):
    _inherit = 'report.all.channels.sales'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_sales_rel', 'channel_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(ChannelSales, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        channelsales = super(ChannelSales, self).create(vals)

        if channelsales.branch_id:
            message = _(" A New Sales Channels has been added in '%s'. '%s' branch.") % (
                channelsales.company_id.name, channelsales.branch_id.name)
        else:
            message = _(" A New Sales Channels has been added in '%s'. Without branch.") % (channelsales.company_id.name)

        channelsales.env.user.notify_info(message)

        return channelsales


class Website(models.Model):
    _inherit = 'website'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_website_rel', 'website_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(Website, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        website = super(Website, self).create(vals)

        if website.branch_id:
            message = _(" A New Website has been added in '%s'. '%s' branch.") % (
                website.company_id.name, website.branch_id.name)
        else:
            message = _(" A New Website has been added in '%s'. Without branch.") % (website.company_id.name)

        website.env.user.notify_info(message)

        return website

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_purchase_rel', 'purchase_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(PurchaseOrder, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        purchaseorder = super(PurchaseOrder, self).create(vals)

        if purchaseorder.branch_id:
            message = _(" A New Purchase Order has been added in '%s'. '%s' branch.") % (
                purchaseorder.company_id.name, purchaseorder.branch_id.name)
        else:
            message = _(" A New Purchase Order has been added in '%s'. Without branch.") % (purchaseorder.company_id.name)

        purchaseorder.env.user.notify_info(message)

        return purchaseorder

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_line_rel', 'order_line_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(PurchaseOrderLine, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        orderline = super(PurchaseOrderLine, self).create(vals)

        if orderline.branch_id:
            message = _(" A New Purchase OrderLine has been added in '%s'. '%s' branch.") % (
                orderline.company_id.name, orderline.branch_id.name)
        else:
            message = _(" A New Purchase OrderLine has been added in '%s'. Without branch.") % (orderline.company_id.name)

        orderline.env.user.notify_info(message)

        return orderline

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_requisition_rel', 'requisition_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(PurchaseRequisition, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        purchase = super(PurchaseRequisition, self).create(vals)

        if purchase.branch_id:
            message = _(" A New Purchase Requisition has been added in '%s'. '%s' branch.") % (
                purchase.company_id.name, purchase.branch_id.name)
        else:
            message = _(" A New Purchase Requisition has been added in '%s'. Without branch.") % (purchase.company_id.name)

        purchase.env.user.notify_info(message)

        return purchase


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_supplier_rel', 'supplier_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(ProductSupplierInfo, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        productsupplier = super(ProductSupplierInfo, self).create(vals)

        if productsupplier.branch_id:
            message = _(" A New Product Supplierinfo has been added in '%s'. '%s' branch.") % (
                productsupplier.company_id.name, productsupplier.branch_id.name)
        else:
            message = _(" A New Product Supplierinfo has been added in '%s'. Without branch.") % (productsupplier.company_id.name)

        productsupplier.env.user.notify_info(message)

        return productsupplier


class AccountMove(models.Model):
    _inherit = 'account.move'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_move_rel', 'move_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(AccountMove, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        move = super(AccountMove, self).create(vals)

        if move.branch_id:
            message = _(" A New Account Move has been added in '%s'. '%s' branch.") % (
                move.company_id.name, move.branch_id.name)
        else:
            message = _(" A New Account Move has been added in '%s'. Without branch.") % (move.company_id.name)

        move.env.user.notify_info(message)

        return move


class BranchStockPicking(models.Model):
    _inherit = 'stock.picking'


    branch_id = fields.Many2one('branch.master.company', 'Branch', compute='_compute_user_allowed_branch_id', store=True,inverse='_compute_user_allowed_branch_id')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_picking_rel', 'picking_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        print('BRANCH IDSSS')
        for rec in self:
            if not rec.allowed_branch_ids:
                rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    def _compute_user_allowed_branch_id(self):
        uid = self.env.context['uid'] if 'uid' in self.env.context else False
        user = self.env['res.users'].browse(uid)
        for rec in self:
        # user = self.env.user
            if user.branch_id and not rec.branch_id:
                rec.branch_id = user.branch_id.id


    # @api.model
    # def default_get(self, fields_list):
    #     """Set default branch and allowed branches based on the logged-in user."""
    #     res = super(BranchStockPicking, self).default_get(fields_list)
    #     uid = self.env.context['uid'] if 'uid' in self.env.context else False
    #     user = self.env['res.users'].browse(uid)
    #     # user = self.env.user
    #     if user.branch_id:
    #         res['branch_id'] = user.branch_id.id
    #     if user.allowed_branch_ids:
    #         res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
    #     return res

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

    @api.model
    def create(self, vals):
        stockpicking = super(BranchStockPicking, self).create(vals)

        if stockpicking.branch_id:
            message = _(" A New Stock Picking has been added in '%s'. '%s' branch.") % (stockpicking.company_id.name, stockpicking.branch_id.name)
        else:
            message = _(" A New Stock Picking has been added in '%s'. Without branch.") % (stockpicking.company_id.name)

        stockpicking.env.user.notify_info(message)

        return stockpicking

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        res = super(StockMove, self)._get_new_picking_values()

        # Pass branch_id from sale order if available
        if self.sale_line_id and self.sale_line_id.order_id.branch_id:
            res['branch_id'] = self.sale_line_id.order_id.branch_id.id

        return res



class BranchStockInventory(models.Model):
    _inherit = 'stock.inventory'


    branch_id = fields.Many2one('branch.master.company', 'Branch', required=True)
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_inventory_rel', 'inventory_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchStockInventory, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchStockInventory, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Stock Inventory has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Stock Inventory has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle
#
# class BranchStockProduction(models.Model):
#     _inherit = 'stock.production.lot'
#
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch')
#     allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_lot_rel', 'lot_id', 'branch_id',
#                                           string='Allowed Branches', ondelete='cascade')
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch and allowed branches based on the logged-in user."""
#         res = super(BranchStockProduction, self).default_get(fields_list)
#         user = self.env.user
#         if user.branch_id:
#             res['branch_id'] = user.branch_id.id
#         if user.allowed_branch_ids:
#             res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
#         return res
#
#     @api.onchange('company_ids')
#     def _onchange_company_id(self):
#         if self.company_ids:
#             selected_company_ids = self.company_ids.ids
#
#             user_branch_allowed = self.allowed_branch_ids.filtered(lambda b: b.company_id.id in selected_company_ids)
#             user_branch = self.branch_id if self.branch_id.company_id.id in selected_company_ids else False
#
#             self.allowed_branch_ids = user_branch_allowed if user_branch_allowed else False
#             self.branch_id = user_branch if user_branch else False
#         else:
#             self.allowed_branch_ids = False
#             self.branch_id = False
#
#     @api.onchange('allowed_branch_ids')
#     def _onchange_allowed_branch_ids(self):
#         if self.branch_id and self.branch_id not in self.allowed_branch_ids:
#             self.branch_id = False
#
#     # @api.model
#     def create(self, vals):
#         vehicle = super(BranchStockProduction, self).create(vals)
#
#         if vehicle.branch_id:
#             message = _(" A New Lead has been added in '%s'. '%s' branch.") % (
#                 vehicle.company_id.name, vehicle.branch_id.name)
#         else:
#             message = _(" A New Lead has been added in '%s'. Without branch.") % (vehicle.company_id.name)
#
#         vehicle.env.user.notify_info(message)
#
#         return vehicle


class BranchWarehouse(models.Model):
    _inherit = 'stock.warehouse'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_warehouse_rel', 'warehouse_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchWarehouse, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchWarehouse, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Warehouse has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Warehouse has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchWarehouseLocation(models.Model):
    _inherit = 'stock.location'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_location_rel', 'location_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchWarehouseLocation, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchWarehouseLocation, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Location has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Location has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchLocationRoute(models.Model):
    _inherit = 'stock.location.route'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_route_rel', 'route_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchLocationRoute, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchLocationRoute, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Stock Location Route has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Stock Location Route has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchProcurement(models.Model):
    _inherit = 'procurement.rule'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_rule_rel', 'rule_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchProcurement, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchProcurement, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Procurement Rule has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Procurement Rule has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchProductProduct(models.Model):
    _inherit = 'product.product'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_product_product_rel', 'product_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchProductProduct, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchProductProduct, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Product has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Product has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchMoveLine(models.Model):
    _inherit = 'account.move.line'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_move_line_rel', 'move_line_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchMoveLine, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchMoveLine, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Move Line has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Move Line has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchAccountPayment(models.Model):
    _inherit = 'account.payment'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_payment_rel', 'payment_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchAccountPayment, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchAccountPayment, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Payment has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Payment has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchStockQuant(models.Model):
    _inherit = 'stock.quant'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_quant_rel', 'quant_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchStockQuant, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchStockQuant, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Stock Quant has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Stock Quant has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchAccountAccount(models.Model):
    _inherit = 'account.account'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_account_rel', 'account_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchAccountAccount, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchAccountAccount, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Account has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Account has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchAccountTax(models.Model):
    _inherit = 'account.tax'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_tax_rel', 'tax_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchAccountTax, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchAccountTax, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Tax has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Tax has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchAccountFiscal(models.Model):
    _inherit = 'account.fiscal.position'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_fiscal_rel', 'fiscal_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchAccountFiscal, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchAccountFiscal, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Fiscal Position has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Fiscal Position has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle



class BranchAccountJournal(models.Model):
    _inherit = 'account.journal'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_journal_rel', 'journal_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchAccountJournal, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchAccountJournal, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Journal has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Journal has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchAccountFinancial(models.Model):
    _inherit = 'account.financial.html.report'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_financial_rel', 'financial_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchAccountFinancial, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchAccountFinancial, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Account Financial has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Account Financial has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchHrPayslip(models.Model):
    _inherit = 'hr.payslip'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_payslip_rel', 'payslip_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchHrPayslip, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchHrPayslip, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Payslip has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Payslip has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchHrPayroll(models.Model):
    _inherit = 'hr.payroll.structure'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_payroll_rel', 'payroll_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids


    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchHrPayroll, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchHrPayroll, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Payroll Structure has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Payroll Structure has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchHrSalary(models.Model):
    _inherit = 'hr.salary.rule'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_rule_rel', 'rule_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchHrSalary, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchHrSalary, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Salary Rule has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Salary Rule has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchHrReg(models.Model):
    _inherit = 'hr.contribution.register'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_register_rel', 'register_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchHrReg, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchHrReg, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Contribution has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Contribution has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchProjectTask(models.Model):
    _inherit = 'project.task'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_task_rel', 'task_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchProjectTask, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchProjectTask, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Project Task has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Project Task has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchProjectTaskUser(models.Model):
    _inherit = 'report.project.task.user'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_task_user_rel', 'task_user_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchProjectTaskUser, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchProjectTaskUser, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Project Task User has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Project Task User has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchIrAttachment(models.Model):
    _inherit = 'ir.attachment'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_attachment_rel', 'attachment_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchIrAttachment, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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
    #
    @api.model
    def create(self, vals):
        vehicle = super(BranchIrAttachment, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Attachment has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Attachment has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle



class BranchAnalytic(models.Model):
    _inherit = 'account.analytic.line'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_analytic_line_rel', 'analytic_line_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchAnalytic, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchAnalytic, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Analytic Line has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Analytic Line has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchHrEmployee(models.Model):
    _inherit = 'hr.employee'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_employee_rel', 'employee_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchHrEmployee, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchHrEmployee, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Employee has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Employee has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchHrContract(models.Model):
    _inherit = 'hr.contract'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_contract_rel', 'contract_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchHrContract, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchHrContract, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Contract has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Contract has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchHrDepartment(models.Model):
    _inherit = 'hr.department'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_department_rel', 'department_id', 'branch_id',compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchHrDepartment, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchHrDepartment, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Department has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Department has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle


class BranchLabour(models.Model):
    _inherit = 'labour.group'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_group_rel', 'labour_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchLabour, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchLabour, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Labour Group has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Labour Group has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchApplicant(models.Model):
    _inherit = 'hr.applicant'


    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_applicant_rel', 'applicant_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchApplicant, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(BranchApplicant, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Applicant has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Applicant has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle
#
# class AccountInvoiceAC(models.Model):
#     _inherit = 'account.invoice'
#
#     branch_id = fields.Many2one('branch.master.company', 'Branch')
#     allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_invoice_rel', 'invoice_id', 'branch_id',
#                                           string='Allowed Branches', ondelete='cascade')
#
#     # @api.depends('user_id')
#     def _compute_user_allowed_branch_ids(self):
#         for rec in self:
#             rec.allowed_branch_ids = self.env.user.allowed_branch_ids
#
#     @api.model
#     def default_get(self, fields_list):
#         """Set default branch and allowed branches based on the logged-in user."""
#         res = super(AccountInvoice, self).default_get(fields_list)
#         user = self.env.user
#         if user.branch_id:
#             res['branch_id'] = user.branch_id.id
#         if user.allowed_branch_ids:
#             res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
#         return res
#
#     @api.onchange('company_ids')
#     def _onchange_company_id(self):
#         if self.company_ids:
#             selected_company_ids = self.company_ids.ids
#
#             user_branch_allowed = self.allowed_branch_ids.filtered(lambda b: b.company_id.id in selected_company_ids)
#             user_branch = self.branch_id if self.branch_id.company_id.id in selected_company_ids else False
#
#             self.allowed_branch_ids = user_branch_allowed if user_branch_allowed else False
#             self.branch_id = user_branch if user_branch else False
#         else:
#             self.allowed_branch_ids = False
#             self.branch_id = False
#
#     @api.onchange('allowed_branch_ids')
#     def _onchange_allowed_branch_ids(self):
#         if self.branch_id and self.branch_id not in self.allowed_branch_ids:
#             self.branch_id = False
#
#     @api.model
#     def create(self, vals):
#         invoice = super(AccountInvoice, self).create(vals)
#
#         if invoice.branch_id:
#             message = _(" A New Invoice has been added in '%s'. '%s' branch.") % (
#                 invoice.company_id.name, invoice.branch_id.name)
#         else:
#             message = _(" A New Invoice has been added in '%s'. Without branch.") % (invoice.company_id.name)
#
#         invoice.env.user.notify_info(message)
#
#         return invoice

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_orderpoint_rel', 'orderpoint_id', 'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(StockWarehouse, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

    @api.model
    def create(self, vals):
        vehicle = super(StockWarehouse, self).create(vals)

        if vehicle.branch_id:
            message = _(" A New Warehouse OrderPoint has been added in '%s'. '%s' branch.") % (
                vehicle.company_id.name, vehicle.branch_id.name)
        else:
            message = _(" A New Warehouse OrderPoint has been added in '%s'. Without branch.") % (vehicle.company_id.name)

        vehicle.env.user.notify_info(message)

        return vehicle

class BranchHrJob(models.Model):
    _inherit = 'hr.job'

    branch_id = fields.Many2one('branch.master.company', 'Branch')
    allowed_branch_ids = fields.Many2many('branch.master.company', 'branch_job_rel', 'job_id',
                                          'branch_id', compute='_compute_user_allowed_branch_ids',
                                          string='Allowed Branches', ondelete='cascade')

    # @api.depends('user_id')
    def _compute_user_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.allowed_branch_ids

    @api.model
    def default_get(self, fields_list):
        """Set default branch and allowed branches based on the logged-in user."""
        res = super(BranchHrJob, self).default_get(fields_list)
        user = self.env.user
        if user.branch_id:
            res['branch_id'] = user.branch_id.id
        if user.allowed_branch_ids:
            res['allowed_branch_ids'] = [(6, 0, user.allowed_branch_ids.ids)]
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

            @api.model
            def create(self, vals):
                vehicle = super(BranchHrJob, self).create(vals)

                if vehicle.branch_id:
                    message = _(" A New HR Job has been added in '%s'. '%s' branch.") % (
                        vehicle.company_id.name, vehicle.branch_id.name)
                else:
                    message = _(" A New HR Job has been added in '%s'. Without branch.") % (vehicle.company_id.name)

                vehicle.env.user.notify_info(message)

                return vehicle