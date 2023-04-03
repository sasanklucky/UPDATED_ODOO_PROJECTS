# -*- coding: utf-8 -*-
{
    'name': "ARS Parts Management",
    'summary': """ARS Parts Management""",
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    'category': 'ARS',
    'version': '0.1',
    'depends': ['base', 'sale', 'purchase','purchase_requisition',
                'ac_product_catalog',
                'ars_after_sales',
                'ars_vehicle_sales'],
    'data': [
        # 'security/ir.model.access.csv',
        'demo/demo.xml',
        'views/parts_purchase.xml',
        'security/ars_parts_security.xml',
        'menus/parts_purchase.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
