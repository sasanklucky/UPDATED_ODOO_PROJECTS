import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class ARS_account_invoice(models.Model):
    _inherit = "account.invoice"

    gate_pass_date = fields.Date(string='Gate Pass Date')
    service_type = fields.Many2one('service.type', 'Service Type')
    service_options = fields.Many2one('service.options', 'Service Options')
    product_model = fields.Many2one('product.template', related="model.product_tmpl_id", store=True, string='Model')
    admin_access = fields.Boolean(compute="_check_if_admin")

    @api.constrains('mobile')
    def mobile_validation(self):
        pattern = r'^[1-9]\d{9}$'
        if not re.match(pattern, self.mobile):
            raise ValidationError(_('Mobile number should contain 10 digits and the first digit should not be zero'))

    @api.multi
    @api.depends('invoice_line_ids')
    def _check_if_admin(self):
        for record in self:
            record.admin_access = False
            user = self.env['res.users'].browse(int(self.env.context.get('uid')))
            if user:
                if user.has_group("base.group_system"):
                    record.admin_access = True
                else:
                    record.admin_access = False

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

    # create service history if service order created
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
    reg_no = fields.Many2one('fleet.vehicle', string="Regn No")
    vin = fields.Char(string="VIN")
    model = fields.Many2one('product.product', string="Model Variant")
    kilometer = fields.Float(string="Kilometer", required=True)
    kilometer_out = fields.Float(string="Kilometer Out", required=True)
    delivery_service_advisor = fields.Many2one('res.users')
    doc_type = fields.Selection([
        ('appointment', 'Appointment'),
        ('walkin', 'Walkin'),
        ('res_drop', 'RSA Drop'),
        ('p&d', 'P&D')
    ], string='Type', default='appointment')
    appointment_date = fields.Datetime(string="Appointment Date")
    delivery_date = fields.Datetime(string="Delivery Date")
    count_vehicle = fields.Integer()

    @api.multi
    def check_valid_sales_channel(self, sales_team):
        if sales_team.team_type == 'after_sales':
            pass
        else:
            raise ValidationError(
                _("You are not belongs to After Sales  channel, Please select After Sales channel and try again"))

    def action_invoice_open(self):
        if self.ars_invoice_type == 'after_sales' and self.kilometer_out == 0.00:
            raise UserError('Please Enter Kilometer Out ')
        if self.ars_invoice_type == 'after_sales' and self.kilometer == 0.00:
            raise UserError('Please Enter Kilometer IN')
        if self.ars_invoice_type == 'after_sales' and self.kilometer_out < self.kilometer:
            raise UserError(_("Kilometer Out is lesser than Kilometer In"))
        if self.ars_invoice_type == 'after_sales':
            sale_team = self.env['crm.team'].search(
                [('member_ids', 'in', self.user_id.id), ('member_ids', 'in', self.env.user.ids)])
            self.check_valid_sales_channel(sale_team)
        if not self.gate_pass_date:
            self.gate_pass_date = date.today()
        res = super(ARS_account_invoice,self).action_invoice_open()
        return res

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
                    # multiple_regno = {}
                    # multiple_regno['domain'] = {'reg_no': [('id', '=', customer_details.ids)]}
                    # return multiple_regno
        if self.reg_no:
            customer_details = self.env['fleet.vehicle'].search([('license_plate', '=', self.reg_no.id)])
            self.count_vehicle = len(customer_details)
            if len(customer_details) == 1:
                self.partner_id = self.partner_id.id
                self.phone = self.partner_id.phone
                self.reg_no = customer_details.id
                self.vin = customer_details.vin_sn
                product_name = self.env['product.product'].search(
                    [('product_tmpl_id', '=', customer_details.model_id.id)])
                self.model = product_name.id

    @api.onchange('kilometer_out')
    def UpdateKilometerOut(self):
        if self.reg_no and self.kilometer_out != 0 and self.kilometer != 0:
            if self.kilometer < self.kilometer_out:
                self.reg_no.write({'odometer': self.kilometer_out})
            else:
                raise UserError(_("Kilometer Out is lesser than Kilometer In"))
        elif self.reg_no and self.kilometer and self.kilometer_out == 0:
            raise UserError(_("Please Enter the Kilometer Out"))

    @api.multi
    def _invoice_line_tax_values_by_type(self, tax_product={}, tax_service={}):
        self.ensure_one()
        tax_datas = {}
        product_tax_list = []
        service_tax_list = []
        tax_product.clear()
        tax_service.clear()
        TAX = self.env['account.tax']
        for line in self.mapped('invoice_line_ids'):
            if line.product_id.type in ['product', 'consu']:
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                tax_lines = line.invoice_line_tax_ids.compute_all(price_unit, line.invoice_id.currency_id,
                                                                  line.quantity,
                                                                  line.product_id,
                                                                  line.invoice_id.partner_id)['taxes']
                for tax_line in tax_lines:
                    tax_line['tag_ids'] = TAX.browse(tax_line['id']).tag_ids.ids
                    if tax_line['id'] not in tax_product:
                        # product_tax_list.append([tax_line['id'], tax_line['name']])
                        tax_product[tax_line['id']] = {'id': tax_line['id'],
                                                       'name': tax_line['name'],
                                                       'amount': tax_line['amount'],
                                                       'base': tax_line['base']}
                    else:
                        tax_product[tax_line['id']]['amount'] += tax_line['amount']
                        tax_product[tax_line['id']]['base'] += tax_line['base']
            if line.product_id.type in ['service']:
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                tax_lines = \
                    line.invoice_line_tax_ids.compute_all(price_unit, line.invoice_id.currency_id, line.quantity,
                                                          line.product_id, line.invoice_id.partner_id)['taxes']
                for tax_line in tax_lines:
                    tax_line['tag_ids'] = TAX.browse(tax_line['id']).tag_ids.ids
                    if tax_line['id'] not in tax_service:
                        # service_tax_list.append([tax_line['id'], tax_line['name']])
                        tax_service[tax_line['id']] = {'id': tax_line['id'],
                                                       'name': tax_line['name'],
                                                       'amount': tax_line['amount'],
                                                       'base': tax_line['base']}
                    else:
                        tax_service[tax_line['id']]['amount'] += tax_line['amount']
                        tax_service[tax_line['id']]['base'] += tax_line['base']
        if not product_tax_list:
            product_tax_list = list(tax_product.keys())
        if not service_tax_list:
            service_tax_list = list(tax_service.keys())
        tax_datas['product_list'] = product_tax_list
        tax_datas['service_tax_list'] = service_tax_list
        tax_datas['product'] = tax_product
        tax_datas['service'] = tax_service
        return tax_datas
