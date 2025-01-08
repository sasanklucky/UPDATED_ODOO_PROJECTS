import datetime
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from openerp.exceptions import UserError, ValidationError
from openerp.exceptions import except_orm, Warning, RedirectWarning
from lxml import etree
from odoo.http import request
from datetime import datetime, timedelta, date
import re


class ARS_crm_lead(models.Model):
    _name = "crm.lead"
    _inherit = "crm.lead"

    @api.constrains('mobile')
    def mobile_validation(self):
        pattern = r'^[1-9]\d{9}$'
        if not re.match(pattern, self.mobile) if self.mobile  else True:
            raise ValidationError(_('Mobile number should contain 10 digits and the first digit should not be zero'))

    stage_name = fields.Char(compute='_compute_stage_name', store=True)

    @api.depends('stage_id')
    def _compute_stage_name(self):
        for record in self:
            record.stage_name = record.stage_id.name if record.stage_id else ''

    def update_model_info(self):
        crm_lead = self.search([('vehicle_line', '!=', False)])
        for record in crm_lead:
            record.model_id = record.vehicle_line[0].product_template_id
        crm_lead = self.search([('vehicle_line', '!=', False), ('active', '=', False)])
        for record in crm_lead:
            record.model_id = record.vehicle_line[0].product_template_id

    def update_booking_date(self):
        cr = self.env.cr
        for res in self:
            query = f"""select date::Date from mail_message mm
                        join mail_tracking_value mtv on mm.id = mtv.mail_message_id
                        where mm.res_id = {res.id} and mm.model = 'crm.lead' and mtv.new_value_char ilike 'Booked' 
                        limit 1
                    """
            cr.execute(query)
            all_data = cr.dictfetchall()
            # print(all_data)
            if all_data and all_data[0]:
                res.write({'booking_date': all_data[0].get('date')})

    @api.onchange('vehicle_line')
    def _onchange_vehicle_line(self):
        for record in self:
            if record.vehicle_line:
                record.model_id = record.vehicle_line[0].product_template_id.id

    # _rec_name = "company_type"
    # user_id1 = fields.Many2one('res.users', string='Service Advisor', index=True, track_visibility='onchange',
    #                           default=lambda self: self.env.user)
    @api.onchange('email_from')
    def email_validation(self):
        match_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if self.email_from:
            if not re.match(match_email, self.email_from):
                raise UserError(f'{self.email_from} is not a valid email')

    @api.model
    def default_team_id(self):
        # channel = self.env['res.users'].browse(self.env.uid).sale_team_id
        return self.env['res.users'].browse(self.env.uid).sale_team_id

    # @api.model
    # def default_saleperson(self):
    #     ids = []
    #     res = self.env['res.users'].search([])
    #     hr_category = self.env['hr.employee.category'].search([('id', '=', 1)])
    #     hr_employee = self.env['hr.employee'].search([('category_ids', 'in', hr_category.ids)])
    #     for record in hr_employee:
    #         if hr_employee:
    #             ids.append(record.user_id.id)
    #     return [('id', 'in', ids)]
    @api.multi
    @api.depends('contact_name')
    def name_get(self):
        result = []
        for rec in self:
            name = rec.contact_name
            result.append((rec.id, name))
        return result

    @api.multi
    def changeservice(self):
        userid = self.env.user
        if userid.sale_team_id.team_type == 'after_sales':
            return 'Service'

    # @api.one
    # def _get_filter(self):
    #     ids = []
    #     res = self.env['res.users'].search([])
    #     hr_category = self.env['hr.employee.category'].search([('id', '=', 3)])
    #     for record in res:
    #         hr_employee = self.env['hr.employee'].search([('user_id', '=', record.id), ('category_ids', 'in', hr_category.ids)])
    #         if hr_employee:
    #             ids.append(record.id)
    #     return [('id', 'in', ids)]
    @api.depends('order_ids')
    def _compute_sale_amount_total_estimate(self):
        for lead in self:
            total = 0
            nbr = 0
            for order in lead.order_ids:
                if order.state in ('draft', 'sent'):
                    nbr += 1
                if order.state not in ('draft', 'so', 'sent', 'cancel'):
                    total += 1
            lead.sale_amount_total_estimation = total
            lead.sale_number_estimation = nbr

    @api.depends('order_ids')
    def _compute_sale_amount_before_estimate(self):
        for lead in self:
            total = 0
            for order in lead.order_ids:
                if order.state not in ('draft', 'done', 'sale', 'cancel'):
                    total += 1
            lead.sale_number_before_estimation = total

    company_type = fields.Selection([('individual', 'Individual'), ('company', 'Company')], string="Customer Type")
    name = fields.Char('Opportunity', required=False, index=True, default=changeservice)
    team_id = fields.Many2one('crm.team', string='Sales Channel', oldname='section_id',
                              default=default_team_id, index=True, track_visibility='onchange',
                              help='When sending mails, the default email address is taken from the sales channel.')
    vehicle_line = fields.One2many('crm.lead.line', 'lead_order_id', string='Vehicle Lines')
    regn_no = fields.Many2one('fleet.vehicle')
    vin_no = fields.Char(help='vin no changes')
    vehicle_model = fields.Many2one('product.product', string="Vehicle Model")
    vehicle_model_char = fields.Char(string="Vehicle Model")
    appo_date = fields.Datetime(string="Appointment Date")
    delivery_time = fields.Datetime(string="Delivery Date")
    kilometer_in = fields.Integer(string="Kilometer")
    sec_at_gatetime = fields.Datetime(string="At Gate Time")
    customer_voice = fields.One2many("customer.voice", 'customer_voice_id')
    count_vehicle = fields.Integer()
    html = fields.Html()
    type_lead = fields.Selection([
        ('appointment', 'Appointment'),
        ('walkin', 'Walk In'),
        ('p&d', 'P&D'),
    ], string='Type', default='appointment')
    user_id = fields.Many2one('res.users', default=False)
    hr_emp_cat = fields.Many2one('hr.employee.category')
    resource_id_lead = fields.Many2one('resource.resource', string="Service Advisor")
    sale_number_estimation = fields.Integer(compute='_compute_sale_amount_total_estimate',
                                            string="Number of Estimations")
    sale_amount_total_estimation = fields.Integer(compute='_compute_sale_amount_total_estimate', string="Sum of Orders",
                                                  help="Untaxed Total of Confirmed Orders")
    # is_aftersale = fields.Boolean(default=False)
    # instructions = fields.Many2one('instructions')
    sale_number_before_estimation = fields.Integer(compute='_compute_sale_amount_before_estimate',
                                                   string="Number of Estimations")
    delivery_service_advisor = fields.Many2one('res.users')
    time_at_gate = fields.Date(string="Gate Time")
    is_estimation = fields.Char(default='No Estimation')
    crm_lead_stage = fields.Many2one('crm.lead.stage', string="Lead Stage")
    enquiry_date = fields.Datetime(string=" Enquiry Date", default=fields.Datetime.now)
    opportunity_conversion_date = fields.Date('Opportunity Conversion Date')
    model_id = fields.Many2one('product.template', string="Model")
    lead_token = fields.Char("Lead Token")

    # booking_date = fields.Date(string="Booking Date")

    # @api.onchange('stage_id')
    # def _set_booking_date(self):
    #     booking_stage = self.env['ir.config_parameter'].sudo().get_param('ars_after_sales.booking_stage_id')
    #     if booking_stage and self.stage_id.id == int(booking_stage):
    #         print('booking_stage', booking_stage, self.stage_id, datetime.date.today())
    #         self.booking_date = datetime.date.today()

    # planned_revenue = fields.Float('Expected Revenue', compute="_get_compute_expected_revenue",
    #                                track_visibility='always', store=True)

    @api.multi
    @api.onchange('vehicle_line.product_id')
    def _get_compute_expected_revenue(self):
        for rec in self:
            if rec.type == 'opportunity' and rec.team_id.team_type == 'sales':
                # print("Expected Revenue", rec.stage, sum(rec.vehicle_line.mapped('product_template_id.list_price')))
                rec.write({'planned_revenue': sum(rec.vehicle_line.mapped('product_template_id.list_price'))})
            else:
                print("Expected Revenue")

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        user_team_id = self.env.user.sale_team_id.id
        team_id = user_team_id
        # context = dict(self.env.context)
        # context['default_team_id'] = team_id
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    # @api.onchange('user_id')
    # def in_advisor_change_crmlead(self):
    #     if self.user_id.id:
    #         self.user_id = self.user_id.id
    #     else:
    #         self.user_id = False

    @api.multi
    @api.onchange('resource_id_lead')
    def resource_map(self):
        self.user_id = self.resource_id_lead.user_id.id

    @api.multi
    def check_valid_sales_channel(self, sales_team):
        if not sales_team:
            raise ValidationError(_("You are not belongs to any channel, Please select any channel and try again"))
        else:
            return True

    # Crm Menu - On Click Of New Qutation Button In Opportunity Form View
    @api.multi
    def get_prod_action(self):
        if not self.partner_id:
            raise UserError(_('Please Enter The Customer Name'))
        orderid = self.env['sale.order']
        orderline = self.env['sale.order.line']
        action_rec = self.env.ref('sale_crm.sale_action_quotations_new')
        sale_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.ids)])
        self.check_valid_sales_channel(sale_team)
        if sale_team.team_type == 'sales':
            sale_type = 'vehicle'
        elif sale_team.team_type == 'after_sales':
            sale_type = 'parts'
        else:
            sale_type = 'others'
        for record in self:
            if action_rec:
                action = action_rec.read([])[0]
                lines = []
                for vehicle in record.vehicle_line:
                    lines.append((0, 0, {'product_catalog_id': vehicle.product_catalog_id.id,
                                         'product_template_id': vehicle.product_template_id.id,
                                         'product_id': vehicle.product_id.id, 'name': vehicle.name}))
                order_id = orderid.create({'opportunity_id': self.id,
                                           'user_id': record.user_id.id,
                                           'partner_id': record.partner_id.id, 'sale_type': sale_type,
                                           'order_line': lines, 'mobile': self.mobile, 'email': self.email_from})
                action['res_id'] = order_id.id
                return action

    # After Sales Menu - On Click Of New Estimation Button In Appointment Form View
    @api.multi
    def action_set_new_appointment(self):
        sale_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.ids)])
        if sale_team.team_type != 'after_sales':
            raise UserError(_('User Not Belongs to After Sales chanel'))
        if not self.partner_id:
            raise UserError(_('Please Enter The Customer Name'))
        if not self.customer_voice:
            raise UserError(_('Please Enter The Customer Voice'))
        orderid = self.env['sale.order']
        action_rec = self.env.ref('ars_after_sales.sale_action_quotations_new1')
        view = self.env.ref('ars_after_sales.view_order_form_inherit')
        crm_stage = self.env['crm.stage'].search([('category_stage', '=', 'after_sales'),
                                                  ('name', '=', 'Estimation'),
                                                  ('team_id.company_id.id', '=', self.company_id.id)])
        for record in self:
            record.is_estimation = 'Estimation'
            if action_rec:
                action = action_rec.read([])[0]
                voiceline = []
                order_line = []
                cal_obj = self.env['calendar.event'].search([('res_id', '=', record.id)], limit=1)
                for voice in record.customer_voice:
                    voiceline.append((0, 0, {'name': voice.name, 'instructions': voice.instructions.id}))
                    count = 0
                    cust_voices = voice.instructions.order_line
                    for cust_voice in cust_voices:
                        data = self.env['sale.order']._prepare_so_line(cust_voice, self.env['sale.order'].order_line,
                                                                       count, record.partner_id.id)
                        order_line.append((0, 0, data))
                        count += 1
                warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', record.regn_no.company_id.id), ('ars_type', 'in', ['after_sales'])])
                customer_voice = self.env['customer.voice'].search([('customer_voice_id', '=', record.id)])

                order_id = orderid.create({'opportunity_id': self.id,
                                           'partner_id': record.partner_id.id,
                                           'customer_voice_sale': voiceline,
                                           'appointment_date': record.appo_date,
                                           'delivery_date': record.delivery_time,
                                           'mileage_in': record.kilometer_in,
                                           'doc_type': record.type_lead,
                                           'vin_no': record.vin_no,
                                           'regn_no': record.regn_no.id,
                                           'user_id': record.user_id.id,
                                           'model': record.vehicle_model.id,
                                           'order_line': order_line,
                                           'mobile': record.mobile,
                                           'email': record.email_from,
                                           'sale_type': 'parts',
                                           'sale_aftersales': 'after_sales',
                                           'warehouse_id': warehouse_id.id,
                                           'service_options': record.service_options.id,
                                           'service_type': record.service_type.id,
                                           # 'main_process_id':record.main_process_id.id,
                                           # 'cre_work-_flow':record.cre_work_flow,
                                           # 'sa_work_flow':record.sa_work_flow,
                                           # 'gate_in_time':record.sec_at_gatetime
                                           })
                cust_vals = {
                    'name': customer_voice.name,
                    'instructions': customer_voice.instructions.id,
                    'customer_voice_id': order_id.id
                }
                self.env['customer.voice'].create(cust_vals)
                # di = {'record_id':record,'order_id':order_id}

                sale_msg_id = self.env['mail.message'].search([('res_id', '=', order_id.id)], limit=1)
                sale_msg_id.active = False
                values = {}
                msg = self.env['mail.message'].sudo().search([('res_id', '=', record.id)])
                sort_msg = msg.sorted(key=lambda r: r.id)
                for msg_id in sort_msg:
                    track_msg = self.env['mail.tracking.value'].search([('mail_message_id', '=', msg_id.id), (
                        'new_value_char', 'not in', [record.main_process_id.name])])
                    values['res_id'] = order_id
                    values['model'] = 'sale.order'
                    msg_log = msg_id.copy(default=values).id
                    msg_values = {}
                    msg_values['mail_message_id'] = msg_log
                    for track_msg_id in track_msg:
                        track_msg_log = track_msg_id.copy(default=msg_values).id
                # action['view_id'] = view.id
                action['res_id'] = order_id.id
                record.stage_id = crm_stage.id
                return action

    @api.model
    def create(self, vals):
        con = self.env.context
        res_value = {}
        partner_create_id = self.env['res.partner'].search([('id', '=', vals.get('partner_id'))])
        if partner_create_id:
            if 'gender' in vals:
                res_value.update({'gender': vals['gender']})
            if 'annual_income' in vals:
                res_value.update({'annual_income': vals['annual_income']})
            if 'street' in vals:
                res_value.update({'street': vals['street']})
            if 'city' in vals:
                res_value.update({'city': vals['city']})
            if 'street2' in vals:
                res_value.update({'street2': vals['street2']})
            if 'mobile' in vals:
                res_value.update({'mobile': vals['mobile']})
            if 'email_from' in vals:
                res_value.update({'email': vals['email_from']})
            if res_value:
                partner_create_id.write(res_value)
            partner_id = vals.get('partner_id')
            partner = self.env['res.partner'].browse(partner_id)
            partner_name = partner.parent_id.name
            if not partner_name and partner.is_company:
                partner_name = partner.name
            vals.update({'partner_name': partner_name,
                         'contact_name': partner.name if not partner.is_company else False,
                         'title': partner.title.id,
                         'street': partner.street,
                         'street2': partner.street2,
                         'city': partner.city,
                         'state_id': partner.state_id.id,
                         'country_id': partner.country_id.id,
                         'email_from': partner.email,
                         'phone': partner.phone,
                         'mobile': partner.mobile,
                         'zip': partner.zip,
                         'function': partner.function,
                         'website': partner.website,

                         })
            if vals.get('product_id'):
                product = self.env['product.product'].browse(int(vals.get('product_id')))
                description = product.name
                catalog = product.catalog_type
                product_template = product.product_tmpl_id
                vals.update({'vehicle_line': [(0, 0, {'product_id': vals.get('product_id'), 'name': description,
                                                      'product_template_id': product_template.id,
                                                      'product_catalog_id': catalog.id
                                                      })]})
            if vals.get('regn_no'):
                customer_details = self.env['fleet.vehicle'].search(
                    [('id', '=', vals.get('regn_no'))])
                model_sn = customer_details.mvariant_id.id
                vals.update({'vehicle_model': model_sn})
        res = super(ARS_crm_lead, self).create(vals)
        if res.type == 'opportunity':
            if not any([res.mobile, res.email_from, res.source_id, res.city]):
                raise UserError(_("The following fields are mandatory please fill it to continue\n"
                                  " Mobile,Email,Source,City"))
        if res.vehicle_line:
            if res.type == 'opportunity' and res.team_id.team_type == 'sales':
                res.planned_revenue = sum(res.vehicle_line.mapped('product_template_id.list_price'))
        if not vals['model_id']:
            raise ValidationError(_('Please Update Model'))
        return res

    @api.multi
    def write(self, vals):
        # booking_stage = self.env['ir.config_parameter'].sudo().get_param('ars_after_sales.booking_stage_id')
        # stage = vals.get('stage_id')
        # if stage and booking_stage:
        #     if int(stage) == int(booking_stage):
        #         vals['booking_date'] = datetime.date.today()
        res = super(ARS_crm_lead, self).write(vals)
        for res in self:
            if res.type == 'opportunity' and self.team_id.team_type == 'sales':
                if len(res.vehicle_line) < 1:
                    raise ValidationError("Please add at least one product before saving.")
        if not self.model_id:
            raise ValidationError(_('Please Update Model'))
        return res

    #     if self.vehicle_line:
    #         if 'vehicle_line' in vals:
    #             print(vals['vehicle_line'])
    #             for val in vals['vehicle_line']:
    #                 print("Val", val)
    #         #         if 'product_template_id' in val:
    #         #             product_template = self.env['product.template'].browse('product_template_id')
    #         #     planned_revenue = sum(
    #         #         self.vehicle_line.mapped('product_template_id.list_price')) + product_template.list_price
    #         # print("Planned Revenue", planned_revenue)
    #         # vals['planned_revenue'] = planned_revenue
    #     return super(ARS_crm_lead, self).write(vals)

    # Appointment stage id default set in 'Service Due'

    def _default_stage_id(self):
        team = self.env['crm.team'].sudo()._get_default_team_id(user_id=self.env.uid)
        userid = self.env.user
        stage = self._stage_find(team_id=team.id, domain=[('fold', '=', False), ('name', '=', 'New')]).id
        if userid.sale_team_id.team_type == 'after_sales':
            companyid = self.env.user.company_id
            if companyid.team_stage_id.id:
                stage = companyid.team_stage_id.id
        return stage

    # service advisor field bydefault blank
    # @api.onchange('user_id')
    # def _onchange_user_id(self):
    #     res = super(ARS_crm_lead, self)._onchange_user_id()
    #     values = {
    #         'user_id': ''
    #     }
    #     self.update(values)

    @api.multi
    @api.onchange('partner_id')
    def appointment_change(self):
        partner = False
        if self.phone and not self.partner_id.id:
            partner = self.env['res.partner'].search([('phone', '=', self.phone)], order="id desc", limit=1)

        if self.partner_id.id or partner:
            if not partner:
                partner = self.partner_id
            if partner:
                customer_details = self.env['fleet.vehicle'].search([('driver_id', '=', partner.id)])
                if len(customer_details) == 1:
                    vin_no_details = self.env['stock.production.lot'].search([('name', '=', customer_details.vin_sn)])
                    self.count_vehicle = len(customer_details)
                    self.partner_id = customer_details.driver_id.id
                    self.phone = customer_details.driver_id.phone
                    self.regn_no = customer_details.id
                    self.vin_no = customer_details.vin_sn
                    self.vehicle_model = customer_details.mvariant_id.id
                    self.vehicle_model_char = customer_details.mvariant_id.name
                    self.kilometer_in = customer_details.odometer
                # if len(customer_details) != 1:
                #     lot_pro_id = []
                #     for cus in customer_details:
                #         vin_no_details = self.env['stock.production.lot'].search([('name', '=', cus.vin_sn)])
                #         lot_pro_id.append(vin_no_details.id)
                #     self.partner_id = self.partner_id.id
                #     self.phone = self.partner_id.phone or False
                #     multiple_regno = {}
                #     multiple_regno['domain'] = {'regn_no': [('id', '=', customer_details.ids)],
                #                                 'vin_no': [('id', '=', customer_details.ids)]}
                #     return multiple_regno
                else:
                    lot_pro_id = []
                    # self.regn_no = True
                    # self.vin_no = False
                    # self.vehicle_model = False
                    for cus in customer_details:
                        vin_no_details = self.env['stock.production.lot'].search([('name', '=', cus.vin_sn)])
                        lot_pro_id.append(vin_no_details.ids)
                    self.partner_id = self.partner_id.id
                    self.phone = self.partner_id.phone or False
                    # if self.regn_no == False:
                    self.regn_no = False
                    self.vin_no = False
                    self.vehicle_model = False
                    self.vehicle_model_char = False
                    multiple_regno = {}
                    # multiple_regno['domain'] = {'regn_no': [('id', '=', customer_details.ids)], 'vin_no': [('id', '=', customer_details.ids)]}
                    multiple_regno['domain'] = {'regn_no': [('id', '=', customer_details.ids)]}
                    return multiple_regno
        # if self.regn_no:
        #     customer_details = self.env['fleet.vehicle'].search([('license_plate', '=', self.regn_no.license_plate)])
        #     vin_no_details = self.env['stock.production.lot'].search([('name', '=', customer_details.vin_sn)])
        #     self.count_vehicle = len(customer_details)
        #     if len(customer_details) == 1:
        #         self.partner_id = customer_details.driver_id.id
        #         self.phone = customer_details.driver_id.phone
        #         self.regn_no = customer_details.id
        #         self.vin_no = vin_no_details.id
        #         self.vehicle_model = customer_details.model_id.id
        # if self.vin_no:
        #     customer_details = self.env['fleet.vehicle'].search([('vin_sn', '=', self.vin_no.name)])
        #     self.count_vehicle = len(customer_details)
        #     if len(customer_details) == 1:
        #         self.partner_id = customer_details.driver_id.id
        #         self.phone = customer_details.driver_id.phone
        #         self.regn_no = customer_details.id
        #         self.vin_no = self.vin_no.id
        #         self.vehicle_model = customer_details.model_id.id

    @api.multi
    @api.onchange('regn_no')
    def regn_change(self):
        if self.partner_id.id:
            customer_details = self.env['fleet.vehicle'].search([('driver_id', '=', self.partner_id.id)])
            if len(customer_details) > 1:
                multiple_regno = {}
                vehicle_obj = self.env['fleet.vehicle'].search([('id', '=', self.regn_no.id)])
                self.vin_no = vehicle_obj.vin_sn
                self.vehicle_model = vehicle_obj.mvariant_id.id
                self.vehicle_model_char = vehicle_obj.mvariant_id.name
                self.kilometer_in = vehicle_obj.odometer
                multiple_regno['domain'] = {'regn_no': [('id', '=', customer_details.ids)]}
                return multiple_regno
        if self.regn_no.license_plate != '/':
            customer_details = self.env['fleet.vehicle'].search([('license_plate', '=', self.regn_no.license_plate)])

            if len(customer_details) == 1:
                # vin_no_details = self.env['stock.production.lot'].search([('name', '=', customer_details.vin_sn)])
                self.count_vehicle = len(customer_details)
                self.partner_id = customer_details.driver_id.id
                self.phone = customer_details.driver_id.phone
                self.regn_no = customer_details.id
                self.vin_no = customer_details.vin_sn
                # self.vin_no = customer_details.vin_sn
                self.vehicle_model = customer_details.mvariant_id.id
                self.vehicle_model_char = customer_details.mvariant_id.name
                self.kilometer_in = customer_details.odometer

    @api.multi
    @api.onchange('vin_no')
    def vinno_change(self):
        if self.vin_no:
            customer_details = self.env['fleet.vehicle'].search([('vin_sn', '=', self.vin_no)])
            self.count_vehicle = len(customer_details)
            if len(customer_details) == 1:
                self.partner_id = customer_details.driver_id.id
                self.phone = customer_details.driver_id.phone
                self.regn_no = customer_details.id
                self.vin_no = self.vin_no
                self.vehicle_model = customer_details.mvariant_id.id
                self.vehicle_model_char = customer_details.mvariant_id.name

    @api.multi
    @api.onchange('mobile')
    def mobile_change(self):
        request.session['mobile'] = self.mobile
        if self.mobile:
            # pattern = "^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$"
            # if not re.match(pattern, self.mobile):
            #     raise UserError(f'{self.mobile} Please enter a valid mobile number')
            res_details = self.env['res.partner'].search([('mobile', '=', self.mobile)], order="id desc", limit=1)
            if res_details:
                self.partner_id = res_details.id
            else:
                self.partner_id.write({'mobile': self.mobile})

    # onchange of regn no
    #     @api.multi
    #     @api.onchange('regn_no')
    #     def regn_change(self):
    #         customer_details = self.env['stock.production.lot'].search([('id', '=', self.regn_no.id)])
    #         self.vin_no = customer_details.name
    #         self.vehicle_model = customer_details.product_id.id

    # onchange of regn no
    # @api.multi
    # @api.onchange('regn_no')
    # def regn_change(self):
    #     customer_details = self.env['stock.production.lot'].search([('id', '=', self.regn_no.id)])
    #     self.vin_no = customer_details.name
    #     self.vehicle_model = customer_details.product_id.id

    # Check appointment customer having how much count of vehicle(Regn No) in Customer table
    @api.multi
    def check_regn(self):
        self.ensure_one()
        if self.partner_id.id:
            customer_details = self.env['fleet.vehicle'].search([('driver_id', '=', self.partner_id.id)])
            TransientModel = self.env["check.regn"]
            list_view = self.env.ref('ars_after_sales.regn_popup_tree')
            customer_regn = []
            trans_id = []
            for customer in customer_details:
                customer_regn.append(customer.license_plate)
                customer_regn.append(customer.vin_sn)
                customer_regn.append(customer.model_id.name)
                vals = {
                    'regi_no': customer.license_plate, 'vin': customer.vin_sn, 'model': customer.model_id.name
                }
                totalid = TransientModel.create(vals)
                trans_id.append(totalid.id)
            if len(trans_id) > 1:
                return {
                    'name': _('Vehicle'),
                    'res_model': 'check.regn',
                    'view_id': list_view.id,
                    'views': [(list_view.id, 'tree'), ],
                    'domain': [('id', 'in', trans_id)],
                    'type': 'ir.actions.act_window',
                    'target': 'new'
                }
            else:
                return False

    @api.multi
    def redirect_opportunity_view(self):
        userid = self.env.user
        form_view = False
        if userid.sale_team_id.team_type == 'sales':
            form_view = self.env.ref('crm.crm_case_form_view_oppor')
        elif userid.sale_team_id.team_type == 'after_sales':
            form_view = self.env.ref('ars_after_sales.crm_case_form_view_oppor_inherit')
        # tree_view = self.env.ref('crm.crm_case_tree_view_oppor')
        res = super(ARS_crm_lead, self).redirect_opportunity_view()
        res.get('views')[0] = (form_view.id, 'form')
        return res

    # Appointment Create & Edit Inherited
    @api.multi
    def edit_dialog(self):
        userid = self.env.user
        if userid.sale_team_id.team_type == 'sales':
            form_view = self.env.ref('crm.crm_case_form_view_oppor')
        elif userid.sale_team_id.team_type == 'after_sales':
            form_view = self.env.ref('ars_after_sales.crm_case_form_view_oppor_inherit')
        return {
            'name': _('Opportunity'),
            'res_model': 'crm.lead',
            'res_id': self.id,
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'inline'
        }

    # @api.multi
    # def write(self, vals):
    #     sale_order_obj = self.env['sale.order'].search([('opportunity_id','=',self.id)])
    #     if sale_order_obj:
    #         for sale_id in sale_order_obj:
    #             if vals.get('main_process_id'):
    #                 sale_id.main_process_id = vals.get('main_process_id')
    #     return super(ARS_crm_lead, self).write(vals)

class CRMLeadStage(models.Model):
    _name = "crm.lead.stage"

    name = fields.Char(string="Name")


class ARS_crm_lead_line(models.Model):
    _name = "crm.lead.line"

    @api.model
    def _get_default_product_catalog(self):
        print("product_catalog")
        # if self.lead_order_id.team_id.team_type == 'sales':
        product_catalog = self.env['product.catalog'].search([('name', '=', 'Vehicle')])
        return product_catalog.id

    lead_order_id = fields.Many2one('crm.lead', string='Lead Order Lines')
    name = fields.Text(string='Description', required=True)
    product_catalog_id = fields.Many2one('product.catalog', string='Product Catalog',
                                         default=_get_default_product_catalog)
    product_template_id = fields.Many2one('product.template', string='Model')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True)

    @api.multi
    @api.onchange('product_catalog_id')
    def onchange_product_based_on_catalog(self):
        if self.product_catalog_id:
            product = self.env['product.template'].sudo().search([('catalog_type', '=', self.product_catalog_id.id)])
            return {'domain': {'product_template_id': [('id', 'in', product.ids)]}}
        else:
            return {'domain': {'product_template_id': [('id', 'in', False)]}}

    @api.multi
    @api.onchange('product_template_id')
    def onchange_product_template_id(self):
        self.product_id = False
        if self.product_template_id and self.product_template_id.attribute_line_ids:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            return {'domain': {'product_id': [('id', 'in', varient_ids.ids)]}}
        else:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            self.product_id = varient_ids.id
            return {'domain': {'product_id': [('id', 'in', False)]}}

    @api.multi
    @api.onchange('product_id')
    def lead_product_id_change(self):
        self.name = self.product_id.name


class ARS_customer_voice(models.Model):
    _name = "customer.voice"

    cust_sale = fields.Many2one('sale.order')
    order_line = fields.Many2one('sale.order.line', 'Order', ondelete='cascade')
    name = fields.Char(string="Customer Voice")
    instructions = fields.Many2one('instructions', string="Instructions", ondelete='cascade')
    customer_voice_id = fields.Many2one('crm.lead', string='Lead Customer Voice')

    # @api.multi
    # def unlink(self):
    #     activities = self.search([('instructions', '=', self.instructions.id)])
    #     if len(activities) == 1:
    #         self.new_lines.unlink()
    #     return super(ARS_customer_voice, self).unlink()


class ARS_instructions(models.Model):
    _name = "instructions"

    order_id = fields.Many2one('sale.order', 'Order', ondelete='cascade')
    name = fields.Char()
    description = fields.Char()
    order_line = fields.One2many('sale.order.line', 'instruction_id', ondelete='cascade', copy=True)

    # @api.multi
    # def unlink(self):
    #     activities = self.search([('order_line', '=', self.order_line.id)])
    #     if len(activities) == 1:
    #         self.new_lines.unlink()
    #     return super(ARS_instructions, self).unlink()


class ARSSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    instruction_id = fields.Many2one('instructions')
    lead_order_id = fields.Many2one('crm.lead', string='Lead Order Lines')
    order_id = fields.Many2one('sale.order', string='Order Reference', required=False, ondelete='cascade', index=True,
                               copy=False)
    # price_unit = fields.Float(related='product_id.list_price', string="Price")
    category = fields.Many2one('order.line.category', string="Category")
    qty_available_line = fields.Float(string='Qty Available',
                                      compute='_compute_product_qty_on_hand')
    admin_access = fields.Boolean(related='order_id.admin_access')
    admin_access_sale = fields.Boolean(compute="_compute_admin_access_sale", string='Admin Sale Access')

    @api.depends('product_id')
    def _compute_admin_access_sale(self):
        user = self.env.user
        setting_price_config = user.company_id.inv_line_unit_price
        for record in self:
            catalog = self.env['product.catalog'].search(
                [('name', '=', record.product_id.catalog_type.name), ('unit_price', '=', True)])
            record.admin_access_sale = True if record.product_template_id.access_price_unit else any(
                user in group.users for catalog_group in catalog for group in catalog_group.groups) if (
                    catalog and setting_price_config) else False

    @api.depends('product_id', 'order_id.company_id')
    def _compute_product_qty_on_hand(self):
        for line in self:
            product = line.product_id
            company = line.order_id.company_id

            if product and company:
                # Adjust this logic based on your actual product and company structure
                stock_quant = self.env['stock.quant'].search([
                    ('product_id', '=', product.id),
                    ('location_id.company_id', '=', company.id), ('location_id.usage', 'in', ['internal', 'transit'])
                ])

                total_qty = sum(stock_quant.mapped('quantity'))
                line.qty_available_line = total_qty
            else:
                line.qty_available_line = 0.0

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(ARSSaleOrderLine, self).product_id_change()
        if self.env.context.get('counter_parts'):
            return {'domain': {'product_id': [('catalog_type.name', '=', 'Parts')]}}


class SaleOrderCategory(models.Model):
    _name = 'order.line.category'

    name = fields.Char()
    order_line = fields.Many2one('sale.order.line', readonly=1)
    type = fields.Char('Issue Type')


class ARS_aftersale_lead2opportunity(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    aftersale_opp = fields.Boolean(default=False)
    resource_id_opportunity = fields.Many2one('resource.resource', string="Service Advisor")

    @api.multi
    @api.onchange('resource_id_opportunity')
    def resource_map(self):
        self.user_id = self.resource_id_opportunity.user_id.id

    # @api.onchange('team_id')
    # def change_saleperson(self):
    #     print(self.team_id.name)
    #     if self.team_id.team_type == "after_sales":
    #         self.aftersale_opp = True
    #     else :
    #         self.aftersale_opp = False

    # @api.onchange('resource_id_opportunity')
    # def saname_change(self):
    #     act = self.env["crm.lead"]
    #     act_id = act.browse(self.env.context.get('active_id'))
    #     self.resource_id_opportunity = act_id.resource_id_lead.id
    # print(self.resource_id_opportunity)


class customer_regn(models.Model):
    _name = 'customer.regn'

    name = fields.Char()


class ARS_CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def create(self, vals):
        event = super(ARS_CalendarEvent, self).create(vals)
        crm_id = False
        if vals.get('activity_ids'):
            crm_res_id = [crm_id for crm_id in vals.get('activity_ids') if vals.get('activity_ids')]
            if crm_id:
                lead_res_id = crm_id[2].get('res_id')
                if self.env.context.get('active_model') == 'crm.lead':
                    crm_obj = self.env['crm.lead'].search([('id', '=', lead_res_id)], limit=1)
                    crm_obj.appo_date = vals.get('start')
                elif self.env.context.get('active_model') == 'sale.order':
                    sale_obj = self.env['sale.order'].search([('id', '=', lead_res_id)], limit=1)
                    sale_obj.appointment_date = vals.get('start')
        return event

    @api.model
    def default_get(self, fields):
        defaults = super(ARS_CalendarEvent, self).default_get(fields)
        if self.env.context.get('active_model') == 'sale.order':
            model = self.env['ir.model'].search([('model', '=', 'sale.order')]).id
            defaults['res_model_id'] = model
            del defaults['opportunity_id']
        return defaults


class ARS_ResUsers(models.Model):
    _inherit = 'res.users'

    salesperson = fields.Boolean()
    serviceadvisor = fields.Boolean()
    # company = fields.Char()
    # phone = fields.Char()


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    _description = 'Lead To Opportunity Partner'

    @api.multi
    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        present_partner = 0
        multiple_regno = {}
        self.ensure_one()
        values = {
            'team_id': self.team_id.id,
        }

        leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))
        date_today = date.today()
        leads.write({'opportunity_conversion_date': date_today})
        for lead in leads:
            if not all([lead.mobile, lead.email_from, lead.source_id, lead.city]):
                raise UserError(_("The following fields are mandatory please fill it to continue\n"
                                  " Mobile,Email,Source,City,Model"))
            else:
                pattern = "^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$"
                match_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
                # if lead.mobile:
                #     if not re.match(pattern, lead.mobile):
                #         raise UserError(f'{lead.mobile} Mobile Number Should Contain 10 Numbers')
                if lead.email_from:
                    if not re.match(match_email, lead.email_from):
                        raise UserError(f'{lead.email_from} is not a valid email')

        if self.partner_id:
            values['partner_id'] = self.partner_id.id
            customer_details = self.env['fleet.vehicle'].search([('driver_id', '=', self.partner_id.id)])
            if len(customer_details) == 1:
                present_partner = 1
            else:
                present_partner = 10

        if self.name == 'merge':
            leads = self.with_context(active_test=False).opportunity_ids.merge_opportunity()
            if not leads.active:
                leads.write({'active': True, 'activity_type_id': False, 'lost_reason': False})
            if leads.type == "lead":
                values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
                self.with_context(active_ids=leads.ids)._convert_opportunity(values)
            elif not self._context.get('no_force_assignation') or not leads.user_id:
                values['user_id'] = self.user_id.id
                leads.write(values)
        else:
            leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))
            # customer_details = self.env['fleet.vehicle'].search([('driver_id', '=', self.partner_id.id)])
            # print (customer_details+"---------------------------------------------------------")
            values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
            self._convert_opportunity(values)
            if present_partner == 1:
                vin_no_details = self.env['stock.production.lot'].search([('name', '=', customer_details.vin_sn)])
                leads.write({'regn_no': customer_details.id,
                             'vin_no': customer_details.vin_sn,
                             'vehicle_model': customer_details.mvariant_id.id,
                             'kilometer_in': customer_details.odometer})
            # elif present_partner == 10:
            #     multiple_regno['domain'] = {'regn_no': [('id', '=', customer_details.ids)],'vin_no': [('id', '=', customer_details.ids)]}

        return leads[0].redirect_opportunity_view()
