# -*- coding: utf-8 -*-
{
    'name': "ARS Consolidation",
    'summary': """ARS Consolidated DB""",
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'fleet', 'mail',
                'ars_vehicle_sales', 'ars_after_sales'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/templates.xml',
        'views/ars_dealer_views.xml',
        'views/service_history.xml',
        'report/service_history_report_inherit.xml',
        'menus/ac_ars_consolidation_menus.xml',
        'wizard/vehicle_card_update_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
