# -*- coding: utf-8 -*-
{
    'name': "ARS Vehicle Management",
    'summary': """ARS Vehicle Management""",
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base','sale', 'purchase','purchase_requisition',
                'ac_product_catalog',
                'ars_after_sales',
                'ars_vehicle_sales'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'demo/ars_vehicle_purchase.xml',
        'security/ars_vehicle_security.xml',
        'views/views.xml',
        'views/vehicle_purchase.xml',
        'menu/ac_vehicle_menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
