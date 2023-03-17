# -*- coding: utf-8 -*-
{
    'name': "Report EVP Sales Enquiry",
    'summary': """ """,
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.autochip.cin",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','crm','ars_after_sales','ars_vehicle_sales'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}