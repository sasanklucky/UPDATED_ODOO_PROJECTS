# -*- coding: utf-8 -*-
{
    'name': "ARS Product Catalog",
    'summary': """ARS Product Catalog""",
    'description': """
        Product catalogs are useful to several business users and groups such as sales reps, inside sales, buyers, 
        store clerks, field marketers, and managers. Here's how each group uses it:
    """,
    'author': "Autochip India",
    'website': "https://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase', 'purchase_requisition', 'stock'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/account_invoice.xml',
        'views/ars_stock_warehouse_views.xml',
        # 'views/stock_picking.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
