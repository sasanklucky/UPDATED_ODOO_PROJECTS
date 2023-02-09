from odoo import models, fields, api,_
import time
from datetime import datetime, timedelta

    
class resource_cander(models.Model):
       
    _inherit = 'resource.resource'
       
    planner_calender_id = fields.Many2one('planner.calender', 'Calender Resource')
    planner_resource_id = fields.Many2one('planner.calender', 'Resource Pull')
     
    
class planner_cander(models.Model):
    
    _name = 'planner.calender'

    name = fields.Char()
    resource_category = fields.Many2one('resource.category')
    resource_calender = fields.Many2one('resource.calendar')
    member_ids = fields.One2many('resource.resource', 'planner_calender_id', string='Resource')
    resorce_pull_ids = fields.One2many('resource.resource', 'planner_resource_id', string='Resource Pull')
    vehicle = fields.Boolean()
    resource = fields.Boolean()
    shift_end = fields.Boolean()
    activity_types = fields.Many2many('mail.activity.type', string='Activity Types')
    vehicle_process = fields.Many2many('main.process', string='Vehicle Process')

    
class planner_cander_event(models.Model):
    
    _inherit = 'calendar.event'
    
    entry_type = fields.Selection([('plan', 'Plan'), ('actual', 'Actual')], string='Entry Type')
    so_process = fields.Char()
    stop = fields.Datetime('Stop', help="Stop date of an event, without time for full days events")
    event_type = fields.Char()
    # event_ids = fields.Char(string='Events')

class main_process(models.Model):
    _name = 'main.process'

    name = fields.Char()
    sequence = fields.Integer()
    sub_process_id = fields.One2many('sub.process','main_process_id')

class sub_process(models.Model):
    _name = 'sub.process'

    name = fields.Char()
    sequence = fields.Integer()
    main_process_id = fields.Many2one('main.process')


class sale_order(models.Model):
    _inherit = 'sale.order'

    main_process_id = fields.Many2one('main.process', track_visibility='onchange', limit=1)
    main_process_wiget = fields.Char(default='widget')
    bay_tech_allocation = fields.Boolean(default=lambda self: 0)
    is_additional_job = fields.Boolean(default=lambda self: 0)
    is_partial = fields.Boolean(default=lambda self: 0)
    is_hold_approve = fields.Boolean(default=lambda self: 0)
    is_carry_over = fields.Boolean(default=lambda self: 0)
    is_reschedule = fields.Boolean(default=lambda self: 0)
    is_fi_rejection = fields.Boolean(default=lambda self: 0)
    time_at_gate = fields.Date(string="Gate Time")



    def _technician_actual_starttime(self):
        cr = self.env.cr
        cr.execute(""" select (to_char((start_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        'Asia/kolkata','dd-mm-YYYY HH12:MI AM') ) as start_datetime from account_analytic_line a
                        inner join resource_resource res on res.id = a.resource_name
                        inner join project_task pj on pj.id = a.task_id
                        inner join sale_order_line sl on sl.id = pj.sale_line_id
                        inner join sale_order so on so.id = sl.order_id
                        where a.entry_type = 'actual'
                        and so.id = %s
                        and res.resource_category = (SELECT id from resource_category WHERE name = 'Technician')

                    """, (self.id,))

        tech_actual_time = cr.fetchall()
        if tech_actual_time:
            str = tech_actual_time[0][0]
        else:
            str = ''
        return str


    @api.multi
    def time_line_wizard(self):
        self.ensure_one()
        if self:
            action = self.env.ref('ac_rms.action_time_line').read()[0]
            # list_view = self.env.ref('ars_after_sales.action_time_line')
            TransientModel = self.env["time.line"]
            trans_id = []
            cr = self.env.cr
            cr.execute("""select
                                mt.new_value_char as main_process
                                ,mt.create_date as start_date 
                                ,(select t1.create_date from mail_tracking_value t inner join  mail_message t1 
    		                        on t1.id =  t.mail_message_id where t.old_value_integer = mt.new_value_integer and res_id = %s and t.field = 'main_process_id' and t1.model = 'sale.order' limit 1) as end_date
                                ,mt.create_uid as resource
                                from mail_tracking_value mt
                                --inner join resource_resource rc on rc.user_id = mt.create_uid
                                inner join mail_message mm on mm.id =  mt.mail_message_id
                                where mm.res_id = %s
                                and mt.field = 'main_process_id'
                                and mm.model = 'sale.order'""", (self.id, self.id,))
            # cr.execute("""select array_agg(mt.id) as mt_ids
            #                 from mail_tracking_value mt
            #                 inner join mail_message mm on mm.id = mt.mail_message_id
            #                 where mm.res_id = %s
            #                 and mt.field = 'main_process_id'""",(self.id,))
            tracking_data = cr.dictfetchall()
            if tracking_data:
                for data in tracking_data:
                    # for mt_obj in self.env['mail.tracking.value'].browse(data['mt_ids']):
                    # create_uid = self.env['resource.resource'].search([('user_id','=',mt_obj.create_uid.id)]).id
                    # main_process_id = self.env['main.process'].search([('name', '=', mt_obj.new_value_char)]).id
                    vals = {'main_process_id': data['main_process'],
                            'start': data['start_date'],
                            'end': data['end_date'],
                            'user': data['resource']
                            }

                    totalid = TransientModel.create(vals)
                    trans_id.append(totalid.id)
            action['domain'] = [('id', 'in', trans_id)]

            return action

    @api.multi
    def write(self, vals):
        if 'order_line' in vals:
            for line in vals.get('order_line'):
                if line[0] == 0:
                    if self.bay_tech_allocation  == True:
                        vals['is_additional_job'] = True
                        vals['bay_tech_allocation'] = False
                    elif self.is_partial == True:
                        vals['is_additional_job'] = True
                        vals['is_partial'] = False
        res = super(sale_order, self).write(vals)
        return res

    @api.multi
    def action_start(self):
        process_id3 = self.env.ref('ac_rms.main_process3')
        process_id4 = self.env.ref('ac_rms.main_process4')
        process_id5 = self.env.ref('ac_rms.main_process5')
        process_id6 = self.env.ref('ac_rms.main_process6')
        main_process15 = self.env.ref('ac_rms.main_process15')
        main_process16 = self.env.ref('ac_rms.main_process16')
        main_process17 = self.env.ref('ac_rms.main_process17')
        main_process19 = self.env.ref('ac_rms.main_process19')
        crm_id = self.env["crm.lead"].search([('id', '=', self.opportunity_id.id)])
        if self.main_process_id == process_id3:
            self.write({'main_process_id' : process_id4.id,'cre_work_flow' : 'Finish'})
            if crm_id:
                crm_id.write({'cre_work_flow' : 'Finish'})
        elif self.main_process_id == process_id5:
            self.write({'main_process_id': process_id6.id, 'sa_work_flow': 'Finish'})
            if crm_id:
                crm_id.write({'sa_work_flow' : 'Finish'})
        elif self.main_process_id == main_process15:
            self.main_process_id = main_process16
        elif self.main_process_id == main_process17:
            self.write({'main_process_id': main_process19.id, 'sa_work_flow': 'SA Delivery Process'})



    @api.multi
    def action_finish(self):
        process_id4 = self.env.ref('ac_rms.main_process4')
        process_id5 = self.env.ref('ac_rms.main_process5')
        process_id6 = self.env.ref('ac_rms.main_process6')
        process_id7 = self.env.ref('ac_rms.main_process7')
        main_process16 = self.env.ref('ac_rms.main_process16')
        main_process17 = self.env.ref('ac_rms.main_process17')
        main_process19 = self.env.ref('ac_rms.main_process19')
        main_process20 = self.env.ref('ac_rms.main_process20')
        crm_id = self.env["crm.lead"].search([('id', '=', self.opportunity_id.id)])
        if self.main_process_id == process_id4:
            self.write({'main_process_id' : process_id5.id,'cre_work_flow':'Operation Done','sa_work_flow':'Start'})
            if crm_id:
                crm_id.write({'cre_work_flow' : 'Operation Done','sa_work_flow':'Start'})
        elif self.main_process_id == process_id6:
            self.write({'main_process_id': process_id7.id,'sa_work_flow': 'Operation Done'})
            if crm_id:
                crm_id.write({'sa_work_flow':'Operation Done'})
        elif self.main_process_id == main_process16:
            self.write({'main_process_id': main_process17.id, 'sa_work_flow': 'Ready for Delivery'})
            # self.calculate_efficiency()
        elif self.main_process_id == main_process19:
            self.write({'main_process_id': main_process20.id, 'sa_work_flow': 'Operation Done'})
            # self.calculate_efficiency()

    def compute_duration(self, times):
        duration = fields.Datetime.from_string(times[1] + ':00') - \
                   fields.Datetime.from_string(times[0] + ':00')
        duration = duration.total_seconds() and duration.total_seconds() or 1
        return duration

    @api.multi
    def calculate_efficiency(self):
        """
        This method id used to calculate the efficiency of a technician
        based on task in an RO.
        :return:
        """
        tmObj = self.env['account.analytic.line']
        eff_obj = self.env['task.efficiency']
        proj_task = self.env['project.task']

        for case in self:
            duration = {}
            duplicate = []
            resource_vals = {}
            for t in case.tasks_ids:
                for a in t.timesheet_ids.filtered(lambda x: x.status.name in ('Start', 'Restart') and x.resource_type.name == 'Technician'
                and x.entry_type == 'actual').sorted(key=lambda r: r.resource_name.id and r.end_datetime):
                    check_in = (
                    datetime.strptime(a.start_datetime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M')
                    check_out = (
                    datetime.strptime(a.end_datetime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M')

                    # if not resource then create a line.
                    if a.resource_name.id not in resource_vals:
                        resource_vals[a.resource_name.id] = [[check_in, check_out]]

                    else:
                        for t in resource_vals.get(a.resource_name.id):
                            if check_in <= t[1] and check_out >= t[1]:
                                t[1] = check_out

                            else:
                                if check_in > t[1] and [check_in, check_out] not in resource_vals.get(a.resource_name.id):
                                    resource_vals.get(a.resource_name.id).append([check_in, check_out])

            # caluclate the difference in time
            for r in resource_vals:
                duration.update({r: 0})
                for d in resource_vals.get(r):
                    if d not in duplicate:
                        duration[r] += self.compute_duration(d)
                        duplicate.append(d)

            for t in case.tasks_ids:
                if t.planned_hours:
                    no_res = len(t.timesheet_ids.mapped('resource_name')) or 1
                    resource_records = t.timesheet_ids.filtered(lambda x: x.status.name in ('Start', 'Restart') and x.resource_type.name == 'Technician')
                    resource_len = len(resource_records.mapped('resource_name'))
                    records = t.timesheet_ids.filtered(lambda x: x.status.name in ('Start', 'Restart') and x.resource_type.name == 'Technician')
                    finish_date = records.sorted(key=lambda r: r.end_datetime)

                    for r in records.filtered(lambda x: x.status.name in ('Start', 'Restart')).mapped('resource_name'):
                        # weihgted average
                        total_stu = sum([(tk.planned_hours / len(
                            tk.timesheet_ids.mapped('resource_name'))) if tk.timesheet_ids.filtered(
                            lambda x: x.resource_name.id == r.id and x.status.name in ('Start', 'Restart') and x.resource_type.name == 'Technician') else 0 for tk in
                                         case.tasks_ids])

                        weighted = (((((t.planned_hours * 0.6) / no_res) * 100) / ((total_stu * 0.6))) * (
                                    duration.get(r.id)) / 60) / 100

                        eff_obj.create({
                            'task_id': t.id,
                            'plan_stu': t.planned_hours/resource_len,
                            'actual_time': weighted and weighted or 0,
                            'finish_date': finish_date[-1].end_datetime,
                            'resource_id': r.id,
                            'company_id': t.company_id.id
                        })

        # exist_ids = eff_obj.search([])
        # exist_ids.unlink()

        # for t in self.tasks_ids:
        #     for a in t.timesheet_ids.filtered(lambda x: x.entry_type == 'Actual'
        #         and x.status.name in ('Start','Restart') and x.resource_type in ('Technician') and x.resource_name.resource_category in ('Technician')):
        #         eff_obj.create({
        #             'resource_id': a.id,
        #             'plan_stu': a.id,
        #         })
        #
        #         check_in = (datetime.strptime(a.start_datetime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)).strftime(
        #             '%Y-%m-%d %H:%M')
        #
        #         check_out = (datetime.strptime(a.end_datetime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)).strftime(
        #             '%Y-%m-%d %H:%M')


            # for a in t.search([('planned_hours','=', self.tasks_ids.planned_hours)]):
            #     eff_obj.create({
            #         'plan_stu': a.id,
            #     })

            # for r in self.env['resource.resource'].search([('resource_category','=','Technician')]):
            #     eff_obj.create({
            #         'resource_id': r.id,
            #     })

        # for r in self.env['project.task'].search([('planned_hours','=', self.planned_hours)]):
        #     proj_task.create({
        #         'plan_stu': r.id,
        #     })


class crm_lead_main(models.Model):
    _inherit = 'crm.lead'


    main_process_id = fields.Many2one('main.process', track_visibility='onchange', limit=1)
    cre_work_flow = fields.Char(default='No Operation')
    sa_work_flow = fields.Char(default='No Operation')
    is_estimation = fields.Char(default='No Estimation')

    @api.multi
    def action_start(self):
        process_id3 = self.env.ref('ac_rms.main_process3')
        process_id4 = self.env.ref('ac_rms.main_process4')
        process_id5 = self.env.ref('ac_rms.main_process5')
        process_id6 = self.env.ref('ac_rms.main_process6')
        main_process15 = self.env.ref('ac_rms.main_process15')
        main_process16 = self.env.ref('ac_rms.main_process16')
        main_process17 = self.env.ref('ac_rms.main_process17')
        main_process19 = self.env.ref('ac_rms.main_process19')
        # crm_id = self.env["crm.lead"].search([('id', '=', self.opportunity_id.id)])
        if self.main_process_id == process_id3:
            self.write({'main_process_id': process_id4.id, 'cre_work_flow': 'Finish'})
            # if crm_id:
            #     crm_id.write({'cre_work_flow': 'Finish'})
        elif self.main_process_id == process_id5:
            self.write({'main_process_id': process_id6.id, 'sa_work_flow': 'Finish'})
            # if crm_id:
            #     crm_id.write({'sa_work_flow': 'Finish'})
        elif self.main_process_id == main_process15:
            self.main_process_id = main_process16
        elif self.main_process_id == main_process17:
            self.write({'main_process_id': main_process19.id, 'sa_work_flow': 'SA Delivery Process'})

    @api.multi
    def action_finish(self):
        process_id4 = self.env.ref('ac_rms.main_process4')
        process_id5 = self.env.ref('ac_rms.main_process5')
        process_id6 = self.env.ref('ac_rms.main_process6')
        process_id7 = self.env.ref('ac_rms.main_process7')
        main_process16 = self.env.ref('ac_rms.main_process16')
        main_process17 = self.env.ref('ac_rms.main_process17')
        main_process19 = self.env.ref('ac_rms.main_process19')
        main_process20 = self.env.ref('ac_rms.main_process20')
        # crm_id = self.env["crm.lead"].search([('id', '=', self.opportunity_id.id)])
        if self.main_process_id == process_id4:
            self.write({'main_process_id': process_id5.id, 'cre_work_flow': 'Operation Done', 'sa_work_flow': 'Start'})
            # if crm_id:
            #     crm_id.write({'cre_work_flow': 'Operation Done', 'sa_work_flow': 'Start'})
        elif self.main_process_id == process_id6:
            self.write({'main_process_id': process_id7.id, 'sa_work_flow': 'Operation Done'})
            # if crm_id:
            #     crm_id.write({'sa_work_flow': 'Operation Done'})
        elif self.main_process_id == main_process16:
            self.main_process_id = main_process17
        elif self.main_process_id == main_process19:
            self.write({'main_process_id': main_process20.id, 'sa_work_flow': 'Operation Done'})

    @api.multi
    def action_set_new_appointment(self):
        res = super(crm_lead_main,self).action_set_new_appointment()
        action_rec = self.env.ref('ars_after_sales.sale_action_quotations_new1')
        if res.get('res_id'):
            order = self.env["sale.order"].browse(int(res.get('res_id')))
            order.write({'main_process_id': self.main_process_id.id,
                         'cre_work_flow': self.cre_work_flow,
                         'sa_work_flow': self.sa_work_flow,
                         'gate_in_time': self.sec_at_gatetime,
                         'time_at_gate':self.time_at_gate,
                         'delivery_service_advisor':self.delivery_service_advisor.id})
        for record in self:
            if action_rec:
                action = action_rec.read([])[0]
                action['res_id'] = order.id
                return action
        return res


    @api.model
    def create(self, vals):
        vals['main_process_id'] = self.env.ref('ac_rms.main_process1').id
        return super(crm_lead_main, self).create(vals)

    @api.multi
    def write(self, vals):
        for rec in self:
            sale_order_obj = self.env['sale.order'].search([('opportunity_id', '=', rec.id)])
            if sale_order_obj:
                for sale_id in sale_order_obj:
                    if vals.get('main_process_id'):
                        sale_id.main_process_id = vals.get('main_process_id')
        return super(crm_lead_main, self).write(vals)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    main_process_id = fields.Many2one('main.process')


class ActivitySetup(models.Model):
    _name = 'rms.activity.setup'

    stages = fields.Many2one('main.process')
    activity_type = fields.Many2one('mail.activity.type')
    assigned_to = fields.Many2one('res.users')
    mark_as_done = fields.Boolean()


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def create(self, values):
        res_id = super(MailThread, self).create(values)
        if values.get('main_process_id'):
            res_model_id = ''
            res_model = self._name
            if res_model == 'sale.order':
                res_model_id = self.env.ref('sale.model_sale_order').id
            if res_model == 'crm.lead':
                res_model_id = self.env.ref('crm.model_crm_lead').id
            activity_obj = self.env["rms.activity.setup"].search([('stages','=',values.get('main_process_id'))])
            if activity_obj:
                vals = {'res_id':res_id.id,
                        'res_model_id':res_model_id,
                        'res_model':res_model,
                        'res_name': activity_obj.stages.name,
                        'activity_type_id': activity_obj.activity_type.id,
                        'summary': activity_obj.stages.name,
                        # 'note':'',
                        'user_id':activity_obj.assigned_to.id,
                        # 'date_deadline':'',
                        # 'calendar_event_id':''
                        'mark_as_done':activity_obj.mark_as_done
                        }
                mail_activity = self.env["mail.activity"].create(vals)

        return res_id

    @api.multi
    def write(self, values):
        result = super(MailThread, self).write(values)
        if values.get('main_process_id'):
            res_model_id = ''
            res_model = self._name
            if res_model == 'sale.order':
                res_model_id = self.env.ref('sale.model_sale_order').id
            if res_model == 'crm.lead':
                res_model_id = self.env.ref('crm.model_crm_lead').id
            activity_obj = self.env["rms.activity.setup"].search([('stages','=',values.get('main_process_id'))])
            if activity_obj:
                vals = {'res_id':self.id,
                        'res_model_id':res_model_id,
                        'res_model':res_model,
                        'res_name': activity_obj.stages.name,
                        'activity_type_id': activity_obj.activity_type.id,
                        'summary': activity_obj.stages.name,
                        # 'note':'',
                        'user_id':activity_obj.assigned_to.id,
                        # 'date_deadline':'',
                        # 'calendar_event_id':''
                        'mark_as_done':activity_obj.mark_as_done
                        }
                mail_activity = self.env["mail.activity"].create(vals)
        return result


class MailActivity(models.Model):
    _inherit = "mail.activity"

    mark_as_done = fields.Boolean()
    activity_start = fields.Boolean()

    @api.model
    def start_activity(self,record):
        status = False
        if record:
            activity_obj = self.env["mail.activity"].browse(record)
            if activity_obj.res_model == 'sale.order':
                status = True
                sale_obj = self.env["sale.order"].browse(activity_obj.res_id)
                main_process_sequence = sale_obj.main_process_id.sequence + 1
                sale_obj.main_process_id = self.env["main.process"].browse(main_process_sequence)
                activity_obj.activity_start = True
            if activity_obj.res_model == 'crm.lead':
                status = True
                lead_obj = self.env["crm.lead"].browse(activity_obj.res_id)
                main_process_sequence = lead_obj.main_process_id.sequence + 1
                lead_obj.main_process_id = self.env["main.process"].browse(main_process_sequence)
                activity_obj.activity_start = True
        return {'status':status}

    @api.model
    def finish_activity(self, record):
        if record:
            activity_obj = self.env["mail.activity"].browse(record)
            if activity_obj.res_model == 'sale.order':
                sale_obj = self.env["sale.order"].browse(activity_obj.res_id)
                main_process_sequence = sale_obj.main_process_id.sequence + 1
                sale_obj.main_process_id = self.env["main.process"].browse(main_process_sequence)

            if activity_obj.res_model == 'crm.lead':
                lead_obj = self.env["crm.lead"].browse(activity_obj.res_id)
                main_process_sequence = lead_obj.main_process_id.sequence + 1
                lead_obj.main_process_id = self.env["main.process"].browse(main_process_sequence)

            activity_obj.unlink()
        return {}


class rms_company(models.Model):
    _inherit = 'res.company'

    rms_team_typ_id = fields.Many2one('crm.team', 'Team Type')
    rms_team_stage_id = fields.Many2one('crm.stage', 'Stage')
    rms_app_type = fields.Selection([('appointment', 'Appointment'), ('walkin', 'Walk-In')], string='Type')


class ars_configure_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    rms_team_types = fields.Many2one(related="company_id.rms_team_typ_id")
    rms_stages_id = fields.Many2one(related="company_id.rms_team_stage_id")
    rms_appointment_type = fields.Selection([('appointment','Appointment'),('walkin','Walk-In')],related="company_id.rms_app_type", string='Type')

