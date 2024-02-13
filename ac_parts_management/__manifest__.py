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
        'security/ars_parts_security.xml',
        'demo/demo.xml',
        'demo/ars_parts_sales.xml',
        'views/parts_purchase.xml',
        'views/res_company.xml',
        'menus/parts_sales_menus.xml',
        'menus/parts_inventory_menus.xml',
        'menus/parts_purchase.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
