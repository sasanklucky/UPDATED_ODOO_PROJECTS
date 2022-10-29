# -*- coding: utf-8 -*-
{
    'name': "AC RMS",
    'summary': """
        AC RMS""",
    'description': """
        Resource Management System
        a. Calender
        b. Meeting
        c. Call
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['crm','sale','sale_stock','website','ars_after_sales','project','hr_timesheet','mail','project_task_default_stage','rating'],
    'data': [
            'security/rms_security.xml',
             'security/ir.model.access.csv',
             'data/process_data.xml',
             'data/category.xml',
             'data/rms_landing_pages.xml',
             'data/rms_stages.xml',
             'views/client_files.xml',
             'views/planner_view.xml',
             'views/planner_menu.xml',
             'views/rms_resource_calender.xml',
             # 'views/security_login_settings.xml',
             'views/sale_order.xml',
             'views/dashboard_kanban_view.xml',
             'views/rms_all_process.xml',
             'views/project_task.xml',
             'views/crm_lead.xml',
             'views/role_center_rms.xml',
             'views/planner_report_view.xml',
             'wizard/ars_time_line.xml',
    ],

    'qweb': ['static/src/xml/dashboard_template.xml',
             'static/src/xml/client_action_for_cre.xml',
             'static/src/xml/sa_dashboard.xml',
             'static/src/xml/fi_dashboard.xml',
             'static/src/xml/process_stage_template.xml'],

   'installable': True,
   'application': True,
   'auto_install': False,
}