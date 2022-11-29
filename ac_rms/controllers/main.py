# -*- coding: utf-8 -*-
import werkzeug.utils
from odoo import http
from odoo.http import request
import pytz
from odoo import models, fields, api, _
import datetime
import json
import werkzeug.utils
from datetime import datetime, timedelta

DEFAULT_DATE_TIME_FORMATE = '%Y-%m-%d %H:%M:%S'
DEFAULT_DATE_TIME_FORMATE1 = '%Y-%m-%d %I:%M:%S'


class Home(http.Controller):
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
        allo_veh = SaleOrder.search([('main_process_id', 'in', vehicle_processes.ids)])

        for res_c in res_calender:
            if res_c.id == int(view):
                select_view.append('selected')
            else:
                select_view.append('')

        waiting_for_inward = request.env.ref("ac_rms.main_process1").id
        sec_process = request.env.ref("ac_rms.main_process2").id
        watng_at_recpn = request.env.ref("ac_rms.main_process3").id
        waiting_inward = SaleOrder.search([('main_process_id', '=',waiting_for_inward)])
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
                                """,(request.env.ref("ac_rms.main_process15").id,company.id,))

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

        vals = { 'res_planner': res_calender,
                 'view':select_view,
                 'pull_reses':{},
                 'bay_allocation':bay_allocation_count,
                 'hold_approval_count':hold_approval_count,
                 'fi_waiting_count':fi_waiting_count,
                 'ready_for_delivery_count':ready_for_delivery_count,
                 'initial_count':all_count_ids_data[0].get('initial_count'),
                 'initial_ids':all_count_ids_data[0].get('initial_ids'),
                 'partial_count':all_count_ids_data[0].get('partial_count'),
                 'partial_ids':all_count_ids_data[0].get('partial_ids'),
                 'additional_job_count':all_count_ids_data[0].get('additional_job_count'),
                 'additional_job_ids':all_count_ids_data[0].get('additional_job_ids'),
                 'hold_approve_count': all_count_ids_data[0].get('hold_approve_count'),
                 'hold_approve_ids': all_count_ids_data[0].get('hold_approve_ids'),
                 'carry_over_count': all_count_ids_data[0].get('carry_over_count'),
                 'carry_over_ids': all_count_ids_data[0].get('carry_over_ids'),
                 'reschedule_count': all_count_ids_data[0].get('reschedule_count'),
                 'reschedule_ids': all_count_ids_data[0].get('reschedule_ids'),
                 'fi_reject_count': all_count_ids_data[0].get('fi_reject_count'),
                 'fi_reject_ids': all_count_ids_data[0].get('fi_reject_ids'),
                 'job_stoppage_count':len(project_task),
                 'job_stoppage_ids':project_task.ids}
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
        vals.update({ 'shift_end':shift_end,'res_planner': res_calender,'view':select_view,'pull_reses':pull_resource,'col_sm':col_sm,'resource_pl':event_resource,'event':event_check,'ros':allo_veh})
        return request.render("ac_rms.resource_planner", vals)

    @http.route(['/fi_process_details/get'], type='json', auth='user', website=True, csrf=False)
    def fi_process_details_on_planner(self, **kwargs):
        cr = request.env.cr
        cr.execute("""select 
                        count(distinct(a.fi_process_waiting)) as fi_waiting_counts,
                        array_remove(array_agg(distinct(a.fi_process_waiting)),NULL) as fi_waiting_ids,
                        count(distinct(a.fi_in_progress)) as fi_in_progress_counts,
                        array_remove(array_agg(distinct(a.fi_in_progress)),NULL) as fi_in_progress_ids,
                        count(distinct(a.fi_rejected)) as fi_rejected_counts,
                        array_remove(array_agg(distinct(a.fi_rejected)),NULL) as fi_rejected_ids,
                        count(distinct(a.fi_completed)) as fi_completed_counts,
                        array_remove(array_agg(distinct(a.fi_completed)),NULL) as fi_completed_ids
                        from
                        (select 
                        case when so.main_process_id = %s then so.id end AS fi_process_waiting,
                        case when so.main_process_id = %s then so.id end AS fi_in_progress,
                        case when so.is_fi_rejection = True then so.id end AS fi_rejected,
                        case when so.main_process_id = %s then so.id end AS fi_completed
                        from sale_order so
                        inner join sale_order_line sl on sl.order_id = so.id
                        inner join project_task pt on pt.sale_line_id = sl.id)a
                        """,(request.env.ref("ac_rms.main_process15").id,request.env.ref("ac_rms.main_process16").id,request.env.ref("ac_rms.main_process17").id))
        all_fi_details = cr.dictfetchall()
        vals = {'fi_waiting_counts':all_fi_details[0].get('fi_waiting_counts'),
                'fi_waiting_ids':all_fi_details[0].get('fi_waiting_ids'),
                'fi_in_progress_counts':all_fi_details[0].get('fi_in_progress_counts'),
                'fi_in_progress_ids':all_fi_details[0].get('fi_in_progress_ids'),
                'fi_rejected_counts':all_fi_details[0].get('fi_rejected_counts'),
                'fi_rejected_ids':all_fi_details[0].get('fi_rejected_ids'),
                'fi_completed_counts':all_fi_details[0].get('fi_completed_counts'),
                'fi_completed_ids':all_fi_details[0].get('fi_completed_ids')}

        return vals


    @http.route(['/jobstopage_bucket_clk'], type='json', auth='user', website=True, csrf=False)
    def jobstoppage_bucket_clk(self, project_task=False, **kwargs):
        tech_categ = request.env.ref('ac_rms.resource_categories_tech')
        project_obj = request.env['project.task'].browse(eval(project_task))
        res = request.env.ref('ac_rms.job_stoppage').render({'project_task': project_obj,'tech_categ':tech_categ})
        return {'status': True, 'result': res}


    @http.route(['/bay-tech-popup/get'], type='json', auth='user', website=True, csrf=False)
    def bay_tech_popup(self, orders=False,color_header=False, **kwargs):
        waiting_for_vehicle_inward = request.env.ref('ac_rms.main_process1').id
        security_process = request.env.ref('ac_rms.main_process2').id
        if orders and color_header:
            orders = orders
            color_header = color_header
        else:
            if kwargs.get('result'):
                orderss = request.env['sale.order'].search([('name', 'ilike', kwargs.get('result'))])
                if orderss:
                    orders = str(orderss.ids)
                    if orderss[-1].main_process_id.id == waiting_for_vehicle_inward:
                        color_header = '#065364'
                    elif orderss[-1].main_process_id.id == security_process:
                        color_header = '#026242'
        color = color_header and color_header or ''
        allocation_html = ''
        allocation_html += '<table class="table table-fixed cls-table-search" id="techallocation_table" data-firstsort="asc">'
        allocation_html += '<thead>'
        allocation_html += '<tr style="background-color:'+color+'">'
        allocation_html += '<th width="4%" style="text-align:left;"></th>'
        allocation_html += '<th width="17%" style="text-align:center;color:white;">Vehicle Reg #</th>'
        allocation_html += '<th width="17%" style="text-align:center;color:white;">Total Time Unit</th>'
        allocation_html += '<th width="17%" style="text-align: center;color:white;">Repair Order(RO)</th>'
        allocation_html += '<th width="17%" style="text-align: center;color:white;">Delivery Date &amp; Time</th>'
        allocation_html += '<th width="17%" style="text-align: center;color:white;">Job Controller</th>'
        allocation_html += '<th width="17%" style="text-align: center;color:white;">Service Advisor</th>'
        allocation_html += '</tr>'
        allocation_html += '</thead>'
        allocation_html += '<tbody>'
        for order in request.env['sale.order'].browse(eval(orders)):
            if order.tasks_ids:
                order_name = order.name and order.name or ''
                reg_no = order.regn_no.license_plate and order.regn_no.license_plate or ''
                delivery_date = order.delivery_date and order.delivery_date or ''
                if delivery_date:
                    delivery_date = (datetime.strptime(delivery_date, "%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)).strftime("%m/%d/%Y %I:%M %p")
                service_advisor = order.user_id.name and order.user_id.name or ''
                allocation_html += '<tr class="modal_rows">'
                allocation_html += '<td width="4%" style="text-align:left;">'
                allocation_html += '<input type="checkbox" class="select_check" name="select"/></td>'
                allocation_html += '<td width="17%" style="text-align:center;"><a href="#" class="regn_clk">'+reg_no+'</a><input class="order hidden" name="order-ids" type="text" value="'+str(order.id)+'" /></td>'
                allocation_html += '<td width="17%" style="text-align:center;">'+'0'+'</td>'
                allocation_html += '<td width="17%" style="text-align:center;">'+order_name+'</td>'
                allocation_html += '<td width="17%" style="text-align:center;" class="sort_td">'+delivery_date+'</td>'
                allocation_html += '<td width="17%" style="text-align: center;">'+service_advisor+'</td>'
                allocation_html += '<td width="17%" style="text-align:center;">'+service_advisor+'</td>'
                allocation_html += '</tr>'
                allocation_html += '<tr class="modal_rows" id="task_'+str(order.id)+'"></tr>'
        allocation_html += '</tbody>'
        allocation_html += '</table>'


        return {'html_data':allocation_html}

    @http.route(['/resource_planner/double_click'], type='json', auth="user", website=True, csrf=False)
    def chip_double_click(self, event_id, **kwargs):
        if event_id:
            event_obj = request.env["calendar.event"].browse(event_id)
            task_obj = request.env["project.task"].search([('order_id','=',event_obj.res_id)])
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
        return {'status': True,'order_id':order_obj.id,'reg_no':reg_no,'repair_order':repair_order,'delivery_datetime':delivery_datetime,'service_advisor':service_advisor}

    @http.route(['/dbl_clk_popup'], type='json', auth="user", website=True, csrf=False)
    def chip_doubleclk(self,order_id, **kwargs):
        vehicle_html = ''
        if order_id:
            bay_category = request.env.ref('ac_rms.resource_categories_bay')
            bays = request.env['resource.resource'].search([('resource_category', '=', bay_category.id)])
            # bay_opt = ''
            # for bay in bays:
            #     bay_opt += '<option value="' + bay.name + '">' + bay.name + '</option>'
            tech_category = request.env.ref('ac_rms.resource_categories_tech')
            # techs = request.env['resource.resource'].search([('resource_category', '=', tech_category.id)])
            # tech_opt = ''
            # for tech in techs:
            #     tech_opt += '<option value="' + str(tech.id) + '">' + tech.name + '</option>'
            order_obj = request.env["sale.order"].browse(eval(order_id))
            tasks = order_obj.tasks_ids
            vehicle_html = ''
            vehicle_html += '<td colspan="6">'
            vehicle_html += '<div style="margin-left: 103%;"><button type="button"  id="taskconfirm" class="btn btn-primary tawindow">Confirm</button></div>'
            vehicle_html += '<div><a href = "#" class ="test_cls">Select All</a><a href="#" class ="selectallclass1" style="margin-left:8%;">Assign</a></div>'
            vehicle_html += '<table id="dbl_alloc_table"  data-firstsort="asc">'
            vehicle_html += '<thead>'
            vehicle_html += '<tr>'
            vehicle_html += '<th width="5%" style="text-align:left;"></th>'
            vehicle_html += '<th width="10%" style="text-align:center;">Labour</th>'
            vehicle_html += '<th width="12%" style="text-align:center;">Bay</th>'
            vehicle_html += '<th width="12%" style="text-align:center;">Technician</th>'
            vehicle_html += '<th width="18%" style="text-align: center;">Start Time</th>'
            vehicle_html += '<th width="16%" style="text-align: center;">End Time</th>'
            vehicle_html += '<th></th>'
            vehicle_html += '<th></th>'
            vehicle_html += '</tr>'
            vehicle_html += '</thead>'
            vehicle_html += '<tbody>'
            vehicle_html1 = ''
            start_datetime = ''
            end_datetime = ''
            bay_name = ''
            resource_name = ''
            for task in tasks:
                plan_sheet_ids = task.timesheet_ids.filtered(lambda x: x.resource_type == tech_category and x.entry_type == 'plan')

                bay_opt = ''
                for bay in bays:
                    if bay.name == plan_sheet_ids.mapped_bay_resource.name:
                        bay_opt += '<option value="' + str(bay.id) + '" selected>' + bay.name + '</option>'
                    else:
                        bay_opt += '<option value="' + str(bay.id) + '">' + bay.name + '</option>'
                # tech_category = request.env.ref('ac_rms.resource_categories_tech')
                techs = request.env['resource.resource'].search([('resource_category', '=', tech_category.id)])
                tech_opt = ''
                for tech in techs:
                    if tech.name == plan_sheet_ids.resource_name.name:
                        tech_opt += '<option value="' + str(tech.id) + '" selected>' + tech.name + '</option>'
                    else:
                        tech_opt += '<option value="' + str(tech.id) + '">' + tech.name + '</option>'
                resource_name = plan_sheet_ids.resource_name
                bay_name = plan_sheet_ids.mapped_bay_resource
                start_datetime = datetime.strptime(plan_sheet_ids.start_datetime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)
                end_datetime = datetime.strptime(plan_sheet_ids.end_datetime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)
                # start_datetime = plan_sheet_ids.start_datetime
                # end_datetime = plan_sheet_ids.end_datetime
                vehicle_html1 += '<tr class="tech_labour_date_tr modal_rows">'
                vehicle_html1 += '<td width="5%" style="text-align:left;">'
                vehicle_html1 += '<span class="clone-no-add"><input name="inner-chckbox" type="checkbox"/><span style="display:none;" class="dbl_order">'+str(order_obj.id)+'</span></span></td>'
                vehicle_html1 += '<td width="10%" style="text-align:center;"><span class="clone-no-add"><input type="text" class="hidden" id="task_ids" name="task_ids" value="' + str(
                    task.id) + '"/>' + task.name + '</span></td>'
                vehicle_html1 += '<td width="12%" style="text-align:right;"><select style="width:94%;" class="form-control" name="bay" id="bay_select"><option/>' + str(bay_opt) + '</select></td>'
                vehicle_html1 += '<td width="12%" style="text-align:right;"><select style="width:94%;" class="form-control" name="tech" id="tech_select"><option/>' + str(tech_opt) + '</select></td>'
                vehicle_html1 += '<td><div class="form-group" style="margin: 6% 7% 6% 7%;width:85%;"><div class="input-group date" id="datetimepicker1"><input type="text" class="form-control st_date" value="'+str(start_datetime)+'"/><span class="input-group-addon"><span class="fa fa-calendar start_datetime"></span></span></div></td>'
                vehicle_html1 += '<td><div class="form-group" style="margin: 6% 7% 6% 0%;width:93%;"><div class="input-group date" id="datetimepicker2"><input type="text" class="form-control en_date" value="'+str(end_datetime)+'"/><span class="input-group-addon"><span class="fa fa-calendar end_datetime"></span></span></div></td>'
                vehicle_html1 += '<td width = "5%" class ="tr_clone_add"><button class ="btn btn-primary btn-color-plus" id = "addnew" name = "addnew" type = "button" ><i class ="fa fa-plus"/></ button></td>'
            vehicle_html1 += '</tr>'
            vehicle_html += vehicle_html1
            vehicle_html += '</tbody>'
            vehicle_html += '</table>'
            vehicle_html += '</td>'

        return {'status': True,'vehicle_html':vehicle_html}

    @http.route(['/fi_details'], type='json', auth='user', website=True, csrf=False)
    def final_inspection_details(self, fi_ids,waiting_ids,current_color,status, **kwargs):
        waiting_for_vehicle_inward = request.env.ref('ac_rms.main_process1').id
        security_process = request.env.ref('ac_rms.main_process2').id
        allocation_html = ''
        allocation_html += '<table style="font-size: 9px;" class="table table-fixed cls-table-search" id="fi_details_tbl" data-firstsort="asc">'
        allocation_html += '<thead>'
        allocation_html += '<tr style="background-color:'+current_color+'">'
        allocation_html += '<th width="4%" style="text-align:left;"></th>'
        allocation_html += '<th width="17%" style="text-align:center;color:white;">Vehicle Reg #</th>'
        allocation_html += '<th width="17%" style="text-align:center;color:white;">Total Time Unit</th>'
        allocation_html += '<th width="17%" style="text-align: center;color:white;">Repair Order(RO)</th>'
        allocation_html += '<th width="17%" style="text-align: center;color:white;">Delivery Date &amp; Time</th>'
        allocation_html += '<th width="17%" style="text-align: center;color:white;">Job Controller</th>'
        allocation_html += '<th width="17%" style="text-align: center;color:white;">Service Advisor</th>'
        allocation_html += '</tr>'
        allocation_html += '</thead>'
        allocation_html += '<tbody style="background-color: #e7e7e7;display: block;max-height: 240px;overflow-y: scroll;">'
        if fi_ids:
            all_ids = fi_ids
        if waiting_ids:
            all_ids = waiting_ids
        if all_ids:
            for orders in all_ids:
                allorder = int(orders)
                order = request.env['sale.order'].browse(allorder)
                if order.tasks_ids:
                    order_name = order.name and order.name or ''
                    regn_no = order.regn_no.license_plate and order.regn_no.license_plate or ''
                    delivery_date = order.create_date and order.create_date or ''
                    service_advisor = order.user_id.name and order.user_id.name or ''
                    allocation_html += '<tr class="modal_rows">'
                    allocation_html += '<td width="4%" style="text-align:left;">'
                    allocation_html += '<input type="checkbox" class="select_check" name="select"/></td>'
                    allocation_html += '<td width="17%" style="text-align:center;"><a href="#~" class="fi_regn_clk">' + regn_no + '</a><input class="order hidden" name="order-ids" type="text" value="' + str(order.id) + '" /><input class="status hidden" name="status" type="text" value="' + str(status) + '" /></td>'
                    allocation_html += '<td width="17%" style="text-align:center;color:black;">' + '0' + '</td>'
                    allocation_html += '<td width="17%" style="text-align:center;color:black;">' + order_name + '</td>'
                    allocation_html += '<td width="17%" style="text-align:center;color:black;" class="sort_td">' + delivery_date + '</td>'
                    allocation_html += '<td width="17%" style="text-align: center;color:black;">' + service_advisor + '</td>'
                    allocation_html += '<td width="17%" style="text-align:center;color:black;">' + service_advisor + '</td>'
                    allocation_html += '</tr>'
                    allocation_html += '<tr class="modal_rows" id="task_' + str(order.id) + '"></tr>'
            allocation_html += '</tbody>'
            allocation_html += '</table>'

        return {'html_data': allocation_html}

    @http.route(['/bay-tech-popup/vehicle-details'], type='json', auth='user', website=True, csrf=False)
    def bay_tech_popup_vehicle_details(self, order_id, **kwargs):
        cr = request.env.cr
        bay_category = request.env.ref('ac_rms.resource_categories_bay')
        bays = request.env['resource.resource'].search([('resource_category', '=', bay_category.id)])
        bay_opt = ''
        for bay in bays:
            bay_opt += '<option value="' + bay.name + '">' + bay.name + '</option>'
        tech_category = request.env.ref('ac_rms.resource_categories_tech')
        techs = request.env['resource.resource'].search([('resource_category', '=', tech_category.id)])
        tech_opt = ''
        for tech in techs:
            tech_opt += '<option value="'+str(tech.id)+'">'+tech.name+'</option>'
        if order_id:
            vehicle_html = ''
            vehicle_html += '<td colspan="6">'
            vehicle_html += '<div style="margin-left: 103%;"><button type="button"  id="taskconfirm" class="btn btn-primary tawindow">Confirm</button></div>'
            vehicle_html += '<div><a href = "#" class ="test_cls">Select All</a><a href="#" class ="selectallclass1" style="margin-left:8%;">Assign</a></div>'
            vehicle_html += '<table id="alloc_table"  data-firstsort="asc">'
            vehicle_html += '<thead>'
            vehicle_html += '<tr>'
            vehicle_html += '<th width="5%" style="text-align:left;"></th>'
            vehicle_html += '<th width="10%" style="text-align:center;">Labour</th>'
            vehicle_html += '<th width="12%" style="text-align:center;">Bay</th>'
            vehicle_html += '<th width="12%" style="text-align:center;">Technician</th>'
            vehicle_html += '<th width="18%" style="text-align: center;">Start Time</th>'
            vehicle_html += '<th width="16%" style="text-align: center;">End Time</th>'
            vehicle_html += '<th></th>'
            vehicle_html += '<th></th>'
            vehicle_html += '</tr>'
            vehicle_html += '</thead>'
            vehicle_html += '<tbody>'
            order_obj = request.env['sale.order'].browse(eval(order_id))
            vehicle_html1 = ''
            order_tasks = order_obj.tasks_ids.ids
            if order_tasks:
                cr.execute("""select array_agg(pt.id ) as task_ids
                                            from project_task pt 
                                            inner join project_task_type pty on pty.id = pt.stage_id
                                            where pty.sequence in (0,7,5,4)
                                            and pt.id in %s
                                        """,(tuple(order_tasks),))
                all_task_ids = cr.dictfetchall()
                if all_task_ids:
                    if all_task_ids[0].get('task_ids'):
                        for task in request.env['project.task'].browse(all_task_ids[0].get('task_ids')):
                            vehicle_html1 += '<tr class="tech_labour_date_tr modal_rows">'
                            vehicle_html1 += '<td width="5%" style="text-align:left;">'
                            vehicle_html1 += '<span class="clone-no-add"><input name="inner-chckbox" type="checkbox"/></span></td>'
                            vehicle_html1 +=  '<td width="10%" style="text-align:center;"><span class="clone-no-add"><input type="text" class="hidden" id="task_ids" name="task_ids" value="'+str(task.id)+'"/>'+task.name+'</span></td>'
                            vehicle_html1 += '<td width="12%" style="text-align:right;"><select style="width:94%;" class="form-control" name="bay" id="bay_select"><option/>'+bay_opt+'</select></td>'
                            vehicle_html1 += '<td width="12%" style="text-align:right;"><select style="width:94%;" class="form-control" name="tech" id="tech_select"><option/>'+tech_opt+'</select></td>'
                            vehicle_html1 += '<td><div class="form-group" style="margin: 6% 7% 6% 7%;width:85%;"><div class="input-group date" id="datetimepicker1"><input type="text" class="form-control st_date"/><span class="input-group-addon"><span class="fa fa-calendar start_datetime"></span></span></div></td>'
                            vehicle_html1 += '<td><div class="form-group" style="margin: 6% 7% 6% 0%;width:93%;"><div class="input-group date" id="datetimepicker2"><input type="text" class="form-control en_date"/><span class="input-group-addon"><span class="fa fa-calendar end_datetime"></span></span></div></td>'
                            vehicle_html1 += '<td width = "5%" class ="tr_clone_add"><button class ="btn btn-primary btn-color-plus" id = "addnew" name = "addnew" type = "button" ><i class ="fa fa-plus"/></ button></td>'
                        vehicle_html1 += '</tr>'
                        vehicle_html += vehicle_html1
                        vehicle_html += '</tbody>'
                        vehicle_html += '</table>'
                        vehicle_html += '</td>'
            # print(vehicle_html)

        return {'vehicle_details_data': vehicle_html}

    @http.route(['/fi_task_details'], type='json', auth='user', website=True, csrf=False)
    def fi_task_details(self, order_id,status, **kwargs):
        cr = request.env.cr
        bay_category = request.env.ref('ac_rms.resource_categories_bay')
        bays = request.env['resource.resource'].search([('resource_category', '=', bay_category.id)])
        bay_opt = ''
        for bay in bays:
            bay_opt += '<option value="' + bay.name + '">' + bay.name + '</option>'
        tech_category = request.env.ref('ac_rms.resource_categories_tech')
        techs = request.env['resource.resource'].search([('resource_category', '=', tech_category.id)])
        tech_opt = ''
        for tech in techs:
            tech_opt += '<option value="' + str(tech.id) + '">' + tech.name + '</option>'
        button = ''
        if order_id:
            order_obj = request.env['sale.order'].browse(eval(order_id))
            if order_obj.main_process_id == request.env.ref("ac_rms.main_process15"):
                button =  '<button style = "float: right;" type = "button" id = "taskstart"  class ="btn btn-primary fistart">Start</ button>'
            if order_obj.main_process_id == request.env.ref("ac_rms.main_process16"):
                button = '<button style = "float: right;" type = "button" id = "taskstart"  class ="btn btn-primary fistart">Finish</ button>'
            vehicle_html = ''
            vehicle_html += '<td colspan="6">'
            # vehicle_html += '<div style="margin-left: 103%;"></div>'
            vehicle_html += '<div style="margin-left: 103%;"></div>'
            vehicle_html += '<div><a href = "#~" class ="test_cls">Select All</a><a href="#~" class ="selectallclass1" style="margin-left:8%;">Assign</a>'+button+'</div>'
            vehicle_html += '<div>'
            vehicle_html += '<div style="float:left;width: 78%;">'
            vehicle_html += '<table id="fi_alloc_table"  data-firstsort="asc" width="100%">'
            vehicle_html += '<thead>'
            vehicle_html += '<tr>'
            vehicle_html += '<th style="text-align:left;"></th>'
            vehicle_html += '<th style="text-align:center;color:black;">Labour</th>'
            vehicle_html += '<th style="text-align:center;color:black;">STU</th>'
            vehicle_html += '<th style="color:black;">Technician</th>'
            vehicle_html += '<th style="color:black;">Status</th>'
            # vehicle_html += '<th></th>'
            # vehicle_html += '<th></th>'
            vehicle_html += '</tr>'
            vehicle_html += '</thead>'
            vehicle_html += '<tbody>'
            vehicle_html1 = ''
            order_tasks = order_obj.tasks_ids.ids
            if order_tasks:
                for task in request.env['project.task'].browse(order_tasks):
                    resource = task.user_id and task.user_id.name or ''
                    task_name = task.name.split(':')
                    labour_name = task_name and task_name[1]  or ''
                    vehicle_html1 += '<tr class="tech_labour_date_tr modal_rows">'
                    vehicle_html1 += '<td style="text-align:left;">'
                    vehicle_html1 += '<span class="clone-no-add"><input name="inner-chckbox" type="checkbox"/></span></td>'
                    vehicle_html1 += '<td style="text-align:center;color:black;"><span class="clone-no-add"><input type="text" class="hidden" id="task_ids" name="task_ids" value="' + str(task.id) + '"/>' + labour_name + '</span></td>'
                    vehicle_html1 += '<td style="text-align:right;color:black;"></td>'
                    vehicle_html1 += '<td style="color:black;"><span id="tech_name">'+ resource +'</span></td>'
                    if status == 'True':
                        vehicle_html1 += '<td style="text-align:right;color:black;"><select disabled class="form-control" name="status" id="status"><option value="pass">Pass</option><option value="fail">Fail</option></select></td>'
                    else:
                        vehicle_html1 += '<td style="text-align:right;color:black;"><select class="form-control" name="status" id="status"><option value="pass">Pass</option><option value="fail">Fail</option></select></td>'
                vehicle_html1 += '</tr>'
                vehicle_html += vehicle_html1
                vehicle_html += '</tbody>'
                vehicle_html += '</table>'
                vehicle_html += '</div>'
                vehicle_html += '<div style="float:right;width: 22%;">'
                vehicle_html += '<span id="reason-string">Reason</span><div id="textbox-reason"><textarea name="reason" id="reason"></textarea></div>'
                vehicle_html += '</div>'
                vehicle_html += '</div>'
                vehicle_html += '</td>'

        return {'vehicle_details_data': vehicle_html}

    @http.route(['/final_inspection_start'], type='json', auth='user', website=True, csrf=False)
    def final_inspection_start(self, status,task_ids,button_text, **kwargs):
        if task_ids:
            start = False
            finish = False
            is_fi_rejection = False
            ready_for_delivery = ''
            sa_stage = ''
            task_obj = request.env['project.task'].browse(eval(task_ids))
            if button_text == 'Start':
                task_obj.order_id.write({'main_process_id':request.env.ref("ac_rms.main_process16").id})
                start = True
            if button_text == 'Finish':
                if status == 'fail':
                    is_fi_rejection = True
                    task_obj.stage_id = request.env['project.task.type'].search([('sequence', '=', 4)]).id
                    ready_for_delivery = request.env.ref("ac_rms.main_process16").id
                if status == 'pass':
                    is_fi_rejection = False
                    ready_for_delivery = request.env.ref("ac_rms.main_process17").id
                    sa_stage = 'Ready for Delivery'
                task_obj.sale_line_id.write({'fi_status':status})
                task_obj.order_id.write({'bay_tech_allocation': False,'main_process_id':ready_for_delivery ,'is_fi_rejection':is_fi_rejection,'sa_work_flow':sa_stage})
                finish = True
        return {'start':start,'finish': finish}

    @http.route(['/resource_planner/chip_clk'], type='json', auth="user", website=True, csrf=False)
    def modal(self,event_id, **kwargs):
        if request.env.user.has_group('ac_rms.group_technician'):
            tech_categ = request.env.ref('ac_rms.resource_categories_tech')
            # techs = request.env['resource.resource'].search([('resource_category', '=', tech_categ)])
            if event_id:
                event_obj = request.env['calendar.event'].browse(event_id).res_id
                project_task_obj = request.env['sale.order'].browse(event_obj).tasks_ids
                sale_order_obj = request.env['sale.order'].browse(event_obj)
                # task_name = project_task_obj.name
                # sheet_ids = project_task_obj.timesheet_ids.filtered(lambda x: x.resource_type == tech_categ and  x.entry_type == 'plan')

            res = request.env.ref('ac_rms.modal').render({'tasks':project_task_obj,'tech_categ':tech_categ,'regn_no':sale_order_obj.regn_no.license_plate,'so_name':sale_order_obj.name,'event':event_id})
            return {'status':True,'clk':'single','result':res}
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
            return {'status': True,'clk':'dbl','order_id': order_obj.id, 'reg_no': reg_no, 'repair_order': repair_order,
                    'delivery_datetime': delivery_datetime, 'service_advisor': service_advisor}

    def calendar_event_insert(self,tasks,order_id,timesheet_ids,name):
        # order_id = order_id.id
        user = request.env['res.users'].browse(request.env.uid)
        if user.partner_id.tz:
            tz = pytz.timezone(user.partner_id.tz)
        else:
            tz = pytz.utc
        for sheet in timesheet_ids:
            resource = request.env['resource.resource'].search([('name', '=', sheet.resource_name.name)])
            resource_category = request.env['resource.category'].search([('id', '=', resource.resource_category.id)])
            if sheet.resource_name.resource_category.id == request.env.ref("ac_rms.resource_categories_bay").id:
                resource_user = 1
            if sheet.resource_name.resource_category.id == request.env.ref("ac_rms.resource_categories_tech").id:
                resource_user = resource.user_id.id
            employee = request.env['hr.employee'].search([('user_id', '=', resource.user_id.id)])
            model_id = request.env['ir.model'].search([('model', '=', 'sale.order')]).id
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
                False, False, False, False, 'date', 1, resource_user and resource_user or  1, True, 'actual',))
            cal_id = request.env.cr.dictfetchall()
            eve_id = cal_id[0].get('id')
            events = request.env['calendar.event'].browse(eve_id)
            if events:
                events.partner_ids = [(6, 0, [resource.resource_partner.id])]
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

    def technician_actaul_process(self, tasks):
        if tasks:
            for data in request.env['project.task'].browse(tasks):
                self.calendar_event_insert(tasks, data.order_id, data.timesheet_ids,data.name)
                self.timesheet_create(data,data.timesheet_ids)

        return {}



    @http.route(['/tech_start'], type='json', auth="user", website=True, csrf=False)
    def technician_start(self, tasks, **kwargs):
        self.technician_actaul_process(tasks)
        return {}

    @http.route(['/tech_pause'], type='json', auth="user", website=True, csrf=False)
    def technician_pause(self, tasks, onhold, otherreason, **kwargs):
        for task in request.env['project.task'].browse(tasks):
            task.sudo().timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and not x.end_datetime).write({'end_datetime':datetime.now()})
            for sheet in task.timesheet_ids.filtered(lambda x: x.entry_type == 'plan'):
                resource = request.env['resource.resource'].search([('name', '=', sheet.resource_name.name)])
                resource_category = request.env['resource.category'].search([('id', '=', resource.resource_category.id)])
                employee = request.env['hr.employee'].search([('user_id', '=', resource.user_id.id)])
                timesheet_data_entry = {
                    'account_id': 1,
                    'date': datetime.now(),
                    'status': request.env.ref("ac_rms.status2").id,
                    'entry_type': 'actual',
                    'resource_type': resource_category.id,
                    'resource_name': resource.id,
                    'start_datetime': datetime.now(),
                    'end_datetime': '',
                    'break_reason': onhold if onhold != 'Others' else otherreason,
                    'employee_id': employee.id,
                    'name': task.name
                }
                task.sudo().timesheet_ids = [(0, 0, timesheet_data_entry)]

            task.stage_id = request.env['project.task.type'].search([('sequence', '=', 3)]).id
            task.order_id.main_process_id = request.env.ref("ac_rms.main_process11").id
            event_obj = request.env['calendar.event'].search(
                [('res_id', '=', task.order_id.id), ('entry_type', '=', 'actual')])
            current_time = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(hours=5, minutes=30)
            if event_obj:
                event_obj.write({'stop': current_time,
                                                  'stop_date':datetime.now().date(),
                                                   'stop_datetime':current_time})
        return {}


    @http.route(['/tech_realease_approve'], type='json', auth="user", website=True, csrf=False)
    def technician_release_approve(self, tasks, **kwargs):
        login_user = request.env["resource.resource"].search([('user_id', '=', request.env.uid)])
        for task in request.env['project.task'].browse(tasks):
            task.sudo().timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and not x.end_datetime and x.status == request.env.ref("ac_rms.status2")).write({'end_datetime':datetime.now()})
            if len(task.user_id) == 1 and len(task.order_id.tasks_ids) == 1:
                technician_plan = task.timesheet_ids.filtered(lambda x: x.entry_type == 'plan' and x.resource_type == request.env.ref("ac_rms.resource_categories_tech"))
                technician_plan.write({'end_datetime': datetime.now(),'is_release':True})
                task.timesheet_ids.filtered(lambda x: x.entry_type == 'plan' and x.resource_type == request.env.ref("ac_rms.resource_categories_bay") and x.resource_name == technician_plan.mapped_bay_resource).write({'end_datetime': datetime.now(),'is_release':True})
            for sheet in task.timesheet_ids.filtered(lambda x: x.entry_type == 'plan'):
                resource = request.env['resource.resource'].search([('name', '=', sheet.resource_name.name)])
                resource_category = request.env['resource.category'].search([('id', '=', resource.resource_category.id)])
                employee = request.env['hr.employee'].search([('user_id', '=', resource.user_id.id)])
                timesheet_data_entry = {
                    'account_id': 1,
                    'date': datetime.now(),
                    'status': request.env.ref("ac_rms.status3").id,
                    'entry_type': 'actual',
                    'resource_type': resource_category.id,
                    'resource_name': resource.id,
                    'start_datetime': datetime.now(),
                    'end_datetime': datetime.now(),
                    'break_reason': '',
                    'employee_id': employee.id,
                    'name': task.name,
                }
                task.timesheet_ids = [(0, 0, timesheet_data_entry)]

            task.stage_id = request.env['project.task.type'].search([('sequence', '=', 5)]).id
            task.user_id = ""
            task.order_id.write({'bay_tech_allocation' : False,'is_hold_approve':True})
        return {}

    @http.route(['/tech_realease_reject'], type='json', auth="user", website=True, csrf=False)
    def technician_release_reject(self, tasks, **kwargs):
        for task in request.env['project.task'].browse(tasks):
            task.timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and not x.end_datetime and x.status == request.env.ref("ac_rms.status2")).write({'end_datetime': datetime.now()})
            for sheet in task.timesheet_ids.filtered(lambda x: x.entry_type == 'plan'):
                resource = request.env['resource.resource'].search([('name', '=', sheet.resource_name.name)])
                resource_category = request.env['resource.category'].search(
                    [('id', '=', resource.resource_category.id)])
                employee = request.env['hr.employee'].search([('user_id', '=', resource.user_id.id)])
                timesheet_data_entry = {
                    'account_id': 1,
                    'date': datetime.now(),
                    'status': request.env.ref("ac_rms.status4").id,
                    'entry_type': 'actual',
                    'resource_type': resource_category.id,
                    'resource_name': resource.id,
                    'start_datetime': datetime.now(),
                    'end_datetime': datetime.now(),
                    'break_reason': '',
                    'employee_id': employee.id,
                    'name': task.name
                }
                task.timesheet_ids = [(0, 0, timesheet_data_entry)]

            task.stage_id = request.env['project.task.type'].search([('sequence', '=', 4)]).id
        return {}

    @http.route(['/tech_break'], type='json', auth="user", website=True, csrf=False)
    def technician_break(self, brk_typ,brk_reason, **kwargs):
        tech_categ = request.env.ref("ac_rms.resource_categories_tech").id
        login_user = request.env["resource.resource"].search([('user_id','=',request.env.uid)])
        # current_time = datetime.now()
        c = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(hours=5, minutes=30)
        current_time = (c.replace(tzinfo=pytz.utc)).strftime(DEFAULT_DATE_TIME_FORMATE)
        cr = request.env.cr
        cr.execute("""select pt.id as task_id
                        from project_task pt 
                        inner join account_analytic_line al on al.task_id = pt.id
                        inner join project_task_type pty on pty.id = pt.stage_id
                        inner join resource_resource rc on rc.id = al.resource_name
                        inner join res_users ru on ru.id = rc.user_id
                        where pty.sequence = 1
                        and al.entry_type = 'actual'
                        and al.resource_type = %s
                        and ru.id = %s
                        and pt.active = True
                        """,(tech_categ,request.session.uid))
        all_data = cr.dictfetchall()
        if all_data:
            for data in all_data:
                task_id = data.get('task_id')
                task_obj = request.env["project.task"].browse(task_id)
                # if login_user.partner_id:
                #     calendar_actual_obj = request.env["calendar.event"].search([('entry_type', '=', 'actual'),('partner_ids','in',login_user.partner_id.id),('res_id', '=',task_obj.order_id.id)])
                if login_user.user_id:
                    calendar_actual_obj = request.env["calendar.event"].search([('entry_type', '=', 'actual'),('res_id', '=', task_obj.order_id.id)])
                    calendar_actual_obj.write({'stop': current_time,
                                     'stop_date': datetime.now().date(),
                                     'stop_datetime': current_time})
                vals = {}
                if brk_typ == 'shiftend':
                    reason = 'Shift End'
                    tech_multi_entry = task_obj.timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and x.resource_type == request.env.ref("ac_rms.resource_categories_tech") and not x.end_datetime)
                    if len(tech_multi_entry) == 1:
                        vals.update({'bay_tech_allocation': False})
                    vals.update({'is_carry_over':True,
                                 'main_process_id' : request.env.ref("ac_rms.main_process14").id})
                    shiftend = request.env.ref("ac_rms.status6").id
                    tech_actual_entry = task_obj.timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and x.resource_type == request.env.ref("ac_rms.resource_categories_tech") and x.resource_name == login_user and not x.end_datetime)
                    bay_actual_entry = task_obj.timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and x.resource_type == request.env.ref("ac_rms.resource_categories_bay")  and not x.end_datetime)
                    all_actual_entry = tech_actual_entry | bay_actual_entry
                    all_actual_entry.write({'end_datetime': datetime.now(),'status': shiftend,'break_reason':reason})
                    task_obj.stage_id = request.env['project.task.type'].search([('sequence', '=', 7)]).id
                    if len(task_obj.user_id) == 1 and len(task_obj.order_id.tasks_ids) == 1:
                        technician_plan = task_obj.timesheet_ids.filtered(lambda x: x.entry_type == 'plan' and x.resource_type == request.env.ref("ac_rms.resource_categories_tech") and x.resource_name == login_user)
                        technician_plan.write({'end_datetime': datetime.now()})
                        task_obj.timesheet_ids.filtered(lambda x: x.entry_type == 'plan' and x.resource_type == request.env.ref("ac_rms.resource_categories_bay") and x.resource_name == technician_plan.mapped_bay_resource).write({'end_datetime': datetime.now()})
                        calendar_plan_entry = request.env["calendar.event"].search([('entry_type', '=', 'plan'),('res_id', '=', task_obj.order_id.id)])
                        calendar_plan_entry.write({'stop': current_time,
                                                   'stop_date': datetime.now().date(),
                                                   'stop_datetime': current_time})
                if brk_typ in ('lunch','tea','others'):
                    if brk_typ == 'tea':
                        reason = 'Tea Break'
                    if brk_typ == 'lunch':
                        reason = 'Lunch Break'
                    if brk_typ == 'others':
                        reason = brk_reason
                    vals.update({'main_process_id': request.env.ref("ac_rms.main_process9").id})
                    tech_timesheet_ids = task_obj.timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and x.resource_type == request.env.ref("ac_rms.resource_categories_tech") and x.resource_name == login_user and not x.end_datetime)
                    bay_timesheet_ids = task_obj.timesheet_ids.filtered(lambda x: x.entry_type == 'actual' and x.resource_type == request.env.ref("ac_rms.resource_categories_bay") and not x.end_datetime)
                    all_timesheet_ids = tech_timesheet_ids | bay_timesheet_ids
                    all_timesheet_ids.sudo().write({'end_datetime':datetime.now(),'status':request.env.ref("ac_rms.status7").id,'break_reason':reason})
                    # bay_timesheet_ids.sudo().write({'end_datetime': datetime.now(), 'status': request.env.ref("ac_rms.status7").id,'break_reason': reason})
                    task_obj.stage_id = request.env['project.task.type'].search([('sequence', '=', 2)]).id
                task_obj.order_id.write(vals)
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
            time_sheet_record = task.timesheet_ids.filtered(lambda x: x.resource_type in (tech_categ,bay_categ) and x.entry_type == 'actual' and not x.end_datetime)
            time_sheet_record.write({'end_datetime': datetime.now()})
            order_id = task.order_id
            resource_ids = time_sheet_record.mapped('resource_name').mapped('resource_partner').ids
            event_obj = request.env['calendar.event'].search([('res_id','=',order_id.id),('partner_ids','in',resource_ids),('entry_type','=','actual')])
            # date = datetime.now().date()
            current_time = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(hours=5, minutes=30)
            if event_obj:
                event_obj.write({'stop': current_time,
                                                  'stop_date':datetime.now().date(),
                                                   'stop_datetime':current_time})
            return {'tasks':tasks,'event':event}
#             task.stage_id = request.env['project.task.type'].search([('sequence', '=', 6)]).id
#             task.order_id.write({'main_process_id':request.env.ref("ac_rms.main_process15").id}
#         return {}

    @http.route(['/tech_finish_time_sheet'], type='json', auth="user", website=True, csrf=False)
    def technician_finish_timesheet(self, tasks, event, **kwargs):
        tech_categ = request.env.ref('ac_rms.resource_categories_tech')
        bay_categ = request.env.ref('ac_rms.resource_categories_bay')
        current_time = fields.Datetime.from_string(fields.Datetime.now())
        for task in request.env['project.task'].browse(tasks):
            time_sheet_record = task.timesheet_ids.filtered(lambda x: x.resource_type in (tech_categ,bay_categ) and x.entry_type == 'actual' and not x.end_datetime)
            time_sheet_record.write({'end_datetime': current_time})
            task.stage_id = request.env['project.task.type'].search([('sequence', '=', 6)]).id
            task.order_id.write({'main_process_id':request.env.ref("ac_rms.main_process15").id})
        return {}

    def actual_chip_default_width_after_event_render(self, time_unit,current_time):
        import time
        current_time1 = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        start_stop_time = datetime.strptime(time_unit, "%Y-%m-%d %H:%M:%S")
        first = time.mktime(current_time1.timetuple())
        second = time.mktime(start_stop_time.timetuple())
        min = int(first - second) / 60

        # current_start_diff = current_time1 - start_stop_time
        # datetime.datetime.timedelta(0,8,562000)
        # td = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        # hours, remainder = divmod(td.seconds, 3600)
        # min, seconds = divmod(remainder, 60)
        # final_diff = divmod(current_start_diff.days * 86400 + current_start_diff.seconds,60)
        # hours, remainder = divmod(current_start_diff.seconds, 3600)
        # min, seconds = divmod(remainder, 60)

        if min < 5:
            return True
        else:
            return False
        
    @http.route(['/resource_planner/get'], type='json', auth="user", website=True, csrf=False)
    def get_resource_planner(self, view,showall,button_text,**kwargs):
        user = request.env['res.users'].browse(request.env.uid)
        if user.partner_id.tz:
            tz = pytz.timezone(user.partner_id.tz)
        else:
            tz = pytz.utc
        res_calender = request.env['planner.calender'].browse(int(view))
        resources = res_calender.member_ids
        if request.env.user.has_group('ac_rms.group_technician') and showall == 'False':
            resource_user = request.env["resource.resource"].search([('user_id','=',request.env.user.id)])
            resources = resource_user
        if button_text == 'Show All':
            resources = resources
        resources_list = []
        events_list = []
        for resource in resources:
            partner = False
            partner = resource.resource_partner.ids
            if not partner:
                partner = resource.user_id.partner_id.ids
            plan_resource = str(resource.id)+'-'+str(partner[0])
            resources_list.append({'id': plan_resource, 'title': 'Plan','resource':resource.name})
            actual_resource = str(partner[0])+'-'+str(resource.id)
            resources_list.append({'id': actual_resource, 'title': 'Actual','resource':resource.name})
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
                    fields.Datetime.from_string(event.stop_datetime).replace(tzinfo=pytz.utc).astimezone(tz)).strftime(
                        DEFAULT_DATE_TIME_FORMATE)
                    add_time = self.actual_chip_default_width_after_event_render(stop_date,event.start)
                    if add_time and event.entry_type == 'actual':
                        stop = (fields.Datetime.from_string(stop_date) + timedelta(minutes=5)).strftime(DEFAULT_DATE_TIME_FORMATE)
                    else:
                        stop = fields.Datetime.from_string(stop_date).strftime(DEFAULT_DATE_TIME_FORMATE)


                else:
                    # start1 = datetime.strptime(event.start, "%Y-%m-%d %H:%M:%S")
                    c = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(hours=5, minutes=30)
                    add_time = self.actual_chip_default_width_after_event_render(event.start,c.strftime(DEFAULT_DATE_TIME_FORMATE))
                    if add_time and event.entry_type == 'actual':
                        c = c + timedelta(minutes=5)
                        stop = (c.replace(tzinfo=pytz.utc).astimezone(tz)).strftime(DEFAULT_DATE_TIME_FORMATE)
                    else:
                        stop =  (c.replace(tzinfo=pytz.utc).astimezone(tz)).strftime(DEFAULT_DATE_TIME_FORMATE)

                if event.entry_type == 'plan':

                    events_list.append(
                        {'id': event.id, 'resourceId': plan_resource, 'start': start, 'end': stop, 'title': event.name,
                         'color': '#3498db;','event_type':'plan'})


                if event.entry_type == 'actual':


                    events_list.append(
                        {'id': event.id, 'resourceId': actual_resource, 'start': start, 'end': stop, 'title': event.name,
                         'color': '#008000;','event_type':'actual'})


        vals = {'status': True, 'resource': resources_list, 'events': events_list}
        return vals

    def calendar_insert(self, values,bay_tech):
        if values:
            cr = request.env.cr
            calendar_event_obj = request.env['calendar.event']
            partner = bay_tech.resource_partner.id

            cr.execute("""INSERT INTO calendar_event(
                                                name, state, display_start, start, stop, allday, start_date,
                                                start_datetime, stop_date, stop_datetime, duration,
                                                privacy, show_as, res_id, res_model_id, res_model, recurrency, recurrent_id,
                                                end_type, "interval", count, mo, tu, we, th, fr, sa, su, month_by,
                                                day, user_id, active,entry_type)
                                                VALUES ( %s, %s, %s,%s, %s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,
                                                                %s, %s, %s, %s, %s,
                                                                %s,%s, %s, %s, %s, %s, %s, %s, %s,%s,%s,
                                                                %s) RETURNING id;
                                                """, (values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7],
                                                      values[8],
                                                      values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18], values[19], values[20], values[21],
                                                      values[22], values[23],
                                                      values[24], values[25], values[26], values[27], values[28],values[29], values[30], values[31], values[32],))
            cal_id = cr.dictfetchall()
            eve_id = cal_id[0].get('id')
            events = calendar_event_obj.browse(eve_id)
            if events:
                events.partner_ids = [(6, 0, [partner])]
                events.create_attendees()
        return eve_id

    @http.route(['/timesheet_record_ins'], type='json', auth="user", website=True, csrf=False)
    def timesheet_record_ins(self, **post):
        cr = request._cr
        uid = request.env.user.id
        vals = {}
        is_partial = False
        bay_tech_allocation = False
        multi_restrict = False
        resource_obj = request.env['resource.resource']
        analytic_line = request.env["account.analytic.line"]
        res_categ_obj = request.env['resource.category']
        task_obj = request.env['project.task']
        employee_obj = request.env['hr.employee']

        task_type_obj = request.env['project.task.type']
        order_obj = request.env['sale.order']
        category_tech = request.env.ref("ac_rms.resource_categories_tech")
        category_bay = request.env.ref("ac_rms.resource_categories_bay")
        waiting_to_start_process = request.env.ref("ac_rms.main_process9")
        model_id = request.env['ir.model'].search([('model', '=', 'sale.order')]).id
        if post.get('result'):
            task_list = set()
            for labs in post.get('result')[0].get('labour'):
                order = order_obj.browse(int(labs.get('order')))
                for data in labs.get('data'):
                    task_list.add(data.get('task_id'))
                    bay = resource_obj.search([('name', '=', data.get('bay_name'))])
                    tech = resource_obj.search([('name', '=', data.get('technicain'))])
                    account_line = analytic_line.search(
                        [('resource_name.name', '=', data.get('bay_name')), ('resource_type', '=', category_bay.id),
                         ('entry_type', '=', 'plan'), ('task_id', '=', int(data.get('task_id'))),
                         ('is_release', '=', False)])
                    resource = resource_obj.search([('name', '=', data.get('technicain'))])
                    resource_category = res_categ_obj.search([('id', '=', resource.resource_category.id)])
                    if resource_category.id == category_tech.id:
                        user_id = resource.user_id.id
                    task_id = task_obj.browse(eval(data.get('task_id')))
                    resource_category_tech = res_categ_obj.search([('id', '=', tech.resource_category.id)])
                    resource_category_bay = res_categ_obj.search([('id', '=', bay.resource_category.id)])
                    employee = employee_obj.search([('user_id', '=', uid)])
                    start_date = data.get('start_date')
                    date_start = datetime.strptime(start_date, '%m/%d/%Y %I:%M %p')
                    st_date = datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
                    end_date = data.get('end_date')
                    date_end = datetime.strptime(end_date, '%m/%d/%Y %I:%M %p')
                    en_date = datetime.strftime(date_end, '%Y-%m-%d %H:%M:%S')
                    start_entry = (
                    datetime.strptime(st_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=5, minutes=30)).strftime(
                        "%Y-%m-%d %H:%M:%S")
                    end_entry = (
                    datetime.strptime(en_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=5, minutes=30)).strftime(
                        "%Y-%m-%d %H:%M:%S")
                    timesheet_data_tech_entry = {
                        'account_id': 1,
                        'date': datetime.now(),
                        'status': '',
                        'entry_type': 'plan',
                        'resource_type': resource_category_tech.id,
                        'resource_name': tech.id,
                        'start_datetime': start_entry,
                        'end_datetime': end_entry,
                        'break_reason': '',
                        'employee_id': employee.id,
                        'name': task_id.name,
                        'mapped_bay_resource': bay.id, }
                    # vals.update({'sheet_tech_entry': timesheet_data_tech_entry, 'task_id': task_id.id})
                    task_id.timesheet_ids = [(0, 0,timesheet_data_tech_entry)]
                    if not account_line:
                        timesheet_data_bay_entry = {
                            'account_id': 1,
                            'date': datetime.now(),
                            'status': '',
                            'entry_type': 'plan',
                            'resource_type': resource_category_bay.id,
                            'resource_name': bay.id,
                            'start_datetime': start_entry,
                            'end_datetime': end_entry,
                            'break_reason': '',
                            'employee_id': employee.id,
                            'name': task_id.name,
                            'mapped_bay_resource': tech.id}
                        # vals.update({'sheet_bay_entry': timesheet_data_bay_entry, 'task_id': task_id.id})
                        task_id.timesheet_ids = [(0, 0, timesheet_data_bay_entry)]
                    shiftend = task_type_obj.search([('sequence', '=', 7)]).id
                    approved = task_type_obj.search([('sequence', '=', 5)]).id
                    rejected = task_type_obj.search([('sequence', '=', 4)]).id
                    task_user_id = ''
                    if task_id.stage_id.id in (shiftend, approved,rejected):
                        task_id.stage_id = task_type_obj.search([('sequence', '=', 0)]).id
                    if user_id:
                        task_user_id = user_id
                    vals.update({'status': True})
                    task_id.user_id = task_user_id

            if len(task_list) != len(order.tasks_ids) and order.is_additional_job == False:
                is_partial = True
                task_id.stage_id = task_type_obj.search([('sequence', '=', 8)]).id

            else:
                bay_tech_allocation = True

            order.write({'main_process_id': waiting_to_start_process.id, 'is_partial': is_partial,
                             'bay_tech_allocation': bay_tech_allocation})
        return True

    @http.route(['/resource_planner/bay_tech_update'], type='json', auth="user", website=True, csrf=False)
    def bay_tech_update_resource_planner(self, **post):
        resource_obj = request.env['resource.resource']
        analytic_line = request.env["account.analytic.line"]
        task_obj = request.env['project.task']
        employee_obj = request.env['hr.employee']
        order_obj = request.env['sale.order']
        category_bay = request.env.ref("ac_rms.resource_categories_bay")
        model_id = request.env['ir.model'].search([('model','=','sale.order')]).id
        cr = request._cr
        cr.execute("""delete from calendar_event where res_id = %s;""", ( int(order_obj.id),))
        if post.get('result'):
            for labs in post.get('result')[0].get('labour'):
                order = order_obj.browse(int(labs.get('order')))
                for data in labs.get('data'):
                    bay = resource_obj.browse(int(data.get('bay_name')))
                    tech = resource_obj.browse(int(data.get('technicain')))
                    account_line = analytic_line.search([('resource_name.name','=',bay.name),('resource_type', '=', category_bay.id),('entry_type', '=', 'plan'), ('task_id', '=', int(data.get('task_id'))),('is_release','=',False)])
                    task_id = task_obj.browse(eval(data.get('task_id')))
                    start_date = data.get('start_date')
                    date_start = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                    st_date = datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
                    end_date = data.get('end_date')
                    date_end = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
                    en_date = datetime.strftime(date_end, '%Y-%m-%d %H:%M:%S')
                    start_entry = (datetime.strptime(st_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                    end_entry = (datetime.strptime(en_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                    event_data = [order.regn_no.license_plate, 'draft', st_date, st_date, en_date, False, st_date, st_date,
                            en_date,en_date, 0.5, 'public', 'busy', order.id, model_id, 'sale_order', False, 0,
                            'count', 1, 1, False,False, False,False, False, False, False, 'date', 1, tech.user_id.id,
                            True, 'plan']
                    self.calendar_insert(event_data,tech)

                    if not account_line:
                        event_data_other = [order.regn_no.license_plate, 'draft', st_date, st_date, en_date, False, st_date, st_date,
                            en_date,en_date, 0.5, 'public', 'busy', order.id, model_id, 'sale_order', False, 0, 'count',
                            1, 1, False,False, False,False, False, False, False, 'date', 1, 1, True, 'plan']
                        self.calendar_insert(event_data_other, bay)
        return {}
    @http.route(['/resource_planner/bay_tech'], type='json', auth="user", website=True, csrf=False)
    def bay_tech_resource_planner(self, **post):
        resource_obj = request.env['resource.resource']
        analytic_line = request.env["account.analytic.line"]
        task_obj = request.env['project.task']
        employee_obj = request.env['hr.employee']
        order_obj = request.env['sale.order']
        category_bay = request.env.ref("ac_rms.resource_categories_bay")
        model_id = request.env['ir.model'].search([('model','=','sale.order')]).id
        if post.get('result'):
            for labs in post.get('result')[0].get('labour'):
                # event_list = []
                order = order_obj.browse(int(labs.get('order')))
                for data in labs.get('data'):
                    bay = resource_obj.search([('name', '=', data.get('bay_name'))])
                    tech = resource_obj.search([('name', '=', data.get('technicain'))])
                    account_line = analytic_line.search([('resource_name.name','=',data.get('bay_name')),('resource_type', '=', category_bay.id),('entry_type', '=', 'plan'), ('task_id', '=', int(data.get('task_id'))),('is_release','=',False)])
                    task_id = task_obj.browse(eval(data.get('task_id')))
                    start_date = data.get('start_date')
                    date_start = datetime.strptime(start_date, '%m/%d/%Y %I:%M %p')
                    st_date = datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
                    end_date = data.get('end_date')
                    date_end = datetime.strptime(end_date, '%m/%d/%Y %I:%M %p')
                    en_date = datetime.strftime(date_end, '%Y-%m-%d %H:%M:%S')
                    start_entry = (datetime.strptime(st_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                    end_entry = (datetime.strptime(en_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

                    event_data = [order.regn_no.license_plate, 'draft', st_date, st_date, en_date, False, st_date, st_date,
                            en_date,en_date, 0.5, 'public', 'busy', order.id, model_id, 'sale_order', False, 0,
                            'count', 1, 1, False,False, False,False, False, False, False, 'date', 1, tech.user_id.id,
                            True, 'plan']
                    tech_event_id = self.calendar_insert(event_data,tech)

                    if not account_line:
                        event_data_other = [order.regn_no.license_plate, 'draft', st_date, st_date, en_date, False, st_date, st_date,
                            en_date,en_date, 0.5, 'public', 'busy', order.id, model_id, 'sale_order', False, 0, 'count',
                            1, 1, False,False, False,False, False, False, False, 'date', 1, 1, True, 'plan']
                        bay_event_id = self.calendar_insert(event_data_other, bay)

            #         event_list.append(tech_event_id)
            #         event_list.append(bay_event_id)
            # join_list = '-'.join(event_list)
            # for event in event_list:
            #     event_obj = self.env["calendar.event"].browse(event)
            #     event_obj.event_ids = join_list

        return True

    @http.route(['/resource_planner/update_event'], type='json', auth="user", website=True, csrf=False)
    def update_resource_event(self, event_id, start, stop, resourceId, duration, **kwargs):
        events = request.env['calendar.event'].browse(int(event_id))
        if events:
            res_str = str(resourceId)
            spilt_str = res_str.split('-')
            resource = request.env['resource.resource'].browse(int(spilt_str[0]))
            old_start = datetime.strptime(events.start_datetime, '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(events.stop_datetime, '%Y-%m-%d %H:%M:%S')
            duration = end - old_start
            sec = duration.total_seconds() / 60
            #             minutes=(duration/(1000*60))
            minutes = int(sec)
            str_start = str(start)
            rlpc_start = str_start.replace("T", " ")
            current_start = datetime.strptime(rlpc_start, '%Y-%m-%d %H:%M:%S')
            #             st_tm = datetime.strftime(current_start, '%Y-%m-%d %H:%M:%S')
            current_end = current_start + timedelta(minutes=minutes)
            #             (datetime.strptime(i.get('start_date'), '%d/%m/%Y %H:%M:%S') - timedelta(hours=5, minutes=30)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            events.write({'user_id': int(resource.user_id.id), 'start': str(current_start), 'stop': str(current_end),
                          'start_datetime': str(current_start), 'stop_datetime': str(current_end)})
        # events.user_id = int(resourceId)
        #             events.start = current_start
        #             events.start_datetime = current_start
        #             events.stop = current_end
        #             events.stop_datetime = current_end
        vals = {'status': True}
        return vals
    
    
    @http.route(['/resource_planner/external_event_timesheet'], type='json', auth="user", website=True, csrf=False)
    def external_event_timesheet(self, start, resourceId,ro_details,event_type=False, **kwargs):
        if ro_details:
            order = request.env['sale.order'].browse(int(ro_details[0].get('ro_id')))
            tasks = order.tasks_ids
            res_str = str(resourceId)
            spilt_str = res_str.split('-')
            for task in tasks:
                for ro_detail in ro_details:
                    if 'res_id' not in ro_detail:
                        resour_id = int(spilt_str[0])
                        category = 'Bay'
                    else:
                        resour_id = int(ro_detail.get('res_id'))
                        category = 'Tech'

                    resource = request.env['resource.resource'].browse(resour_id)
                    employee = request.env['hr.employee'].search([('user_id', '=', resource.user_id.id)],limit=1)
                    timesheet_data_entry = {
                        'account_id': 1,
                        'date': datetime.now(),
                        'status': request.env.ref("ac_rms.status1").id,
                        'entry_type': 'plan',
                        'resource_type': resource.resource_category.id,
                        'resource_name': resource.id,
                        'start_datetime': datetime.now(),
                        'end_datetime': '',
                        'break_reason': '',
                        'employee_id': employee.id,
                        'name': task.name
                    }
                    task.sudo().timesheet_ids = [(0, 0, timesheet_data_entry)]
        return {'status':True}
        

    @http.route(['/resource_planner/external_event'], type='json', auth="user", website=True, csrf=False)
    def external_resource_event(self, start, resourceId,ro_details,event_type=False, **kwargs):
        cr = request._cr
        res_str = str(resourceId)
        spilt_str = res_str.split('-')
        str_start = str(start)
        model_id = request.env['ir.model'].search([('model','=','sale.order')]).id
        # event_list = []
        for ro_detail in ro_details:
            if 'res_id' not in ro_detail:
                resour_id = int(spilt_str[0])
            else:
                resour_id = int(ro_detail.get('res_id'))

            ro_id = int(ro_detail.get('ro_id'))
#             title = ro_detail.get('title').strip()
            so = request.env['sale.order'].browse(int(ro_id))
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
                day, user_id, active,entry_type)
                VALUES ( %s, %s, %s,%s, %s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, 
                                %s, %s, %s, %s, %s, 
                                %s,%s, %s, %s, %s, %s, %s, %s, %s,%s,%s, 
                                %s) RETURNING id;
                """, (
            title, 'draft', rlpc_start, rlpc_start, str(current_end), False, rlpc_start, rlpc_start, str(current_end),
            str(current_end), 0.5, 'public', 'busy', int(ro_id), model_id, 'sale_order', False, 0, 'count', 1, 1, False, False, False,
            False, False, False, False, 'date', 1, 1, True, 'plan',))
            cal_id = cr.dictfetchall()
            eve_id  = cal_id[0].get('id')
            events = request.env['calendar.event'].browse(eve_id)
            if event_type:
                events.event_type = event_type
            if events:
                events.partner_ids = [(6, 0, [resource.resource_partner.id])]
                events.create_attendees()

            
            so.write({'main_process_id':request.env.ref("ac_rms.main_process9").id,'bay_tech_allocation':True})
            # event_list.append(eve_id)
        # join_list = '-'.join(event_list)
        # for event in event_list:
        #     event_obj = self.env["calendar.event"].browse(event)
        #     event_obj.event_ids = join_list
        vals = {'status': True,'ro_details':ro_details}
        return vals

    @http.route(['/resource_planner/get_event_types'], type='json', auth="user", website=True, csrf=False)
    def get_event_type(self,selected_view,**kwargs):
        calendar_obj = request.env["planner.calender"].browse(int(selected_view))
        type = []
        for activity_type in calendar_obj.activity_types:
            type.append(activity_type.name)
        vals = {'activity_types':type}
        return vals

    @http.route(['/resource_planner/event_extended'], type='json', auth="user", website=True, csrf=False)
    def resource_event_extended(self, stop, id, **kwargs):
        events_obj = request.env['calendar.event'].browse(int(id))
        events = request.env['calendar.event'].search([('res_id','=',events_obj.res_id),('entry_type','=','plan')])
        if events:
            str_stop = str(stop)
            rlpc_stop = str_stop.replace("T", " ")
            current_stop = datetime.strptime(rlpc_stop, '%Y-%m-%d %H:%M:%S')
            events.write({'stop': str(current_stop), 'stop_datetime': str(current_stop)})
            # if events.event_ids:
            #     all_events = events.event_ids.split('_')
            #     event_obj = request.env['calendar.event'].browse(all_events)
            #     for eve in event_obj:
            #         eve.write({'stop': str(current_stop), 'stop_datetime': str(current_stop)})
        vals = {'status': True}
        return vals

    @http.route(['/resource_planner/event_extend_timesheet'], type='json', auth="user", website=True, csrf=False)
    def resource_event_timesheet_extended(self, stop, event_id, **kwargs):
        str_stop = str(stop)
        rlpc_stop = str_stop.replace("T", " ")
        current_stop = datetime.strptime(rlpc_stop, '%Y-%m-%d %H:%M:%S') - timedelta(hours=5,minutes=30)
        events_obj = request.env['calendar.event'].browse(int(event_id))
        order_obj = request.env['sale.order'].browse(events_obj.res_id)
        order_obj.tasks_ids.timesheet_ids.filtered(lambda x: x.entry_type == 'plan').write({'end_datetime':str(current_stop)})
        vals = {'status': True}
        return vals

    @http.route(['/resource_planner/external_event_tech'], type='json', auth="user", website=True, csrf=False)
    def resource_external_event_tech(self, start, resourceId, title,event_type,**kwargs):
        resource = request.env['resource.resource'].browse(int(resourceId))
        cr = request._cr
        str_start = str(start)
        rlpc_start = str_start.replace("T", " ")
        model_id = request.env['ir.model'].search([('model','=','sale.order')]).id
        current_start = datetime.strptime(rlpc_start, '%Y-%m-%d %H:%M:%S')
        current_end = current_start + timedelta(minutes=30)
        cr.execute("""INSERT INTO calendar_event(
            name, state, display_start, start, stop, allday, start_date, 
            start_datetime, stop_date, stop_datetime, duration, 
            privacy, show_as, res_id, res_model_id, res_model, recurrency, recurrent_id, 
            end_type, "interval", count, mo, tu, we, th, fr, sa, su, month_by, 
            day, user_id, active,entry_type)
            VALUES ( %s, %s, %s,%s, %s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, 
                            %s, %s, %s, %s, %s, 
                            %s,%s, %s, %s, %s, %s, %s, %s, %s,%s,%s, 
                            %s) RETURNING id;
            """, (
        title, 'draft', rlpc_start, rlpc_start, str(current_end), False, rlpc_start, rlpc_start, str(current_end),
        str(current_end), 0.5, 'public', 'busy', 12, model_id, 'sale_order', False, 0, 'count', 1, 1, False, False, False,
        False, False, False, False, 'date', 1, 1, True, 'plan',))
        cal_id = cr.dictfetchall()
        eve_id = cal_id[0].get('id')
        events = request.env['calendar.event'].browse(eve_id)
        events.event_type = event_type
        if events:
            events.partner_ids = [(6, 0, [resource.resource_partner.id])]
            events.create_attendees()
        vals = {'status': True}
        return vals

    @http.route(['/resource_planner/tech_skill_grp'], type='json', auth="user", website=True, csrf=False)
    def resource_tech_skill_grp(self, skill, tech_id, **kwargs):
        vals = {}
        if skill == 'Skill Set':
            cr = request._cr
            cr.execute("""select rs.name,count(rr.name) from resource_resource as rr
                            inner join resource_skill as rs on rs.id = rr.resource_skill
                            where rr.id in  %s group by rs.name""", (tuple(tech_id),))
            res_skill_grps = cr.dictfetchall()
            grp_str = ''
            for res_skill_grp in res_skill_grps:
                grp_str += '<p>' + str(res_skill_grp.get('name')) + '-(' + str(res_skill_grp.get('count')) + ')</p>'
                resource_by_group = []
                res_skl = request.env['resource.skill'].search([('name', '=', str(res_skill_grp.get('name')))])
                res_grp = request.env['resource.resource'].search([('resource_skill', '=', res_skl.id)])
                #             resource_by_group.append(res_grp)
                #             res_skill_grp['grouped_tech'] = resource_by_group
                for res_gp in res_grp:
                    grp_str += '<div class="fc-event res_div" id=' + str(res_gp.id) + '>' + str(res_gp.name) + '</div>'
            print(grp_str)
            vals = {'status': True, 'grp': grp_str}
        return vals

    ####Security Login######

    @http.route(['/security_login'], type='http', auth="user", website=True, csrf=False)
    def security_smartdevice(self, **kwargs):
        confirmation = {}
        if 'vals' in kwargs:
            vals_data = kwargs.get('vals')
            if vals_data:
                confirmation = {'confirmation_msg': 'Successful'}
        confirmation.update(self.counts_clk())
        return request.render("ac_rms.security_login", confirmation)

    @http.route(['/security_action'], type='http', auth="user", website=True, csrf=False)
    def security_ok(self, **post):
        result =  '%'+post.get('regno')+'%'
        process1 = request.env.ref("ac_rms.main_process1").id
        process20 = request.env.ref("ac_rms.main_process20").id
        if post.get('sale_id') and post.get('model'):
            if post.get('model') == 'crm.lead':
                apps = request.env['crm.lead'].browse(int(post.get('sale_id')))
                if apps.is_estimation == 'No Estimation':
                    appointments = [{'regn_no': apps.regn_no.license_plate,
                                 'partner': apps.partner_id.name,
                                 'order_id': apps.id,
                                 'mobile': apps.mobile,
                                 'model': 'crm.lead',
                                 'process':apps.main_process_id.name}]
            elif post.get('model') == 'sale.order':
                apps= request.env['sale.order'].browse(int(post.get('sale_id')))
                appointments = [{'regn_no': apps.regn_no.license_plate,
                                 'partner': apps.partner_id.name,
                                 'order_id': apps.id,
                                 'mobile': apps.mobile,
                                 'model': 'sale.order',
                                 'process': apps.main_process_id.name}]
        else:
            # lead_appointments = request.env['crm.lead'].search([('regn_no', 'in', get_reg.ids),('main_process_id','=',request.env.ref("ac_rms.main_process1").id)])
            # order_appointments = request.env['sale.order'].search([('regn_no', 'in', get_reg.ids), ('main_process_id', '=', request.env.ref("ac_rms.main_process20").id)])
            # appointments = lead_appointments | order_appointments
            cr = request._cr
            cr.execute("""select x.order_id
                            ,x.model
                            ,x.partner
                            ,x.regn_no
                            ,x.mobile
                            ,x.doc_name
                            ,x.app_date
                            ,x.process
                            from
                            (select cl.id as order_id
                             ,'crm.lead' as model 
                             ,rp.name as partner
                             ,fv.license_plate as regn_no
                             ,rp.mobile as mobile
                             ,cl.name as doc_name
                             ,cl.appo_date as app_date
                             ,mp.name as process
                             from crm_lead cl
                              inner join fleet_vehicle fv on fv.id = cl.regn_no
                              inner join res_partner rp on rp.id = cl.partner_id
                              inner join main_process mp on mp.id = cl.main_process_id
                              where main_process_id = %s
                              and fv.license_plate ilike %s
                              and cl.is_estimation = 'No Estimation'
                            union
                            select  so.id as order_id
                             ,'sale.order' as model 
                             ,rp.name as partner
                             ,fv.license_plate as regn_no
                             ,rp.mobile as mobile
                             ,so.name as doc_name
                             ,so.appointment_date as app_date
                             ,mp.name as process
                             from sale_order so
                              inner join fleet_vehicle fv on fv.id = so.regn_no
                              inner join res_partner rp on rp.id = so.partner_id
                              inner join main_process mp on mp.id = so.main_process_id
                             where main_process_id in %s
                             and fv.license_plate ilike %s)x""",(process1,result,(process1,process20),result,))
            appointments = cr.dictfetchall()

        template_render = ''
        if not appointments:

            vals = {
                'regno': post.get('regno')
             }
        obj = request.env['crm.lead']
        if len(appointments) > 1:
            template_render = request.render("ac_rms.security_appointment_tree", {'process':appointments[0]['process'],'appointment': appointments,'reg_num':post.get('regno')})
        elif len(appointments) == 1:
            app = appointments[0]
            appo_vals = {'regno': app['regn_no'],
                         'customer_name': app['partner'],
                         'appointment': app['order_id'],
                         'mobile': app['mobile'],
                         'model':app['model'],
                         'process':app['process']}
            template_render = request.render("ac_rms.appointment_form", appo_vals)
        else:
            template_render = request.render("ac_rms.security_walkin_form", vals)
        # template_render = request.render("ac_rms.security_login",walk_c)
        return template_render


    # Security Appointment Form
    @http.route(['/appointment_form'], type='http', auth="user", website=True, csrf=False)
    def appointment_confirm(self, **post):
        if post.get('appointment') and post.get('app_model'):
            record = ''
            current_date = fields.datetime.now()
            c = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(hours=5, minutes=30)
            current_time = (c.replace(tzinfo=pytz.utc)).strftime(DEFAULT_DATE_TIME_FORMATE)
            if post.get('app_model') == 'crm.lead':
                record = request.env['crm.lead'].browse(int(post.get('appointment')))
                if record.main_process_id == request.env.ref("ac_rms.main_process1"):
                    record.main_process_id = request.env.ref("ac_rms.main_process2").id
                    kilometer_in = ''
                    if post.get('mileage_in'):
                        kilometer_in = post.get('mileage_in')
                    record.write({'main_process_id':request.env.ref("ac_rms.main_process3").id,'cre_work_flow':'Start','kilometer_in':kilometer_in,'sec_at_gatetime':current_time,'time_at_gate':current_date.date()})
            elif post.get('app_model') == 'sale.order':
                record = request.env['sale.order'].browse(int(post.get('appointment')))
                if record.main_process_id == request.env.ref("ac_rms.main_process1"):
                    record.main_process_id = request.env.ref("ac_rms.main_process2").id
                    mileage_in = ''
                    if post.get('mileage_in'):
                        mileage_in = post.get('mileage_in')
                    record.write({'main_process_id': request.env.ref("ac_rms.main_process3").id,'cre_work_flow':'Start','gate_in_time':current_time,'time_at_gate':current_date.date(),'mileage_in':mileage_in})

                elif record.main_process_id == request.env.ref("ac_rms.main_process20"):
                    mileage_out = ''
                    if post.get('mileage_in'):
                        mileage_out = post.get('mileage_in')
                    record.write({'main_process_id':request.env.ref("ac_rms.main_process22").id,'mileage_out':mileage_out})

            # if record.main_process_id.name == 'Test Drive In':
            #     record.main_process_id = request.env['main.process'].search(
            #         [('name', '=', 'Security delivery Process')], limit=1).id


            # sale_order_obj = request.env['sale.order'].search([('opportunity_id','=',crm_record.id)])
            # if sale_order_obj:
            #     sale_order_obj.main_process_id = request.env.ref("ac_rms.main_process2").id
            #     sale_order_obj.main_process_id = request.env.ref("ac_rms.main_process3").id

        vals = {
            'confirmation_msg': 'Successful'
        }

        template_render = request.redirect('/security_login?vals=1')

        return template_render

    #Security Walkin Form
    @http.route(['/security_walkin_action'], type='http', auth="user", website=True, csrf=False)
    def walkin_confirm(self, **post):
        new_lead = request.env['crm.lead']
        company = request.env.user.company_id
        stage = company.rms_team_stage_id.id and company.rms_team_stage_id.id or ''
        vals1 = {
            # 'regn_no': post.get('regno'),
            'name': post.get('regno'),
            'stage_id':stage
            }
        walkin = new_lead.sudo().create(vals1)
        values = {
            'team_id': walkin.team_id.id,
        }
        values.update({'lead_ids': walkin})
        vals = walkin._convert_opportunity_data(walkin.partner_id,walkin.team_id.id)
        vals.update({'type_lead': 'walkin','main_process_id':request.env.ref('ac_rms.main_process2').id})
        walkin.write(vals)
        c = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(hours=5, minutes=30)
        current_time = (c.replace(tzinfo=pytz.utc)).strftime(DEFAULT_DATE_TIME_FORMATE)
        walkin.write({'kilometer_in':post.get('mileage'),'sec_at_gatetime':current_time,'main_process_id':request.env.ref('ac_rms.main_process3').id,'cre_work_flow' :'Start','appo_date':current_time})
        vals = {
            'confirmation_msg': 'Successful'
        }

        template_render = request.redirect('/security_login?vals=1')

        return template_render

    # Security Tree View To Walkin Form
    @http.route(['/security_walkin'], type='http', auth="user", website=True, csrf=False)
    def walkin_form(self, **post):
        reg = ''
        if post.get('reg_num'):
            reg = post.get('reg_num')
        vals = {
            'regno': reg

        }
        template_render = request.render("ac_rms.security_walkin_form", vals)

        return template_render

    # Security Testdrive Form
    @http.route(['/security_testdrive_action'], type='http', auth="user", website=True, csrf=False)
    def testdrive_confirm(self, **post):
        if post.get('regno'):
            record = request.env['sale.order'].search([('regn_no', '=', post.get('regno'))], limit=1)

            if record.main_process_id.name == 'Test Drive Out':
                record.main_process_id = request.env['main.process'].search([('name', '=', 'Test Drive In')],
                                                                            limit=1).id
            if record.main_process_id.name == 'Waiting at reception':
                record.main_process_id = request.env['main.process'].search([('name', '=', 'Test Drive Out')],
                                                                            limit=1).id
        vals = {
            'confirmation_msg': 'Successful'
        }
        template_render = request.redirect('/security_login?vals=1')

        return template_render

    def counts_clk(self):
        confirmation = {}
        cr = request._cr
        user = request.env.user
        userid = request.env.user.id
        company_id = request.env.user.company_id.id
        proccess_id2 = request.env.ref('ac_rms.main_process2').id
        proccess_id3 = request.env.ref('ac_rms.main_process3').id
        proccess_id4 = request.env.ref('ac_rms.main_process4').id
        proccess_id5 = request.env.ref('ac_rms.main_process5').id
        proccess_id6 = request.env.ref('ac_rms.main_process6').id
        proccess_id15 = request.env.ref('ac_rms.main_process15').id
        proccess_id16 = request.env.ref('ac_rms.main_process16').id
        main_process17 = request.env.ref('ac_rms.main_process17').id
        main_process22 = request.env.ref('ac_rms.main_process22').id

        ##Waiting at Reception & Front Desk process
        cr.execute("""select count(so.id)
                        ,array_agg(so.id) as so_ids
                        from crm_lead so
                        where so.main_process_id in %s
                        --and so.sale_aftersales = 'after_sales'
                        and so.company_id = %s
                        and so.cre_work_flow != 'Operation Done'""", ((proccess_id3,proccess_id4), company_id,))

        waiting_at_reception = cr.dictfetchall()
        at_reception_count = waiting_at_reception[0].get('count')
        at_reception_ids = waiting_at_reception[0].get('so_ids')
        at_reception_browse = request.env['crm.lead'].browse(at_reception_ids)

        ##Waiting For SA & SO Preparation Process
        # cr.execute("""select count(so.id)
        #                 ,array_agg(so.id) as so_ids
        #                 from crm_lead so
        #                 where so.main_process_id in %s
        #                 --and so.sale_aftersales = 'after_sales'
        #                 and so.user_id = %s
        #                 and so.company_id = %s""", ((proccess_id5,proccess_id6),userid, company_id,))

        cr.execute("""select x.counts
                        ,x.cl_ids
                        ,x.model
                        from
                        (select count(cl.id) as counts
                        ,array_agg(cl.id) as cl_ids
                        ,'crm_lead' as model
                        from crm_lead cl
                        where cl.main_process_id in %s
                        and cl.company_id = %s
                        and cl.sa_work_flow != 'Operation Done'
                        and cl.user_id = %s
                        and cl.is_estimation != 'Estimation'
                        union
                        select count(so.id) as counts
                        ,array_agg(so.id) as cl_ids
                        ,'sale_order' as model
                        from sale_order so
                        where so.main_process_id in %s
                        and so.company_id = %s
                        and so.sa_work_flow != 'Operation Done'
                        and so.user_id = %s)x""", ((proccess_id5,proccess_id6),company_id,userid, (proccess_id5,proccess_id6),company_id,userid,))
        waiting_for_sa = cr.dictfetchall()
        sa_count = 0
        sa_records = []
        for sa in waiting_for_sa:
            sa_count += sa.get('counts')
            if sa.get('cl_ids'):
                for sa_id in sa.get('cl_ids'):
                    sa_records.append(str(sa_id)+ '#'+sa.get('model'))
            # else:
            #     pass
        sa_records.append(sa_count)
        waiting_for_sa_count = sa_records[-1]
        waiting_for_sa_ids = sa_records[0:-1]
        #TO DO
        # at_sa_browse = request.env['crm.lead'].browse(waiting_for_sa_ids)

        ##FI Process Waiting & FI In Progress
        cr.execute("""select count(so.id)
                        ,array_agg(so.id) as so_ids
                        from sale_order so
                        where so.main_process_id in %s
                        and so.sale_aftersales = 'after_sales'
                        and so.company_id = %s""", ((proccess_id15,proccess_id16), company_id,))

        fi_process = cr.dictfetchall()
        fi_process_count = fi_process[0].get('count')
        fi_process_ids = fi_process[0].get('so_ids')
        fi_browse = request.env['sale.order'].browse(fi_process_ids)

        cr.execute("""select 
                        x.order_id
                        ,x.model
                        ,x.regno
                        ,x.customer
                        ,x.mobile
                        ,x.typevehicle
                        ,x.gatetime
                        ,x.kilometer
                        ,x.roname
                        ,x.appdate
                        ,x.deliverydate
                        ,x.serviceadvisor
                        ,x.delivery_service_advisor
                        ,x.cre_stage
                        ,x.type
                        from
                        (select cl.id as order_id
                        ,'crm.lead' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,cl.mobile as mobile
                        ,cl.type_lead as typevehicle
                        ,cl.sec_at_gatetime as gatetime
                        ,cl.kilometer_in as kilometer
                        ,cl.name as roname
                        ,cl.appo_date as appdate
                        ,cl.delivery_time as deliverydate
                        ,cl.user_id as serviceadvisor
                        ,cl.delivery_service_advisor as delivery_service_advisor
                        ,cl.cre_work_flow as cre_stage
                        ,cl.type_lead as type
                        from crm_lead cl
                        inner join fleet_vehicle fv on fv.id = cl.regn_no
                        inner join res_partner rp on rp.id = cl.partner_id
                        where cl.main_process_id in %s
                        and cl.company_id = %s
                        and cl.cre_work_flow != 'Operation Done'
                        and cl.is_estimation != 'Estimation'
                        union
                        select	so.id as order_id
                        ,'sale.order' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mobile as mobile
                        ,so.doc_type as typevehicle
                        ,so.gate_in_time as gatetime
                        ,so.mileage_in as kilometer
                        ,so.name as roname
                        ,so.appointment_date as appdate
                        ,so.delivery_date as deliverydate
                        ,so.user_id as serviceadvisor
                        ,so.delivery_service_advisor as delivery_service_advisor
                        ,so.cre_work_flow as cre_stage
                        ,so.doc_type as type
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.main_process_id in %s
                        and so.company_id = %s
                        and so.cre_work_flow != 'Operation Done')x""", ((proccess_id3,proccess_id4), company_id,(proccess_id3,proccess_id4),company_id,))

        cre_process = cr.dictfetchall()
        cre_process_len = len(cre_process)
        cre_app = []
        cre_walkin = []
        for record in cre_process:
            if record.get('type') == 'appointment':
                cre_app.append(record)
            elif record.get('type') == 'walkin':
                cre_walkin.append(record)
        cre_app_count = len(cre_app)
        cre_walkin_count = len(cre_walkin)

        cr.execute("""select x.order_id
                        ,x.model
                        ,x.regno
                        ,x.customer
                        ,x.mobile
                        ,x.typevehicle
                        ,x.gatetime
                        ,x.kilometer
                        ,x.roname
                        ,x.appdate
                        ,x.deliverydate
                        ,x.serviceadvisor
                        ,x.delivery_service_advisor
                        ,x.sa_stage
                        ,x.type
                        from
                        (select cl.id as order_id
                        ,'crm.lead' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,cl.mobile as mobile
                        ,cl.type_lead as typevehicle
                        ,cl.sec_at_gatetime as gatetime
                        ,cl.kilometer_in as kilometer
                        ,cl.name as roname
                        ,cl.appo_date as appdate
                        ,cl.delivery_time as deliverydate
                        ,cl.user_id as serviceadvisor
                        ,cl.delivery_service_advisor as delivery_service_advisor
                        ,cl.sa_work_flow as sa_stage
                        ,cl.type_lead as type
                        from crm_lead cl
                        inner join fleet_vehicle fv on fv.id = cl.regn_no
                        inner join res_partner rp on rp.id = cl.partner_id
                        where cl.main_process_id in %s
                        and cl.company_id = %s
                        and cl.sa_work_flow != 'Operation Done'
                        and cl.user_id = %s
                        and cl.is_estimation != 'Estimation'
                        union
                        select so.id as order_id
                        ,'sale.order' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mobile as mobile
                        ,so.doc_type as typevehicle
                        ,so.gate_in_time as gatetime
                        ,so.mileage_in as kilometer
                        ,so.name as roname
                        ,so.appointment_date as appdate
                        ,so.delivery_date as deliverydate
                        ,so.user_id as serviceadvisor
                        ,so.delivery_service_advisor as delivery_service_advisor
                        ,so.sa_work_flow as sa_stage
                        ,so.doc_type as type
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.main_process_id in %s
                        and so.company_id = %s
                        and so.sa_work_flow != 'Operation Done'
                        and so.user_id = %s)x""", (
                        (proccess_id5, proccess_id6), company_id, userid, (proccess_id5, proccess_id6), company_id,userid,))

        sa_process = cr.dictfetchall()
        sa_process_len = len(sa_process)
        sa_app = []
        sa_walkin = []
        for pro in sa_process:
            if pro.get('type') == 'appointment':
                sa_app.append(pro)
            elif pro.get('type') == 'walkin':
                sa_walkin.append(pro)
        sa_app_count = len(sa_app)
        sa_walkin_count = len(sa_walkin)

        cr.execute("""select x.order_id
                                ,x.model
                                ,x.regno
                                ,x.customer
                                ,x.mobile
                                ,x.typevehicle
                                ,x.gatetime
                                ,x.kilometer
                                ,x.roname
                                ,x.appdate
                                ,x.deliverydate
                                ,x.serviceadvisor
                                ,x.delivery_service_advisor
                                ,x.sa_stage
                                ,x.type
                                from
                                (select cl.id as order_id
                                ,'crm.lead' as model
                                ,fv.license_plate as regno
                                ,rp.name as customer
                                ,cl.mobile as mobile
                                ,cl.type_lead as typevehicle
                                ,cl.sec_at_gatetime as gatetime
                                ,cl.kilometer_in as kilometer
                                ,cl.name as roname
                                ,cl.appo_date as appdate
                                ,cl.delivery_time as deliverydate
                                ,cl.user_id as serviceadvisor
                                ,cl.delivery_service_advisor as delivery_service_advisor
                                ,cl.sa_work_flow as sa_stage
                                ,cl.type_lead as type
                                from crm_lead cl
                                inner join fleet_vehicle fv on fv.id = cl.regn_no
                                inner join res_partner rp on rp.id = cl.partner_id
                                where cl.main_process_id in %s
                                and cl.company_id = %s
                                and cl.sa_work_flow != 'Operation Done'
                                and cl.is_estimation != 'Estimation'
                                union
                                select so.id as order_id
                                ,'sale.order' as model
                                ,fv.license_plate as regno
                                ,rp.name as customer
                                ,so.mobile as mobile
                                ,so.doc_type as typevehicle
                                ,so.gate_in_time as gatetime
                                ,so.mileage_in as kilometer
                                ,so.name as roname
                                ,so.appointment_date as appdate
                                ,so.delivery_date as deliverydate
                                ,so.user_id as serviceadvisor
                                ,so.delivery_service_advisor as delivery_service_advisor
                                ,so.sa_work_flow as sa_stage
                                ,so.doc_type as type
                                from sale_order so
                                inner join fleet_vehicle fv on fv.id = so.regn_no
                                inner join res_partner rp on rp.id = so.partner_id
                                where so.main_process_id in %s
                                and so.company_id = %s
                                and so.sa_work_flow != 'Operation Done'
                                )x""", (
            (proccess_id5, proccess_id6), company_id,(proccess_id5, proccess_id6), company_id,))

        cre_sa_process = cr.dictfetchall()
        cre_sa_process_len = len(cre_sa_process)

        cr.execute("""select x.order_id
                                ,x.model
                                ,x.regno
                                ,x.customer
                                ,x.mobile
                                ,x.typevehicle
                                ,x.gatetime
                                ,x.kilometer
                                ,x.roname
                                ,x.appdate
                                ,x.deliverydate
                                ,x.serviceadvisor
                                ,x.delivery_service_advisor
                                ,x.sa_stage
                                ,x.type
                                from
                                (select cl.id as order_id
                                ,'crm.lead' as model
                                ,fv.license_plate as regno
                                ,rp.name as customer
                                ,cl.mobile as mobile
                                ,cl.type_lead as typevehicle
                                ,cl.sec_at_gatetime as gatetime
                                ,cl.kilometer_in as kilometer
                                ,cl.name as roname
                                ,cl.appo_date as appdate
                                ,cl.delivery_time as deliverydate
                                ,cl.user_id as serviceadvisor
                                ,cl.delivery_service_advisor as delivery_service_advisor
                                ,cl.sa_work_flow as sa_stage
                                ,cl.type_lead as type
                                from crm_lead cl
                                inner join fleet_vehicle fv on fv.id = cl.regn_no
                                inner join res_partner rp on rp.id = cl.partner_id
                                where cl.main_process_id in %s
                                and cl.company_id = %s
                                and cl.sa_work_flow != 'Operation Done'
                                and cl.is_estimation != 'Estimation'
                                and cl.user_id = %s
                                union
                                select so.id as order_id
                                ,'sale.order' as model
                                ,fv.license_plate as regno
                                ,rp.name as customer
                                ,so.mobile as mobile
                                ,so.doc_type as typevehicle
                                ,so.gate_in_time as gatetime
                                ,so.mileage_in as kilometer
                                ,so.name as roname
                                ,so.appointment_date as appdate
                                ,so.delivery_date as deliverydate
                                ,so.user_id as serviceadvisor
                                ,so.delivery_service_advisor as delivery_service_advisor
                                ,so.sa_work_flow as sa_stage
                                ,so.doc_type as type
                                from sale_order so
                                inner join fleet_vehicle fv on fv.id = so.regn_no
                                inner join res_partner rp on rp.id = so.partner_id
                                where so.main_process_id in %s
                                and so.company_id = %s
                                and so.sa_work_flow != 'Operation Done'
                                and so.user_id = %s
                                )x""", (
            (proccess_id5, proccess_id6), company_id,userid,(proccess_id5, proccess_id6), company_id,userid,))

        waitingsa_process = cr.dictfetchall()
        waitingsa_process_len = len(waitingsa_process)




        cr.execute("""select count(so.id),
                        array_agg(so.id) as wk_ids
                        from sale_order so
                        where so.main_process_id = %s
                        and so.company_id = %s
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date
                     """,(main_process22,company_id,))
        delivery_process = cr.dictfetchall()
        delivery_process_len = delivery_process[0].get('count')
        delivery_process_count = delivery_process[0].get('count')
        delivery_process_ids = delivery_process[0].get('wk_ids')
        delivery_process_browse = request.env['crm.lead'].browse(delivery_process_ids)

        confirmation.update({'waiting_at_reception_count': at_reception_count,
                             'waiting_at_reception_ids': at_reception_ids,
                             'waiting_at_reception_browse': at_reception_browse,
                             'waiting_for_sa_count': waiting_for_sa_count,
                             'waiting_for_sa_ids': waiting_for_sa_ids,
                             'waiting_for_sa_browse': True,
                             'fi_process_count': fi_process_count,
                             'fi_process_ids': fi_process_ids,
                             'fi_process_browse': fi_browse,
                             'cre_dashboard_data':cre_process,
                             'sa_dashboard_data':sa_process,
                             'cre_process_len':cre_process_len,
                             'cre_process':cre_process,
                             'sa_process_len': sa_process_len,
                             'delivery_process_len':delivery_process_len,
                             'cre_app_count':cre_app_count,
                             'cre_app':cre_app,
                             'cre_walkin':cre_walkin,
                             'cre_walkin_count': cre_walkin_count,
                             'sa_process':sa_process,
                             'sa_app_count': sa_app_count,
                             'sa_app':sa_app,
                             'sa_walkin':sa_walkin,
                             'sa_walkin_count': sa_walkin_count,
                             'cre_sa_process_len':cre_sa_process_len,
                             'cre_sa_process':cre_sa_process,
                             'waitingsa_process':waitingsa_process,
                             'delivery_process_count': delivery_process_count,
                             'delivery_process_ids': delivery_process_ids,
                             'delivery_process_browse': delivery_process_browse,
                             })
        ## Security Front Page all count
        cr.execute("""select count(so.id),
                                array_agg(so.id) as wk_ids
                                from crm_lead so
                                where so.type_lead = 'walkin'
                                and so.company_id = %s
                                and to_char((so.appo_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date""",
                   (company_id,))

        walkin1 = cr.dictfetchall()
        walkin1_count = walkin1[0].get('count')
        walkin1_ids = walkin1[0].get('wk_ids')

        cr.execute("""select 
                            cl.id as order_id
                            ,'crm.lead' as model
                            ,cl.mobile as mobile
                            ,cl.type_lead as typevehicle
                            ,cl.sec_at_gatetime as gatetime
                            ,cl.kilometer_in as kilometer
                            ,cl.name as roname
                            ,cl.appo_date as appdate
                            ,cl.delivery_time as deliverydate
                            ,cl.user_id as serviceadvisor
                            ,cl.delivery_service_advisor as delivery_service_advisor
                            ,cl.cre_work_flow as cre_stage
                            ,cl.type_lead as type
                            from crm_lead cl
                            where cl.type_lead = 'walkin'
                            and cl.company_id = %s
                            and to_char((cl.appo_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date
                            """, (company_id,))

        walkin_click = cr.dictfetchall()

        cr.execute("""select count(so.id),
                                        array_agg(so.id) as so_ids
                                        from crm_lead so
                                        where so.type_lead = 'appointment'
                                        and so.type = 'opportunity'
                                        and so.company_id = %s
                                        and to_char((so.appo_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date""",
                   (company_id,))

        app = cr.dictfetchall()
        app_count = app[0].get('count')
        app_ids = app[0].get('so_ids')

        cr.execute("""select 
                        x.order_id
                        ,x.model
                        ,x.regno
                        ,x.customer
                        ,x.mobile
                        ,x.typevehicle
                        ,x.gatetime
                        ,x.kilometer
                        ,x.roname
                        ,x.appdate
                        ,x.deliverydate
                        ,x.serviceadvisor
                        ,x.delivery_service_advisor
                        ,x.cre_stage
                        ,x.type
                        from
                        (select cl.id as order_id
                        ,'crm.lead' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,cl.mobile as mobile
                        ,cl.type_lead as typevehicle
                        ,cl.sec_at_gatetime as gatetime
                        ,cl.kilometer_in as kilometer
                        ,cl.name as roname
                        ,cl.appo_date as appdate
                        ,cl.delivery_time as deliverydate
                        ,cl.user_id as serviceadvisor
                        ,cl.delivery_service_advisor as delivery_service_advisor
                        ,cl.cre_work_flow as cre_stage
                        ,cl.type_lead as type
                        from crm_lead cl
                        inner join fleet_vehicle fv on fv.id = cl.regn_no
                        inner join res_partner rp on rp.id = cl.partner_id
                        where cl.company_id = %s
                        and cl.is_estimation != 'Estimation'
                        and cl.type_lead = 'appointment'
                        and to_char((cl.appo_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date
                        union
                        select so.id as order_id
                        ,'sale.order' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mobile as mobile
                        ,so.doc_type as typevehicle
                        ,so.gate_in_time as gatetime
                        ,so.mileage_in as kilometer
                        ,so.name as roname
                        ,so.appointment_date as appdate
                        ,so.delivery_date as deliverydate
                        ,so.user_id as serviceadvisor
                        ,so.delivery_service_advisor as delivery_service_advisor
                        ,so.sa_work_flow as sa_stage
                        ,so.doc_type as type
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.company_id = %s
                        and so.doc_type = 'appointment'
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date)x
                        """,(company_id,company_id,))

        app_click = cr.dictfetchall()

        cr.execute("""select 
                        x.regno
                        ,x.customer
                        ,x.kilometer
                        from
                        (select fv.license_plate as regno
                        ,rp.name as customer
                        ,cl.kilometer_in as kilometer
                        from crm_lead cl
                        inner join fleet_vehicle fv on fv.id = cl.regn_no
                        inner join res_partner rp on rp.id = cl.partner_id
                        where cl.company_id = %s
                        and cl.is_estimation != 'Estimation'
                        and cl.type_lead = 'appointment'
                        and to_char((cl.appo_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date
                        union
                        select fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mileage_in as kilometer
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.company_id = %s
                        and so.doc_type = 'appointment'
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date)x
                                          """,(company_id,company_id,))

        app_security_click = cr.dictfetchall()

        cr.execute("""select 
                        x.regno
                        ,x.customer
                        ,x.kilometer
                        from
                        (select fv.license_plate as regno
                        ,rp.name as customer
                        ,cl.kilometer_in as kilometer
                        from crm_lead cl
                        inner join fleet_vehicle fv on fv.id = cl.regn_no
                        inner join res_partner rp on rp.id = cl.partner_id
                        where cl.company_id = %s
                        and cl.time_at_gate = now()::date
                        and cl.is_estimation != 'Estimation'
                        union
                        select fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mileage_in as kilometer
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.company_id = %s
                        and so.time_at_gate = now()::date)x
                        """, (company_id, company_id,))

        turnup_security_click = cr.dictfetchall()

        cr.execute("""select 
                        x.order_id
                        ,x.model
                        ,x.regno
                        ,x.customer
                        ,x.mobile
                        ,x.typevehicle
                        ,x.gatetime
                        ,x.kilometer
                        ,x.roname
                        ,x.appdate
                        ,x.deliverydate
                        ,x.serviceadvisor
                        ,x.delivery_service_advisor
                        ,x.cre_stage
                        ,x.type
                        from
                        (select cl.id as order_id
                        ,'crm.lead' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,cl.mobile as mobile
                        ,cl.type_lead as typevehicle
                        ,cl.sec_at_gatetime as gatetime
                        ,cl.kilometer_in as kilometer
                        ,cl.name as roname
                        ,cl.appo_date as appdate
                        ,cl.delivery_time as deliverydate
                        ,cl.user_id as serviceadvisor
                        ,cl.delivery_service_advisor as delivery_service_advisor
                        ,cl.cre_work_flow as cre_stage
                        ,cl.type_lead as type
                        from crm_lead cl
                        inner join fleet_vehicle fv on fv.id = cl.regn_no
                        inner join res_partner rp on rp.id = cl.partner_id
                        where cl.company_id = %s
                        and cl.time_at_gate = now()::date
                        and cl.is_estimation != 'Estimation'
                        union
                        select so.id as order_id
                        ,'sale.order' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mobile as mobile
                        ,so.doc_type as typevehicle
                        ,so.gate_in_time as gatetime
                        ,so.mileage_in as kilometer
                        ,so.name as roname
                        ,so.appointment_date as appdate
                        ,so.delivery_date as deliverydate
                        ,so.user_id as serviceadvisor
                        ,so.delivery_service_advisor as delivery_service_advisor
                        ,so.sa_work_flow as sa_stage
                        ,so.doc_type as type
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.company_id = %s
                        and so.time_at_gate = now()::date)x
                    """,(company_id,company_id,))

        turnup_click = cr.dictfetchall()

        cr.execute("""select so.id as order_id
                        ,'sale.order' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mobile as mobile
                        ,so.doc_type as typevehicle
                        ,so.gate_in_time as gatetime
                        ,so.mileage_in as kilometer
                        ,so.name as roname
                        ,so.appointment_date as appdate
                        ,so.delivery_date as deliverydate
                        ,so.user_id as serviceadvisor
                        ,so.delivery_service_advisor as delivery_service_advisor
                        ,so.sa_work_flow as sa_stage
                        ,so.doc_type as type
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.company_id = %s
                        and so.main_process_id = %s
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date
                    """,(company_id,main_process22,))

        delivered_click = cr.dictfetchall()

        cr.execute("""select so.id as order_id
                        ,'sale.order' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mobile as mobile
                        ,so.doc_type as typevehicle
                        ,so.gate_in_time as gatetime
                        ,so.mileage_in as kilometer
                        ,so.name as roname
                        ,so.appointment_date as appdate
                        ,so.delivery_date as deliverydate
                        ,so.user_id as serviceadvisor
                        ,so.delivery_service_advisor as delivery_service_advisor
                        ,so.sa_work_flow as sa_stage
                        ,so.doc_type as type
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.company_id = %s
                        and so.state = 'cancel'
                        and so.sale_aftersales = 'after_sales'
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = now()::date
                        """,(company_id,))

        cancel_click = cr.dictfetchall()
        len_cancel_click = len(cancel_click)

        cr.execute("""select 
                        x.order_id
                        ,x.model
                        ,x.regno
                        ,x.customer
                        ,x.mobile
                        ,x.typevehicle
                        ,x.gatetime
                        ,x.kilometer
                        ,x.roname
                        ,x.appdate
                        ,x.deliverydate
                        ,x.serviceadvisor
                        ,x.delivery_service_advisor
                        ,x.cre_stage
                        ,x.type
                        from
                        (select cl.id as order_id
                        ,'crm.lead' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,cl.mobile as mobile
                        ,cl.type_lead as typevehicle
                        ,cl.sec_at_gatetime as gatetime
                        ,cl.kilometer_in as kilometer
                        ,cl.name as roname
                        ,cl.appo_date as appdate
                        ,cl.delivery_time as deliverydate
                        ,cl.user_id as serviceadvisor
                        ,cl.delivery_service_advisor as delivery_service_advisor
                        ,cl.cre_work_flow as cre_stage
                        ,cl.type_lead as type
                        from crm_lead cl
                        inner join fleet_vehicle fv on fv.id = cl.regn_no
                        inner join res_partner rp on rp.id = cl.partner_id
                        where cl.company_id = %s
                        and cl.is_estimation != 'Estimation'
                        and cl.type_lead = 'appointment'
                        union
                        select so.id as order_id
                        ,'sale.order' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mobile as mobile
                        ,so.doc_type as typevehicle
                        ,so.gate_in_time as gatetime
                        ,so.mileage_in as kilometer
                        ,so.name as roname
                        ,so.appointment_date as appdate
                        ,so.delivery_date as deliverydate
                        ,so.user_id as serviceadvisor
                        ,so.delivery_service_advisor as delivery_service_advisor
                        ,so.sa_work_flow as sa_stage
                        ,so.doc_type as type
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.company_id = %s
                        and so.doc_type = 'appointment')x
                            
                            """,(company_id,company_id,))

        app_till_click = cr.dictfetchall()
        len_app_till_click = len(app_till_click)

        cr.execute("""select so.id as order_id
                        ,'sale.order' as model
                        ,fv.license_plate as regno
                        ,rp.name as customer
                        ,so.mobile as mobile
                        ,so.doc_type as typevehicle
                        ,so.gate_in_time as gatetime
                        ,so.mileage_in as kilometer
                        ,so.name as roname
                        ,so.appointment_date as appdate
                        ,so.delivery_date as deliverydate
                        ,so.user_id as serviceadvisor
                        ,so.delivery_service_advisor as delivery_service_advisor
                        ,so.sa_work_flow as sa_stage
                        ,so.doc_type as type
                        from sale_order so
                        inner join fleet_vehicle fv on fv.id = so.regn_no
                        inner join res_partner rp on rp.id = so.partner_id
                        where so.company_id = %s
                        and so.main_process_id = %s
                        and so.sale_aftersales = 'after_sales'
                        """, (company_id,request.env.ref("ac_rms.main_process10").id, ))

        wip_click = cr.dictfetchall()
        len_wip_click = len(wip_click)

        cr.execute("""select so.id as order_id
                                ,'sale.order' as model
                                ,fv.license_plate as regno
                                ,rp.name as customer
                                ,so.mobile as mobile
                                ,so.doc_type as typevehicle
                                ,so.gate_in_time as gatetime
                                ,so.mileage_in as kilometer
                                ,so.name as roname
                                ,so.appointment_date as appdate
                                ,so.delivery_date as deliverydate
                                ,so.user_id as serviceadvisor
                                ,so.delivery_service_advisor as delivery_service_advisor
                                ,so.sa_work_flow as sa_stage
                                ,so.doc_type as type
                                ,so.sa_work_flow as sa_stage
                                from sale_order so
                                inner join fleet_vehicle fv on fv.id = so.regn_no
                                inner join res_partner rp on rp.id = so.partner_id
                                where so.company_id = %s
                                and so.main_process_id = %s
                                and so.sale_aftersales = 'after_sales'
                                """, (company_id, request.env.ref("ac_rms.main_process17").id,))

        waiting_for_delivery_click = cr.dictfetchall()
        len_waiting_for_delivery_click = len(waiting_for_delivery_click)

        cr.execute("""select so.id as order_id
                                        ,'sale.order' as model
                                        ,fv.license_plate as regno
                                        ,rp.name as customer
                                        ,so.mobile as mobile
                                        ,so.doc_type as typevehicle
                                        ,so.gate_in_time as gatetime
                                        ,so.mileage_in as kilometer
                                        ,so.name as roname
                                        ,so.appointment_date as appdate
                                        ,so.delivery_date as deliverydate
                                        ,so.user_id as serviceadvisor
                                        ,so.delivery_service_advisor as delivery_service_advisor
                                        ,so.sa_work_flow as sa_stage
                                        ,so.doc_type as type
                                        from sale_order so
                                        inner join fleet_vehicle fv on fv.id = so.regn_no
                                        inner join res_partner rp on rp.id = so.partner_id
                                        where so.company_id = %s
                                        and so.main_process_id = %s
                                        and so.sale_aftersales = 'after_sales'
                                        """, (company_id, request.env.ref("ac_rms.main_process11").id,))

        hold_click = cr.dictfetchall()
        len_hold_click = len(hold_click)

        cr.execute("""select count(distinct(cl.id)),array_agg(distinct(cl.id)) as cl_ids
                    from crm_lead cl
                    where cl.time_at_gate = now()::date
                    and cl.company_id = %s """,(company_id,))



        turnup = cr.dictfetchall()
        turnup_count = turnup[0].get('count')
        turnup_ids = turnup[0].get('cl_ids')

        confirmation.update({'walk_in_count': walkin1_count,
                             'walk_in_ids': walkin1_ids,
                             'app_count': app_count,
                             'app_ids': app_ids,
                             'app_click':app_click,
                             'turnup_count': turnup_count,
                             'turnup_ids': turnup_ids,
                             'turnup_click':turnup_click,
                             'delivered_click':delivered_click,
                             'app_len':len(app_click),
                             'turnup_len':len(turnup_click),
                             'app_security_click':app_security_click,
                             'turnup_security_click':turnup_security_click,
                             'walkin_click':walkin_click,
                             'cancel_click':cancel_click,
                             'len_cancel_click':len_cancel_click,
                             'app_till_click':app_till_click,
                             'len_app_till_click':len_app_till_click,
                             'wip_click':wip_click,
                             'len_wip_click':len_wip_click,
                             'waiting_for_delivery_click': waiting_for_delivery_click,
                             'len_waiting_for_delivery_click': len_waiting_for_delivery_click,
                             'hold_click': hold_click,
                             'len_hold_click': len_hold_click
                             })

        return confirmation

    @http.route(['/security_action_clk'], type='http', auth="user", website=True, csrf=False)
    def security_action_clk(self, **post):
        vals = self.counts_clk()
        # print 'post', post
        if post.get('app_ids_nm'):
            html_txt = ''

            # app_ids = request.env['crm.lead'].browse(eval(post.get('app_ids_nm')))
            for index,app in enumerate(eval(post.get('app_ids_nm'))):
                index += 1
                html = '<tr>'
                html += '<td width="17%" style="border:1px solid grey;">'+ str(index) + '</td>'
                html += '<td width="17%" style="border:1px solid grey;">'+app["regno"]+'</td>'
                html += '<td width="17%" style="border:1px solid grey;">' + str(app["kilometer"]) + '</td>'
                html += '<td width="17%" style="border:1px solid grey;">' + app["customer"] + '</td>'
                html += '</tr>'
                html_txt += html

            vals.update(
                {'clk_type': 'app', 'type': 'not_walkin', 'gate_in_out_type': 'in', 'color': '#bf5cb9;','app_data':html_txt})

        if post.get('turnup_ids_nm'):
            # app_ids = request.env['crm.lead'].browse(eval(post.get('turnup_ids_nm')))
            html_txt = ''

            # app_ids = request.env['crm.lead'].browse(eval(post.get('app_ids_nm')))
            for index, app in enumerate(eval(post.get('turnup_ids_nm'))):
                index += 1
                html = '<tr>'
                html += '<td width="17%" style="border:1px solid grey;">' + str(index) + '</td>'
                html += '<td width="17%" style="border:1px solid grey;">' + app["regno"] + '</td>'
                html += '<td width="17%" style="border:1px solid grey;">' + str(app["kilometer"]) + '</td>'
                html += '<td width="17%" style="border:1px solid grey;">' + app["customer"] + '</td>'
                html += '</tr>'
                html_txt += html
            vals.update({'clk_type': 'turnup', 'type': 'not_walkin', 'gate_in_out_type': 'in', 'color': '#f5474d;', 'app_data': html_txt})

        if post.get('walk_in_nm'):
            app_ids1 = request.env['crm.lead'].browse(eval(post.get('walk_in_nm')))
            vals.update({'clk_type': 'walkin', 'type': 'walkin', 'gate_in_out_type': 'in', 'color': '#27b94d;',
                         'ids': app_ids1,'model':'crm_lead'})


        if post.get('delivered_ids_nm'):
            app_ids = request.env['sale.order'].browse(eval(post.get('delivered_ids_nm')))
            vals.update({'clk_type': 'delivered', 'type': 'not_walkin', 'gate_in_out_type': 'out', 'color': '#ff9c33;',
                         'ids': app_ids,'model':'sale_order'})
        #
        # if post.get('testdrive_ids_nm'):
        #     app_ids = request.env['vehicle.testing'].browse(eval(post.get('testdrive_ids_nm')))
        #     vals.update({'type': 'testdrive', 'color': '#2ec3c6;', 'ids': app_ids})

        return request.render("ac_rms.security_login", vals)

    def advisor_name(self,advisor):
        if advisor:
            user = request.env["res.users"].browse(advisor)
            partner = user.partner_id.name
        return partner


    ####CRE Login######
    @http.route(['/cre_login'], type='json', auth="public", website=True, csrf=False)
    def cre_login(self, **post):
        vals = {}
        estimate_tree = request.env.ref('ars_after_sales.action_quotations_inherit').id
        vals.update(self.counts_clk())
        process_id3 = request.env.ref('ac_rms.main_process3')
        process_id4 = request.env.ref('ac_rms.main_process4')
        # pending_task_object = vals.get('waiting_at_reception_browse')
        pending_task_object = vals.get('cre_dashboard_data')
        html_txt = ''
        blank_txt = ''
        # pend_task = ''
        for indx,pend_task in enumerate(pending_task_object):
            appo_time = ''
            deli_time = ''
            sec_gate_time = ''
            resource = ''
            delivery_sa = ''
            regn = pend_task.get('regno') if pend_task.get('regno') else blank_txt
            customer = pend_task.get('customer') if pend_task.get('customer') else blank_txt
            mobile = pend_task.get('mobile') if pend_task.get('mobile') else blank_txt
            type = pend_task.get('typevehicle') if pend_task.get('typevehicle') else blank_txt
            kilometer = pend_task.get('kilometer') if pend_task.get('kilometer') else blank_txt
            roname = pend_task.get('roname') if pend_task.get('roname') else blank_txt
            if pend_task.get('gatetime'):
                sec_gate_time =  (datetime.strptime(pend_task.get('gatetime'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                # sec_gate_time = (datetime.strptime(gate_time, "%Y-%m-%d")).strftime("%Y-%m-%d")
            # start_time = pend_task.appo_date if pend_task.appo_date else blank_txt
            if pend_task.get('appdate'):
                appo_time = (datetime.strptime(pend_task.get('appdate'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)).strftime( "%Y-%m-%d %H:%M:%S")
            # end_time = pend_task.delivery_time if pend_task.delivery_time else blank_txt
            if pend_task.get('deliverydate'):
                deli_time = (datetime.strptime(pend_task.get('deliverydate'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            if pend_task.get('serviceadvisor'):
                resource = self.advisor_name(pend_task.get('serviceadvisor'))
            if pend_task.get('delivery_service_advisor'):
                delivery_sa = self.advisor_name(pend_task.get('delivery_service_advisor'))
            # resource = pend_task.get('serviceadvisor') if pend_task.get('serviceadvisor') else blank_txt
            # delivery_sa = pend_task.get('delivery_service_advisor') if pend_task.get('delivery_service_advisor') else blank_txt
            html_txt += '<tr style="border:1px solid black;cursor:pointer;" class="modal_rows_task">'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">'+str(indx+1)+'</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;"><input type="text" id="click_form_id" class="hidden" value="'+str(pend_task.get('order_id'))+'" name="regno"/><input type="text" id="click_form_model" class="hidden" value="'+str(pend_task.get('model'))+'" name="model"/>'+regn+'</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' +customer+ '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + mobile + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + type + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + sec_gate_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(kilometer) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + roname + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + appo_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + deli_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + resource + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + delivery_sa + '</td>'
            # if pend_task.main_process_id == process_id3:
            html_txt += '<td  class="process" style="border:1px solid grey;text-align: center;height: 37px;">'
            if pend_task.get('cre_stage') == 'Start':
                html_txt += '<button style="height: 20px;width: 41px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_start_submit" id="cre_start">Start<span class="order_id" style="display: none;">'+str(pend_task.get('order_id'))+'</span><span class="form_model"  style="display: none;">'+str(pend_task.get('model'))+'</span></button>'

            if pend_task.get('cre_stage') == 'Finish':
                html_txt += '<button style="height: 20px;width: 41px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Finish<span class="order_id" style="display: none;">'+str(pend_task.get('order_id'))+'</span><span class="form_model"  style="display: none;">'+str(pend_task.get('model'))+'</span></button>'
            html_txt += '</td></tr>'
        if vals.get('waiting_at_reception_browse'):
            vals.update(
                {'color': '#bf5cb9;', 'ids': vals.get('waiting_at_reception_browse'),'tree': estimate_tree,'html_txt': html_txt})
            if pending_task_object:
                if pend_task:
                    vals.update({'model': pend_task.get('model')})
        return {'count_mytask': vals}

    @http.route(['/single_image_click'], type='json', auth="public", website=True, csrf=False)
    def single_image_click(self, **post):
        vals = {}
        cre_all_app = ''
        vals.update(self.counts_clk())
        if post.get('text'):
            if post.get('text') == 'app':
                cre_all_task = vals.get('cre_app')
            elif post.get('text') == 'my_task':
                cre_all_task = vals.get('cre_process')
            elif post.get('text') == 'walkin':
                cre_all_task = vals.get('cre_walkin')
            elif post.get('text') == 'sa_app':
                cre_all_task = vals.get('sa_app')
            elif post.get('text') == 'sa_my_task':
                cre_all_task = vals.get('sa_process')
            elif post.get('text') == 'sa_walkin':
                cre_all_task = vals.get('sa_walkin')
            elif post.get('text') == 'sa_waiting':
                cre_all_task = vals.get('waitingsa_process')
            elif post.get('text') == 'cre_sa_process':
                cre_all_task = vals.get('cre_sa_process')



        html_txt = ''
        blank_txt = ''
        for indx, pend_task in enumerate(cre_all_task):
            appo_time = ''
            deli_time = ''
            sec_gate_time = ''
            resource = ''
            delivery_sa = ''
            regn = pend_task.get('regno') if pend_task.get('regno') else blank_txt
            customer = pend_task.get('customer') if pend_task.get('customer') else blank_txt
            mobile = pend_task.get('mobile') if pend_task.get('mobile') else blank_txt
            type = pend_task.get('typevehicle') if pend_task.get('typevehicle') else blank_txt
            kilometer = pend_task.get('kilometer') if pend_task.get('kilometer') else blank_txt
            roname = pend_task.get('roname') if pend_task.get('roname') else blank_txt

            if pend_task.get('gatetime'):
                sec_gate_time = (datetime.strptime(pend_task.get('gatetime'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,
                                                                                                               minutes=30)).strftime(
                    "%Y-%m-%d %H:%M:%S")
                # sec_gate_time = (datetime.strptime(gate_time, "%Y-%m-%d")).strftime("%Y-%m-%d")
            # start_time = pend_task.appo_date if pend_task.appo_date else blank_txt
            if pend_task.get('appdate'):
                appo_time = (datetime.strptime(pend_task.get('appdate'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,
                                                                                                          minutes=30)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            # end_time = pend_task.delivery_time if pend_task.delivery_time else blank_txt
            if pend_task.get('deliverydate'):
                deli_time = (datetime.strptime(pend_task.get('deliverydate'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,
                                                                                                               minutes=30)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            if pend_task.get('serviceadvisor'):
                resource = self.advisor_name(pend_task.get('serviceadvisor'))
            if pend_task.get('delivery_service_advisor'):
                delivery_sa = self.advisor_name(pend_task.get('delivery_service_advisor'))
            # resource = pend_task.get('serviceadvisor') if pend_task.get('serviceadvisor') else blank_txt
            # delivery_sa = pend_task.get('delivery_service_advisor') if pend_task.get('delivery_service_advisor') else blank_txt
            html_txt += '<tr style="border:1px solid black;cursor:pointer;" class="modal_rows_task">'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(indx + 1) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;"><input type="text" id="click_form_id" class="hidden" value="' + str(
                pend_task.get(
                    'order_id')) + '" name="regno"/><input type="text" id="click_form_model" class="hidden" value="' + str(
                pend_task.get('model')) + '" name="model"/>' + regn + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + customer + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + mobile + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + type + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + sec_gate_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(kilometer) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + roname + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + appo_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + deli_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + resource + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + delivery_sa + '</td>'
            # if pend_task.main_process_id == process_id3:
            html_txt += '<td  class="process" style="border:1px solid grey;text-align: center;height: 37px;">'
            if pend_task.get('cre_stage') == 'Start' or pend_task.get('sa_stage') == 'Start':
                html_txt += '<button style="height: 20px;width: 41px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_start_submit" id="cre_start">Start<span class="order_id" style="display: none;">' + str(
                    pend_task.get(
                        'order_id')) + '</span><span class="form_model"  style="display: none;">' + str(
                    pend_task.get('model')) + '</span></button>'

            if pend_task.get('cre_stage') == 'Finish' or pend_task.get('sa_stage') == 'Finish':
                html_txt += '<button style="height: 20px;width: 41px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Finish<span class="order_id" style="display: none;">' + str(
                    pend_task.get(
                        'order_id')) + '</span><span class="form_model"  style="display: none;">' + str(
                    pend_task.get('model')) + '</span></button>'
            html_txt += '</td></tr>'
        vals.update({'html_txt': html_txt})

        return {'click_mytask': vals}

    @http.route(['/all_count_click'], type='json', auth="public", website=True, csrf=False)
    def all_count_click(self, **post):
        vals = {}
        pending_task_object = ''
        estimate_tree = request.env.ref('ars_after_sales.action_quotations_inherit').id
        vals.update(self.counts_clk())
        process_id3 = request.env.ref('ac_rms.main_process3')
        process_id4 = request.env.ref('ac_rms.main_process4')
        # pending_task_object = vals.get('waiting_at_reception_browse')
        if post.get('clk_type') == 'app_clk':
            pending_task_object = vals.get('app_click')
        elif post.get('clk_type') == 'turnup_clk':
            pending_task_object = vals.get('turnup_click')
        elif post.get('clk_type') == 'walkin_clk':
            pending_task_object = vals.get('walkin_click')
        elif post.get('clk_type') == 'delivered_clk':
            pending_task_object = vals.get('delivered_click')
        elif post.get('clk_type') == 'return_clk':
            pending_task_object = vals.get('cancel_click')
        elif post.get('clk_type') == 'app_till_clk':
            pending_task_object = vals.get('app_till_click')
        elif post.get('clk_type') == 'waiting_delivery_clk':
            pending_task_object = vals.get('waiting_for_delivery_click')
        elif post.get('clk_type') == 'wip_clk':
            pending_task_object = vals.get('wip_click')
        elif post.get('clk_type') == 'hold_clk':
            pending_task_object = vals.get('hold_click')


        html_txt = ''
        blank_txt = ''
        # pend_task = ''
        for indx, pend_task in enumerate(pending_task_object):
            appo_time = ''
            deli_time = ''
            sec_gate_time = ''
            resource = ''
            delivery_sa = ''
            regn = pend_task.get('regno') if pend_task.get('regno') else blank_txt
            customer = pend_task.get('customer') if pend_task.get('customer') else blank_txt
            mobile = pend_task.get('mobile') if pend_task.get('mobile') else blank_txt
            type = pend_task.get('typevehicle') if pend_task.get('typevehicle') else blank_txt
            kilometer = pend_task.get('kilometer') if pend_task.get('kilometer') else blank_txt
            roname = pend_task.get('roname') if pend_task.get('roname') else blank_txt

            if pend_task.get('gatetime'):
                # if pend_task.get('type') == 'walkin':
                sec_gate_time = pend_task.get('gatetime')
                # else:
                #     sec_gate_time = (datetime.strptime(pend_task.get('gatetime'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,
                #                                                                                                minutes=30)).strftime(
                    # "%Y-%m-%d %H:%M:%S")
                # sec_gate_time = (datetime.strptime(gate_time, "%Y-%m-%d")).strftime("%Y-%m-%d")
            # start_time = pend_task.appo_date if pend_task.appo_date else blank_txt
            if pend_task.get('appdate'):
                if pend_task.get('type') == 'walkin':
                    appo_time = pend_task.get('appdate')
                else:
                    appo_time = (datetime.strptime(pend_task.get('appdate'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,
                                                                                                          minutes=30)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            # end_time = pend_task.delivery_time if pend_task.delivery_time else blank_txt
            if pend_task.get('deliverydate'):
                deli_time = (datetime.strptime(pend_task.get('deliverydate'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,
                                                                                                               minutes=30)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            if pend_task.get('serviceadvisor'):
                resource = self.advisor_name(pend_task.get('serviceadvisor'))
            if pend_task.get('delivery_service_advisor'):
                delivery_sa = self.advisor_name(pend_task.get('delivery_service_advisor'))
            # resource = pend_task.get('serviceadvisor') if pend_task.get('serviceadvisor') else blank_txt
            # delivery_sa = pend_task.get('delivery_service_advisor') if pend_task.get('delivery_service_advisor') else blank_txt
            html_txt += '<tr style="border:1px solid black;cursor:pointer;" class="modal_rows_task">'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(indx + 1) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;"><input type="text" id="click_form_id" class="hidden" value="' + str(
                pend_task.get(
                    'order_id')) + '" name="regno"/><input type="text" id="click_form_model" class="hidden" value="' + str(
                pend_task.get('model')) + '" name="model"/>' + regn + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + customer + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + mobile + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + type + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + sec_gate_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(kilometer) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + roname + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + appo_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + deli_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + resource + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + delivery_sa + '</td>'
            # if pend_task.main_process_id == process_id3:
            html_txt += '<td  class="process" style="border:1px solid grey;text-align: center;height: 37px;">'
            if pend_task.get('cre_stage') == 'Start' or pend_task.get('sa_stage') == 'Start' or pend_task.get('sa_stage') == 'Ready for Delivery':
                html_txt += '<button style="height: 20px;width: 41px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_start_submit" id="cre_start">Start<span class="order_id" style="display: none;">' + str(
                    pend_task.get(
                        'order_id')) + '</span><span class="form_model"  style="display: none;">' + str(
                    pend_task.get('model')) + '</span></button>'

            if pend_task.get('cre_stage') == 'Finish' or pend_task.get('sa_stage') == 'Finish' or pend_task.get('sa_stage') == 'SA Delivery Process':
                html_txt += '<button style="height: 20px;width: 41px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Finish<span class="order_id" style="display: none;">' + str(
                    pend_task.get(
                        'order_id')) + '</span><span class="form_model"  style="display: none;">' + str(
                    pend_task.get('model')) + '</span></button>'
            html_txt += '</td></tr>'
        html_txt += '''<script>
                $(document).ready(function() {
                
                
                    $('.tree_app_security').find('.modal_rows_task').on('click', 'td:not(.process)', function(){
                        var current_id = $(this).parent().find('#click_form_id').val();
                        var current_model = $(this).parent().find('#click_form_model').val();
                            $.ajax({
                                url: "/cre_formview",
                                type: "POST",
                                dataType: 'json',
                                data: JSON.stringify({params: {'id':current_id,'model':current_model}}),
                                contentType: 'application/json',
                            }).done(function(result) {
                                window.location.href = result.result.form
                            });
                        });
                });
            </script>'''
        if vals.get('app_click') or vals.get('turnup_click') or vals.get('delivered_click') or vals.get('walkin_click') or vals.get('waiting_for_delivery_click'):
            vals.update(
                {'color': '#bf5cb9;', 'ids': vals.get('waiting_at_reception_browse'), 'tree': estimate_tree,
                 'html_txt': html_txt})
            if pending_task_object:
                if pend_task:
                    vals.update({'model': pend_task.get('model')})
        return {'count_mytask': vals}



    @http.route(['/cre_formview'], type='json', auth="public", website=True, csrf=False)
    def cre_formview(self, **post):
        action = ''
        form_id = post.get('id')
        model = post.get('model')
        if model == 'crm.lead':
            action = request.env.ref('ars_after_sales.appointment_form_action_for_credashboard')
        if model == 'sale.order':
            action = request.env.ref('ars_after_sales.action_quotations_inherit')
        # action.sudo().res_id = int(form_id)
        form_action = '/web#id='+form_id+'&view_type=form&model='+model+'&action='+ str(action.id)
        print (form_action)
        print(action)
        return {'form': form_action}

    @http.route(['/start_button'], type='json', auth="public", website=True, csrf=False)
    def start_button(self, **post):
        sale_ids = ''
        process3 = request.env.ref('ac_rms.main_process3')
        process4 = request.env.ref('ac_rms.main_process4')
        process5 = request.env.ref('ac_rms.main_process5')
        process6 = request.env.ref('ac_rms.main_process6')
        process15 = request.env.ref('ac_rms.main_process15')
        process16 = request.env.ref('ac_rms.main_process16')
        process17 = request.env.ref('ac_rms.main_process17')
        process19 = request.env.ref('ac_rms.main_process19')
        start_id = post.get('start_click_id')
        if post.get('model_name') == 'crm.lead':
            sale_ids = request.env['crm.lead'].browse(int(start_id))
        elif post.get('model_name') == 'sale.order':
            sale_ids = request.env['sale.order'].browse(int(start_id))
        if sale_ids.main_process_id == process3:
            sale_ids.write({'main_process_id': process4.id, 'cre_work_flow': 'Finish'})
        elif sale_ids.main_process_id == process5:
            sale_ids.write({'main_process_id': process6.id, 'sa_work_flow': 'Finish'})
        elif sale_ids.main_process_id == process15:
            sale_ids.main_process_id = process16
        elif sale_ids.main_process_id == process17:
            sale_ids.write({'main_process_id': process19.id, 'sa_work_flow': 'SA Delivery Process'})

        return {'model':post.get('model_name')}

    @http.route(['/finish_button'], type='json', auth="public", website=True, csrf=False)
    def finish_button(self, **post):
        start_id = post.get('start_click_id')
        process4 = request.env.ref('ac_rms.main_process4')
        process5 = request.env.ref('ac_rms.main_process5')
        process6 = request.env.ref('ac_rms.main_process6')
        process7 = request.env.ref('ac_rms.main_process7')
        process16 = request.env.ref('ac_rms.main_process16')
        process17 = request.env.ref('ac_rms.main_process17')
        process19 = request.env.ref('ac_rms.main_process19')
        process20 = request.env.ref('ac_rms.main_process20')
        if post.get('model_name') == 'crm.lead':
            sale_ids = request.env['crm.lead'].browse(int(start_id))
        elif post.get('model_name') == 'sale.order':
            sale_ids = request.env['sale.order'].browse(int(start_id))
        if sale_ids.main_process_id == process4:
            sale_ids.write({'main_process_id': process5.id, 'cre_work_flow': 'Operation Done', 'sa_work_flow': 'Start'})
        elif sale_ids.main_process_id == process6:
            sale_ids.write({'main_process_id' : process7.id,'sa_work_flow':'Operation Done'})
        elif sale_ids.main_process_id == process16:
            sale_ids.write({'main_process_id': process17.id, 'sa_work_flow': 'Ready for Delivery'})
        elif sale_ids.main_process_id == process19:
            sale_ids.write({'main_process_id': process20.id,'sa_work_flow':'Operation Done'})
            sale_ids.calculate_efficiency()
        return {'model': post.get('model_name')}

    ####SA Login######
    @http.route(['/sa_login_dashboard'], type='json', auth="public", website=True, csrf=False)
    def sa_login_dashboard(self,**post):
        vals = {}
        estimate_tree = request.env.ref('ars_after_sales.action_quotations_inherit').id
        vals.update(self.counts_clk())
        process_id5 = request.env.ref('ac_rms.main_process5')
        process_id6 = request.env.ref('ac_rms.main_process6')
        # pending_task_object = vals.get('waiting_for_sa_browse')
        pending_task_object = vals.get('sa_dashboard_data')
        html_txt = ''
        blank_txt = ''
        for indx, pend_task in enumerate(pending_task_object):
            appo_time = ''
            deli_time = ''
            sec_gate_time = ''
            resource = ''
            delivery_sa = ''
            regn = pend_task.get('regno') if pend_task.get('regno') else blank_txt
            customer = pend_task.get('customer') if pend_task.get('customer') else blank_txt
            mobile = pend_task.get('mobile') if pend_task.get('mobile') else blank_txt
            type = pend_task.get('typevehicle') if pend_task.get('typevehicle') else blank_txt
            kilometer = pend_task.get('kilometer') if pend_task.get('kilometer') else blank_txt
            roname = pend_task.get('roname') if pend_task.get('roname') else blank_txt
            if pend_task.get('gatetime'):
                sec_gate_time = (datetime.strptime(pend_task.get('gatetime'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                # sec_gate_time = (datetime.strptime(gate_time, "%Y-%m-%d")).strftime("%Y-%m-%d")
            # start_time = pend_task.appo_date if pend_task.appo_date else blank_txt
            if pend_task.get('appdate'):
                appo_time = (datetime.strptime(pend_task.get('appdate'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            # end_time = pend_task.delivery_time if pend_task.delivery_time else blank_txt
            if pend_task.get('deliverydate'):
                deli_time = (datetime.strptime(pend_task.get('deliverydate'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            if pend_task.get('serviceadvisor'):
                resource = self.advisor_name(pend_task.get('serviceadvisor'))
            if pend_task.get('delivery_service_advisor'):
                delivery_sa = self.advisor_name(pend_task.get('delivery_service_advisor'))
            # resource = pend_task.get('serviceadvisor') if pend_task.get('serviceadvisor') else blank_txt
            # delivery_sa = pend_task.get('delivery_service_advisor') if pend_task.get(
            #     'delivery_service_advisor') else blank_txt
            # regn = pend_task.regn_no.license_plate if pend_task.regn_no.license_plate else blank_txt
            # customer = pend_task.partner_id.name if pend_task.partner_id.name else blank_txt
            # mobile = pend_task.partner_id.mobile if pend_task.partner_id.mobile else blank_txt
            # type = pend_task.type_lead if pend_task.type_lead else blank_txt
            # kilometer = pend_task.kilometer_in if pend_task.kilometer_in else blank_txt
            # gate_time = pend_task.sec_at_gatetime if pend_task.sec_at_gatetime else blank_txt
            # if gate_time:
            #     sec_gate_time = (datetime.strptime(gate_time, "%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            #     # sec_gate_time = (datetime.strptime(gate_time, "%Y-%m-%d")).strftime("%Y-%m-%d")
            # start_time = pend_task.appo_date if pend_task.appo_date else blank_txt
            # if start_time:
            #     appo_time = (datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            # end_time = pend_task.delivery_time if pend_task.delivery_time else blank_txt
            # if end_time:
            #     deli_time = (datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            # resource = pend_task.user_id.name if pend_task.user_id.name else blank_txt
            html_txt += '<tr style="border:1px solid black;cursor:pointer;" class="modal_rows_task">'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(indx + 1) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;"><input type="text" id="click_form_id" class="hidden" value="' + str(pend_task.get('order_id')) + '" name="regno"/><input type="text" id="click_form_model" class="hidden" value="' + str(pend_task.get('model')) + '" name="model"/>' + regn + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + customer + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + mobile + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + type + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + sec_gate_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(kilometer) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + roname + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + appo_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + deli_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + resource + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + delivery_sa + '</td>'
            if pend_task.get('sa_stage')== 'Start':
                # if pend_task.main_process_id == process_id5:
                html_txt += '<td  class="process" style="border:1px solid grey;text-align: center;height: 37px;">' \
                            '<button style="height: 20px;width: 41px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_start_submit" id="cre_start">Start<span class="order_id" style="display: none;">' + str(
                    pend_task.get('order_id')) + '</span><span class="form_model"  style="display: none;">'+str(pend_task.get('model'))+'</span></button></td></tr>'
            if pend_task.get('sa_stage') == 'Finish':
                html_txt += '<td  class="process" style="border:1px solid grey;text-align: center;height: 37px;">' \
                            '<button style="height: 20px;width: 41px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Finish<span class="order_id" style="display: none;">' + str(
                    pend_task.get('order_id')) + '</span><span class="form_model"  style="display: none;">'+str(pend_task.get('model'))+'</span></button></td></tr>'

        if vals.get('waiting_for_sa_browse'):
            vals.update(
                {'color': '#bf5cb9;', 'ids': vals.get('waiting_for_sa_browse'), 'tree': estimate_tree,
                 'html_txt': html_txt})

        return {'count_mytask': vals}

    @http.route(['/fi_login_dashboard'], type='json', auth="public", website=True, csrf=False)
    def fi_login_dashboard(self, **post):
        vals = {}
        estimate_tree = request.env.ref('ars_after_sales.action_quotations_inherit').id
        vals.update(self.counts_clk())
        process_id15 = request.env.ref('ac_rms.main_process15')
        process_id16 = request.env.ref('ac_rms.main_process16')
        pending_task_object = vals.get('fi_process_browse')
        html_txt = ''
        blank_txt = ''
        for indx, pend_task in enumerate(pending_task_object):
            regn = pend_task.regn_no.license_plate if pend_task.regn_no.license_plate else blank_txt
            customer = pend_task.partner_id.name if pend_task.partner_id.name else blank_txt
            mobile = pend_task.partner_id.mobile if pend_task.partner_id.mobile else blank_txt
            type = pend_task.doc_type if pend_task.doc_type else blank_txt
            appo_time = pend_task.appointment_date if pend_task.appointment_date else blank_txt
            deli_time = pend_task.delivery_date if pend_task.delivery_date else blank_txt
            resource = pend_task.resource_id_sale.name if pend_task.resource_id_sale.name else blank_txt
            html_txt += '<tr style="border:1px solid black;cursor:pointer;" class="modal_rows_task">'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(indx + 1) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;"><input type="text" id="click_form_id" class="hidden" value="' + str(
                pend_task.id) + '" name="regno"/><input type="text" id="click_form_model" class="hidden" value="' + str(
                pend_task.id) + '" name="regno"/>' + regn + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + customer + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + mobile + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + type + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">time</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + str(
                pend_task.mileage_in) + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + pend_task.name + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + appo_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + deli_time + '</td>'
            html_txt += '<td  style="border:1px solid grey;text-align: center;">' + resource + '</td>'
            if pend_task.main_process_id == process_id15:
                html_txt += '<td  class="process" style="border:1px solid grey;text-align: center;height: 37px;">' \
                            '<button style="height: 20px;width: 41px;background-color: teal;font-weight: bold; border-color: teal; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_start_submit" id="cre_start">Start<span class="order_id" style="display: none;">' + str(
                    pend_task.id) + '</span></button></td></tr>'
            else:
                html_txt += '<td  class="process" style="border:1px solid grey;text-align: center;height: 37px;">' \
                            '<button style="height: 20px;width: 41px;background-color: teal;font-weight: bold; border-color: teal; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Finish<span class="order_id" style="display: none;">' + str(
                    pend_task.id) + '</span></button></td></tr>'

        if vals.get('fi_process_browse'):
            vals.update(
                {'color': '#bf5cb9;', 'ids': vals.get('fi_process_browse'), 'tree': estimate_tree,
                 'html_txt': html_txt})

        return {'count_mytask': vals}


            # @http.route(['/cre_action_clk'], type='http', auth="user", website=True, csrf=False)
        # def cre_action_clk(self, **post):
        #     vals = self.counts_clk()
        #     if post.get('at_reception_ids_nm'):
        #         at_reception_ids = request.env['sale.order'].browse(eval(post.get('at_reception_ids_nm')))
        #         if len(at_reception_ids) > 1:
        #             vals.update(
        #                 {'type':'tree','clk_type': 'cre','color': '#bf5cb9;', 'ids': at_reception_ids,
        #                  'reception_ids': at_reception_ids.ids, 'reception_count': len(at_reception_ids)})
        #         elif len(at_reception_ids) == 1:
        #             vals.update(
        #                 {'type': 'form', 'clk_type': 'cre', 'color': '#bf5cb9;', 'ids': at_reception_ids,
        #                  'reception_ids': at_reception_ids.ids, 'reception_count': len(at_reception_ids)})
        #
        #     if post.get('front_desk_ids_nm'):
        #         at_front_desk_ids = request.env['sale.order'].browse(eval(post.get('front_desk_ids_nm')))
        #         if len(at_front_desk_ids) > 1:
        #             vals.update(
        #                 {'type':'tree','clk_type': 'cre','color': '#bf5cb9;', 'ids': at_front_desk_ids,
        #                  'reception_ids': at_front_desk_ids.ids, 'reception_count': len(at_front_desk_ids)})
        #         elif len(at_front_desk_ids) == 1:
        #             vals.update(
        #                 {'type': 'form', 'clk_type': 'cre', 'color': '#bf5cb9;', 'ids': at_front_desk_ids,
        #                  'reception_ids': at_front_desk_ids.ids, 'reception_count': len(at_front_desk_ids)})

        # type = ''
        # if post.get('regno'):
        #     result = post.get('regno')
        # if post.get('sale_id'):
        #     appointments = request.env['sale.order'].browse(int(post.get('sale_id')))
        # else:f
        #     appointments = request.env['sale.order'].search([('regn_no', '=', result)])
        #
        # for appo in appointments:
        #     obj = appo
        #     if obj.main_process_id.name in ('Waiting at reception', 'Waiting for SA'):
        #         type = 'start'
        #     if obj.main_process_id.name == 'Front desk process':
        #         type = 'finish'
        # vals.update({'regno': obj.regn_no or result,
        #         'customer_name': obj.partner_id,
        #
        #         'button_type': type,
        #         'sale_ids': obj})


        # return request.render("ac_rms.cre_login", vals)

    @http.route(['/action_open_form'], type='json', auth="user", website=True, csrf=False)
    def cre_action_form(self, **post):
        type = ''
        if post.get('ids'):
            result = post.get('ids')
            appointments = request.env['sale.order'].browse(int(result))
            # appointments = request.env['sale.order'].search([('regn_no', '=', result.)])
        # for appo in appointments:
        #     if appo.main_process_id.name in ('Waiting at reception','Waiting for SA'):
        #         type= 'start'
        #     if appo.main_process_id.name == 'Front desk process':
        #         type= 'finish'
        vals = {'button_type': type,
                'sale_ids': appointments
                }
        return {'doc': appointments.name, 'regn': appointments.regn_no.license_plate, 'vin': appointments.vin_no,
                'model': appointments.model, 'customer': appointments.partner_id.name,
                'mobile': appointments.partner_id.mobile, 'appointment': appointments.appointment_date,
                'delivery': appointments.delivery_date or '', 'sa': appointments.resource_id_sale.name,
                'type': appointments.type}

    @http.route(['/start'], type='http', auth="user", website=True, csrf=False)
    def cre_start_action(self, **post):
        template_render = ''
        vals = {}
        vals = self.counts_clk()
        if post.get('regno'):
            record = request.env['sale.order'].search([('regn_no', '=', post.get('regno'))], limit=1)
            vals.update({'ids': record})
            # current_date = fields.datetime.now()
            # print('current',current_date)
            if record.main_process_id.name == 'SO preparation':
                record.main_process_id = request.env['main.process'].search(
                    [('name', '=', 'Bay & Technician Allocation Process')], limit=1).id
                template_render = request.redirect('/sa_login')

            if record.main_process_id.name == 'Waiting for SA':
                record.main_process_id = request.env['main.process'].search([('name', '=', 'SO preparation')],
                                                                            limit=1).id
                template_render = request.render("ac_rms.login_form", vals)
            if record.main_process_id.name == 'Front desk process':
                record.main_process_id = request.env['main.process'].search([('name', '=', 'Waiting for SA')],
                                                                            limit=1).id
                # event_id = request.env['calendar.event'].search([('name','=',record.name),('user_id','=',request.env.user.id)])
                # request.env['calendar.event'].write(event_id,{'stop':current_date,
                #
                #                                          'stop_date':current_date.date()})
                template_render = request.redirect('/cre_login')

            if record.main_process_id.name == 'Waiting at reception':
                record.main_process_id = request.env['main.process'].search([('name', '=', 'Front desk process')],
                                                                            limit=1).id
                # request.env['calendar.event'].create({'start':current_date,
                #                                       'stop': current_date,
                #                                       'start_date': current_date.date(),
                #                                       'stop_date': current_date,
                #                                       'name': record.name,
                #                                       'user_id': request.env.user.id,
                #                                       'partner_ids': request.env.user.partner_id.ids})
                template_render = request.render("ac_rms.login_form", vals)

        return template_render

    ####SA Login######

    @http.route(['/sa_login'], type='http', auth="public", website=True, csrf=False)
    def sa_login(self, **kwargs):
        vals = {}
        vals.update(self.counts_clk())
        return request.render("ac_rms.sa_login", vals)

    @http.route(['/sa_action_clk'], type='http', auth="user", website=True, csrf=False)
    def sa_action_clk(self, **post):
        vals = self.counts_clk()
        if post.get('waiting_for_sa_ids_nm'):
            waiting_for_sa_ids = request.env['sale.order'].browse(eval(post.get('waiting_for_sa_ids_nm')))
            if len(waiting_for_sa_ids) > 1:
                vals.update(
                    {'type': 'tree', 'clk_type': 'cre', 'color': '#bf5cb9;', 'ids': waiting_for_sa_ids,
                     'waiting_for_sa_ids': waiting_for_sa_ids.ids, 'waiting_for_sa_count': len(waiting_for_sa_ids)})
            elif len(waiting_for_sa_ids) == 1:
                vals.update(
                    {'type': 'form', 'clk_type': 'cre', 'color': '#bf5cb9;', 'ids': waiting_for_sa_ids,
                     'reception_ids': waiting_for_sa_ids.ids, 'reception_count': len(waiting_for_sa_ids)})

        if post.get('waiting_for_sa_preparation_ids_nm'):
            sa_preparation_ids = request.env['sale.order'].browse(eval(post.get('waiting_for_sa_preparation_ids_nm')))
            if len(sa_preparation_ids) > 1:
                vals.update(
                    {'type': 'tree', 'clk_type': 'cre', 'color': '#bf5cb9;', 'ids': sa_preparation_ids,
                     'waiting_for_sa_ids': sa_preparation_ids.ids, 'waiting_for_sa_count': len(sa_preparation_ids)})
            elif len(sa_preparation_ids) == 1:
                vals.update(
                    {'type': 'form', 'clk_type': 'cre', 'color': '#bf5cb9;', 'ids': sa_preparation_ids,
                     'reception_ids': sa_preparation_ids.ids, 'reception_count': len(sa_preparation_ids)})

        return request.render("ac_rms.sa_login", vals)

    @http.route(['/process_stage_value'], type='json', auth="user", website=True, csrf=False)
    def process_stage(self, **post):
        sale_id = post.get('data')
        cr = request.env.cr
        old_process_name =''
        company_id = request.env.user.company_id.id
        estimate = request.env['sale.order'].browse(sale_id)
        if estimate.main_process_id.id:
            cr.execute("""select mt.old_value_char from mail_message mm
                            inner join mail_tracking_value mt on mt.mail_message_id = mm.id
                            where mm.res_id = %s
                            and mt.field = 'main_process_id'
                            and  mt.new_value_integer = %s
                            """,(sale_id,estimate.main_process_id.id,))
            old_main_process = cr.dictfetchall()
            old_process_name = old_main_process[0]['old_value_char']
        main_process_stage = estimate.main_process_id.name
        main_process_sequence = estimate.main_process_id.sequence
        previous_main_process = main_process_sequence - 1
        previous_main_process_name = request.env['main.process'].search([('sequence', '=', previous_main_process)]).name
        after_main_process = main_process_sequence + 1
        after_main_process_name = request.env['main.process'].search([('sequence', '=', after_main_process)]).name
        main_process_stage_id = request.env['main.process'].search([])
        total_stage = []
        for stage_id in main_process_stage_id:
            main_stage = []
            sub_stage = []
            process_stage_name = stage_id.name
            for sub_process in stage_id.sub_process_id:
                sub_stage.append(sub_process.name)
            main_stage.append(process_stage_name)
            main_stage.append(sub_stage)
            if process_stage_name == main_process_stage:
                main_stage.append(True)
            total_stage.append(main_stage)

        return {'previous_process': old_process_name,'current_process': main_process_stage,
                'after_process': after_main_process_name,'count_process': len(main_process_stage_id),
                'all_stage': total_stage}


    #Reports
    @http.route(['/dashboards'], type='http', auth="user", website=True)
    def multiple_dashboard(self, **kwargs):
        x = {}
        return request.render("ac_rms.multi_dashboard", x)


    @http.route(['/dashboard1'], type='http', auth="user", website=True, csrf=False)
    def dashboard1(self, **kwargs):
        final_list = []
        initial_list = []
        inward_wating_list = []
        total_inward_waiting = ''
        date = ''
        slot_wise_orders = []
        break_resaons = []
        if not kwargs.get('date'):
            current_date = str(datetime.now().date())
            strp_date = datetime.strptime(current_date, '%Y-%m-%d')
            stf_date = datetime.strftime(strp_date, "%m/%d/%Y")
            kwargs['date'] = stf_date
        if kwargs.get('date'):
            entered_date = kwargs.get('date')
            d = datetime.strptime(entered_date, '%m/%d/%Y')
            date = datetime.strftime(d, "%Y-%m-%d")

            yesterday = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)
            y_date = datetime.strftime(yesterday, "%Y-%m-%d")

            kwargs['date'] = datetime.strftime(d, "%m/%d/%Y")
            today = str(datetime.now().date())
            endtime = date + ' 23:59:59'
            starttime = date + ' 00:00:00'
            datestring = datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S")
            datstring = datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S")
            datetimes = datetime.strftime(datestring, "%Y-%m-%d %H:%M:%S")
            datitime = datetime.strftime(datstring, "%Y-%m-%d %H:%M:%S")
            domain = [('appointment_date', '<=', datetimes), ('appointment_date', '>=', datitime)]
            domain1 = [('create_date', '<=', datetimes), ('create_date', '>=', datitime)]
            # domain2 = [('time_at_gate', '<=', datetimes), ('time_at_gate', '>=', datitime)]
            domain3 = [('end', '<=', datetimes), ('end', '>=', datitime)]
            # domain4 = [('create_date', '<=', datetimes), ('create_date', '>=', datitime)]

        cr = request._cr
        company_id = request.env.user.company_id.id
        proccess_id1 = request.env.ref('ac_rms.main_process1').id
        proccess_id2 = request.env.ref('ac_rms.main_process2').name
        proccess_id3 = request.env.ref('ac_rms.main_process3').id
        proccess_id4 = request.env.ref('ac_rms.main_process4').id
        proccess_id15 = request.env.ref('ac_rms.main_process15').id
        proccess_id16 = request.env.ref('ac_rms.main_process16').id
        main_process17 = request.env.ref('ac_rms.main_process17').id
        main_process22 = request.env.ref('ac_rms.main_process22')

        # Total Appointments
        cr.execute("""
                    select so.id as order_id
                        from sale_order so
                        where so.company_id = %s
                        and so.doc_type = 'appointment'
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s
                        """, (company_id, date))

        # total_appointments = cr.dictfetchall()
        total_appointments = [x[0] for x in cr.fetchall()]

        # Total Appointments Turn Up
        cr.execute("""select so.id from sale_order so
                        where to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s
                        and so.time_at_gate = to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date
                        and so.company_id = %s
                        
                    """, (date, company_id))

        inward_vehicle_orders = [x[0] for x in cr.fetchall()]
        # Total Walkin
        cr.execute("""select so.id from sale_order so
                        where so.doc_type = 'walkin'
                        and so.company_id = %s
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s
                        """, (company_id, date))

        total_walkin = [x[0] for x in cr.fetchall()]

        cr.execute(""" select sp.res_id from mail_tracking_value s
                        inner join mail_message sp on sp.id =  s.mail_message_id
                        where s.new_value_char = 'Vehicle Delivered'
                        and to_char((s.create_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s
                        and sp.model = 'sale.order' 
                        """, (date,))

        total_delivered = [x[0] for x in cr.fetchall()]
        # Cancelled Appointments and walkin
        cr.execute("""select so.id 
                        from sale_order so
                        where so.company_id = %s
                        and so.state = 'cancel'
                        and so.sale_aftersales = 'after_sales'
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s
                                """, (company_id, date))

        total_cancel_app = [x[0] for x in cr.fetchall()]

        # Total Security Inward
        cr.execute(""" select sp.res_id from mail_tracking_value s
                        inner join mail_message sp on sp.id =  s.mail_message_id
                        where s.new_value_char = 'Security Process'
                        and to_char((s.create_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s
                        and sp.model = 'sale.order'
                        """, (date, ))

        total_security_in = [x[0] for x in cr.fetchall()]

        # Total Security Outward
        cr.execute(""" select sp.res_id from mail_tracking_value s
                        inner join mail_message sp on sp.id =  s.mail_message_id
                        where s.new_value_char = 'Vehicle Delivered'
                        and to_char((s.create_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s
                        and sp.model = 'sale.order'
                        """, (date, ))

        total_security_out = [x[0] for x in cr.fetchall()]

        # Same Day Security In and Security Outward
        cr.execute("""select a.res_id from
                        (select sp.res_id from mail_tracking_value s
                        inner join mail_message sp on sp.id =  s.mail_message_id
                        inner join sale_order so on so.id = sp.res_id
                        where s.new_value_char = 'Security Process'
                        and sp.model = 'sale.order'
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s 
                        and to_char((s.create_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s)a
                        inner join 
                        (select vd.res_id from mail_tracking_value v
                        inner join mail_message vd on vd.id =  v.mail_message_id
                        inner join sale_order so on so.id = vd.res_id
                        where v.new_value_char = 'Vehicle Delivered'
                        and vd.model = 'sale.order'
                        and to_char((so.appointment_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s
                        and to_char((v.create_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date = %s)b
                        on a.res_id = b.res_id """, (date, date, date, date))

        total_orders = [x[0] for x in cr.fetchall()]
        
        # Total RO of the day
        total_ro_for_the_day = request.env['sale.order'].search(
                                [('state', '=', 'sale'),
                                 ('company_id', '=', request.env.user.company_id.id)] + domain)
        #Total In & Out on 1 hour Duration
        cr.execute("""select * from (select z.day as day, count(distinct sale_in_app_id) as in_app_count ,
                                count(distinct sale_in_walk_id) as in_walk_count,
                                count(distinct sale_out_app_id) as out_app_count,
                                count(distinct sale_out_walk_id) as out_walk_count,
                                array_remove(array_agg(sale_in_app_id),NULL) as s1,
                                array_remove(array_agg(sale_in_walk_id),NULL) as s2,
                                array_remove(array_agg(sale_out_app_id),NULL) as s3,
                                array_remove(array_agg(sale_out_walk_id),NULL) as s4
                                from 
                                (select 
                                case when 
                                  (x.start_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata'>=
                                  %s ::date + '20 hours'::interval then '20:00 - 08:00' else
                                  
                                  to_char(date_trunc('hour', (x.start_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata'),'HH24:MI') ||' - ' ||
                                  to_char(date_trunc('hour', (x.start_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata' + interval '1 hour'), 'HH24:MI') end AS day,
                                
                                case when x.model ='sale.order' and x.main_process = 'Security Process' then (select count(id) 
                                from sale_order where id = x.res_id 
                                and doc_type = 'appointment')
                                end as sale_in_app_count,
                                case when x.model ='sale.order' and x.main_process = 'Security Process' then (select id 
                                from sale_order where id = x.res_id 
                                and doc_type = 'appointment')
                                end as sale_in_app_id, 
                                case when x.model ='sale.order' and x.main_process = 'Vehicle Delivered' then (select count(id) 
                                from sale_order where id = x.res_id 
                                and doc_type = 'appointment')
                                end as sale_out_app_count, 
                                case when x.model ='sale.order' and x.main_process = 'Vehicle Delivered' then (select id 
                                from sale_order where id = x.res_id 
                                and doc_type = 'appointment')
                                end as sale_out_app_id, 
                                
                                case when x.model ='sale.order' and x.main_process = 'Security Process' then (select count(id) 
                                from sale_order where id = x.res_id 
                                and doc_type = 'walkin')
                                end as sale_in_walk_count,
                                case when x.model ='sale.order' and x.main_process = 'Security Process' then (select id 
                                from sale_order where id = x.res_id 
                                and doc_type = 'walkin')
                                end as sale_in_walk_id, 
                                case when x.model ='sale.order' and x.main_process = 'Vehicle Delivered' then (select count(id) 
                                from sale_order where id = x.res_id 
                                and doc_type = 'walkin')
                                end as sale_out_walk_count,
                                case when x.model ='sale.order' and x.main_process = 'Vehicle Delivered' then (select id 
                                from sale_order where id = x.res_id 
                                and doc_type = 'walkin')
                                end as sale_out_walk_id 
                               
                                from
                                (
                                select mt.new_value_char as main_process
                                ,mt.create_date as start_date 
                                ,mm.res_id as res_id
                                ,mm.model as model
                                from mail_tracking_value mt
                                inner join mail_message mm on mm.id =  mt.mail_message_id
                                where mt.new_value_char in ('Security Process','Vehicle Delivered')
                                and (mt.create_date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata' 
                                  between %s ::date + '8 hours'::interval and %s ::date + '1 day 8 hours'::interval)x
                                  )z
                                  group by day
                                  )m
                                right outer join
                                (
                                select * from
                                (
                                    select to_char(('00:00:00'::time + (n) * interval '1 hour' ),'HH24:MI') || ' - '||
                                    to_char(('00:00:00'::time + (n+1) * interval '1 hour' ),'HH24:MI') as day_count
                                    from generate_series(8,19)n
                                    union
                                    select '20:00 - 08:00' as day_count
                                )s
                                order by day_count)y
                                    on m.day = y.day_count

                                        
                                        """, (date, date, date))
        slot_wise_orders = cr.fetchall()
        initial_list.append(len(total_appointments))
        initial_list.append(len(inward_vehicle_orders))
        initial_list.append(len(total_walkin))
        initial_list.append(len(total_delivered))
        initial_list.append(len(total_cancel_app))
        initial_list.append(len(total_security_in))
        initial_list.append(len(total_security_out))
        initial_list.append(len(total_orders))
        initial_list.append(len(total_ro_for_the_day))
        initial_list.append(total_appointments)
        initial_list.append(inward_vehicle_orders)
        initial_list.append(total_walkin)
        initial_list.append(total_delivered)
        initial_list.append(total_cancel_app)
        initial_list.append(total_security_in)
        initial_list.append(total_security_out)
        initial_list.append(total_orders)
        initial_list.append(total_ro_for_the_day.ids)

        final_list.append(initial_list)
        values = {'key': final_list, 'slot_wise_order': slot_wise_orders, 'date': kwargs.get('date')}
        return request.render("ac_rms.dashboard1", values)


    @http.route(['/all-list-vehicle-details'], type='json', auth='user', website=True, csrf=False)
    def list_vehicle_details(self, orders, **post):
        menu_id = request.env['ir.ui.menu'].search([('name', '=', 'AfterSales')])
        action_id = request.env.ref('ac_rms.action_to_order_tree')
        if orders:
            if action_id:
                action_id['domain'] = [('id', 'in', eval(orders))]
                list_url = 'web#min=1&limit=20&view_type=list&model=sale.order&action=' + str(
                    action_id.id) + ' &menu_id=' + str(menu_id.id)

        return {'urls': list_url}

    @http.route(['/all-list-timeslot'], type='json', auth='user', website=True, csrf=False)
    def timeslot_vehicle_details(self, app_walk_id, **post):
        menu_id = request.env['ir.ui.menu'].search([('name', '=', 'AfterSales')])
        action_id = request.env.ref('ac_rms.action_to_order_tree')
        if app_walk_id:
            if action_id:
                action_id['domain'] = [('id', 'in', eval(app_walk_id))]
                list_url = 'web#min=1&limit=20&view_type=list&model=sale.order&action=' + str(
                    action_id.id) + ' &menu_id=' + str(menu_id.id)

        return {'urls': list_url}

    @http.route(['/dashboard2'], type='http', auth="user", website=True, csrf=False)
    def dashboard2(self, **kwargs):
        cr = request._cr
        # cr.execute("""select
        #                 s.id as order_id
        #                 ,fv.license_plate
        #                 ,rep.name as customer
        #                 ,s.mobile
        #                 ,s.appointment_date
        #                 ,s.doc_type
        #                 ,s.gate_in_time
        #                 ,s.user_id
        #                 ,s.delivery_date
        #                 ,mp.name as stage
        #                 from sale_order s
        #                 inner join fleet_vehicle fv on fv.id = s.regn_no
        #                 inner join res_partner rep on rep.id = s.partner_id
        #                 inner join res_users res on res.id = s.user_id
        #                 inner join main_process mp on mp.id = s.main_process_id
        #             """)
        cr.execute("""select
                        distinct(mm.res_id) as res_id
                        from mail_tracking_value mt
                        inner join mail_message mm on mm.id =  mt.mail_message_id
                        where mt.new_value_char not in ('Vehicle Delivered','Waiting For Vehicle Inward')
                        and mt.field = 'main_process_id'
                        and mm.model = 'sale.order'
                            """)

        inward = [x[0] for x in cr.fetchall()]
        order_ids = request.env['sale.order'].browse(inward)

        return request.render("ac_rms.dashboard2", {'key': order_ids})

    @http.route(['/dashboard3'], type='http', auth="user", website=True, csrf=False)
    def dashboard3(self, **kwargs):
        date = ''
        all_veh = []
        values = {}
        start_date = ''
        end_date = ''
        start_date1 = ''
        end_date1 = ''
        if not kwargs.get('date1') and not kwargs.get('date2'):
            current_date = str(datetime.now().date())
            strp_date = datetime.strptime(current_date, '%Y-%m-%d')
            stf_date = datetime.strftime(strp_date, "%m/%d/%Y")
            kwargs['date1'] = stf_date
            kwargs['date2'] = stf_date
        if kwargs.get('date1') and kwargs.get('date2'):
            d1 = datetime.strptime(kwargs.get('date1'), '%m/%d/%Y')
            start_date = datetime.strftime(d1, "%Y-%m-%d")
            start_date1 = datetime.strftime(d1, "%d/%m/%Y")
            d2 = datetime.strptime(kwargs.get('date2'), '%m/%d/%Y')
            end_date = datetime.strftime(d2, "%Y-%m-%d")
            end_date1 = datetime.strftime(d2, "%d/%m/%Y")
            # start_date = datetime.date.strftime(d, "%m/%d/%Y")
            cr = request._cr
            company_id = request.env.user.company_id.id

            # cr.execute("""select rc.name, plan_stu, actual_time, productivity, efficiency from task_efficiency te
            #             inner join resource_resource rc on rc.id = te.resource_id
            #                     """,(start_date,end_date,company_id))
            # cr.execute("""select
            #                 array_agg(distinct(mm.res_id)) as res_id,
            #                 ((%s::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::TIMESTAMP
            #                 -
            #                 ((%s ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::TIMESTAMP
            #                 as diff
            #                 from mail_tracking_value mt
            #                 inner join mail_message mm on mm.id =  mt.mail_message_id
            #                 where mt.new_value_char = 'Ready For Delivery'
            #                 and mt.field = 'main_process_id'
            #                 and mm.model = 'sale.order'
            #                 and to_char((mm.date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date
            #                 between %s and %s""",(end_date,start_date,start_date,end_date))

            cr.execute("""select
                            distinct(mm.res_id) as res_id
                            from mail_tracking_value mt
                            inner join mail_message mm on mm.id =  mt.mail_message_id
                            where mt.new_value_char = 'Ready For Delivery'
                            and mt.field = 'main_process_id'
                            and mm.model = 'sale.order'
                            and to_char((mm.date ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date 
                            between %s and %s""", (start_date, end_date))


            # to get records which went for ready for delivery on the date range
            sale_ids = [x[0] for x in cr.fetchall()]
            # all_delvry_records = cr.dictfetchall()
            # if all_delvry_records[0]['res_id']:
            #     sale_ids = all_delvry_records[0]['res_id']
            #     # sale_ids = [x[0] for x in all_delvry_records[0]['res_id']]
            # else:
            #     sale_ids = []
            # if all_delvry_records[0]['diff']:
            #     day_diffs = all_delvry_records[0]['diff']
            #     day_di = str(day_diffs)
            #     spilit_diff = day_di.split(' ')
            #     day_diff = int(spilit_diff[0]) + 1
            # else:
            #     day_diff = 0 + 1

            # cr.execute("""select
            #                 ((max(a.end_datetime)::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date
            #                 -
            #                 ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date
            #                 as diff
            #                 from account_analytic_line a
            #                 inner join resource_resource r on r.id =  a.resource_name
            #                 where a.entry_type = 'actual'
            #                 and r.resource_category = (select id from resource_category where name = 'Technician')
            #                 and to_char((a.start_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date
            #                 between %s and %s
            #                 and to_char((a.end_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date
            #                 between %s and %s
            #                         """, (start_date,end_date , start_date, end_date))
            # day_diff = cr.fetchall()
            # diffs = day_diff[0][0]
            # if diffs == 0:
            #     diff = 1
            # else:
            #     diff = diffs
            if sale_ids:
                cr.execute("""select 
                                name
                                , round(sum(plan_stu)::numeric) as plan_stu
                                , round(sum(actual_time)::numeric ) as actual_time
                                , coalesce(sum(days),0) as days
                                , case when sum(present) > 0 then round(((sum(plan_stu) / sum(present)) * 100)::numeric) else 0 end as productivity
                                , case when sum(actual_time) > 0 then round(((sum(plan_stu) / sum(actual_time)) * 100)::numeric) else 0 end as efficiency
                                , round((coalesce(sum(days),0) * 480)::numeric) as day_mins
                                , id
                                from
                                (
                                select 
                                      round(sum(actual_time)::numeric,2) as actual_time
                                      , sum(plan_stu * 60) as plan_stu
                                      , r.name
                                      , r.id
                                      from task_efficiency t
                                  inner join resource_resource r on r.id = t.resource_id
                                  inner join project_task p on p.id = t.task_id
                                  inner join sale_order_line sl on sl.id = p.sale_line_id
                                  inner join sale_order s on s.id =  sl.order_id
                                  where s.id in %s
                                  and t.company_id = %s
                                  group by r.name, r.id
                                )xy
                            
                                left outer join
                                    (
                                    select 
                                     (case when (((max(a.end_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date 
                                        -
                                        ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date) = 0
                                        then 1
                                        else
                                        ((max(a.end_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date
                                        -
                                        ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date + 1
                                        end) * 8 * 60 as present
                                        ,case when (((max(a.end_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date 
                                            -
                                            ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date) = 0
                                            then 1
                                            else
                                            ((max(a.end_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date
                                            -
                                            ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date + 1
                                            end as days
                                        , r.id as resource
                                        
                                        from  account_analytic_line a
                                        inner join resource_resource r on r.id  = a.resource_name
                                        where a.entry_type = 'actual'
                                        and r.resource_category = (select id from resource_category where name = 'Technician')
                                        and to_char((a.start_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date 
                                        between %s and %s
                                        and to_char((a.end_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date 
                                        between %s and %s
                                        and r.company_id = %s
                                        group by r.id
                                    )z
                                on xy.id = z.resource
                                group by id, name
                                order by name""",(tuple(sale_ids,),company_id,start_date,end_date,start_date,end_date,company_id))

            all_veh = cr.fetchall()
            # print("...........AAA............",all_veh)
        # values = {'key': all_veh, 'date1': start_date1, 'date2': end_date1}
        values = {'key': all_veh, 'date1':start_date1, 'date2':end_date1}
        return request.render("ac_rms.dashboard3", values)

    @http.route(['/dashboard8'], type='http', auth="user", website=True, csrf=False)
    def dashboard8(self, **kwargs):
        date = ''
        bay_list = []
        tech_list = []
        if not kwargs.get('date'):
            current_date = str(datetime.now().date())
            strp_date = datetime.strptime(current_date, '%Y-%m-%d')
            stf_date = datetime.strftime(strp_date, "%m/%d/%Y")
            kwargs['date'] = stf_date
        if kwargs.get('date'):
            entered_date = kwargs.get('date')
            d = datetime.strptime(entered_date, '%m/%d/%Y')
            date = datetime.strftime(d, "%Y-%m-%d")
            kwargs['date'] = datetime.strftime(d, "%m/%d/%Y")
            today = str(datetime.now().date())
            endtime = date + ' 23:59:59'
            starttime = date + ' 00:00:00'
            datestring = datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S")
            datstring = datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S")
            datetimes = datetime.strftime(datestring, "%Y-%m-%d %H:%M:%S")
            datitime = datetime.strftime(datstring, "%Y-%m-%d %H:%M:%S")
            domain = [('appointment', '<=', datetimes), ('appointment', '>=', datitime)]
            domain1 = [('check_in', '<=', datetimes), ('check_in', '>=', datitime)]
            domain2 = [('time_at_gate', '<=', datetimes), ('time_at_gate', '>=', datitime)]
            domain3 = [('check_out', '<=', datetimes), ('check_out', '>=', datitime)]
            mainprocess10 = request.env.ref('ac_rms.main_process10')
            start_status = request.env.ref('ac_rms.status1')
            company_id = request.env.user.company_id.id
            request.env.cr.execute(
                "SELECT id,name FROM resource_resource WHERE resource_category in (SELECT id from resource_category WHERE name = 'Bay') AND active = true AND company_id = %s order by id asc" % (
                request.env.user.company_id.id))
            bay_record = request.env.cr.fetchall()
            request.env.cr.execute(
                "SELECT id,name FROM resource_resource WHERE resource_category in (SELECT id from resource_category WHERE name = 'Technician') AND active = true AND company_id = %s order by name asc" % (
                request.env.user.company_id.id))
            tech_record = request.env.cr.fetchall()
            cr = request._cr
            # cr.execute("""select t.id
            #     from time_line t
            #     inner join resource_timeline_rel tr
            #     on tr.timeline_id = t.id
            #     inner join resource_resource r
            #     on r.id = tr.resource_id
            #     where t.sub_process_id = %s
            #     and t.entry_type = 'actual'
            #     and t.company_id = %s
            #     and r.resource_category_id in (SELECT id from resource_category WHERE name = 'Bay')
            #     and (to_char((check_in::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd'))::date = %s """,
            #            (mainprocess10.id, company_id, date))

            cr.execute("""select a.id
                                            from account_analytic_line a
                                            inner join resource_resource r on r.id = a.resource_name
                                            where a.entry_type = 'actual'
                                            and a.company_id = %s
                                            and a.status = %s
                                            and r.resource_category = (SELECT id from resource_category WHERE name = 'Bay')
                                            and (to_char((a.start_datetime::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd'))::date = %s
                                        """, (company_id,start_status.id , date))

            bay_id = [x[0] for x in cr.fetchall()]
            bay_list = []
            for each_bay in bay_record:
                bayls = []
                bayls.append(each_bay[1])
                inward = request.env['account.analytic.line'].search([('id', 'in', bay_id), ('resource_name', 'in', [each_bay[0]])])
                if inward:
                    order_ids = []
                    for inw in inward:
                        if inw.task_id.order_id.id not in order_ids:
                            order_id = inw.task_id.order_id.id
                            order_ids.append(order_id)
                    bayls.append(len(order_ids))
                    bayls.append(True)
                    bayls.append(order_ids)

                else:
                    bayls.append(0)
                    bayls.append(False)
                bay_list.append(bayls)

            # cr.execute("""select t.id
            #                 from time_line t
            #                 inner join resource_timeline_rel tr
            #                 on tr.timeline_id = t.id
            #                 inner join resource_resource r
            #                 on r.id = tr.resource_id
            #                 where t.sub_process_id = %s
            #                 and t.entry_type = 'actual'
            #                 and t.company_id = %s
            #                 and r.resource_category_id in (SELECT id from resource_category WHERE name = 'Technician')
            #                 and (to_char((check_in::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd'))::date = %s """,
            #            (mainprocess10.id, company_id, date))

            cr.execute("""select a.id
                                from account_analytic_line a
                                inner join resource_resource r on r.id = a.resource_name
                                where a.entry_type = 'actual'
                                and a.company_id = %s
                                and a.status = %s
                                and r.resource_category = (SELECT id from resource_category WHERE name = 'Technician')
                                and (to_char((a.start_datetime::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd'))::date = %s
                            """,(company_id,start_status.id, date))
            tech_id = [x[0] for x in cr.fetchall()]
            tech_list = []
            for each_tech in tech_record:
                techls = []
                techls.append(each_tech[1])
                inward = request.env['account.analytic.line'].search(
                    [('id', 'in', tech_id), ('resource_name', 'in', [each_tech[0]])])
                if inward:
                    order_ids = []
                    for inw in inward:
                        if inw.task_id.order_id.id not in order_ids:
                            order_id = inw.task_id.order_id.id
                            order_ids.append(order_id)
                    techls.append(len(order_ids))
                    techls.append(True)
                    techls.append(order_ids)
                else:
                    techls.append(0)
                    techls.append(False)
                tech_list.append(techls)
                # print tech_list

        return request.render("ac_rms.dashboard8",
                                       {'date': kwargs.get('date'), 'total_appointments_bays': bay_list,
                                        'total_appointments_techs': tech_list})

    @http.route(['/dashboard4'], type='http', auth="user", website=True, csrf=False)
    def dashboard4(self, **kwargs):
        values = {}
        start_date = ''
        end_date = ''
        start_date1 = ''
        end_date1 = ''
        cr = request._cr
        company_id = request.env.user.company_id.id
        tech_categ = request.env.ref("ac_rms.resource_categories_tech")

        if not kwargs.get('date1') and not kwargs.get('date2'):
            current_date = str(datetime.now().date())
            strp_date = datetime.strptime(current_date, '%Y-%m-%d')
            stf_date = datetime.strftime(strp_date, "%m/%d/%Y")
            kwargs['date1'] = stf_date
            kwargs['date2'] = stf_date
        if kwargs.get('date1') and kwargs.get('date2'):
            d1 = datetime.strptime(kwargs.get('date1'), '%m/%d/%Y')
            start_date = datetime.strftime(d1, "%Y-%m-%d")
            start_date1 = datetime.strftime(d1, "%m/%d/%Y")
            d2 = datetime.strptime(kwargs.get('date2'), '%m/%d/%Y')
            end_date = datetime.strftime(d2, "%Y-%m-%d")
            end_date1 = datetime.strftime(d2, "%m/%d/%Y")

        ids = request.env['resource.resource'].search([('resource_category', '=', tech_categ.id),('company_id', '=', company_id)])
        res = ','.join(str(e) for e in ids._ids)
        cr.execute("""
                    select
                    resource_name,
                    sum(tot_minute) as tot_minute ,
                    round(EXTRACT(EPOCH from sum(zz.diff)) / 60) / (sum(days) * 480) * 100 as utilization,
                    sum(days) as days,
                    max(zz.hrs) as hrs

                     from
                        (
                        SELECT
                                to_char(date_part('epoch', sum(diff)) * INTERVAL
                                '1 second' + interval
                                '30 second', 'HH24:MI') as hrs,
                                x.resource_name,
                                sum(diff) as diff,
                                round(EXTRACT(EPOCH from sum(diff)) / 60) as tot_minute,
                                x.resource_id
                                --sum(days) as days,
                                --round(EXTRACT(EPOCH from sum(diff)) / 60) / (sum(days) * 480) * 100 as utilization
                                from
                            (

                                    select
                                        resource_id
                                        ,resource_name
                                        ,(check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata'
                                        ,(check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata'
                                        , case when ((check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date !=
                                          ((check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date --or check_out is null
                                            then
                                            (((check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date || ' 23:59:59')::TIMESTAMP
                                            -
                                            ((check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::TIMESTAMP

                                            else
                                            ((check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::TIMESTAMP
                                            -
                                            ((check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::TIMESTAMP
                                            end as diff


                                         from agg_data(%s,%s,%s,%s)
                                         where ((check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date
                                            between %s and %s

                                        union all
                                          select
                                            resource_id
                                            ,resource_name
                                            ,(check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata'
                                            ,(check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata'
                                            , case when ((check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date !=
                                              ((check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date
                                                then
                                                (((check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata'))::TIMESTAMP
                                                -
                                                (((check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date || ' 00:00:00')::TIMESTAMP

                                                else
                                                ((check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::TIMESTAMP
                                                -
                                                ((check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::TIMESTAMP
                                                end as hrs


                                              from agg_data(%s,%s,%s,%s)
                                              where ((check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata') :: date
                                              between %s and %s
                                              and ((check_out ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata') :: date
                                              != ((check_in ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata') :: date
                                    )x

                                    group by x.resource_name , x.resource_id
                        )zz
                            left outer join
                                    (
                                    select 
                                     (case when (((max(a.end_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date 
                                        -
                                        ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date) = 0
                                        then 1
                                        else
                                        ((max(a.end_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date
                                        -
                                        ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date + 1
                                        end) * 8 * 60 as present
                                        ,case when (((max(a.end_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date 
                                            -
                                            ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date) = 0
                                            then 1
                                            else
                                            ((max(a.end_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date
                                            -
                                            ((min(a.start_datetime) ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata')::date + 1
                                            end as days
                                        , r.id as resource
                                        
                                        from  account_analytic_line a
                                        inner join resource_resource r on r.id  = a.resource_name
                                        where a.entry_type = 'actual'
                                        and r.resource_category = (select id from resource_category where name = 'Technician')
                                        and to_char((a.start_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date 
                                        between %s and %s
                                        and to_char((a.end_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date 
                                        between %s and %s
                                        and r.company_id = %s
                                        group by r.id
                                )z
                                on zz.resource_id = z.resource
                                group by zz.resource_id ,zz.resource_name
    	      """, (
            start_date, end_date, res, company_id, start_date, end_date,
            start_date, end_date, res, company_id, start_date, end_date,
            start_date, end_date,start_date, end_date, company_id,))
        qry2 = cr.fetchall()

        values = {'date1': start_date1, 'date2': end_date1, 'key2': qry2}
        return request.render("ac_rms.dashboard_four", values)



    @http.route(['/baylist'], type='http', auth="user", website=True)
    def baylist(self, **post):
        menu_id = request.env['ir.ui.menu'].search([('name', '=', 'Aftersales')])
        action_id = request.env.ref('ac_rms.action_to_bay_tree')
        bay_tech = post.get('order_id')
        bays_techs = eval(bay_tech)
        action_id['domain'] = [('id', 'in', bays_techs)]
        bay_tech_url = 'web#min=1&limit=20&view_type=list&model=sale.order&action=' + str(
            action_id.id) + ' &menu_id=' + str(menu_id.id)

        return werkzeug.utils.redirect(bay_tech_url)