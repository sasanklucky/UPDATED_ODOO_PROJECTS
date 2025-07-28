import json
import re
from odoo import models, fields, api, _
from datetime import datetime, time, date
from datetime import timedelta
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from openerp.exceptions import UserError, ValidationError



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    booking_amount_total = fields.Integer(compute="_compute_booking_amount_total", string="Booking Count")
    booking_amount_total_value = fields.Float(compute="_compute_booking_amount_total_value", string="Total Booking Amount")

    mileage_in = fields.Integer(string="Mileage")
    mileage_out = fields.Integer(string="Kilometer Out")

    def _compute_booking_amount_total_value(self):
        """Compute the total booking amount for the customer."""
        for order in self:
            total_value = sum(self.env['booking.amount'].search([
                ('customer_name', '=', order.partner_id.id)
            ]).mapped('booking_amount'))
            order.booking_amount_total_value = total_value

    def _compute_booking_amount_total(self):
        """Compute the number of booking records for the customer."""
        for order in self:
            order.booking_amount_total = self.env['booking.amount'].search_count([
                ('customer_name', '=', order.partner_id.id)
            ])

    def action_view_booking_amount(self):
        """Opens booking amount records or a form to create a new one."""
        self.ensure_one()
        booking_count = self.booking_amount_total

        context_data = {
            'default_customer_name': self.partner_id.id,
            'default_total_booking_amount': self.amount_total,
        }

        if booking_count == 0:
            return {
                'name': 'Create Booking Amount',
                'type': 'ir.actions.act_window',
                'res_model': 'booking.amount',
                'view_mode': 'form',
                'views': [(self.env.ref('ars_vehicle_sales.view_booking_amount_form').id, 'form')],
                'target': 'new',
                'context': context_data
            }
        else:
            return {
                'name': 'Booking Amount Details',
                'type': 'ir.actions.act_window',
                'res_model': 'booking.amount',
                'view_mode': 'tree,form',
                'views': [
                    (self.env.ref('ars_vehicle_sales.view_booking_amount_tree').id, 'tree'),
                    (self.env.ref('ars_vehicle_sales.view_booking_amount_form').id, 'form')
                ],
                'target': 'current',
                'context': context_data,
                'domain': [('customer_name', '=', self.partner_id.id)]
            }


#
# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     booking_amount = fields.Float()
#     booking_amount_total = fields.Integer(compute="_compute_booking_amount_total")
#     booking_amount_total_value = fields.Float(compute="_compute_booking_amount_total_value", string="Total Booking Amount")
#
#     def _compute_booking_amount_total_value(self):
#         for order in self:
#             total_value = sum(self.env['booking.amount'].search([('customer_name', '=', order.partner_id.id)]).mapped(
#                 'booking_amount'))
#             order.booking_amount_total_value = total_value
#
#
#     def _compute_booking_amount_total(self):
#         for order in self:
#             order.booking_amount_total = self.env['booking.amount'].search_count([('customer_name', '=', order.partner_id.id)])
#
#     def action_view_booking_amount(self):
#         self.ensure_one()
#
#         booking_count = self.env['booking.amount'].search_count([('customer_name', '=', self.partner_id.id)])
#
#         # Ensure product_template_id is valid
#         product_template_id = self.order_line[0].product_template_id.id if self.order_line and self.order_line[
#             0].product_template_id else False
#         product_id = self.order_line[0].product_id.id if self.order_line and self.order_line[0].product_id else False
#
#         context_data = {
#             'default_customer_name': self.partner_id.id,
#             'default_total_booking_amount': self.amount_total,
#         }
#
#         if product_template_id:
#             context_data['default_product_template_id'] = product_template_id
#         if product_id:
#             context_data['default_product_id'] = product_id
#
#         if booking_count == 0:
#             return {
#                 'name': 'Create Booking Amount',
#                 'type': 'ir.actions.act_window',
#                 'res_model': 'booking.amount',
#                 'view_mode': 'form',
#                 'views': [(self.env.ref('ars_vehicle_sales.view_booking_amount_form').id, 'form')],
#                 'target': 'new',
#                 'context': context_data
#             }
#         else:
#             return {
#                 'name': 'Booking Amount Details',
#                 'type': 'ir.actions.act_window',
#                 'res_model': 'booking.amount',
#                 'view_mode': 'tree,form',
#                 'views': [
#                     (self.env.ref('ars_vehicle_sales.view_booking_amount_tree').id, 'tree'),
#                     (self.env.ref('ars_vehicle_sales.view_booking_amount_form').id, 'form')
#                 ],
#                 'target': 'current',
#                 'context': context_data,
#                 'domain': [('customer_name', '=', self.partner_id.id)]
#             }


class BookingAmount(models.Model):
    _name = 'booking.amount'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Booking Amount'
    _rec_name = 'customer_name'

    customer_name = fields.Many2one('res.partner', string='Customer Name', track_visibility='always')
    date = fields.Datetime('Date', default=fields.Datetime.now, track_visibility='always')
    total_booking_amount = fields.Float('Total Amount', default=lambda self: self._default_total_booking_amount())
    booking_amount = fields.Float('Booking Amount', track_visibility='always')
    remaining_booking_amount = fields.Float('Remaining Amount', compute="_compute_on_remaining_amount_value")
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ('bank', 'cash'))])
    journal_type = fields.Selection(related='journal_id.type', store=True, string='Journal Type')
    bank_id= fields.Many2one('res.bank', string="Bank")
    product_template_id = fields.Many2one('product.template', string="Model")
    product_id = fields.Many2one('product.product', string="Variant")
    status = fields.Selection([('draft', 'Draft'), ('booked', 'Booked'), ('cancel', 'Canceled')], default='draft')
    remarks = fields.Text('Remarks', track_visibility='always')


    def _default_total_booking_amount(self):
        return self.env.context.get('default_total_booking_amount', 0.0)

    @api.depends('total_booking_amount', 'booking_amount')
    def _compute_on_remaining_amount_value(self):
        for rec in self:
            rec.remaining_booking_amount = rec.total_booking_amount - rec.booking_amount

    @api.onchange('booking_amount')
    def _onchange_booking_amount(self):
        for rec in self:
            if rec.booking_amount > 0 and rec.status != 'cancel':
                rec.status = 'booked'
            elif rec.booking_amount:
                rec.status = 'cancel'
            else:
                rec.status ='draft'

    def write(self, vals):
        res = super(BookingAmount, self).write(vals)
        for rec in self:
            if 'booking_amount' in vals and rec.booking_amount > 0:
                rec.status = 'booked'
            elif 'booking_amount' in vals and rec.booking_amount == 0:
                rec.status = 'cancel'
        return res

    def cancel_booking(self):
        for rec in self:
            rec.status = 'cancel'
            rec.booking_amount = 0
            rec.journal_id = False
            rec.bank_id = False

