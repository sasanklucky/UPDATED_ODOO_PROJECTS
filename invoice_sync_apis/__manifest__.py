# -*- coding: utf-8 -*-
{
    'name': "Invoice Sync API",
    'summary': """
        Invoice Sync API""",
    'description': """
       Invoice Sync API
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
             'views/invoice_inherit.xml',
             'views/sync_log.xml',
             'views/res_partner_inherited.xml',
             'wizard/sync_check_wizard.xml',
    ],
   'installable': True,
   'application': True,
   'auto_install': False,
}