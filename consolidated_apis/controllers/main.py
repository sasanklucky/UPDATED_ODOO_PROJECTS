# # -*- coding: utf-8 -*-
# import werkzeug.utils
# from odoo import http
# from odoo.http import request
# import pytz
# from odoo import models, fields, api, _
# import datetime
# import json
# import werkzeug.utils
# from datetime import datetime, timedelta

# DEFAULT_DATE_TIME_FORMATE = '%Y-%m-%d %H:%M:%S'
# DEFAULT_DATE_TIME_FORMATE1 = '%Y-%m-%d %I:%M:%S'


# class Home(http.Controller):
#     @http.route(['/resource_planner'], type='http', auth="public", website=True, csrf=False)
#     def planner(self, **kwargs):
#         event_check = False
#         event_resource = False
#         shift_end = False
#         view = kwargs.get('view') or 1
#         select_view = []
#         cr = request.env.cr
#         company = request.env.user.company_id
#         res_calender = request.env['planner.calender'].search([])
#         res_pull = request.env['planner.calender'].browse(int(view))

#         pull_resource = res_pull.resorce_pull_ids
#         SaleOrder = request.env['sale.order']
#         vehicle_processes = res_pull.vehicle_process
#         allo_veh = SaleOrder.search([('main_process_id', 'in', vehicle_processes.ids)])

#         for res_c in res_calender:
#             if res_c.id == int(view):
#                 select_view.append('selected')
#             else:
#                 select_view.append('')

#         waiting_for_inward = request.env.ref("ac_rms.main_process1").id
#         sec_process = request.env.ref("ac_rms.main_process2").id
#         watng_at_recpn = request.env.ref("ac_rms.main_process3").id
#         waiting_inward = SaleOrder.search([('main_process_id', '=',waiting_for_inward)])
#         sec = SaleOrder.search([('main_process_id', '=', sec_process)])
#         watng_reception = SaleOrder.search([('main_process_id', '=', watng_at_recpn)])
#         # bay_allocation = waiting_inward | sec | watng_reception
#         cr.execute("""select count(distinct(so.id)) as sale_count,
#                         array_agg(distinct(so.id)) as sale_id
#                         from sale_order so 
#                         inner join sale_order_line sl on sl.order_id = so.id
#                         inner join project_task pt on pt.sale_line_id = sl.id
#                         inner join project_task_type pty on pty.id = pt.stage_id
#                         where so.bay_tech_allocation = false
#                         and so.sale_aftersales = 'after_sales'
#                         and pty.sequence in (0,7,5,4)
#                         order by sale_id
#                         """)
#         all_data = cr.dictfetchall()
#         bay_allocation_count = all_data[0].get('sale_count')
#         bay_allocation_id = all_data[0].get('sale_id')
#         bay_allocation_ids = []
#         if bay_allocation_id:
#             bay_allocation_ids = sorted(bay_allocation_id, reverse=True)

#         cr.execute("""select count(so.id)
#                             ,array_agg(so.id) as so_ids
#                             from sale_order so
#                             where so.main_process_id = %s
#                             and so.sale_aftersales = 'after_sales'
#                             and so.company_id = %s
#                             """, (request.env.ref("ac_rms.main_process11").id, company.id,))

#         hold_approval = cr.dictfetchall()
#         hold_approval_count = hold_approval[0].get('count')
#         rhold_approval_ids = hold_approval[0].get('so_ids')

#         cr.execute("""select count(so.id)
#                         ,array_agg(so.id) as so_ids
#                             from sale_order so
#                              where main_process_id = %s
#                               and company_id = %s
#                                 """,(request.env.ref("ac_rms.main_process15").id,company.id,))

#         fi_waiting = cr.dictfetchall()
#         fi_waiting_count = fi_waiting[0].get('count')
#         fi_waiting_ids = fi_waiting[0].get('so_ids')

#         cr.execute("""select count(so.id)
#                                 ,array_agg(so.id) as so_ids
#                                     from sale_order so
#                                      where main_process_id = %s
#                                       and company_id = %s
#                                         """, (request.env.ref("ac_rms.main_process17").id, company.id,))

#         ready_for_delivery = cr.dictfetchall()
#         ready_for_delivery_count = ready_for_delivery[0].get('count')
#         ready_for_delivery_ids = ready_for_delivery[0].get('so_ids')


#         cr.execute("""select count(distinct(b.initial_count)) as initial_count,
#                        array_remove(array_agg(distinct(b.initial_ids)),NULL) as initial_ids,
#                        count(distinct(b.partial_count)) as partial_count,
#                        array_remove(array_agg(distinct(b.partial_ids)),NULL) as partial_ids,
#                        count(distinct(b.additional_job_count)) as additional_job_count,
#                        array_remove(array_agg(distinct(b.additional_job_ids)),NULL) as additional_job_ids,
#                        count(distinct(b.hold_approve_count)) as hold_approve_count,
#                        array_remove(array_agg(distinct(b.hold_approve_ids)),NULL) as hold_approve_ids,
#                        count(distinct(b.carry_over_count)) as carry_over_count,
#                        array_remove(array_agg(distinct(b.carry_over_ids)),NULL) as carry_over_ids,
#                        count(distinct(b.reschedule_count)) as reschedule_count,
#                        array_remove(array_agg(distinct(b.reschedule_ids)),NULL) as reschedule_ids,
#                        count(distinct(b.fi_reject_count)) as fi_reject_count,
#                        array_remove(array_agg(distinct(b.fi_reject_ids)),NULL) as fi_reject_ids
#                        from
#                        (select 
#                         case when so.is_partial = false and so.is_additional_job = false and so.is_hold_approve = false and so.is_carry_over = false and so.is_reschedule = false and so.is_fi_rejection = false then so.id end AS initial_count,
#                     case when so.is_partial = false and so.is_additional_job = false and so.is_hold_approve = false and so.is_carry_over = false and so.is_reschedule = false and so.is_fi_rejection = false then so.id end AS initial_ids,
#                     case when so.is_partial = true then so.id end AS partial_count,
#                     case when so.is_partial = true then so.id end AS partial_ids,
#                     case when so.is_additional_job = true then so.id end AS additional_job_count,
#                     case when so.is_additional_job = true then so.id end AS additional_job_ids,
#                     case when so.is_hold_approve = true then so.id end AS hold_approve_count,
#                     case when so.is_hold_approve = true then so.id end AS hold_approve_ids,
#                     case when so.is_carry_over = true then so.id end AS carry_over_count,
#                     case when so.is_carry_over = true then so.id end AS carry_over_ids,
#                     case when so.is_reschedule = true then so.id end AS reschedule_count,
#                     case when so.is_reschedule = true then so.id end AS reschedule_ids,
#                     case when so.is_fi_rejection = true then so.id end AS fi_reject_count,
#                     case when so.is_fi_rejection = true then so.id end AS fi_reject_ids
#                     from sale_order so
#                     inner join sale_order_line sl on sl.order_id = so.id
#                     inner join project_task pt on pt.sale_line_id = sl.id
#                     inner join project_task_type pty on pty.id = pt.stage_id
#                     where so.bay_tech_allocation = false
#                     and so.sale_aftersales = 'after_sales'
#                     and pty.sequence in (0,7,5,4))b""")
#         all_count_ids_data = cr.dictfetchall()

#         # bay_allocation_id = all_data[0].get('sale_id')

#         task_type = request.env['project.task.type'].search([('sequence', '=', 3)]).id
#         project_task = request.env['project.task'].search([('stage_id', '=', task_type)])
#         job_stoppage_sale_id = project_task.mapped("order_id").ids

#         vals = { 'res_planner': res_calender,
#                  'view':select_view,
#                  'pull_reses':{},
#                  'bay_allocation':bay_allocation_count,
#                  'hold_approval_count':hold_approval_count,
#                  'fi_waiting_count':fi_waiting_count,
#                  'ready_for_delivery_count':ready_for_delivery_count,
#                  'initial_count':all_count_ids_data[0].get('initial_count'),
#                  'initial_ids':all_count_ids_data[0].get('initial_ids'),
#                  'partial_count':all_count_ids_data[0].get('partial_count'),
#                  'partial_ids':all_count_ids_data[0].get('partial_ids'),
#                  'additional_job_count':all_count_ids_data[0].get('additional_job_count'),
#                  'additional_job_ids':all_count_ids_data[0].get('additional_job_ids'),
#                  'hold_approve_count': all_count_ids_data[0].get('hold_approve_count'),
#                  'hold_approve_ids': all_count_ids_data[0].get('hold_approve_ids'),
#                  'carry_over_count': all_count_ids_data[0].get('carry_over_count'),
#                  'carry_over_ids': all_count_ids_data[0].get('carry_over_ids'),
#                  'reschedule_count': all_count_ids_data[0].get('reschedule_count'),
#                  'reschedule_ids': all_count_ids_data[0].get('reschedule_ids'),
#                  'fi_reject_count': all_count_ids_data[0].get('fi_reject_count'),
#                  'fi_reject_ids': all_count_ids_data[0].get('fi_reject_ids'),
#                  'job_stoppage_count':len(project_task),
#                  'job_stoppage_ids':project_task.ids}
#         if res_pull.vehicle:
#             event_check = True
#         if res_pull.resource:
#             event_resource = True
#         if res_pull.shift_end:
#             shift_end = True
#         if not event_check and not event_resource:
#             col_sm = 'col-sm-11'
#         if event_check and event_resource:
#             col_sm = 'col-sm-9'
#         if event_check and not event_resource:
#             col_sm = 'col-sm-10'
#         if not event_check and event_resource:
#             col_sm = 'col-sm-10'
#         vals.update({ 'shift_end':shift_end,'res_planner': res_calender,'view':select_view,'pull_reses':pull_resource,'col_sm':col_sm,'resource_pl':event_resource,'event':event_check,'ros':allo_veh})
#         return request.render("ac_rms.resource_planner", vals)

 