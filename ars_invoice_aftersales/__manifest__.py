{
    'name': "ARS invoice Aftersales",
    'summary': """
        ARS invoice Aftersales""",
    'description': """
        Automobile Retail System
        a. Parts
        b. Accessories
        c. Labor
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['product', 'crm', 'sale', 'ars_after_sales', 'account'],
    'data': [

        'data/account_invoice.xml',
        'views/ars_res_partner_views.xml',
        'views/ars_after_sale_views.xml',
        'views/ars_templates.xml',
        'wizard/ars_split_line_item_views.xml',
    ],

    'qweb': ['static/src/xml/ars_split_template.xml','static/src/xml/template.xml',],

    'installable': True,
    'application': True,
    'auto_install': False,
}