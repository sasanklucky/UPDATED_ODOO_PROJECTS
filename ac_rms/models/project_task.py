from odoo import models, fields, api,_
from odoo import http
from odoo.http import request
import pytz
import datetime
import json
from datetime import datetime, timedelta
DEFAULT_DATE_TIME_FORMATE = '%Y-%m-%d %H:%M:%S'


class TaskStatus(models.Model):
    _name = "task.status"

    name = fields.Char()



class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.multi
    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for record in self.filtered(lambda r: r.end_datetime and r.start_datetime):
            duration = fields.Datetime.from_string(record.end_datetime) - fields.Datetime.from_string(record.start_datetime)
            record.unit_amount = duration.total_seconds() / 3600

    # def _default_resource(self):
    #     return self.env['resource.resource'].search([('user_id', '=', self.env.uid)])

    # @api.multi
    # @api.depends('resource_ids')
    # def _compute_resource_catg(self):
    #     for record in self:
    #         record.resource_type = record.resource_ids.mapped('resource_type').id


    status = fields.Many2one('task.status', string='Status')
    entry_type = vehicle_status = fields.Selection([('actual', 'Actual'), ('plan', 'Plan')],'Entry Type')
    resource_type = fields.Many2one('resource.category', string='Resource Type')
    resource_name = fields.Many2one('resource.resource',string='Resource Name')
    mapped_bay_resource = fields.Many2one('resource.resource', string='Bay Resource Name')
    start_datetime = fields.Datetime('Start Date & Time')
    end_datetime = fields.Datetime('End Date & Time')
    break_reason = fields.Char('Break Reason')
    date = fields.Datetime('Date', required=True, default=fields.Datetime.now)
    unit_amount = fields.Float(compute="_compute_duration", default=0.0)
    is_release = fields.Boolean('Is Release')
    # resource_ids = fields.Many2many('resource.resource', 'resource_account_line_rel', 'account_line_id', 'resource_id',
    #                                 string='Resource Name', readonly=True,
    #                                 default=lambda self: self._default_resource())



class TaskEfficiency(models.Model):
    _name = 'task.efficiency'
    _rec_name = 'task_id'
    _description = 'Efficiency and Productivity'


    @api.depends('actual_time','plan_stu')
    @api.multi
    def _get_prod_eff(self):
        for case in self:
            if case.productivity > 0:
                case.productivity = ((case.plan_stu * 0.6) / 480) * 100
            if case.efficiency > 0:
                case.efficiency = (((case.plan_stu * 0.6) / (case.actual_time))) * 100


    task_id = fields.Many2one('project.task')
    plan_stu = fields.Float("Plan Time")
    actual_time = fields.Float("Actual Time")
    finish_date = fields.Date("Complete Date")
    resource_id = fields.Many2one('resource.resource','Technician')
    productivity = fields.Float(string="Productivity", store=True,compute="_get_prod_eff")
    efficiency = fields.Float(string="Efficiency", store=True, compute="_get_prod_eff")
    company_id = fields.Many2one('res.company','Company')

class Task(models.Model):
    _inherit = "project.task"

    def _compute_start_end_datetime(self):
        user = request.env['res.users'].browse(self.env.uid)
        if user.partner_id.tz:
            tz = pytz.timezone(user.partner_id.tz)
        else:
            tz = pytz.utc
        for data in self:
            analytic_line = data.timesheet_ids.filtered(lambda x:x.entry_type == 'actual' and x.status != request.env.ref("ac_rms.status2")  and x.resource_type == request.env.ref("ac_rms.resource_categories_tech"))
            # users = analytic_line.mapped('resource_name').mapped('user_id')
            for line in analytic_line:
                if line.start_datetime:
                    start_time = fields.Datetime.from_string(line.start_datetime) + timedelta(hours=5, minutes=30)
                    # start_time = (fields.Datetime.from_string(line.start_datetime).replace(tzinfo=pytz.utc).astimezone(tz)).strftime(
                    #     DEFAULT_DATE_TIME_FORMATE)
                    data.start_datetime_fn = start_time
                if line.end_datetime:
                    end_time = fields.Datetime.from_string(line.end_datetime) + timedelta(hours=5, minutes=30)
                    # end_time = (fields.Datetime.from_string(line.end_datetime).replace(tzinfo=pytz.utc).astimezone(tz)).strftime(
                    #     DEFAULT_DATE_TIME_FORMATE)
                    data.end_datetime_fn = end_time
            # return data

    def _compute_break_reason(self):
        for data in self:
            analytic_line = data.timesheet_ids.filtered(lambda x:x.entry_type == 'actual' and x.status == request.env.ref("ac_rms.status2")  and x.resource_type == request.env.ref("ac_rms.resource_categories_tech"))
            for line in analytic_line:
                if line.break_reason:
                    data.break_reason_fn = line.break_reason

    effect_ids = fields.One2many('task.efficiency', 'task_id')
    start_datetime_fn = fields.Datetime(compute='_compute_start_end_datetime')
    end_datetime_fn = fields.Datetime(compute='_compute_start_end_datetime')
    break_reason_fn = fields.Char(compute='_compute_break_reason')
    order_id = fields.Many2one('sale.order', related="sale_line_id.order_id")
    fi_status_new = fields.Selection([('pass', 'Pass'),('fail', 'Fail'),],related='sale_line_id.fi_status',string="FI Status")




    @api.multi
    def task_start_time(self,task_id):
        task_obj = self.env["project.task"].browse(task_id)
        timesheet_obj = task_obj.timesheet_ids.filtered(lambda x:x.entry_type =='actual' and x.resource_type == request.env.ref('ac_rms.resource_categories_tech') and x.status == request.env.ref("ac_rms.status1"))
        if timesheet_obj:
            if timesheet_obj[-1].start_datetime:
                start_time = (datetime.strptime(timesheet_obj[-1].start_datetime, "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                return start_time

    @api.multi
    def break_rerasons(self, task_id):
        break_reason = ''
        resource = request.env["resource.resource"].search([('user_id', '=', self.env.uid)])
        task_obj = self.env["project.task"].browse(task_id)
        timesheet_obj = task_obj.timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and x.resource_name == resource and x.status == request.env.ref("ac_rms.status7"))
        if timesheet_obj:
            break_reason = timesheet_obj[-1].break_reason
        return break_reason

class TaskType(models.Model):
    _inherit = "project.task.type"

    stage_display_name = fields.Char('Display Name')


# class SOAllocationType(models.Model):
#     _name = "order.allocation.type"
#
#     allocation_type_name = fields.Char()
#     ro_id = fields.Many2one('sale.order')

class saleorder(models.Model):
    _inherit = "sale.order"

    cre_work_flow = fields.Char(default='No Operation')
    sa_work_flow = fields.Char(default='No Operation')
    gate_in_time = fields.Datetime('Gate Time')

class saleline(models.Model):
    _inherit = "sale.order.line"

    fi_status = fields.Selection([('pass', 'Pass'), ('fail', 'Fail'), ], default='pass', string="FI Status")




