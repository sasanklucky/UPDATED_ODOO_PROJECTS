# -*- coding: utf-8 -*-
{
    'name': "ARS After Sales",
    'summary': """
        ARS After Sales""",
    'description': """
        Automobile Retail System
        a. After Sales
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['web','product','crm','sale','sale_stock','stock_account',
                'ars_vehicle_sales','account','website','sale_crm','hr','sale_timesheet',
                'l10n_in_sale','fleet','mail', 'auth_signup','purchase_requisition','web_domain_field'],
    'data': [

                'security/ars_security_xml.xml',
                'security/ir.model.access.csv',
                # 'security/ars_security_xml.xml',
                # 'security/ir.model.access.csv',
                'views/ars_parts_views.xml',
                'views/ars_lead.xml',
                'views/ars_pipeline.xml',
                'views/ars_crm_team.xml',
                'views/ars_crm_stage.xml',
                
                # 'views/ars_menuspare.xml',
                
                
                'views/ars_customer_xml.xml',
                'views/ars_invoice_report.xml',
                'views/report_estimate.xml',
                'views/estimate_report.xml',
                'views/ars_sale_views.xml',
                'views/ars_mail_activity_type_views.xml',
                'views/ars_resource_resource_views.xml',
                'views/ars_csstemplates.xml',
                'wizard/ars_check_regn.xml',
                # 'wizard/ars_time_line.xml',
                'views/customer_dump_mis.xml',
                'views/client_files.xml',
                'views/planner_view.xml',
                'views/ars_email_aftersales_invoice.xml',
                'views/role_center.xml',
                'views/ars_warranty.xml',
                'data/product_data.xml',
                'data/landing_page.xml',
                'views/templates.xml',
                'reports/employee_mis_report.xml',
                'views/ars_menus.xml',
                'views/ars_config.xml',
                'views/ars_menu_access.xml',
                'views/ars_sign_up_view.xml',
            ],
    'qweb': [
                'static/src/xml/rolesetup.xml',
                'static/src/xml/stage_template.xml',
                # 'static/src/xml/base.xml',
            ],
   'installable': True,
   'application': True,
   'auto_install': False,
}