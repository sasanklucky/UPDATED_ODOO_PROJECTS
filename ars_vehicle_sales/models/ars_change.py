import json
import re
from odoo import models, fields, api, _
from datetime import datetime, time, date
from datetime import timedelta
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from openerp.exceptions import UserError, ValidationError
from ast import literal_eval
from lxml import etree


class arsCompany(models.Model):
    _inherit = 'res.company'

    dealer_code = fields.Char(string="Dealer Code", required=True)
    make_id = fields.Many2one('fleet.vehicle.model.brand', string="Make")
    sale_report_format = fields.Selection([('format1', 'Format1'), ('format2', 'Format2'), ('format3', 'Format3')],
                                          default='format1')
    dealer_zone = fields.Selection([
        ('east', 'EAST'),
        ('west', 'WEST'),
        ('north', 'NORTH'),
        ('south', 'SOUTH')
    ], 'Dealer Zone')
    display_name_short = fields.Char(string="Display Name", track_visibility='always')
    restrict_bd_inv = fields.Boolean()
    booking_stage_id = fields.Many2one('crm.stage', 'Booking Stage')


class ArsConfigureSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    booking_stage_id = fields.Many2one(related="company_id.booking_stage_id")
    pipeline_stages_ids = fields.Many2many('crm.stage', 'crm_pipline_stages_rel', 'crm_id', 'pipline_id',
                                           string='Pipeline Stages')

    @api.multi
    def set_values(self):
        res = super(ArsConfigureSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('ars_vehicle_sales.booking_stage_id', self.booking_stage_id.id)
        self.env['ir.config_parameter'].sudo().set_param('ars_vehicle_sales.pipeline_stages_ids',
                                                         self.pipeline_stages_ids.ids)
        return res

    @api.model
    def get_values(self):
        res = super(ArsConfigureSettings, self).get_values()
        booking_stage_id = self.env['ir.config_parameter'].sudo().get_param('ars_vehicle_sales.booking_stage_id')
        pipeline_stages_ids = self.env['ir.config_parameter'].sudo().get_param('ars_vehicle_sales.pipeline_stages_ids')
        res.update(
            pipeline_stages_ids=[(6, 0, literal_eval(pipeline_stages_ids))] if pipeline_stages_ids else False,
            booking_stage_id=booking_stage_id if booking_stage_id else False)
        return res


class ars_sale_crm_lead(models.Model):
    _inherit = 'crm.lead'

    company_type = fields.Selection([('individual', 'Individual'), ('company', 'Company')], string="Customer Type")
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict')
    is_test_drive = fields.Boolean("Test Drive")
    no_of_test_drive = fields.Integer(compute='_total_test_drive')
    dob = fields.Date('DOB')
    age = fields.Integer(compute='_compute_age_from_dob')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('transgender', 'Transgender')])
    annual_income = fields.Many2one('annual.income', 'Annual Income')
    sales_type = fields.Selection([('vehicle', 'Vehicle'), ('parts', 'Parts'),
                                   ('after_sales', 'After Sales'), ('others', 'Others')])
    model_id = fields.Many2one('product.template', string="Model")
    # enquiry_date = fields.Datetime(string=" Enquiry Date", default=fields.Datetime.now)
    booking_date = fields.Datetime(string="Booking Date")

    # @api.constrains('mobile')
    # def check_mobile_with_model(self):
    #     company_id = self.env.user.company_id.id
    #     user = self.env.user.id
    #     crm_team = self.env['crm.team'].search([('company_id', '=', company_id), ('team_type', 'in', ['sales']), ('member_ids', 'in', user)])
    #     if crm_team:
    #         if self.type == 'lead':
    #             if self.mobile:
    #                 mobile = self.mobile.strip()
    #                 existing_lead = self.env['crm.lead'].search([('mobile','=',mobile),('id','!=', self.id)])
    #                 if existing_lead:
    #                     product_id = []
    #                     for lead in existing_lead:
    #                         for lead_line in lead.vehicle_line:
    #                             product_id.append(lead_line.product_id.id)
    #                     for line in self.vehicle_line:
    #                         if line.product_id.id in product_id:
    #                             raise ValidationError(_(f"This Mobile Number already Exist with same Model, These all are the existing lead ids.{existing_lead.ids}"))
    #         if self.type == 'opportunity':
    #             existing_lead = self.env['crm.lead'].search([('mobile', '=', self.mobile), ('id','!=', self.id)])
    #             if existing_lead:
    #                 if self.product_id:
    #                     product_id = []
    #                     for lead in existing_lead:
    #                         for lead_line in lead.vehicle_line:
    #                             product_id.append(lead_line.product_id.id)
    #                     if self.product_id.id  in product_id:
    #                         raise ValidationError(_(f"This Mobile Number already Exist with same Model, These all are the existing lead ids.{existing_lead.ids}"))
    #                 else:
    #                     product_id = []
    #                     for lead in existing_lead:
    #                         for lead_line in lead.vehicle_line:
    #                             product_id.append(lead_line.product_id.id)
    #                     for line in self.vehicle_line:
    #                         if line.product_id.id in product_id:
    #                             raise ValidationError(_(f"This Mobile Number already Exist with same Model, These all are the existing lead ids.{existing_lead.ids}"))


    @api.onchange('stage_id')
    def _set_booking_date(self):
        booking_stage = self.env['ir.config_parameter'].sudo().get_param('ars_vehicle_sales.booking_stage_id')
        if booking_stage and self.stage_id.id == int(booking_stage):
            if not self.booking_date:
                self.booking_date = datetime.now()

    enquiry_date = fields.Datetime(string=" Enquiry Date", default=fields.Datetime.now)

    # @api.multi
    # def write(self, values):
    #     booking_stage = self.env['ir.config_parameter'].sudo().get_param('ars_vehicle_sales.booking_stage_id')
    #     stage = values.get('stage_id')
    #     if stage and booking_stage:
    #         if int(stage) == int(booking_stage):
    #             values['booking_date'] = date.today()
    #     if len(self.ids) == 1:
    #         previous_state_id = self.stage_id
    #     result = super(ars_sale_crm_lead, self).write(values)
    #     if len(self.ids) == 1:
    #         if previous_state_id.probability == 100 and self.stage_id != previous_state_id and not self.env.user.has_group('ars_vehicle_sales.group_access_crm_stage'):
    #             raise ValidationError('You do not have access to change the state')
    #     res_value = {}
    #     for res in self:
    #         if res.partner_id:
    #             if 'gender' in values:
    #                 res_value.update({'gender': values['gender']})
    #             if 'annual_income' in values:
    #                 res_value.update({'annual_income': values['annual_income']})
    #             if 'street' in values:
    #                 res_value.update({'street': values['street']})
    #             if 'street2' in values:
    #                 res_value.update({'street2': values['street2']})
    #             if res_value:
    #                 res.partner_id.write(res_value)
    #     return result

    # Mandatory fields (street, pan no, zip) when pipline stage is going to booked
    @api.multi
    def write(self, vals):
        new_stage = None
        uid = self.env.context['uid'] if 'uid' in self.env.context else False
        user_id = self.env['res.users'].browse(uid)
        if 'stage_id' in vals:
            company = self.env.user.company_id.id
            user = self.env.user.id
            # new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            new_stage = self.env['crm.stage'].browse(vals['stage_id']) if 'stage_id' in vals else self.stage_id
            # booking_stage_id = int(
            #     self.env['ir.config_parameter'].sudo().get_param('ars_vehicle_sales.booking_stage_id'))
            config_group_records = literal_eval(self.env['ir.config_parameter'].sudo().get_param('ars_vehicle_sales.pipeline_stages_ids'))
            teams = self.env['crm.team'].search(
                [('company_id', '=', company), ('team_type', 'in', ['sales']), ('user_id', '=', user)])
            if new_stage.id in config_group_records:
                for lead in self:
                    if not teams:
                        raise ValidationError(
                            f"You do not have access for the stage - '{new_stage.name}.'")
                    if not lead.partner_id.street or not lead.partner_id.pan_no or not lead.partner_id.zip:
                        raise ValidationError(
                            "Please fill the mandatory fields in Customer - Street, PIN Code, and PAN No.")
        # booking_stage = self.env['ir.config_parameter'].sudo().get_param('ars_vehicle_sales.booking_stage_id')
        booking_stage = user_id.company_id.booking_stage_id
        stage = vals.get('stage_id')
        if stage and booking_stage:
            if int(stage) == int(booking_stage.id):
                if not self.booking_date:
                    vals['booking_date'] = datetime.now()
                    test_msg = {'message': f'Booking successfully confirmed for [{self.contact_name if self.contact_name else ""}]. Awaiting further instructions.', 'title': 'title', 'sticky': True}
                    self.env.user.notify_info(**test_msg)
        elif stage:
            test_msg = {'message': f'Pipeline updated: [{new_stage.name if new_stage is not None else ""}]',
                        'title': 'title', 'sticky': True}
            self.env.user.notify_info(**test_msg)
        if len(self.ids) == 1:
            previous_state_id = self.stage_id
        result = super(ars_sale_crm_lead, self).write(vals)
        # The below line of code is commented because now every thing is going to happens based on fields values changes in crm.
        # we restrict the drag & drop option in pipeline so, the below lines of code not using.
        # if len(self.ids) == 1:
        #     if previous_state_id.probability == 100 and self.stage_id != previous_state_id and not self.env.user.has_group('ars_vehicle_sales.group_access_crm_stage'):
        #         raise ValidationError('You do not have access to change the state')
        res_value = {}
        for res in self:
            if res.partner_id:
                if 'gender' in vals:
                    res_value.update({'gender': vals['gender']})
                if 'annual_income' in vals:
                    res_value.update({'annual_income': vals['annual_income']})
                if 'street' in vals:
                    res_value.update({'street': vals['street']})
                if 'street2' in vals:
                    res_value.update({'street2': vals['street2']})
                if res_value:
                    res.partner_id.write(res_value)
        return result

    @api.multi
    def create(self, vals):
        if 'stage_id' in vals:
            company = self.env.user.company_id.id
            user = self.env.user.id
            new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            booking_stage_id = int(
                self.env['ir.config_parameter'].sudo().get_param('ars_vehicle_sales.pipeline_stages_ids'))
            teams = self.env['crm.team'].search(
                [('company_id', '=', company), ('team_type', 'in', ['sales']), ('user_id', '=', user)])
            if new_stage.id == booking_stage_id:
                for lead in self:
                    if not teams:
                        raise UserError(
                            f"You do not have access for the stage - '{new_stage.name}.'")
                    if not lead.partner_id.street or not lead.partner_id.pan_no or not lead.partner_id.zip:
                        raise ValidationError(
                            "Please fill the mandatory fields in Customer - Street, PIN Code, and PAN No.")
        return super(ars_sale_crm_lead, self).create(vals)
    # //

    @api.model
    def create(self, values):
        res_id = super(ars_sale_crm_lead, self).create(values)
        return res_id

    @api.depends('dob')
    def _compute_age_from_dob(self):
        today = date.today()
        if self.dob:
            dob = datetime.strptime(self.dob, '%Y-%m-%d')
            self.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if self.partner_id:
                self.partner_id.write({'dob': self.dob})

    @api.depends('is_test_drive')
    def _total_test_drive(self):
        self.no_of_test_drive = self.env['ars.test.drive'].search_count([('opportunity_id', '=', self.id)])


class ars_sale_crm_sale(models.Model):
    _inherit = 'sale.order'

    bank_account = fields.Many2one('res.bank', string="Financer")
    sale_aftersales = fields.Char('Team Type')
    transfer_type = fields.Selection(
        [('internal_transfer', 'Internal Transfer'), ('external_transfer', 'External Transfer')],
        string="Transfer Type")
    # wh_approve = fields.Boolean(default=False, copy=False, string="WH Request", track_visibility='onchange')
    # fin_approve = fields.Boolean(default=False, copy=False, string="FIN Request", track_visibility='onchange')
    # wh_approved = fields.Boolean(default=False, copy=False, string="WH Approved", track_visibility='onchange')
    # fin_approved = fields.Boolean(default=False, copy=False, string="FIN Approved", track_visibility='onchange')
    # sale_type = fields.Selection([('vehicle', 'Vehicle'), ('parts', 'Parts'),
    #                               ('accessories', 'Accessories'), ('others', 'Others')])
    # customer_reference = fields.Char(string="Customer Reference")
    # customer_reference_date = fields.Date(string="Customer Reference Date")
    # sale_order_number = fields.Char('SO Number', copy=False)

    # @api.model
    # def fields_view_get(self, view_id="sale.view_order_form", view_type='form', toolbar=False, submenu=False):
    #     res = super(ars_sale_crm_sale, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     transfer_type = self.env.context.get('default_transfer_type')
    #     if transfer_type:
    #         if transfer_type == 'internal_transfer':
    #             domain = [('is_dealer', '=', True)]
    #             doc = etree.XML(res['arch'])
    #             for node in doc.xpath("//field[@name='partner_id']"):
    #                 node.set('domain', str(domain))
    #             res['arch'] = etree.tostring(doc, encoding='unicode')
    #         else:
    #             domain = []
    #             doc = etree.XML(res['arch'])
    #             for node in doc.xpath("//field[@name='partner_id']"):
    #                 node.set('domain', str(domain))
    #             res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res

    @api.model
    def fields_view_get(self, view_id="sale.view_order_form", view_type='form', toolbar=False, submenu=False):
        res = super(ars_sale_crm_sale, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                             submenu=submenu)

        transfer_type = self.env.context.get('default_transfer_type')
        if transfer_type:
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='partner_id']"):
                node.set('context', "{'default_is_dealer': True}")

                if transfer_type == 'internal_transfer':
                    node.set('domain', "[('is_dealer', '=', True)]")
                    node.set('options', "{'no_create': True}")
                    node.set('readonly', '0')
                else:
                    node.set('domain', "[]")

            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for sale in self:
            rounded_value = round(sale.amount_total, 0)
            sale.amount_total_words = sale.currency_id.amount_to_text(rounded_value)

    # @api.multi
    # def _get_proforma_invoice_types(self):
    #     self.ensure_one()
    #     proforma_type = ''
    #     if len(self.order_line) == 1:
    #         for line in self.order_line:
    #             # print("catalog",line.product_id.catalog_type.name)
    #             if line.product_id.catalog_type.name == 'Vehicle':
    #                 proforma_type = 'vehicle'
    #     # print("proforma",proforma_type)
    #     return proforma_type

    @api.model
    def create(self, vals):
        sale_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.ids)])
        if vals.get('name', _('New')) == _('New'):
            if sale_team or 'sale_type' in vals:
                if sale_team.team_type == 'sales' and vals['sale_type'] == 'vehicle':
                    if 'company_id' in vals:
                        # vals['name'] = self.env['ir.sequence'].with_context(
                        #     force_company=vals['company_id']).next_by_code('vehicle.sale.quotation') or _('New')

                        seq = self.env['ir.sequence'].search([
                            ('code', '=', 'vehicle.sale.quotation'),
                            ('branch', '=', vals['branch_id'])
                        ], limit=1)
                        if seq:
                            vals['name'] = seq.with_context(force_company=self.company_id.id).next_by_id()
                        else:
                            raise UserError(f"Please create a sequence for branch {self.branch_id.name}")
                    else:
                        # vals['name'] = self.env['ir.sequence'].next_by_code('vehicle.sale.quotation') or _('New')

                        seq = self.env['ir.sequence'].search([
                            ('code', '=', 'vehicle.sale.quotation'),
                            ('branch', '=', vals['branch_id'])
                        ], limit=1)
                        if seq:
                            vals['name'] = seq.next_by_id()
                        else:
                            raise UserError(f"Please create a sequence for branch {self.branch_id.name}")



                elif sale_team.team_type == 'sales' and vals['sale_type'] == 'parts':
                    if 'company_id' in vals:
                        # vals['name'] = self.env['ir.sequence'].with_context(
                        #     force_company=vals['company_id']).next_by_code('parts.sale.quotation') or _('New')

                        seq = self.env['ir.sequence'].search([
                            ('code', '=', 'parts.sale.quotation'),
                            ('branch', '=', vals['branch_id'])
                        ], limit=1)
                        if seq:
                            vals['name'] = seq.with_context(force_company=self.company_id.id).next_by_id()
                        else:
                            raise UserError(f"Please create a sequence for branch {vals['branch_id']}")

                    else:
                        seq = self.env['ir.sequence'].search([
                            ('code', '=', 'parts.sale.quotation'),
                            ('branch', '=', vals['branch_id'])
                        ], limit=1)
                        if seq:
                            vals['name'] = seq.next_by_id()
                        else:
                            raise UserError(f"Please create a sequence for branch {vals['branch_id']}")
                        # vals['name'] = self.env['ir.sequence'].next_by_code('parts.sale.quotation') or _('New')
        res = super(ars_sale_crm_sale, self).create(vals)
        return res

    @api.multi
    def _get_vehicle_tax_amount_by_group_wise(self):
        self.ensure_one()
        res = {}
        for line in self.order_line:
            if line.product_id.catalog_type.name == 'Vehicle':
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
                                                partner=self.partner_shipping_id)['taxes']
                for tax in line.tax_id:
                    group = tax.tax_group_id
                    print(group.name)
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['name'] = tax.name
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            else:
                pass
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [(l[1]['name'], l[1]['amount'], l[1]['base'], len(res)) for l in res]
        # print(res)
        return res

    @api.multi
    def _get_tcs_vehicle_tax_amount(self):
        self.ensure_one()
        tcs = {}
        other_tax = {}
        tax_amount = {'amount': 0.0}
        for line in self.order_line:
            if line.product_id.catalog_type.name == 'Vehicle':
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
                                                partner=self.partner_shipping_id)['taxes']
                for tax in line.tax_id:
                    group = tax.tax_group_id
                    if 'TCS' in group.name:
                        tcs.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    else:
                        other_tax.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            if 'TCS' in tax.name:
                                tcs[group]['name'] = tax.name
                                tcs[group]['amount'] += t['amount']
                                tcs[group]['base'] += t['base']
                            else:
                                other_tax[group]['name'] = tax.name
                                other_tax[group]['amount'] += t['amount']
                                other_tax[group]['base'] += t['base']
                                tax_amount['amount'] += t['amount']
            else:
                pass
        tcs = sorted(tcs.items(), key=lambda l: l[0].sequence)
        tcs = [(l[1]['name'], l[1]['amount'], l[1]['base'] + tax_amount['amount'], len(tcs)) for l in tcs]
        other_tax = sorted(other_tax.items(), key=lambda l: l[0].sequence)
        other_tax = [(l[1]['name'], l[1]['amount'], l[1]['base'], len(other_tax)) for l in other_tax]
        return tcs

    @api.multi
    def _get_other_tax_amount_by_group_wise(self):
        self.ensure_one()
        res = {}
        for line in self.order_line:
            if line.product_id.catalog_type.name != 'Vehicle':
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
                                                partner=self.partner_shipping_id)['taxes']
                for tax in line.tax_id:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['name'] = tax.name
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            else:
                pass
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
                emp = self.env['hr.employee'].search([('user_id', '=', order.user_id and order.user_id.id or False)])
                emp = emp and emp[0] or False
                user_list = []
                emp and emp.parent_id and emp.parent_id.user_id and user_list.append(emp.parent_id.user_id.id)
                admin_lst = self.env['hr.employee'].search_read([('parent_id', '=', False)], fields=['user_id'])
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
    is_approve = fields.Boolean(string='Enable Approve button', compute="_enable_approve_button", copy=False,
                                store=False)

    @api.multi
    def get_sale_type(self):
        if self.sale_type == 'vehicle':
            return 'vehicle'
        elif self.sale_type in ('parts', 'accessories'):
            return 'after_sales'
        else:
            return 'general'

    @api.multi
    def action_confirm(self):
        print('called action confirm')
        self.ensure_one()
        if self.state != 'to_approve':
            approval = self.env['sales.approval'].search(
                [('employee_id.user_id', '=', self.user_id and self.user_id.id or False), ('type', '=', 'sale')])
        elif self.state == 'to_approve':
            approval = self.env['sales.approval'].search(
                [('employee_id.user_id', '=', self._uid), ('type', '=', 'sale')])
        approval = approval and approval[0] or False
        if approval:
            print('approval', approval)
            print('approval', approval.amount, self.amount_total)
            if approval.amount and approval.amount < self.amount_total:
                if self.state == 'to_approve':
                    self.write({'user_id': self._uid})
                    raise UserError(
                        _('Your approval limit has been exceeded. Please contact your admin to proceed further.'))
                self.write({'state': 'to_approve', 'user_id': self._uid})
                return True
            for ol in self.order_line:
                if approval.discount and approval.discount < ol.discount:
                    if self.state == 'to_approve':
                        self.write({'user_id': self._uid})
                        raise UserError(
                            _('Your approval limit has been exceeded. Please contact your admin to proceed further.'))
                    self.write({'state': 'to_approve', 'user_id': self._uid})
                    return True
        # if self.team_id.team_type == 'sales' and
        if not self.order_line:
            raise UserError(_(
                'Not allowed to confirm an order without order lines'))
        result = super(ars_sale_crm_sale, self).action_confirm()
        return result


class ars_sale_order_line(models.Model):
    _inherit = "sale.order.line"

    vin_no = fields.Many2one('stock.production.lot', string="VIN")
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)


class ars_sale_invoice(models.Model):
    _inherit = 'account.invoice'
    e_invoice_status = fields.Char()

    delivery_type = fields.Selection([('home_delivery', 'Home Delivery'), ('showroom', 'Showroom')])
    after_sale_intro = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    model = fields.Many2one('product.product', string="Model Variant")



    @api.constrains('gate_pass_date')
    def gate_pass_date_validation(self):
        for rec in self:
            given_date = rec.gate_pass_date
            if given_date:
                given_date_obj = datetime.strptime(given_date, "%Y-%m-%d")
                date_today = datetime.today()
                if self.env.user.company_id.restrict_gp_date:
                    if given_date_obj.date() < date_today.date():
                        raise ValidationError(_("Warning: Gate pass date can't be set to a date in the past"))
                if given_date_obj > date_today:
                    raise ValidationError(_("Warning: Gate pass date can't be a future date"))

    @api.constrains('date_invoice')
    def invoice_date_validation(self):
        for rec in self:
            given_date = rec.date_invoice
            if given_date and rec.type == 'out_invoice':
                given_date_obj = datetime.strptime(given_date, "%Y-%m-%d")
                date_today = datetime.today()
                if self.env.user.company_id.restrict_bd_inv:
                    if given_date_obj.date() < date_today.date():
                        raise ValidationError(_("Warning: Invoice date can't be set to a date in the past"))
                if given_date_obj > date_today:
                    raise ValidationError(_("Warning: Invoice date can't be a future date"))

    @api.multi
    def invoice_print(self):
        res = super(ars_sale_invoice, self).invoice_print()
        sale_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.ids)])
        if sale_team:
            if sale_team.team_type == 'sales':
                self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
                return self.env.ref('ars_vehicle_sales.before_sales_invoice').report_action(self)
        return res

    @api.multi
    def action_print_gate_pass(self, report=None):
        self.ensure_one()
        if not self.gate_pass_date:
            self.gate_pass_date = date.today()
        if self.ars_invoice_type == 'vehicle':
            vehcile_obj = self.env['fleet.vehicle'].sudo().search(
                [('mvariant_id', 'in', self.invoice_line_ids.mapped('product_id.id')),
                 ('driver_id', '=', self.partner_id.id), ('vin_sn', 'in', self.invoice_line_ids.mapped('vin_no.name'))])
            if not vehcile_obj:
                raise ValidationError(_('Vehicle not found against Customer.'))
            if not vehcile_obj.license_plate:
                raise ValidationError(_('Please enter Registration Number of Vehicle to print Gate Pass.'))
            view = self.env.ref('ars_vehicle_sales.view_gate_pass_wiz')
            return {
                'name': _('Print Gate Pass'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'gate.pass.wiz',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'context': {'report': True},
                'target': 'new',
            }
        # elif report is None:
        #     data = self.env.ref('ars_vehicle_sales.gatepass_report').with_context(doc=self).report_action(
        #         self)
        #     return data
        else:
            return True

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for sale in self:
            sale.amount_total_words = sale.currency_id.amount_to_text(sale.amount_total)

    def get_amount_total_words_rounded(self):
        """Return the rounded amount_total in words for the record."""
        self.ensure_one()
        rounded_total = round(self.amount_total, 0)
        return self.currency_id.amount_to_text(rounded_total)

    @api.multi
    def action_print_gate_pass_button(self):
        if self.state in ['open', 'paid']:
            data = self.env.ref('ars_vehicle_sales.gatepass_report').with_context(doc=self).report_action(
                self)
            return data
        else:
            return True

    def ars_action_invoice_open(self):
        for rec in self:
            given_date_invoice = rec.date_invoice
            if given_date_invoice and rec.type == 'out_invoice':
                given_date_obj = datetime.strptime(given_date_invoice, "%Y-%m-%d")
                date_today = datetime.today()
                if self.env.user.company_id.restrict_bd_inv:
                    if given_date_obj.date() < date_today.date():
                        raise ValidationError(_("Warning: Invoice date can't be set to a date in the past"))
                if given_date_obj > date_today:
                    raise ValidationError(_("Warning: Invoice date can't be a future date"))
            given_gate_pass_date = rec.gate_pass_date
            if given_gate_pass_date:
                given_date_gate_pass = datetime.strptime(given_gate_pass_date, "%Y-%m-%d")
                date_today = datetime.today()
                if self.env.user.company_id.restrict_gp_date:
                    if given_date_gate_pass.date() < date_today.date():
                        raise ValidationError(_("Warning: Gate pass date can't be set to a date in the past"))
                if given_date_gate_pass > date_today:
                    raise ValidationError(_("Warning: Gate pass date can't be a future date"))
            rec.action_invoice_open()
            result = rec.action_print_gate_pass()
            if isinstance(result, dict):  # Check if the result is an action dictionary
                return result
        return True

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
                res = self._create_invoice(order, so_line, amount)
                res.mobile = order.mobile
                res.email = order.email
                if order.sale_type == 'vehicle':
                    res.ars_invoice_type = 'vehicle'
                elif order.sale_type in ('parts', 'accessories'):
                    res.ars_invoice_type = 'after_sales'
                else:
                    res.ars_invoice_type = 'general'
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
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('sales.approval'))
    type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], string='Type')
    amount = fields.Float(string='Amount')
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)


class Menu(models.Model):
    _inherit = "website.menu"

    is_visible = fields.Boolean(compute='_compute_visible', string='Is Visible')

    @api.one
    def _compute_visible(self):
        visible = True
        # print('group portal', self.user_has_groups('base.group_portal'))
        if self.page_id and not self.page_id.sudo().is_visible and (
                not self.user_has_groups('base.group_user') and not self.user_has_groups('base.group_portal')):
            visible = False
        self.is_visible = visible


class ARSCrmLostReason(models.Model):
    _inherit = "crm.lost.reason"

    type = fields.Selection([('lead', 'Lead'), ('opportunity', 'Opportunity'), ],
                            help="Type is used to separate Leads and Opportunities")
    sale_type = fields.Selection([('after_sales', 'After Sales'),
                                  ('sales', 'Sales')], string='Sales Type')

