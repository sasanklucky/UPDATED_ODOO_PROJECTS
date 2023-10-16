from odoo import models, fields, tools, api, _
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from datetime import date


class CrmSummaryReport(models.Model):
    _name = 'crm.summary.report'
    _description = 'CRM Summary Report'
    _auto = False

    sales_consultant = fields.Many2one('res.users', 'Sales Consultant')
    mtd_enquiries = fields.Integer('MTD Enquiries', compute= '_compute_mtd')
    total_open_enquiries = fields.Integer('Total Open Enquiries', compute='_compute_total_open_enquiries')
    lost_enquiries_for_month = fields.Integer('Lost Enquiries for the Month', compute='_compute_lost_enquiries_for_month' )
    hot_prospect = fields.Integer('Hot Prospect', compute='_compute_hot_prospect')
    td = fields.Integer('TD', compute='_compute_td')
    td_ratio = fields.Float('TD Ratio', compute='_compute_td_ratio')
    fresh_bookings = fields.Integer('Fresh Bookings', compute='_compute_fresh_bookings')
    td_to_booking_ratio = fields.Float('TD to Booking Ratio', compute='_compute_booking_ratio' )
    open_bookings = fields.Integer('Open Bookings', compute='_compute_open_bookings')
    deliveries = fields.Integer('Deliveries', compute='_compute_deliveries')

    def _compute_td_ratio(self):
        for data in self:
            if data.mtd_enquiries == 0:
                data.td_ratio = 0
            else:
                data.td_ratio = data.td/data.mtd_enquiries

    def _compute_booking_ratio(self):
        for data in self:
            if data.td == 0:
                data.td_to_booking_ratio = 0
            else:
                data.td_to_booking_ratio = data.open_bookings/data.td

    def _compute_fresh_bookings(self):
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + relativedelta(months=1, days=-1))
        for data in self:
            so = self.env['sale.order'].sudo().search([
                ('create_date', '>=', start_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<=', end_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('user_id', '=', data.sales_consultant.id),
                ('state', 'not in', ('draft', 'sent', 'cancel')),
                ('sale_aftersales', '=', 'sales'),
                ('sale_type', '=', 'vehicle'),
                ('invoice_ids', '=', False)
            ])
            count = 0

            for slo in so:
                status = False
                for picks in slo.picking_ids.filtered(lambda x: x.state not in ('done')):
                    status = True
                if status == True:
                    count += 1
            data.fresh_bookings = count

    def _compute_open_bookings(self):
        for data in self:
            so = self.env['sale.order'].sudo().search([
                ('user_id', '=', data.sales_consultant.id),
                ('state', 'not in', ('draft', 'sent', 'cancel', 'done')),
                ('sale_aftersales', '=', 'sales'),
                ('sale_type', '=', 'vehicle'),
            ])
            count = 0
            for slo in so:
                status = False
                for picks in slo.picking_ids.filtered(lambda x: x.state not in ('done')):
                    print('slo', slo.name)
                    print('team_id', slo.team_id)
                    status = True
                if status == True:
                    count += 1
            data.open_bookings = count

    def _compute_hot_prospect(self):
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', True),
                ('user_id', '=', data.sales_consultant.id),
                ('type', '=', 'opportunity')
            ])
            crm_lead = crm_lead.filtered(lambda x: x.stage_id.name == 'Hot' and x.team_id.team_type == 'sales')
            data.hot_prospect = len(crm_lead)


    def _compute_mtd(self):
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + relativedelta(months=1, days=-1))
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', True),
                ('create_date', '>=', start_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<=', end_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('user_id', '=', data.sales_consultant.id),
                ('type','=','opportunity')
            ])
            crm_lead = crm_lead.filtered(lambda x: x.stage_id.name not in ('Won', 'Lost') and x.team_id.team_type == 'sales')
            data.mtd_enquiries = len(crm_lead)

    def _compute_total_open_enquiries(self):
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', True),
                ('user_id', '=', data.sales_consultant.id),
                ('type', '=', 'opportunity')
            ])
            crm_lead1 = crm_lead.filtered(lambda x: x.stage_id.name not in ('Won', 'Lost') and x.team_id.team_type == 'sales')
            data.total_open_enquiries = len(crm_lead1)


    def _compute_lost_enquiries_for_month(self):
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + relativedelta(months=1, days=-1))
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', False),
                ('create_date', '>=', start_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<=', end_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('type', '=', 'opportunity'),
                ('user_id', '=', data.sales_consultant.id),
            ])
            crm_lead = crm_lead.filtered(lambda x: x.lost_reason is not None and x.team_id.team_type == 'sales')
            data.lost_enquiries_for_month = len(crm_lead)

    def _compute_deliveries(self):
        for data in self:
            invoices = self.env['account.invoice'].sudo().search([
                ('type','=','out_invoice'),
                ('user_id', '=', data.sales_consultant.id),
                ('state', '!=', 'cancel'),
            ])
            invoices = invoices.filtered(lambda x: x.team_id.team_type == 'sales')
            data.deliveries = len(invoices)

    def _compute_td(self):
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', True),
                ('type', '=', 'opportunity'),
                ('user_id', '=', data.sales_consultant.id),
                ('is_test_drive', '=', True),
            ])
            crm_lead = crm_lead.filtered(lambda x: x.stage_id.name != 'Won' and x.stage_id.name != 'Lost' and x.team_id.team_type == 'sales')
            print('this', crm_lead)
            print('len', len(crm_lead))

            data.td = len(crm_lead)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        print("table name", self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
        select row_number() over() as id,
        ru.id as sales_consultant          
        from res_users ru where ru.salesperson = 'true'
        )""" % (self._table))

    #         # Moving the attachments in the message
    #         # TODO: Fix void res_id on attachment when you create an activity with an image
    #         # directly, see route /web_editor/attachment/add
    #         activity_message = record.message_ids[0]
    #         message_attachments = self.env['ir.attachment'].browse(activity_attachments[activity.id])
    #         message_attachments.write({
    #             'res_id': activity_message.id,
    #             'res_model': activity_message._name,
    #         })
    #         activity_message.attachment_ids = message_attachments
    #         message |= activity_message
    #
    #     self.unlink()
    #     return message.ids and message.ids[0] or False






class CrmSummaryReportSource(models.Model):
    _name = 'crm.summary.source.report'
    _description = 'CRM Summary Source Wise Report'
    _auto = False

    source = fields.Many2one('utm.source', 'Source')
    mtd_enquiries = fields.Integer('MTD Enquiries', compute= '_compute_mtd')
    total_open_enquiries = fields.Integer('Total Open Enquiries', compute='_compute_total_open_enquiries')
    lost_enquiries_for_month = fields.Integer('Lost Enquiries for the Month', compute='_compute_lost_enquiries_for_month' )
    hot_prospect = fields.Integer('Hot Prospect', compute='_compute_hot_prospect')
    td = fields.Integer('TD', compute='_compute_td')
    td_ratio = fields.Float('TD Ratio', compute='_compute_td_ratio')
    fresh_bookings = fields.Integer('Fresh Bookings', compute='_compute_fresh_bookings')
    td_to_booking_ratio = fields.Float('TD to Booking Ratio', compute='_compute_booking_ratio' )
    open_bookings = fields.Integer('Open Bookings', compute='_compute_open_bookings')
    deliveries = fields.Integer('Deliveries', compute='_compute_deliveries')

    def _compute_td_ratio(self):
        for data in self:
            if data.mtd_enquiries == 0:
                data.td_ratio = 0
            else:
                data.td_ratio = data.td/data.mtd_enquiries

    def _compute_booking_ratio(self):
        for data in self:
            if data.td == 0:
                data.td_to_booking_ratio = 0
            else:
                data.td_to_booking_ratio = data.open_bookings/data.td

    def _compute_fresh_bookings(self):
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + relativedelta(months=1, days=-1))
        for data in self:
            so = self.env['sale.order'].sudo().search([
                ('create_date', '>=', start_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<=', end_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('source_id', '=', data.source.id),
                ('state', 'not in', ('draft', 'sent', 'cancel')),
                ('sale_aftersales', '=', 'sales'),
                ('sale_type', '=', 'vehicle'),
                ('invoice_ids', '=', False)
            ])
            count = 0

            for slo in so:
                status = False
                for picks in slo.picking_ids.filtered(lambda x: x.state not in ('done')):
                    status = True
                if status == True:
                    count += 1
            data.fresh_bookings = count

    def _compute_open_bookings(self):
        for data in self:
            so = self.env['sale.order'].sudo().search([
                ('source_id', '=', data.source.id),
                ('state', 'not in', ('draft', 'sent', 'cancel', 'done')),
                ('sale_aftersales', '=', 'sales'),
                ('sale_type', '=', 'vehicle'),
            ])
            count = 0
            for slo in so:
                status = False
                for picks in slo.picking_ids.filtered(lambda x: x.state not in ('done')):
                    status = True
                if status == True:
                    count += 1
            data.open_bookings = count

    def _compute_hot_prospect(self):
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', True),
                ('source_id', '=', data.source.id),
                ('type', '=', 'opportunity')
            ])
            crm_lead = crm_lead.filtered(lambda x: x.stage_id.name == 'Hot' and x.team_id.team_type == 'sales')
            data.hot_prospect = len(crm_lead)


    def _compute_mtd(self):
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + relativedelta(months=1, days=-1))
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', True),
                ('create_date', '>=', start_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<=', end_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('source_id', '=', data.source.id),
                ('type','=','opportunity')
            ])
            crm_lead = crm_lead.filtered(lambda x: x.stage_id.name not in ('Won', 'Lost') and x.team_id.team_type == 'sales')
            data.mtd_enquiries = len(crm_lead)

    def _compute_total_open_enquiries(self):
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', True),
                ('source_id', '=', data.source.id),
                ('type', '=', 'opportunity')
            ])
            crm_lead1 = crm_lead.filtered(lambda x: x.stage_id.name not in ('Won', 'Lost') and x.team_id.team_type == 'sales')
            data.total_open_enquiries = len(crm_lead1)


    def _compute_lost_enquiries_for_month(self):
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + relativedelta(months=1, days=-1))
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', False),
                ('create_date', '>=', start_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<=', end_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('type', '=', 'opportunity'),
                ('source_id', '=', data.source.id),
            ])
            crm_lead = crm_lead.filtered(lambda x: x.lost_reason is not None and x.team_id.team_type == 'sales')
            data.lost_enquiries_for_month = len(crm_lead)

    def _compute_deliveries(self):
        for data in self:
            invoices = self.env['account.invoice'].sudo().search([
                ('type','=','out_invoice'),
                ('order_id.source_id', '=', data.source.id),
                ('state', '!=', 'cancel'),
            ])
            invoices = invoices.filtered(lambda x: x.team_id.team_type == 'sales')
            data.deliveries = len(invoices)

    def _compute_td(self):
        for data in self:
            crm_lead = self.env['crm.lead'].sudo().search([
                ('active', '=', True),
                ('type', '=', 'opportunity'),
                ('source_id', '=', data.source.id),
                ('is_test_drive', '=', True),
            ])
            crm_lead = crm_lead.filtered(lambda x: x.stage_id.name != 'Won' and x.stage_id.name != 'Lost' and x.team_id.team_type == 'sales')
            data.td = len(crm_lead)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        print("table name", self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
        select row_number() over() as id,
        utm_source.id as source         
        from utm_source
        )""" % (self._table))
