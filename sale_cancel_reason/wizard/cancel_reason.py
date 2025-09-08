# -*- coding: utf-8 -*-
# Author: Guewen Baconnier
# Copyright 2013 Camptocamp SA
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# (http://www.serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError

QUOTATION_STATES = ['draft', 'sent', 'sale']


class SaleOrderCancel(models.TransientModel):

    """ Ask a reason for the sale order cancellation."""
    _name = 'sale.order.cancel'
    _description = __doc__

    reason_id = fields.Many2one(
        'sale.order.cancel.reason',
        string='Reason',
        required=False)

    sale_lost_reason_id = fields.Many2one('crm.lost.reason', 'Lost Reason', required=False)

    lost_reason_id = fields.Many2one('crm.lost.reason', 'Lost Reason', required=True)
    #
    child_lost_reason_id = fields.Many2one('crm.lost.reason.child', 'Child Lost Reason', required=True)
    check_sales_ids = fields.Text('Message')

    @api.multi
    def confirm_cancel(self):
        act_close = {'type': 'ir.actions.act_window_close'}
        sale_ids = self._context.get('active_ids')
        if sale_ids is None:
            return act_close
        assert len(sale_ids) == 1, "Only 1 sale ID expected"
        sale = self.env['sale.order'].browse(sale_ids)
        sale.cancel_reason_id = self.reason_id.id
        sale.sale_cancel_reason_id = self.sale_lost_reason_id.id
        sale.lost_reason_id = self.lost_reason_id.id
        sale.child_lost_reason_id = self.child_lost_reason_id.id
        # in the official addons, they call the signal on quotations
        # but directly call action_cancel on sales orders
        if sale.state in QUOTATION_STATES:
            sale.action_cancel()
        else:
            raise UserError(_('You cannot cancel the Quotation/Order in the '
                              'current state!'))
        return act_close

    @api.onchange('lost_reason_id')
    def set_sale_lost_reason_ids(self):
        leads = self.env['sale.order'].browse(self.env.context.get('active_ids')).team_id.team_type
        # print(leads, "leadsleadsleadsleadsleadsleadsleads")
        parent_lost_reasons = self.env['crm.lost.reason'].search([('sale_type', '=', leads), ('active', '=', True)])
        # print(len(parent_lost_reasons))
        if parent_lost_reasons:
            return {'domain': {'lost_reason_id': [('id', 'in', parent_lost_reasons.ids)]}}
        else:
            return {'domain': {'lost_reason_id': [('id', 'in', False)]}}

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderCancel, self).default_get(fields)

        active_ids = self._context.get('active_ids') or []
        if not active_ids:
            return res

        # Use browse to avoid repeated searches
        orders = self.env['sale.order'].browse(active_ids)
        lead_ids = orders.mapped('opportunity_id').ids

        if lead_ids:
            sale_orders = self.env['sale.order'].search([
                ('opportunity_id', 'in', lead_ids),
            ])
            if sale_orders:
                res['check_sales_ids'] = (
                        "Warning: This lead has linked quotations/sale orders:\n" +
                        "\n".join("- %s (%s)" % (so.name, so.state) for so in sale_orders)
                )

        return res
