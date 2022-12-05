from odoo import models, fields, api
import re
from openerp.exceptions import UserError, ValidationError


class ars_company(models.Model):
    _inherit = 'res.company'

    team_typ_id = fields.Many2one('crm.team', 'Team Type')
    team_stage_id = fields.Many2one('crm.stage', 'Stage')
    ext_service_due = fields.Char(string="Lead Next Service Due Date")
    next_service_remainder = fields.Char(string="Next Service Date Remainder")
    next_km_service_due_date = fields.Char(string="Lead by K M next Due")
    next_service_due = fields.Char(string="Next Service Due")




class ars_configure_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    # def stage_filters(self):
    #     print("ok im running")
    #     act=self.env['crm.stage']
    #     for r in act.search([('team_id','=','After sales')]):
    #          print("executed")

    configure = fields.Boolean(string="configured")
    team_types = fields.Many2one(related="company_id.team_typ_id")
    stages_id = fields.Many2one(related="company_id.team_stage_id")
    ext_service_due = fields.Char(related="company_id.ext_service_due")
    next_service_remainder = fields.Char(related="company_id.next_service_remainder")
    next_km_service_due_date = fields.Char(related="company_id.next_km_service_due_date")
    next_service_due = fields.Char(related="company_id.next_service_due")
    rms_team_types = fields.Many2one(related="company_id.team_typ_id")
    rms_stages_id = fields.Many2one(related="company_id.team_stage_id")
#     @api.multi
#     @api.onchange('team_types')
#     def team_types_change(self):
#         res = {}
#         res['domain'] = {'stages_id': [('team_id', '=', self.team_types.id)]}
#         return res



#     @api.model
#     def get_values(self):
#         res = super(ars_configure_settings, self).get_values()
#         conf = self.env['ir.config_parameter'].sudo()
#         return res
    


    # @api.multi
    # def set_values(self):
    #     super(ars_configure_settings, self).set_values()
    #     conf = self.env['ir.config_parameter'].sudo()
    #     conf.set_param('ars_after_sales.stages_id',self.stages_id.id)
    #     conf.set_param('ars_after_sales.team_types', self.team_types.id)class ars_landing(models.Model):
    
class landing_urls(models.Model):
    _name = 'landing.url'
    
    name = fields.Char()
    url = fields.Char()

class ars_landing(models.Model):
    _name = 'landing.setting'

    landing_link = fields.Many2one('landing.url')
    landing_user = fields.Many2one('res.users')
    
class labour_group(models.Model):
    _name = 'labour.group'
    _description = 'Configuration for Labour Group'

    name = fields.Char('Name')
    code = fields.Char('Code')
    company_id = fields.Many2one('res.company','Company')
    parent_id = fields.Many2one('labour.group','Parent Group')

    @api.model
    def create(self, vals):
        # Prefix parent labour code to the current record
        if vals.get('parent_id') and vals.get('code'):
            plg = self.env['labour.group'].browse(vals.get('parent_id'))
            vals['code'] = plg.code + vals.get('code','')
        return super(labour_group, self).create(vals)

    @api.multi
    def write(self, vals):
        for lg in self:
            plgcode = self.parent_id and self.parent_id.code or ''
            code = self.code

        if 'parent_id' in vals and 'code' in vals:
            plg = self.env['labour.group'].browse(vals.get('parent_id'))
            if plgcode in vals.get('code'):
               code = vals.get('code').replace(plgcode, '')
               vals['code'] = plg.code + code
            elif plg not in code:
                 vals['code'] = plg.code + code

        elif 'parent_id' in vals:
            plg = self.env['labour.group'].browse(vals.get('parent_id'))
            if plgcode in code:
               code = code.replace(plgcode, '')
               vals['code'] = plg.code + code
            elif plg not in code:
                 vals['code'] = plg.code + code

        elif 'code' in vals:
            if plgcode not in vals['code']:
               vals['code'] = plgcode + code

        return super(labour_group, self).write(vals)

class Employee(models.Model):
    _inherit = 'hr.employee'

    labour_group_ids = fields.Many2many('labour.group', 'employee_labour_rel', 'employee_id', 'lgroup_id')
    blood_group = fields.Char(string="Blood Group")
    emp_code = fields.Char(string="Employee Code")
    education_details = fields.Char(string="Education Details")
    aadhar_id = fields.Char(string="Aadhar No")
    voter_id = fields.Char(string="Voter ID")
    employement_type = fields.Selection([('probationer', 'Probationer'),('permanent', 'Permanent'),('contract', 'Contract')])
    date_of_joining = fields.Date(string="Joining Date")
    date_of_exit = fields.Date(string="Exit Date")

    # @api.constrains('blood_group')
    # def validate_blood_group(self):
    #     regex = re.compile(r"([AaBbOo]|[Aa][Bb])[\+-]")
    #     for rec in self:
    #         if regex.search(rec.blood_group) != None:
    #             raise ValidationError("Please Add correct Blood Group.")
    
    @api.constrains('aadhar_id')
    def validate_aadhar_id(self):
        # regex = re.compile(r"^\d{4}\s\d{4}\s\d{4}$") # if spaces between the numbers
        regex = re.compile(r"^([0-9]){12}$") #if no spaces between the numbers
        for rec in self:
            if regex.search(rec.aadhar_id) != None:
                raise ValidationError("Please Add correct Aadhar No.")
    
    @api.constrains('voter_id')
    def validate_voter_id(self):
        regex = re.compile(r"^[A-Z]{3}\d{7}$") # for voter formate = ABC1234567
        for rec in self:
            if regex.search(rec.voter_id) != None:
                raise ValidationError("Please Add correct Voter ID.")


class ars_sale_warranty(models.Model):
    _name = 'ars.sale.warranty'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    @api.depends('order_lines.wrn_price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for warranty in self:
            amount_untaxed = amount_tax = 0.0
            for line in warranty.order_lines:
                amount_untaxed += line.wrn_price_subtotal
                amount_tax += line.wrn_price_tax
            warranty.update({
                'amount_untaxed': warranty.company_id.currency_id.round(amount_untaxed),
                'amount_tax': warranty.company_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    name = fields.Char('Warranty No.')
    partner_id = fields.Many2one('res.partner', 'Customer')
    regn_no = fields.Many2one('fleet.vehicle','Reg No.')
    model_id = fields.Many2one('product.product','Model')
    vin_no = fields.Char('VIN No.')
    order_id = fields.Many2one('sale.order', 'Service Document')
    order_lines = fields.Many2many('sale.order.line', 'warranty_order_line_rel', )
    vendors = fields.Many2many('res.partner', 'fleet_vehicle_model_vendors', string='Order Lines')
    order_date = fields.Datetime(related='order_id.confirmation_date')
    user_id = fields.Many2one(related='order_id.user_id')

    state   = fields.Selection([('draft','Draft'),('inprocess','In-Process'),('processed','Processed'),('done','Done'),('cancel','Cancel')], default='draft', string='State')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='onchange')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    currency_id = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency", readonly=True, required=True)
    base_url = fields.Char('Base URl', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('web.base.url'))

    @api.multi
    def set_aligment(self):
        for wr in self:
            for ol in wr.order_lines:
                if ol.category and ol.category.name.lower() == 'warranty' and ol.ars_warranty_price != ol.price_unit:
                   ol.price_unit = ol.ars_warranty_price
        return True

    @api.multi
    def write(self, vals):
        for vl in self:
            if self.state == 'cancel':
               vals['state'] = 'draft'

        res = super(ars_sale_warranty, self).write(vals)
        for wc in self:
            state = vals.get('state','draft')
            for ol in wc.order_lines:
                if not ol.apr_action:
                   state = 'draft'
                   break
                elif ol.apr_action in ('hold', 'reject', 're_submission'):
                   state = 'inprocess'
                   break

                elif ol.apr_action == 'approved':
                   state = 'processed'
            self._cr.execute("update ars_sale_warranty set state=%s where id=%s",(state,wc.id))
        return res

    @api.multi
    def action_approval_send(self):
        '''
        This function opens a window to compose an email, with the edi warranty approval template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('ars_after_sales', 'email_template_edi_warranty_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'ars.sale.warranty',
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