# -*- coding: utf-8 -*-
{
    'name': "BYD Stock Picking",
    'summary': """ """,
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase', 'ars_vehicle_sales'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/cron_job.xml',
    ],
    # only loaded in demonstration mode
}
