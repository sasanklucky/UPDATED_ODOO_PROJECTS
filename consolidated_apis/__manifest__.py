# -*- coding: utf-8 -*-
{
    'name': "AC Consolidated API's",
    'summary': """
        AC Consolidated API's""",
    'description': """
       Consolidated API's
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['crm','sale'],
    'data': [
             'security/security.xml',
             'security/ir.model.access.csv',
             'data/ir_cron.xml',
             'views/parent_child_configuration.xml',
             'views/company_configuration.xml',
             'views/res_config.xml',
             'views/menu.xml',
    ],


   'installable': True,
   'application': True,
   'auto_install': False,
}