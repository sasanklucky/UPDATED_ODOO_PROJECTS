# -*- coding: utf-8 -*-
{
    'name': "AC Sale E-Signature",
    'summary': """AC Sale E-Signature""",
    'description': """
       Sale quatation customer e-signature
    """,
    'author': "Autochip India",
    'website': "https://www.autochip.in",
    'category': 'sale',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'website_quote'],
    # always loaded
    'data': [
        'views/website_quote_template.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],

    'installable': True,
    'auto_install': False,
}
