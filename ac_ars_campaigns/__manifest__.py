# -*- coding: utf-8 -*-
{
    'name': "ARS Campaigns",
    'summary': """ARS Campaigns For Vehicles""",
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','ars_vehicle_sales','ars_after_sales','product','fleet','sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/security_groups.xml',
        'views/campaign_views.xml',
        'views/campaign_fleet_vehicle_inherits.xml',
        'views/service_campaign_view.xml',
        'views/labours_setup.xml',
        'views/sales_orders.xml',
        'wizard/import_wizard.xml',
        'wizard/convert_so_wizard.xml',
        'wizard/sim_installation.xml',


    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
