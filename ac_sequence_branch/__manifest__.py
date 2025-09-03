# -*- coding: utf-8 -*-
{
    'name': "AC Sequence",
    'summary': """AC Sequence""",
    'description': """
       AC Sequence number for each branch
    """,
    'author': "Autochip India",
    'website': "https://www.autochip.in",
    'category': 'sale',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'website_quote','ars_after_sales'],
    # always loaded
    'data': [
        'views/sale_order.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],

    'installable': True,
    'auto_install': False,
}
