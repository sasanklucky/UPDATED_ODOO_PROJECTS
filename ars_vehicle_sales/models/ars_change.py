from odoo import models, fields, api, _
from datetime import datetime
from datetime import timedelta
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

class arsCompany(models.Model):
    _inherit = 'res.company'

    dealer_code = fields.Char(string="Dealer Code")
    
class ars_sale_crm_lead(models.Model):
    _inherit = 'crm.lead'
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict') 
class ars_sale_crm_sale(models.Model):
    _inherit = 'sale.order'

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for sale in self:
            rounded_value = round(self.amount_total,0)
            sale.amount_total_words = sale.currency_id.amount_to_text(rounded_value)

    @api.multi
    def _get_proforma_invoice_types(self):
        self.ensure_one()
        proforma_type = ''
        if len(self.order_line) == 1:
            for line in self.order_line:
                # print("catalog",line.product_id.catalog_type.name)
                if line.product_id.catalog_type.name == 'Vehicle':
                    proforma_type = 'vehicle'
        # print("proforma",proforma_type)
        return proforma_type

            
    @api.multi
    def _get_tax_amount_by_group_wise(self):
        self.ensure_one()
        res = {}
        for line in self.order_line:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id, partner=self.partner_shipping_id)['taxes']
            for tax in line.tax_id:
                group = tax.tax_group_id
                res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                for t in taxes:
                    if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                        res[group]['name'] = tax.name
                        res[group]['amount'] += t['amount']
                        res[group]['base'] += t['base']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [(l[1]['name'], l[1]['amount'], l[1]['base'], len(res)) for l in res]
        # print(res)
        return res

    @api.depends('state', 'user_id')
    def _enable_approve_button(self):
        """
        Enable/Disable the approve button based on the state and salesperson
        """
        for order in self:
            order.is_approve = False
            if self.state == 'to_approve':
               emp = self.env['hr.employee'].search([('user_id','=', order.user_id and order.user_id.id or False)])
               emp = emp and emp[0] or False
               user_list = []
               emp and emp.parent_id and emp.parent_id.user_id and user_list.append(emp.parent_id.user_id.id)
               admin_lst = self.env['hr.employee'].search_read([('parent_id', '=', False)],fields=['user_id'])
               for ad in admin_lst:
                   user_list.append(ad.get('user_id')[0])
               if self._uid in user_list:
                  order.is_approve = True

    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('ars_vehicle_sales', 'ars_email_template_edi_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "sale.mail_template_data_notification_email_sale_order",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    amount_total_words = fields.Char("Total (In Words)", compute="_compute_amount_total_words")
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('to_approve', 'To Approve'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    is_approve = fields.Boolean(string='Enable Approve button', compute="_enable_approve_button", copy=False, store=False)

    @api.multi
    def action_confirm(self):
        print ('called action confirm')
        self.ensure_one()
        if self.state != 'to_approve':
           approval = self.env['sales.approval'].search([('employee_id.user_id','=',self.user_id and self.user_id.id or False),('type','=','sale')])
        elif self.state == 'to_approve':
           approval = self.env['sales.approval'].search([('employee_id.user_id','=',self._uid),('type','=','sale')])

        approval = approval and approval[0] or False

        if approval:
           print('approval', approval)
           print('approval', approval.amount, self.amount_total)
           if approval.amount and approval.amount < self.amount_total:
              if self.state == 'to_approve':
                 self.write({'user_id': self._uid})
                 raise UserError(_('Your approval limit has been exceded. Please contact your admin to proceed further.'))
              self.write({'state': 'to_approve','user_id':self._uid})
              return True
           for ol in self.order_line:
               if approval.discount and approval.discount < ol.discount :
                  if self.state == 'to_approve':
                     self.write({'user_id': self._uid})
                     raise UserError(_('Your approval limit has been exceded. Please contact your admin to proceed further.'))
                  self.write({'state': 'to_approve','user_id':self._uid})
                  return True
        result = super(ars_sale_crm_sale, self).action_confirm()
        return result


class ars_sale_order_line(models.Model):
    _inherit = "sale.order.line"

    vin_no = fields.Many2one('stock.production.lot', string="VIN")
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)


class ars_sale_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_print(self):
        res = super(ars_sale_invoice, self).invoice_print()
        sale_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.ids)])
        if sale_team:
            if sale_team.team_type == 'sales':
                self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
                return self.env.ref('ars_vehicle_sales.before_sales_invoice').report_action(self)
        return res

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for sale in self:
            sale.amount_total_words = sale.currency_id.amount_to_text(sale.amount_total)

    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    amount_total_words = fields.Char("Total (In Words)", compute="_compute_amount_total_words")

class ars_sale_advance_payment_inv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_(
                        'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_(
                        "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(
                    lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                context = {'lang': order.partner_id.lang}
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, tax_ids)],
                    'is_downpayment': True,
                })
                del context
                res =self._create_invoice(order, so_line, amount)
                res.mobile = order.mobile
                res.email = order.email

        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_deposit_product(self):
        return {
            'name': 'Down payment',
            'type': 'service',
            'invoice_policy': 'order',
            'property_account_income_id': self.deposit_account_id.id,
            'taxes_id': [(6, 0, self.deposit_taxes_id.ids)],
        }

class HRRmployee(models.Model):
    _inherit = 'hr.employee'

    sale_approval = fields.One2many('sales.approval', 'approval_id')

class HRSalesApproval(models.Model):
    _name = 'sales.approval'

    approval_id = fields.Many2one('hr.employee')
    employee_id = fields.Many2one('hr.employee', string="Employee")
    company_id = fields.Many2one('res.company', string ='Company',default=lambda self: self.env['res.company']._company_default_get('sales.approval'))
    type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], string = 'Type')
    amount = fields.Float(string = 'Amount')
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

class Menu(models.Model):

    _inherit = "website.menu"

    is_visible = fields.Boolean(compute='_compute_visible', string='Is Visible')

    @api.one
    def _compute_visible(self):
        visible = True
        print('group portal', self.user_has_groups('base.group_portal'))
        if self.page_id and not self.page_id.sudo().is_visible and (not self.user_has_groups('base.group_user') and not self.user_has_groups('base.group_portal')):
            visible = False
        self.is_visible = visible
