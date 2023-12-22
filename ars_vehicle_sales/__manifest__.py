# -*- coding: utf-8 -*-
{
    'name': "ARS Vehicle Sales",
    'summary': """
        ARS Before Sales""",
    'description': """
        Automobile Retail System
            a. Model
            b. Model Variants
            c. Vehicle
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['product', 'stock', 'purchase', 'sale', 'fleet', 'account', 'hr','contacts','ac_product_catalog'],
    'data': [
        'data/product_data.xml',
        'data/ars_mail_template_data.xml',
        'data/quotation_sequence.xml',
        'data/ars_cron_job.xml',
        'security/ars_security.xml',
        'security/ir.model.access.csv',
        'views/ars_test_drive.xml',
        'views/ars_gatepass_template.xml',
        'views/ars_model_views.xml',
        'views/annual_income_view.xml',
        'views/ars_menus.xml',
        'views/ars_model_views.xml',
        'views/ars_stock_production_lot.xml',
        'views/ars_sale_change.xml',
        'views/ars_company_header.xml',
        'views/ars_sales_quotation.xml',
        'views/ars_invoice_form.xml',
        'views/ars_sales_invoice_report.xml',
        'views/ars_vehicle.xml',
        'views/crm_lost_reason.xml',
        'views/ars_employee_view.xml',
        'views/ars_activitylist.xml',
        'views/ars_email_sales_quotation.xml',
        'views/ars_email_sales_invoice.xml',
        'views/ars_home.xml',
        'views/ars_footer.xml',
        'views/ars_css.xml',
        'views/stock_picking.xml',
        'views/ars_crm_lost_reason.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
