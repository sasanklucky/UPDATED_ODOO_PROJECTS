# -*- coding: utf-8 -*-
{
    'name': "ARS Account Cancel",
    'summary': """ """,
    'description': """  """,
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['account', 
                'account_cancel', 
                'ars_after_sales'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
