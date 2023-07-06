# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Sync API",
    'summary': """
        Purchase Order Sync API""",
    'description': """
       Purchase Order Sync API
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['purchase','sale'],
    'data': [
             'data/ir_cron.xml',
             'security/ir.model.access.csv',
             'views/res_config.xml',
             'views/po_inherit.xml',
             'views/sale_inherit.xml',
             'views/sync_log.xml',
             'wizard/sync_check_wizard.xml',
    ],
   'installable': True,
   'application': True,
   'auto_install': False,
}