{
    'name': 'model group',
    'version': '1.0',
    'summary': 'Adds Master Product concept',
    "author": "Autochip",
    'depends': ['base','product','stock','ars_after_sales','ars_vehicle_sales', 'fleet','account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_master_views.xml',
        'views/hide_master_id.xml',
        'views/product_template_views.xml',

    ],
    'installable': True,
    'application': True,
}