from odoo import models, fields, api,_
from odoo.exceptions import UserError
from datetime import date


class ARS_account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def invoice_print(self):
        res = super(ARS_account_invoice, self).invoice_print()
        sale_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.ids)])
        if sale_team:
            if sale_team.team_type == 'after_sales':
                self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
                return self.env.ref('account.account_invoices').report_action(self)
        return res


    order_id = fields.Many2one('sale.order')






#     @api.multi
#     def _create_invoice(self, order, so_line, amount):
#         inv_obj = self.env['account.invoice']
#         ir_property_obj = self.env['ir.property']
# 
#         account_id = False
#         if self.product_id.id:
#             account_id = self.product_id.property_account_income_id.id
#         if not account_id:
#             inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
#             account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
#         if not account_id:
#             raise UserError(
#                 _(
#                     'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
#                 (self.product_id.name,))
# 
#         if self.amount <= 0.00:
#             raise UserError(_('The value of the down payment amount must be positive.'))
#         if self.advance_payment_method == 'percentage':
#             amount = order.amount_untaxed * self.amount / 100
#             name = _("Down payment of %s%%") % (self.amount,)
#         else:
#             amount = self.amount
#             name = _('Down Payment')
#         taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
#         if order.fiscal_position_id and taxes:
#             tax_ids = order.fiscal_position_id.map_tax(taxes).ids
#         else:
#             tax_ids = taxes.ids
# 
#         invoice = inv_obj.create({
#             'name': order.client_order_ref or order.name,
#             'origin': order.name,
#             'type': 'out_invoice',
#             'reference': False,
#             'account_id': order.partner_id.property_account_receivable_id.id,
#             'partner_id': order.partner_invoice_id.id,
#             'partner_shipping_id': order.partner_shipping_id.id,
#             'invoice_line_ids': [(0, 0, {
#                 'name': name,
#                 'origin': order.name,
#                 'account_id': account_id,
#                 'price_unit': amount,
#                 'quantity': 1.0,
#                 'discount': 0.0,
#                 'uom_id': self.product_id.uom_id.id,
#                 'product_id': self.product_id.id,
#                 'sale_line_ids': [(6, 0, [so_line.id])],
#                 'invoice_line_tax_ids': [(6, 0, tax_ids)],
#                 'account_analytic_id': order.analytic_account_id.id or False,
#                 'order_id':order.id,
#             })],
#             'currency_id': order.pricelist_id.currency_id.id,
#             'payment_term_id': order.payment_term_id.id,
#             'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
#             'team_id': order.team_id.id,
#             'user_id': order.user_id.id,
#             'comment': order.note,
#         })
#         invoice.compute_taxes()
#         invoice.message_post_with_view('mail.message_origin_link',
#                                        values={'self': invoice, 'origin': order},
#                                        subtype_id=self.env.ref('mail.mt_note').id)
        
        
        
        #create service history if service order created
#         vehicle = self.env['stock.production.lot'].search([('customer_id','=',order.partner_id.id),('reg_no','=',order.regn_no),('name','=',order.vin_no)])
#         nxt_due  = self.env.user.company_id.next_service_due
#         remainder  = self.env.user.company_id.next_service_remainder
#         if vehicle and order.sale_aftersales == 'after_sales':
#             self.env['service.history'].create({
#                               'order':order.id,
#                               'servicetype':'First Free Service',
#                               'date':date.today(),
#                               'next_service_due':date.today() + timedelta(days=nxt_due),
#                               'set_reminder':date.today() + timedelta(days=remainder),
#                               'stock_id4':vehicle.id,    
#                                                 
#                                                 
#                                                 })
#         return invoice

    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    regno = fields.Char()
    reg_no = fields.Many2one('fleet.vehicle',string="Regn No")
    vin = fields.Char(string="VIN")
    model = fields.Many2one('product.product')
    kilometer = fields.Integer(string="Kilometer")
    delivery_service_advisor = fields.Many2one('res.users')
    doc_type = fields.Selection([
        ('appointment', 'Appointment'),
        ('walkin', 'Walkin'),
    ], string='Type', default='appointment')
    appointment_date = fields.Datetime(string="Appointment Date")
    delivery_date = fields.Datetime(string="Delivery Date")
    count_vehicle = fields.Integer()
    @api.onchange('partner_id')
    def change_invoice(self):
        # obj = self.env['res.partner'].browse(self.partner_id)
        self.email = self.partner_id.email
        self.mobile = self.partner_id.mobile

    @api.onchange('delivery_service_advisor')
    def in_advisor_change(self):
        if self.delivery_service_advisor.id:
            self.delivery_service_advisor = self.delivery_service_advisor.id
        else:
            self.delivery_service_advisor = False


    @api.multi
    @api.onchange('partner_id', 'mobile', 'reg_no')
    def invoice_change(self):
        partner = False
        if self.mobile and not self.partner_id.id:
            partner = self.env['res.partner'].search([('mobile', '=', self.mobile)])

        if self.partner_id.id or partner:
            if not partner:
                partner = self.partner_id
            if partner:
                customer_details = self.env['fleet.vehicle'].search([('driver_id', '=', partner.id)])
                self.count_vehicle = len(customer_details)
                if len(customer_details) == 1:
                    self.partner_id = self.partner_id.id
                    self.mobile = self.partner_id.mobile
                    self.reg_no = customer_details.id
                    self.vin = customer_details.vin_sn
                    self.vehicle_model = customer_details.mvariant_id.id
                else:
                    self.partner_id = self.partner_id.id
                    self.mobile = self.partner_id.mobile
                    multiple_regno = {}
                    multiple_regno['domain'] = {'reg_no': [('id', '=', customer_details.ids)]}
                    return multiple_regno
        if self.reg_no:
            customer_details = self.env['fleet.vehicle'].search([('license_plate', '=', self.reg_no.id)])
            self.count_vehicle = len(customer_details)
            if len(customer_details) == 1:
                self.partner_id = self.partner_id.id
                self.phone = self.partner_id.phone
                self.reg_no = customer_details.id
                self.vin = customer_details.vin_sn
                product_name = self.env['product.product'].search([('product_tmpl_id', '=', customer_details.model_id.id)])
                self.model = product_name.id
