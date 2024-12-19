# -*- coding: utf-8 -*-
{
    'name': "ARS Master Data Restriction",
    'summary': """ARS Master Data Restriction""",
    'description': """
        Master Data Restriction
    """,
    'author': "Autochip India",
    'website': "https://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.11',
    'depends': ['base', 'sale', 'purchase', 'purchase_requisition', 'stock', 'stock_account','web','crm','ars_after_sales','product','ars_mail_survey'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ars_master_menu_restriction.xml',
        'views/ars_master_menu_config.xml',
        'views/lines_restriction.xml',
        'wizard/ars_master_data_restriction.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ac_master_data_restriction/static/src/js/menu_logger.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
    ],
}