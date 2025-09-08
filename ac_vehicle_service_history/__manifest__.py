# -*- coding: utf-8 -*-
{
    'name': "ARS Vehicle Service History ",
    'summary': """""",
    'description': """ """,
    'author': "ARS Vehicle Service History Management",
    'website': "http://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'fleet', 'stock', 'sale'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/vehicle_history_views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
