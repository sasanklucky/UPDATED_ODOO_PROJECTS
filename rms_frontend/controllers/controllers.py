# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.ac_rms.controllers.main import Home
import json
import urllib.parse
import werkzeug.utils
from datetime import datetime, timedelta
import werkzeug.utils
from odoo import http
from odoo.http import request
import pytz
from odoo import models, fields, api, _
DEFAULT_DATE_TIME_FORMATE = '%Y-%m-%d %H:%M:%S'
DEFAULT_DATE_TIME_FORMATE1 = '%Y-%m-%d %I:%M:%S'

class RmsFrontend(http.Controller):

    @http.route(['/customer'], type='http', auth="public", website=True, csrf=False)
    def front_customer(self, **kwargs):
        return request.render("rms_frontend.customer",{})

    @http.route(['/save_customer'], type='http', auth="public", website=True, csrf=False)
    def insert_customer(self, **post):
        request.env['res.partner'].create_customer(post)
        return request.render("rms_frontend.customer", {})

class Front_Home(Home):
    @http.route(['/resource_planner'], type='http', auth="public", website=True, csrf=False)
    def planner(self, **kwargs):
        event_check = False
        event_resource = False
        shift_end = False
        view = kwargs.get('view') or 1
        select_view = []
        cr = request.env.cr
        company = request.env.user.company_id
        res_calender = request.env['planner.calender'].search([])
        res_pull = request.env['planner.calender'].browse(int(view))

        pull_resource = res_pull.resorce_pull_ids
        SaleOrder = request.env['sale.order']
        vehicle_processes = res_pull.vehicle_process
        allo_veh = SaleOrder.search([('is_online', '=', True)])

        for res_c in res_calender:
            if res_c.id == int(view):
                select_view.append('selected')
            else:
                select_view.append('')

        waiting_for_inward = request.env.ref("ac_rms.main_process1").id
        sec_process = request.env.ref("ac_rms.main_process2").id
        watng_at_recpn = request.env.ref("ac_rms.main_process3").id
        waiting_inward = SaleOrder.search([('main_process_id', '=', waiting_for_inward)])
        sec = SaleOrder.search([('main_process_id', '=', sec_process)])
        watng_reception = SaleOrder.search([('main_process_id', '=', watng_at_recpn)])
        # bay_allocation = waiting_inward | sec | watng_reception
        cr.execute("""select count(distinct(so.id)) as sale_count,
                                array_agg(distinct(so.id)) as sale_id
                                from sale_order so 
                                inner join sale_order_line sl on sl.order_id = so.id
                                inner join project_task pt on pt.sale_line_id = sl.id
                                inner join project_task_type pty on pty.id = pt.stage_id
                                where so.bay_tech_allocation = false
                                and so.sale_aftersales = 'after_sales'
                                and pty.sequence in (0,7,5,4)
                                order by sale_id
                                """)
        all_data = cr.dictfetchall()
        bay_allocation_count = all_data[0].get('sale_count')
        bay_allocation_id = all_data[0].get('sale_id')
        bay_allocation_ids = []
        if bay_allocation_id:
            bay_allocation_ids = sorted(bay_allocation_id, reverse=True)

        cr.execute("""select count(so.id)
                                    ,array_agg(so.id) as so_ids
                                    from sale_order so
                                    where so.main_process_id = %s
                                    and so.sale_aftersales = 'after_sales'
                                    and so.company_id = %s
                                    """, (request.env.ref("ac_rms.main_process11").id, company.id,))

        hold_approval = cr.dictfetchall()
        hold_approval_count = hold_approval[0].get('count')
        rhold_approval_ids = hold_approval[0].get('so_ids')

        cr.execute("""select count(so.id)
                                ,array_agg(so.id) as so_ids
                                    from sale_order so
                                     where main_process_id = %s
                                      and company_id = %s
                                        """, (request.env.ref("ac_rms.main_process15").id, company.id,))

        fi_waiting = cr.dictfetchall()
        fi_waiting_count = fi_waiting[0].get('count')
        fi_waiting_ids = fi_waiting[0].get('so_ids')

        cr.execute("""select count(so.id)
                                        ,array_agg(so.id) as so_ids
                                            from sale_order so
                                             where main_process_id = %s
                                              and company_id = %s
                                                """, (request.env.ref("ac_rms.main_process17").id, company.id,))

        ready_for_delivery = cr.dictfetchall()
        ready_for_delivery_count = ready_for_delivery[0].get('count')
        ready_for_delivery_ids = ready_for_delivery[0].get('so_ids')

        cr.execute("""select count(distinct(b.initial_count)) as initial_count,
                               array_remove(array_agg(distinct(b.initial_ids)),NULL) as initial_ids,
                               count(distinct(b.partial_count)) as partial_count,
                               array_remove(array_agg(distinct(b.partial_ids)),NULL) as partial_ids,
                               count(distinct(b.additional_job_count)) as additional_job_count,
                               array_remove(array_agg(distinct(b.additional_job_ids)),NULL) as additional_job_ids,
                               count(distinct(b.hold_approve_count)) as hold_approve_count,
                               array_remove(array_agg(distinct(b.hold_approve_ids)),NULL) as hold_approve_ids,
                               count(distinct(b.carry_over_count)) as carry_over_count,
                               array_remove(array_agg(distinct(b.carry_over_ids)),NULL) as carry_over_ids,
                               count(distinct(b.reschedule_count)) as reschedule_count,
                               array_remove(array_agg(distinct(b.reschedule_ids)),NULL) as reschedule_ids,
                               count(distinct(b.fi_reject_count)) as fi_reject_count,
                               array_remove(array_agg(distinct(b.fi_reject_ids)),NULL) as fi_reject_ids
                               from
                               (select 
                                case when so.is_partial = false and so.is_additional_job = false and so.is_hold_approve = false and so.is_carry_over = false and so.is_reschedule = false and so.is_fi_rejection = false then so.id end AS initial_count,
                            case when so.is_partial = false and so.is_additional_job = false and so.is_hold_approve = false and so.is_carry_over = false and so.is_reschedule = false and so.is_fi_rejection = false then so.id end AS initial_ids,
                            case when so.is_partial = true then so.id end AS partial_count,
                            case when so.is_partial = true then so.id end AS partial_ids,
                            case when so.is_additional_job = true then so.id end AS additional_job_count,
                            case when so.is_additional_job = true then so.id end AS additional_job_ids,
                            case when so.is_hold_approve = true then so.id end AS hold_approve_count,
                            case when so.is_hold_approve = true then so.id end AS hold_approve_ids,
                            case when so.is_carry_over = true then so.id end AS carry_over_count,
                            case when so.is_carry_over = true then so.id end AS carry_over_ids,
                            case when so.is_reschedule = true then so.id end AS reschedule_count,
                            case when so.is_reschedule = true then so.id end AS reschedule_ids,
                            case when so.is_fi_rejection = true then so.id end AS fi_reject_count,
                            case when so.is_fi_rejection = true then so.id end AS fi_reject_ids
                            from sale_order so
                            inner join sale_order_line sl on sl.order_id = so.id
                            inner join project_task pt on pt.sale_line_id = sl.id
                            inner join project_task_type pty on pty.id = pt.stage_id
                            where so.bay_tech_allocation = false
                            and so.sale_aftersales = 'after_sales'
                            and pty.sequence in (0,7,5,4))b""")
        all_count_ids_data = cr.dictfetchall()

        # bay_allocation_id = all_data[0].get('sale_id')

        task_type = request.env['project.task.type'].search([('sequence', '=', 3)]).id
        project_task = request.env['project.task'].search([('stage_id', '=', task_type)])
        job_stoppage_sale_id = project_task.mapped("order_id").ids

        vals = {'res_planner': res_calender,
                'view': select_view,
                'pull_reses': {},
                'bay_allocation': bay_allocation_count,
                'hold_approval_count': hold_approval_count,
                'fi_waiting_count': fi_waiting_count,
                'ready_for_delivery_count': ready_for_delivery_count,
                'initial_count': all_count_ids_data[0].get('initial_count'),
                'initial_ids': all_count_ids_data[0].get('initial_ids'),
                'partial_count': all_count_ids_data[0].get('partial_count'),
                'partial_ids': all_count_ids_data[0].get('partial_ids'),
                'additional_job_count': all_count_ids_data[0].get('additional_job_count'),
                'additional_job_ids': all_count_ids_data[0].get('additional_job_ids'),
                'hold_approve_count': all_count_ids_data[0].get('hold_approve_count'),
                'hold_approve_ids': all_count_ids_data[0].get('hold_approve_ids'),
                'carry_over_count': all_count_ids_data[0].get('carry_over_count'),
                'carry_over_ids': all_count_ids_data[0].get('carry_over_ids'),
                'reschedule_count': all_count_ids_data[0].get('reschedule_count'),
                'reschedule_ids': all_count_ids_data[0].get('reschedule_ids'),
                'fi_reject_count': all_count_ids_data[0].get('fi_reject_count'),
                'fi_reject_ids': all_count_ids_data[0].get('fi_reject_ids'),
                'job_stoppage_count': len(project_task),
                'job_stoppage_ids': project_task.ids}
        if res_pull.vehicle:
            event_check = True
        if res_pull.resource:
            event_resource = True
        if res_pull.shift_end:
            shift_end = True
        if not event_check and not event_resource:
            col_sm = 'col-sm-11'
        if event_check and event_resource:
            col_sm = 'col-sm-9'
        if event_check and not event_resource:
            col_sm = 'col-sm-10'
        if not event_check and event_resource:
            col_sm = 'col-sm-10'
        vals.update(
            {'shift_end': shift_end, 'res_planner': res_calender, 'view': select_view, 'pull_reses': pull_resource,
             'col_sm': col_sm, 'resource_pl': event_resource, 'event': event_check, 'ros': allo_veh})
        return request.render("ac_rms.resource_planner", vals)

    @http.route(['/resource_planner/external_event'], type='json', auth="user", website=True, csrf=False)
    def external_resource_event(self, start, resourceId, ro_details, event_type=False, **kwargs):
        bay_num_ip = []
        cr = request._cr
        event_obj = request.env['ir.model'].search([('model', '=', 'calender.event')])
        res_str = str(resourceId)
        spilt_str = res_str.split('-')
        bay_number = int(spilt_str[0])
        bay_obj = request.env['resource.resource'].browse(bay_number)
        for ip in bay_obj.ip_address:
            bay_num_ip.append(ip.id)
        bay_num_ip_id = tuple(bay_num_ip)
        cr.execute("select name from cc_camera where id in " + str(bay_num_ip_id))
        bay_num_ip = [x[0] for x in cr.fetchall()]
        str_start = str(start)
        model_id = request.env['ir.model'].search([('model', '=', 'sale.order')]).id
        for ro_detail in ro_details:
            if 'res_id' not in ro_detail:
                resour_id = int(spilt_str[0])
            else:
                resour_id = int(ro_detail.get('res_id'))

            ro_id = int(ro_detail.get('ro_id'))
            #             title = ro_detail.get('title').strip()
            so = request.env['sale.order'].browse(int(ro_id))
            so.is_online = False
            title = so.regn_no.license_plate
            resource = request.env['resource.resource'].browse(resour_id)
            rlpc_start = str_start.replace("T", " ")
            current_start = datetime.strptime(rlpc_start, '%Y-%m-%d %H:%M:%S')
            current_end = current_start + timedelta(minutes=30)
            cr.execute("""INSERT INTO calendar_event(
                    name, state, display_start, start, stop, allday, start_date, 
                    start_datetime, stop_date, stop_datetime, duration, 
                    privacy, show_as, res_id, res_model_id, res_model, recurrency, recurrent_id, 
                    end_type, "interval", count, mo, tu, we, th, fr, sa, su, month_by, 
                    day, user_id, active,entry_type, token, url)
                    VALUES ( %s, %s, %s,%s, %s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, 
                                    %s, %s, %s, %s, %s, 
                                    %s,%s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,
                                    %s) RETURNING id;
                    """, (
                title, 'draft', rlpc_start, rlpc_start, str(current_end), False, rlpc_start, rlpc_start,
                str(current_end),
                str(current_end), 0.5, 'public', 'busy', int(ro_id), model_id, 'sale_order', False, 0, 'count', 1, 1,
                False, False, False,
                False, False, False, False, 'date', 1, 1, True, 'plan', '', ''))
            cal_id = cr.dictfetchall()
            eve_id = cal_id[0].get('id')
            events = request.env['calendar.event'].browse(eve_id)
            if event_type:
                events.event_type = event_type
            if events:
                events.partner_ids = [(6, 0, [resource.resource_partner.id])]
                events.create_attendees()

            # res = events.push_ccip(bay_num_ip, bay_num_ip_id)
            # customer_email = so.email
            # customer_name = so.partner_id.name
            # url = events.url
            # url_decode = "http://192.168.6.205:8080/camera/index.php/track/5c373440d8d6b"
            # print ("....", customer_email)
            # mail_content = "Dear " + customer_name + "," + "<br>Your vehicle is in Bay. " \
            #             "Please click on this URL: " + url_decode
            # mail_values = {
            #     'email_to': customer_email,
            #     'subject': so.regn_no.license_plate,
            #     'body_html': mail_content,
            # }
            # # create_and_send_email = request.env['mail.message'].sudo().create(mail_values).send()
            # create_and_send_email = request.env['mail.mail'].create(mail_values)
            # print ("............", create_and_send_email)
            # mail = create_and_send_email.send()
            # print("....",mail)
            so.write({'main_process_id': request.env.ref("ac_rms.main_process9").id, 'bay_tech_allocation': True})
            # event_list.append(eve_id)
        # join_list = '-'.join(event_list)
        # for event in event_list:
        #     event_obj = self.env["calendar.event"].browse(event)
        #     event_obj.event_ids = join_list
        vals = {'status': True, 'ro_details': ro_details}
        return vals
    #override for show chip every user
    @http.route(['/resource_planner/get'], type='json', auth="user", website=True, csrf=False)
    def get_resource_planner(self, view, showall, button_text, **kwargs):
        user = request.env['res.users'].browse(request.env.uid)
        if user.partner_id.tz:
            tz = pytz.timezone(user.partner_id.tz)
        else:
            tz = pytz.utc
        res_calender = request.env['planner.calender'].browse(int(view))
        resources = res_calender.member_ids
        # if request.env.user.has_group('ac_rms.group_technician') and showall == 'False':
        #     resource_user = request.env["resource.resource"].search([('user_id', '=', request.env.user.id)])
        #     resources = resource_user
        if button_text == 'Show All':
            resources = resources
        resources_list = []
        events_list = []
        for resource in resources:
            partner = False
            partner = resource.resource_partner.ids
            if not partner:
                partner = resource.user_id.partner_id.ids
            plan_resource = str(resource.id) + '-' + str(partner[0])
            resources_list.append({'id': plan_resource, 'title': 'Plan', 'resource': resource.name})
            actual_resource = str(partner[0]) + '-' + str(resource.id)
            resources_list.append({'id': actual_resource, 'title': 'Actual', 'resource': resource.name})
            events = request.env['calendar.event'].search([('partner_ids', 'in', resource.resource_partner.ids)])
            for event in events:
                stop = ''
                start = datetime.strptime(event.start, "%Y-%m-%d %H:%M:%S").strftime(DEFAULT_DATE_TIME_FORMATE)
                # s = fields.Datetime.from_string(event.start) + timedelta(hours=5, minutes=30)
                # start = (s.replace(tzinfo=pytz.utc).astimezone(tz)).strftime(DEFAULT_DATE_TIME_FORMATE)
                # start = (fields.Datetime.from_string(event.start).replace(tzinfo=pytz.utc).astimezone(tz)).strftime(
                #     DEFAULT_DATE_TIME_FORMATE)
                if event.stop_datetime:
                    stop_date = (
                        fields.Datetime.from_string(event.stop_datetime).replace(tzinfo=pytz.utc).astimezone(
                            tz)).strftime(
                        DEFAULT_DATE_TIME_FORMATE)
                    add_time = self.actual_chip_default_width_after_event_render(stop_date, event.start)
                    if add_time and event.entry_type == 'actual':
                        stop = (fields.Datetime.from_string(stop_date) + timedelta(minutes=5)).strftime(
                            DEFAULT_DATE_TIME_FORMATE)
                    else:
                        stop = fields.Datetime.from_string(stop_date).strftime(DEFAULT_DATE_TIME_FORMATE)


                else:
                    # start1 = datetime.strptime(event.start, "%Y-%m-%d %H:%M:%S")
                    c = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(hours=5, minutes=30)
                    add_time = self.actual_chip_default_width_after_event_render(event.start,
                                                                                 c.strftime(DEFAULT_DATE_TIME_FORMATE))
                    if add_time and event.entry_type == 'actual':
                        c = c + timedelta(minutes=5)
                        stop = (c.replace(tzinfo=pytz.utc).astimezone(tz)).strftime(DEFAULT_DATE_TIME_FORMATE)
                    else:
                        stop = (c.replace(tzinfo=pytz.utc).astimezone(tz)).strftime(DEFAULT_DATE_TIME_FORMATE)

                if event.entry_type == 'plan':
                    events_list.append(
                        {'id': event.id, 'resourceId': plan_resource, 'start': start, 'end': stop, 'title': event.name,
                         'color': '#3498db;', 'event_type': 'plan'})

                if event.entry_type == 'actual':
                    events_list.append(
                        {'id': event.id, 'resourceId': actual_resource, 'start': start, 'end': stop,
                         'title': event.name,
                         'color': '#008000;', 'event_type': 'actual'})

        vals = {'status': True, 'resource': resources_list, 'events': events_list}
        return vals

    @http.route(['/resource_planner/chip_clk'], type='json', auth="user", website=True, csrf=False)
    def modal(self, event_id, **kwargs):

        if request.env.user.has_group('ac_rms.group_technician'):
            tech_categ = request.env.ref('ac_rms.resource_categories_tech')
            # techs = request.env['resource.resource'].search([('resource_category', '=', tech_categ)])
            if event_id:
                bay_num_ip = []
                event_obj = request.env['calendar.event'].browse(event_id).res_id
                id_task = request.env.ref('rms_frontend.default_task').id
                project_task_obj = request.env['project.task'].browse(id_task)
                sale_order_obj = request.env['sale.order'].browse(event_obj)
                # task_name = project_task_obj.name
                # sheet_ids = project_task_obj.timesheet_ids.filtered(lambda x: x.resource_type == tech_categ and  x.entry_type == 'plan')

            res = request.env.ref('ac_rms.modal').render(
                {'tasks': project_task_obj, 'tech_categ': tech_categ, 'regn_no': sale_order_obj.regn_no.license_plate,
                 'so_name': sale_order_obj.name, 'order_id': sale_order_obj.id,'event': event_id})
            return {'status': True, 'clk': 'single', 'result': res}
        if request.env.user.has_group('ac_rms.group_job_controller'):
            if event_id:
                event_obj = request.env["calendar.event"].browse(event_id)
                task_obj = request.env["project.task"].search([('order_id', '=', event_obj.res_id)])
                order_obj = request.env["sale.order"].search([('id', '=', event_obj.res_id)])
                reg_no = order_obj.regn_no.license_plate
                repair_order = order_obj.name
                delivery_datetime = order_obj.delivery_date
                service_advisor = order_obj.user_id.name
                for task in task_obj:
                    task_name = task.name
                    # resource_name = task.resource_name
                    # start_datetime = task.start_datetime
                    # end_datetime = task.end_datetime
            return {'status': True, 'clk': 'dbl', 'order_id': order_obj.id, 'reg_no': reg_no,
                    'repair_order': repair_order,
                    'delivery_datetime': delivery_datetime, 'service_advisor': service_advisor}

    @http.route(['/tech_start'], type='json', auth="user", website=True, csrf=False)
    def technician_start(self, tasks, order_id, **kwargs):
        order_id = order_id.strip()
        order_id = int(order_id)
        print("///",order_id)
        self.technician_actaul_process(tasks, order_id)
        return {}

    def technician_actaul_process(self, tasks, order_id):
        if tasks:
            order = request.env['sale.order'].browse(order_id)
            for task_data in tasks:
                if task_data:
                    data = request.env['project.task'].browse(int(task_data))
                    self.calendar_event_insert(tasks, order, data.timesheet_ids,data.name)

                    self.timesheet_create(data,data.timesheet_ids)

        return {}

    def calendar_event_insert(self,tasks,order_id,timesheet_ids,name):
        # order_id = order_id.id
        user = request.env['res.users'].browse(request.env.uid)
        if user.partner_id.tz:
            tz = pytz.timezone(user.partner_id.tz)
        else:
            tz = pytz.utc
        cr = request.env.cr
        bay_num_ip = []
        # print("..........",resourceId)
        # for sheet in timesheet_ids:
        # resource = request.env['resource.resource'].search([('name', '=', sheet.resource_name.name)])
        # resource_category = request.env['resource.category'].search([('id', '=', resource.resource_category.id)])
        # if sheet.resource_name.resource_category.id == request.env.ref("ac_rms.resource_categories_bay").id:
        #     resource_user = 1
        # if sheet.resource_name.resource_category.id == request.env.ref("ac_rms.resource_categories_tech").id:
        #     resource_user = resource.user_id.id
        # employee = request.env['hr.employee'].search([('user_id', '=', resource.user_id.id)])
        # resource = request.env['resource.resource'].search([('name', '=', resource_name.name)])
        # resource_user = resource.user_id.id
        model_id = request.env['ir.model'].search([('model', '=', 'sale.order')]).id
        bay_number = request.env.ref('rms_frontend.default_bay1').id
        bay_obj = request.env['resource.resource'].browse(bay_number)
        print (".....", bay_obj)
        for ip in bay_obj.ip_address:
            bay_num_ip.append(ip.id)
        bay_num_ip_id = tuple(bay_num_ip)
        cr.execute("select name from cc_camera where id in " + str(bay_num_ip_id))
        bay_num_ip = [x[0] for x in cr.fetchall()]
        # rlpc_start = datetime.now()
        # current_start1 = datetime.strftime(rlpc_start, '%Y-%m-%d %I:%M:%S')
        c = fields.Datetime.from_string(fields.Datetime.now())
        start_time = (c.replace(tzinfo=pytz.utc).astimezone(tz)).strftime(DEFAULT_DATE_TIME_FORMATE)
        current_start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)
        current_end = current_start + timedelta(minutes=5)
        request.env.cr.execute("""INSERT INTO calendar_event(
                        name, state, display_start, start, stop, allday, start_date,
                        start_datetime, duration,
                        privacy, show_as, res_id, res_model_id, res_model, recurrency, recurrent_id,
                        end_type, "interval", count, mo, tu, we, th, fr, sa, su, month_by,
                        day, user_id, active,entry_type)
                        VALUES ( %s, %s,%s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,
                                        %s, %s, %s, %s, %s,
                                        %s,%s, %s, %s, %s, %s, %s, %s, %s,%s,%s,
                                        %s) RETURNING id;
                        """, (
            order_id.regn_no.license_plate, 'draft', current_start, current_start, current_end, False, current_start, current_start,
             0.5, 'public', 'busy', order_id.id, model_id, 'sale_order', False, 0, 'count', 1, 1, False,
            False, False,
            False, False, False, False, 'date', 1,  1, True, 'actual',))
        cal_id = request.env.cr.dictfetchall()
        eve_id = cal_id[0].get('id')
        events = request.env['calendar.event'].browse(eve_id)
        events_id = request.env['calendar.event'].search([('res_id', '=', order_id.id)])[-1]
        for event in events_id:
            # if event.url:
            # res = events.push_ccip(bay_num_ip, bay_num_ip_id)
            so = order_id
            customer_email = so.email
            customer_name = so.partner_id.name
            url_decode = event.url
            print("...",url_decode)
            # url_decode = "www.google.com"
            print ("....", customer_email)
            mail_content = "Dear " + customer_name + "," + "<br>Your vehicle is in Bay. " \
                                                           "Please click on this URL: " + url_decode
            mail_values = {
                'email_to': customer_email,
                'subject': so.regn_no.license_plate,
                'body_html': mail_content,
            }
            # create_and_send_email = request.env['mai  l.message'].sudo().create(mail_values).send()
            create_and_send_email = request.env['mail.mail'].create(mail_values)
            print ("............", create_and_send_email)
            mail = create_and_send_email.send()
            print("....", mail)
            if not events_id.url:
                print("........",events_id.url)
            if events:
                # events.partner_ids = [(6, 0, [resource.resource_partner.id])]
                events.create_attendees()
        return {}

    def timesheet_create_resource_wise(self,resource,task,category):
        uid = request.env.user.id
        employee = request.env['hr.employee'].search([('user_id', '=', uid)],limit=1)
        timesheet_data_entry = {
            'account_id': 1,
            'date': datetime.now(),
            'status': request.env.ref("ac_rms.status1").id,
            'entry_type': 'actual',
            'resource_type': resource.resource_name.resource_category.id if category == 'Tech' else resource.mapped_bay_resource.resource_category.id,
            'resource_name': resource.resource_name.id if category == 'Tech' else resource.mapped_bay_resource.id,
            'start_datetime': datetime.now(),
            'end_datetime': '',
            'break_reason': '',
            'employee_id': employee.id,
            'name': task.name
        }
        task.sudo().timesheet_ids = [(0, 0, timesheet_data_entry)]
        return {}

    def timesheet_create(self,task,timesheet_ids):
        resource = request.env["resource.resource"].search([('user_id','=',request.env.uid)])
        tech_entrys = timesheet_ids.filtered(lambda x: x.entry_type == 'plan' and x.resource_name == resource and x.is_release == False)
        if tech_entrys:
            tech_entry = tech_entrys[-1]
            self.timesheet_create_resource_wise(tech_entry,task,'Tech')
            bay_entry = timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and x.resource_name == tech_entry.mapped_bay_resource and not x.end_datetime)
            if not bay_entry:
                self.timesheet_create_resource_wise(tech_entry, task,'Bay')
        task.stage_id = request.env['project.task.type'].search([('sequence','=',1)]).id
        task.order_id.write({'main_process_id': request.env.ref("ac_rms.main_process10").id})
        return {}

    @http.route(['/tech_finish'], type='json', auth="user", website=True, csrf=False)
    def technician_finish(self, tasks, event, **kwargs):
        # event_obj = request.env['calendar.event'].browse(int(event))
        # current_time = fields.Datetime.from_string(fields.Datetime.now())
        # print('tttttttt')
        # print(current_time)
        # if event_obj:
        #     event_obj.write({'stop': current_time,
        #                                      'stop_date':datetime.now().date(),
        #                                      'stop_datetime':current_time})
        # return {'tasks':tasks,'event':event}
        tech_categ = request.env.ref('ac_rms.resource_categories_tech')
        bay_categ = request.env.ref('ac_rms.resource_categories_bay')
        for task in request.env['project.task'].browse(tasks):
            time_sheet_record = task.timesheet_ids.filtered(lambda x: x.resource_type in (
            tech_categ, bay_categ) and x.entry_type == 'actual' and not x.end_datetime)
            time_sheet_record.write({'end_datetime': datetime.now()})
            order_id = task.order_id
            resource_ids = time_sheet_record.mapped('resource_name').mapped('resource_partner').ids
            event_obj = request.env['calendar.event'].search(
                [('res_id', '=', order_id.id), ('partner_ids', 'in', resource_ids), ('entry_type', '=', 'actual')])
            event_token = event_obj.token
            # date = datetime.now().date()
            current_time = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(hours=5, minutes=30)
            # res = event_obj.close_ccip(event_token)
            if event_obj:
                event_obj.write({'stop': current_time,
                                 'stop_date': datetime.now().date(),
                                 'stop_datetime': current_time})
            return {'tasks': tasks, 'event': event}
            #             task.stage_id = request.env['project.task.type'].search([('sequence', '=', 6)]).id
            #             task.order_id.write({'main_process_id':request.env.ref("ac_rms.main_process15").id}
            #         return {}