# -*- coding: utf-8 -*-
{
    'name': "Credit Note",
    'summary': """Refunds will be sen sale_order_line""",
    'description': """
        Credit Note
    """,
    'author': "Autochip India",
    'website': "https://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.11',
    'depends': ['base','account'],
    # always loaded
    'data': [
        'views/credit_note_button.xml',
    ],
    'assets': {

    },
    # only loaded in demonstration mode
    'demo': [
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}