from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
from odoo.exceptions import UserError
from lxml import etree
from openerp.osv.orm import setup_modifiers
import json


class ARS_sale_order(models.Model):
    _inherit = "sale.order"

    @api.model
    def _ars_default_warehouse_id(self):

        userid = self.env.user
        company = self.env.user.company_id.id
        if userid.sale_team_id.team_type == 'sales':
            warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
            # warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
            return warehouse_ids
        if userid.sale_team_id.team_type == 'after_sales':
            warehouse_ids = self.env['stock.warehouse'].search([('name', '=', 'Parts Warehouse')], limit=1)
            # warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
            return warehouse_ids

    @api.multi
    def _compute_vehicle_count(self):
        for partner in self:
            # operator = 'child_of' if partner.is_company else '='  # the opportunity count should counts the opportunities of this company and all its contacts
            partner.vehicle_count = self.env['fleet.vehicle'].search_count(
                [('driver_id', '=', partner.partner_id.id), ('license_plate', '=', partner.regn_no.license_plate),
                 ('vin_sn', '=', partner.vin_no)])

    @api.multi
    def print_quotation(self):
        res = super(ARS_sale_order, self).print_quotation()
        sale_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.ids)])
        if sale_team:
            if sale_team.team_type == 'after_sales':
                self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
                return self.env.ref('ars_after_sales.estimate_order').report_action(self)
        return res

    @api.multi
    def get_warranty_claims(self):
        for order in self:
            order.warranty_ids = self.env['ars.sale.warranty'].search([('order_id', '=', order.id)])
            order.warranty_cnt = len(order.warranty_ids)

    instructions = fields.Many2one('instructions', ondelete='cascade')
    vehicle_count = fields.Integer("Vehicle", compute='_compute_vehicle_count')
    customer_voice_sale = fields.One2many("customer.voice", 'cust_sale', ondelete='cascade')
    regn_no = fields.Many2one('fleet.vehicle', string="Regn No")
    # doc_no = fields.Char(string='Doc.No')
    doc_type = fields.Selection([('appointment', 'Appointment'), ('walkin', 'Walkin'), ], string='Type',
                                default='appointment')
    vin_no = fields.Char(string="VIN")
    model = fields.Many2one('product.product')
    service_advisor = fields.Many2one('res.users', string="Service Advisor")
    delivery_service_advisor = fields.Many2one('res.users')
    appointment_date = fields.Datetime(string="Appointment Date")
    delivery_date = fields.Datetime(string="Delivery Date & Time")
    mileage_in = fields.Integer(string="Kilometer In")
    mileage_out = fields.Integer(string="Kilometer Out")
    show_cal = fields.Boolean(default=False)
    sale_aftersales = fields.Char()
    resource_id_sale = fields.Many2one('resource.resource', string="Service Advisor")
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', default='')
    mobile = fields.Char(related='partner_id.mobile')
    email = fields.Char(related='partner_id.email')
    warranty_ids = fields.One2many('ars.sale.warranty', 'order_id', 'Warranty Claims', compute='get_warranty_claims',
                                   copy=False)
    warranty_cnt = fields.Integer('Warranty Count', compute='get_warranty_claims')
    warranty_stage_widget = fields.Char(default='widget')
    counter_parts = fields.Boolean(default=False)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_ars_default_warehouse_id)

    product_catalog_id = fields.Many2one('product.catalog', string='Product Catalog',
                                         compute="_get_product_sale_catalog")
    sale_type = fields.Selection([('vehicle', 'Vehicle'), ('parts', 'Parts'),
                                  ('accessories', 'Accessories'), ('others', 'Others')])

    @api.multi
    @api.depends('sale_type')
    def _get_product_sale_catalog(self):
        if self.sale_type == 'vehicle':
            domain = [('name', '=', 'Vehicle')]
        elif self.sale_type == 'parts':
            domain = [('name', '=', 'Parts')]
        elif self.sale_type == 'accessories':
            domain = [('name', '=', 'Accessories')]
        elif self.sale_type == 'others':
            domain = [('name', '=', 'Others')]
        else:
            domain = []
        if domain:
            self.product_catalog_id = self.env['product.catalog'].search(domain, limit=1).id

    @api.multi
    @api.onchange('resource_id_sale')
    def resource_map(self):
        self.service_advisor = self.resource_id_sale.user_id.id

    @api.multi
    @api.onchange('partner_id')
    def Estimate_change(self):
        partner = False
        if self.partner_id.id or partner:
            if not partner:
                partner = self.partner_id
            if partner:
                customer_details = self.env['fleet.vehicle'].search([('driver_id', '=', partner.id)])

                if len(customer_details) == 1:
                    vin_no_details = self.env['stock.production.lot'].search([('name', '=', customer_details.vin_sn)])
                    self.count_vehicle = len(customer_details)
                    self.partner_id = self.partner_id.id
                    self.phone = self.partner_id.phone
                    self.regn_no = customer_details.id
                    self.vin_no = customer_details.vin_sn
                    self.vehicle_model = customer_details.mvariant_id.id
                else:
                    lot_pro_id = []
                    for cus in customer_details:
                        vin_no_details = self.env['stock.production.lot'].search([('name', '=', cus.vin_sn)])
                        lot_pro_id.append(vin_no_details.id)
                    self.env.cr.execute('delete from customer_regn')
                    self.partner_id = self.partner_id.id
                    self.phone = self.partner_id.phone
                    multiple_regno = {}
                    multiple_regno.setdefault('domain', {})
                    multiple_regno['domain']['regn_no'] = repr([('id', 'in', customer_details.ids)])
                    multiple_regno['domain']['vin_no'] = repr([('id', 'in', lot_pro_id)])
                    return multiple_regno

        # if self.regn_no:
        #     customer_details = self.env['stock.production.lot'].search([('reg_no', '=', self.regn_no.id)])
        #     self.count_vehicle = len(customer_details)
        #     if len(customer_details) == 1:
        #         self.partner_id = self.partner_id.id
        #         self.phone = self.partner_id.phone
        #         self.regn_no = customer_details.id
        #         self.vin_no = customer_details.name
        #         self.vehicle_model = customer_details.product_id.name

    # @api.multi
    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     res = super(ARS_sale_order, self).onchange_partner_id()
    #     values = {
    #         'vin_no': ''
    #     }
    #     self.update(values)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        con = self.env.context
        res = super(ARS_sale_order, self).fields_view_get(view_id, view_type, toolbar, submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            fleet_v = self.env['fleet.vehicle'].search([('vehicle_status', '=', 'customer')])
            for node in doc.xpath("//field[@name='regn_no']"):
                user_filter = "[('id', 'in'," + str(fleet_v.ids) + " )]"
                node.set('domain', user_filter)

        res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    @api.onchange('regn_no')
    def regnno_change(self):
        if self.regn_no.license_plate != '/':
            customer_details = self.env['fleet.vehicle'].search([('license_plate', '=', self.regn_no.license_plate)])

            if len(customer_details) == 1:
                vin_no_details = self.env['stock.production.lot'].search([('name', '=', customer_details.vin_sn)])
                self.count_vehicle = len(customer_details)
                self.partner_id = customer_details.driver_id.id
                self.phone = customer_details.driver_id.phone
                self.regn_no = customer_details.id
                self.vin_no = customer_details.vin_sn
                # self.vin_no = customer_details.vin_sn
                # self.vehicle_model = customer_details.mvariant_id.id
                self.model = customer_details.mvariant_id.id
                self.mileage_in = customer_details.odometer

    @api.multi
    @api.onchange('vin_no')
    def vinno_change(self):
        if self.vin_no:
            customer_details = self.env['fleet.vehicle'].search([('vin_sn', '=', self.vin_no)])
            self.count_vehicle = len(customer_details)
            if len(customer_details) == 1:
                self.partner_id = customer_details.driver_id.id
                self.phone = customer_details.driver_id.phone
                # self.regn_no = customer_details.id
                self.vin_no = self.vin_no
                # self.vehicle_model = customer_details.mvariant_id.id
                self.model = customer_details.mvariant_id.id

    @api.multi
    @api.onchange('mobile')
    def mobile_change(self):

        customer_details = self.env['fleet.vehicle'].search([('license_plate', '=', self.regn_no.license_plate)])

    def _prepare_so_line(self, line, sale_line, count, partner):
        rse_data = {}
        data = {
            'product_id': line.product_id.id,
            # 'layout_category_id': line.layout_category_id.id,
            'name': line.name,
            'product_uom_qty': line.product_uom_qty,
            'qty_delivered': line.qty_delivered,
            'qty_invoiced': line.qty_invoiced,
            'product_uom': line.product_uom.id,
            'category': line.category.id,
            # 'analytic_tag_ids': line.analytic_tag_ids.id,
            'price_unit': line.product_id.list_price,
            'tax_id': [(6, 0, line.tax_id.ids)],
            # 'discount': line.discount,
            'price_subtotal': line.price_subtotal,
            'customer_split': partner,
            # 'price_total': line.price_total,
        }
        # if self.partner_id:
        #     data.update({'customer_split':self.partner_id})
        if count == 0 and not sale_line:
            rse_data = data
        else:
            if not sale_line.filtered(lambda y: y.product_id == line.product_id) and line.product_id:
                rse_data = data
        return rse_data

    @api.multi
    @api.onchange('customer_voice_sale')
    def onchange_instructions(self):
        new_lines = self.env['sale.order.line']
        count = 0
        for x in self.customer_voice_sale:
            cust_voices = x.instructions.order_line
            for cust_voice in cust_voices:
                data = self._prepare_so_line(cust_voice, self.order_line, count, self.partner_id)
                if data:
                    new_line = new_lines.new(data)
                    new_lines += new_line
                    count += 1
        if new_lines:
            # self.order_line = False
            self.order_line += new_lines
        # else:
        #     self.order_line = False
        return {}

    # resolve_o2m_commands_to_record_dicts = onchange_instructions

    # @api.multi
    # def unlink(self):
    #     activities = self.search([('cuacstomer_voice_sale', '=', self.customer_voice_sale.id)])
    #     if len(activities) == 1:
    #         self.new_lines.unlink()
    #     return super(ARS_sale_order, self).unlink()

    @api.multi
    def vehicle_info(self):
        vehicle_details = self.env['fleet.vehicle'].search(
            [('driver_id', '=', self.partner_id.id), ('license_plate', '=', self.regn_no.license_plate),
             ('vin_sn', '=', self.vin_no)])
        form_view = self.env.ref('ars_vehicle_sales.ars_vehicle_view_form_inherit')
        return {
            'name': _('Vehicle Info'),
            'res_model': 'fleet.vehicle',
            'view_id': form_view.id,
            'views': [(form_view.id, 'form'), ],
            'res_id': vehicle_details.id,
            'type': 'ir.actions.act_window',
            'target': 'self'
        }

    @api.multi
    def set_aligment(self):
        for od in self:
            for ol in od.order_line:
                if ol.category and ol.category.name.lower() == 'warranty' and ol.ars_warranty_price != ol.price_unit:
                    ol.price_unit = ol.ars_warranty_price
        return True

    @api.model
    def create(self, vals):
        res = super(ARS_sale_order, self).create(vals)
        sale_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.ids)])
        if sale_team:
            if sale_team.team_type == 'after_sales':
                s_name = self.env['ir.sequence'].next_by_code('sale_estimate')
                res.name = s_name
                if self.env.context.get('counter_parts'):
                    res.counter_parts = 'parts'
                else:
                    res.sale_aftersales = 'after_sales'
            elif sale_team.team_type == 'sales':
                res.sale_aftersales = 'sales'
        return res

    @api.multi
    def action_confirm(self):
        print('called action ccccccccccccccccccccccccccccccccccccccccc=')
        result = super(ARS_sale_order, self).action_confirm()
        confirm_so = self.env['ir.sequence'].next_by_code('aftersale_so')
        self.name = confirm_so
        return result

    @api.multi
    def action_cancel(self):
        result = super(ARS_sale_order, self).action_cancel()
        for order in self:
            for wr in order.warranty_ids:
                wr.state = 'draft'
        return result

    # def create_warranty_order(self):
    #     for od in self:
    #         line_ids = []
    #         warnVals = {}
    #         for ol in od.order_line:
    #             if ol.category and ol.category.name == 'Warranty':
    #                line_ids.append(ol.id)
    #
    #         if line_ids and not od.warranty_id:
    #            warnVals = {'partner_id':od.partner_id.id,
    #                        'regn_no': od.regn_no and od.regn_no.id,
    #                        'model_id': od.model and od.model.id,
    #                        'vin_no': od.vin_no or '',
    #                        'order_id': od.id,
    #                        'order_lines' : [(6, 0, line_ids)]}
    #
    #         if od.warranty_id and not line_ids:
    #            warnVals = {'order_lines' : [(6, 0, line_ids)]}
    #
    #         if not od.warranty_id and warnVals:
    #            warnVals['name'] = self.env['ir.sequence'].next_by_code('warranty_claims')
    #            od.warranty_id = self.env['ars.sale.warranty'].create(warnVals)
    #
    #         else:
    #            od.warranty_id.write(warnVals)
    #
    #     return True

    @api.multi
    def write(self, vals):
        res = super(ARS_sale_order, self).write(vals)
        if self.state in ('so', 'sent', 'sale', 'done'):
            self.create_warranty_order()
        return res

    def action_schedule_meeting1(self):
        """ Open meeting's calendar view to schedule meeting on current opportunity.
            :return dict: dictionary value for created Meeting view
        """
        self.ensure_one()
        action = self.env.ref('calendar.action_calendar_event').read()[0]
        partner_ids = self.env.user.partner_id.ids
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        action['context'] = {
            'default_opportunity_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_partner_ids': partner_ids,
            'default_team_id': self.team_id.id,
            'default_name': self.name,
        }
        return action

    # def time_line_wizard(self):
    #     """ Open meeting's calendar view to schedule meeting on current opportunity.
    #         :return dict: dictionary value for created Meeting view
    #     """
    #     self.ensure_one()
    #     action = self.env.ref('ars_after_sales.action_time_line').read()[0]
    #     partner_ids = self.env.user.partner_id.ids
    #     if self.partner_id:
    #         partner_ids.append(self.partner_id.id)
    #     action['context'] = {
    #         'default_opportunity_id': self.id if self.type == 'opportunity' else False,
    #         'default_partner_id': self.partner_id.id,
    #         'default_partner_ids': partner_ids,
    #         'default_team_id': self.team_id.id,
    #         'default_name': self.name,
    #     }
    #     return {
    #         'name':_("Quality Control"),
    #         'view_mode': 'form',
    #         'view_type': 'form',
    #         'view_id': False,
    #         #'model': 'kms.qc.name.wiz',
    #         'res_model': 'kms.qc.name.wiz',
    #         'res_id':wizard_id,
    #         'type': 'ir.actions.act_window',
    #         'nodestroy': True,
    #         'target': 'new',
    #         'domain': '[]',
    #         'context': dict(context, active_ids=ids)
    #     }
    # this function should need to improve
    @api.multi
    def action_view_invoice(self):
        userid = self.env.user
        res = super(ARS_sale_order, self).action_view_invoice()
        if userid.sale_team_id.team_type == 'after_sales':
            invoices = self.mapped('invoice_ids')
            action = self.env.ref('account.action_invoice_tree1').read()[0]
            if len(invoices) > 1:
                action['domain'] = [('id', 'in', invoices.ids)]
            elif len(invoices) == 1:
                action['views'] = [(self.env.ref('ars_after_sales.invoice_form_inherit').id, 'form')]
                action['res_id'] = invoices.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action
        return res

    @api.multi
    def action_view_warranty(self):
        self.ensure_one()
        action = self.env.ref('ars_after_sales.action_warranty_page').read()[0]
        warranty = self.mapped('warranty_ids')
        if len(warranty) > 1:
            action['domain'] = [('id', 'in', warranty.ids)]
        elif len(warranty) == 1:
            action['views'] = [(self.env.ref('ars_after_sales.view_warranty_form').id, 'form')]
            action['res_id'] = warranty and warranty.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        print(warranty)
        return action

    # @api.multi
    # def time_line_wizard(self):
    #     self.ensure_one()
    #     if self:
    #         action = self.env.ref('ars_after_sales.action_time_line').read()[0]
    #         # list_view = self.env.ref('ars_after_sales.action_time_line')
    #         TransientModel = self.env["time.line"]
    #         trans_id = []
    #         cr = self.env.cr
    #         cr.execute("""select
    #                         mt.new_value_char as main_process
    #                         ,mt.create_date as start_date
    #                         ,(select t1.create_date from mail_tracking_value t inner join  mail_message t1
    #                         on t1.id =  t.mail_message_id where t.old_value_integer = mt.new_value_integer and res_id = %s and t.field = 'main_process_id' and t1.model = 'sale.order' limit 1) as end_date
    #                         ,mt.create_uid as resource
    #                         from mail_tracking_value mt
    #                         --inner join resource_resource rc on rc.user_id = mt.create_uid
    #                         inner join mail_message mm on mm.id =  mt.mail_message_id
    #                         where mm.res_id = %s
    #                         and mt.field = 'main_process_id'
    #                         and mm.model = 'sale.order'""",(self.id,self.id,))
    #         # cr.execute("""select array_agg(mt.id) as mt_ids
    #         #                 from mail_tracking_value mt
    #         #                 inner join mail_message mm on mm.id = mt.mail_message_id
    #         #                 where mm.res_id = %s
    #         #                 and mt.field = 'main_process_id'""",(self.id,))
    #         tracking_data = cr.dictfetchall()
    #         if tracking_data:
    #             for data in tracking_data:
    #                 # for mt_obj in self.env['mail.tracking.value'].browse(data['mt_ids']):
    #                     # create_uid = self.env['resource.resource'].search([('user_id','=',mt_obj.create_uid.id)]).id
    #                     # main_process_id = self.env['main.process'].search([('name', '=', mt_obj.new_value_char)]).id
    #                 vals = {'main_process_id': data['main_process'],
    #                         'start': data['start_date'],
    #                         'end': data['end_date'],
    #                         'user':data['resource']
    #                         }
    #
    #                 totalid = TransientModel.create(vals)
    #                 trans_id.append(totalid.id)
    #         action['domain'] = [('id', 'in', trans_id)]
    #
    #         return action

    # @api.onchange('appointment_date')
    # def appoint_calenderI(self):
    #     self.show_cal = True
    #     res_model = self.env['ir.model'].search([('model','=','sale.order')])
    #     starttime = datetime.strptime(self.appointment_date, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=30)
    #     # vals = {'interval': 1,
    #     #         'cout': 1,
    #     #         'name':'Service Adviser Meeting',
    #     #         'end_type': 'count',
    #     #         'user_id':self.service_advisor.id,
    #     #         'res_model': 'sale.order',
    #     #         'res_id': self.id,
    #     #         'res_model_id':res_model.id,
    #     #         'start_datetime':self.appointment_date,
    #     #         'stop_date date':starttime.strftime("%Y-%m-%d %H:%M:%S"),
    #     #         'start':self.appointment_date,
    #     #         'stop':starttime.strftime("%Y-%m-%d %H:%M:%S")}
    #     # self.env['calendar.event'].create(vals)
    #     return False

    @api.multi
    def _prepare_invoice(self):
        res = super(ARS_sale_order, self)._prepare_invoice()
        res.update({'order_id': self.id})
        # create service history if service order created
        vehicle = self.env['fleet.vehicle'].search(
            [('driver_id', '=', self.partner_id.id), ('license_plate', '=', self.regn_no.license_plate),
             ('vin_sn', '=', self.vin_no)])
        nxt_due = self.env.user.company_id.next_service_due
        remainder = self.env.user.company_id.next_service_remainder
        if vehicle and self.sale_aftersales == 'after_sales':
            #             date_1 = datetime.strptime(date.today(), "%m/%d/%y")
            #             fields.Datetime.from_string(date.today()) + timedelta(days=int(nxt_due))
            if not vehicle.service_due:
                next_service_due = datetime.now().date() + timedelta(days=int(nxt_due))
                set_reminder = datetime.now().date() + timedelta(days=int(remainder))
            else:
                ser_history = vehicle.service_due
                last_service_history = ser_history.sorted(key=lambda r: r.id)[-1]
                next_service_due = datetime.strptime(last_service_history.next_service_due, '%Y-%m-%d') + timedelta(
                    days=int(nxt_due))
                set_reminder = datetime.strptime(last_service_history.set_reminder, '%Y-%m-%d') + timedelta(
                    days=int(remainder))
            if self.env.context.get('count_line') == 0:
                self.env['service.history'].create({
                    'order': self.id,
                    'servicetype': 'First Free Service',
                    'date': date.today(),
                    'next_service_due': next_service_due,
                    'set_reminder': set_reminder,
                    'vehicle_id': vehicle.id,
                })
        return res


class ARSPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'

    product_template_id = fields.Many2one('product.template', string='Product')
    product_catalog_id = fields.Many2one('product.catalog', string='Catalog Type')
    product_id_domain = fields.Char(compute="_compute_product_id_domain", readonly=True, store=False)

    @api.multi
    @api.depends('product_catalog_id')
    def _compute_product_id_domain(self):
        for this in self:
            if not this.product_catalog_id:
                this.product_catalog_id = this.order_id.product_catalog_id.id
            domain = ([('catalog_type', '=', this.product_catalog_id.id)] if this.product_catalog_id else [])
            this.product_id_domain = json.dumps(domain)

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     result = {}
    #     res = super(ARSPurchaseOrderLine, self).onchange_product_id()
    #     if self.env.user.has_group('base.group_system'):
    #         pass
    #     elif self.env.user.has_group('ars_after_sales.group_vehicle'):
    #         result['domain'] = {'product_id': [('catalog_type.name', 'in', ('Vehicle', 'Accessories'))]}
    #     elif self.env.user.has_group('ars_after_sales.group_part'):
    #         result['domain'] = {'product_id': [('catalog_type.name', 'in', ('Labor', 'Parts', 'Accessories'))]}
    #     return

    @api.multi
    @api.onchange('product_template_id')
    def onchange_product_template_id(self):
        self.product_id = False
        print(self.product_template_id.attribute_line_ids)
        if self.product_template_id and self.product_template_id.attribute_line_ids:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            return {'domain': {'product_id': [('id', 'in', varient_ids.ids)]}}
        else:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            self.product_id = varient_ids.id
            return {'domain': {'product_id': [('id', 'in', False)]}}


class ARS_AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    _description = "Invoice Line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        res = super(ARS_AccountInvoiceLine, self)._onchange_product_id()
        if self.env.user.has_group('base.group_system'):
            pass
        elif self.env.user.has_group('ars_after_sales.group_sale_invoice'):
            domain['domain'] = {'product_id': [('catalog_type.name', 'in', ('Vehicle', 'Accessories'))]}
        elif self.env.user.has_group('ars_after_sales.group_aftersale_invoice'):
            domain['domain'] = {'product_id': [('catalog_type.name', 'in', ('Labor', 'Parts', 'Accessories'))]}

        return domain


class ARS_PickingType(models.Model):
    _inherit = "stock.picking.type"

    def get_action_picking_tree_ready(self):
        userid = self.env.user
        if userid.sale_team_id.team_type == 'sales':
            return self._get_action('stock.action_picking_tree_ready')
        elif userid.sale_team_id.team_type == 'after_sales':
            return self._get_action('ars_after_sales.action_picking_tree_ready_aftersale')
        else:
            return self._get_action('stock.action_picking_tree_ready')

    # Inventory Dashboard Count for Aftersales or sales In kanban view.
    def _compute_picking_count(self):
        # TDE TODO count picking can be done using previous two
        userid = self.env.user
        if userid.sale_team_id.team_type == 'after_sales':
            domains = {
                'count_picking_draft': [('state', '=', 'draft'), ('is_aftersale', '=', True)],
                'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting')), ('is_aftersale', '=', True)],
                'count_picking_ready': [('state', '=', 'assigned'), ('is_aftersale', '=', True)],
                'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed')), ('is_aftersale', '=', True)],
                'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                       ('state', 'in', ('assigned', 'waiting', 'confirmed')),
                                       ('is_aftersale', '=', True)],
                'count_picking_backorders': [('backorder_id', '!=', False),
                                             ('state', 'in', ('confirmed', 'assigned', 'waiting')),
                                             ('is_aftersale', '=', True)],
            }
            for field in domains:
                data = self.env['stock.picking'].read_group(domains[field] +
                                                            [('state', 'not in', ('done', 'cancel')),
                                                             ('picking_type_id', 'in', self.ids)],
                                                            ['picking_type_id'], ['picking_type_id'])
                count = {
                    x['picking_type_id'][0]: x['picking_type_id_count']
                    for x in data if x['picking_type_id']
                }
                for record in self:
                    record[field] = count.get(record.id, 0)
            for record in self:
                record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
                record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0
        else:
            domains = {
                'count_picking_draft': [('state', '=', 'draft'), ('is_aftersale', '=', False)],
                'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting')), ('is_aftersale', '=', False)],
                'count_picking_ready': [('state', '=', 'assigned'), ('is_aftersale', '=', False)],
                'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed')), ('is_aftersale', '=', False)],
                'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                       ('state', 'in', ('assigned', 'waiting', 'confirmed')),
                                       ('is_aftersale', '=', False)],
                'count_picking_backorders': [('backorder_id', '!=', False),
                                             ('state', 'in', ('confirmed', 'assigned', 'waiting')),
                                             ('is_aftersale', '=', False)],
            }
            for field in domains:
                data = self.env['stock.picking'].read_group(domains[field] +
                                                            [('state', 'not in', ('done', 'cancel')),
                                                             ('picking_type_id', 'in', self.ids)],
                                                            ['picking_type_id'], ['picking_type_id'])
                count = {
                    x['picking_type_id'][0]: x['picking_type_id_count']
                    for x in data if x['picking_type_id']
                }
                for record in self:
                    record[field] = count.get(record.id, 0)
            for record in self:
                record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
                record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0


class ARS_Picking_aftersale(models.Model):
    _inherit = "stock.picking"

    is_aftersale = fields.Boolean(default=False)


class ARS_StockMove(models.Model):
    _inherit = "stock.move"

    is_aftersale = fields.Boolean(default=False)

    # update is_aftersale field(custom) in Base function overwrite.
    def _assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a new
        picking to assign them to. """
        Picking = self.env['stock.picking']
        for move in self:
            recompute = False
            picking = Picking.search([
                ('group_id', '=', move.group_id.id),
                ('location_id', '=', move.location_id.id),
                ('location_dest_id', '=', move.location_dest_id.id),
                ('picking_type_id', '=', move.picking_type_id.id),
                ('printed', '=', False),
                ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])], limit=1)
            if not picking:
                recompute = True
                picking = Picking.create(move._get_new_picking_values())
            move.write({'picking_id': picking.id})
            userid = picking.sale_id.user_id
            if userid.sale_team_id.team_type == 'after_sales':
                move.update({'is_aftersale': True})
                picking.update({'is_aftersale': True})
            # If this method is called in batch by a write on a one2many and
            # at some point had to create a picking, some next iterations could
            # try to find back the created picking. As we look for it by searching
            # on some computed fields, we have to force a recompute, else the
            # record won't be found.
            if recompute:
                move.recompute()
        return True


class ARS_PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    userid = self.env.user
                    if userid.sale_team_id.team_type == 'after_sales':
                        res.update({'is_aftersale': True})
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)
                if userid.sale_team_id.team_type == 'after_sales':
                    moves.update({'is_aftersale': True})
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return True

    @api.depends('purchase_type')
    def _get_default_product_catalog(self):
        print("product_catalog")
        # if self.lead_order_id.team_id.team_type == 'sales':
        product_catalog = []
        if self.purchase_type == 'vehicle':
            product_catalog = self.env['product.catalog'].search([('name', '=', 'Vehicle')], limit=1)
        elif self.purchase_type == 'after_sales':
            product_catalog = self.env['product.catalog'].search([('name', '=', 'Parts')], limit=1)
        else:
            product_catalog = self.env['product.catalog'].search([], limit=1)
        self.product_catalog_id = product_catalog.id

    product_catalog_id = fields.Many2one('product.catalog', string='Catalog Type',
                                         compute='_get_default_product_catalog')


class ars_sale_advance_payment_inv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def create_invoices(self):
        # print("create_invoices----create_invoices===================",self)
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        print('sale_orders', sale_orders)
        for sl in sale_orders:
            warranty_ids = self.env['ars.sale.warranty'].search(
                [('order_id', '=', sl.id), ('state', 'in', ('draft', 'inprocess'))])
            if warranty_ids:
                raise UserError(_('One of the Warranty Claims is in Draft/In-Progress state.'))
            for ln in sl.order_line:
                if not ln.customer_split and sl.sale_aftersales == 'after_sales':
                    raise UserError(
                        _('For one of the lines customer is not selected. Please add customer before proceeding.'))
        super(ars_sale_advance_payment_inv, self).create_invoices()
        return {'type': 'ir.actions.act_window_close'}
