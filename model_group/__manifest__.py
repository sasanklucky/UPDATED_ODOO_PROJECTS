{
    'name': 'model group',
    'version': '1.0',
    'summary': 'Adds Master Product concept',
    "author": "Autochip shambhu",
    'depends': ['base','product','stock','ars_after_sales','ars_vehicle_sales'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_master_views.xml',
        'views/product_template_views.xml',
        # 'views/hide_master_id.xml',
    ],
    'installable': True,
    'application': True,
}