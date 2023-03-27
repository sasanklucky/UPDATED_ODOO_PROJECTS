# -*- coding: utf-8 -*-
{
    'name': "Product Catalog",
    'summary': """ """,
    'description': """ """,
    'author': "Autochip India",
    'website': "https://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
