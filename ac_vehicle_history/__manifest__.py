# -*- coding: utf-8 -*-
{
    'name': "ARS Vehicle History",
    'summary': """ARS Vehicle History""",
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ac_ars_consolidation', 'ac_product_catalog', 'ars_after_sales', 'ars_vehicle_sales', 'ars_reports'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',

        'wizard/vehicle_card_create_wizard.xml',
        'wizard/vehicle_card_message.xml',
        'wizard/vehicle_sync_update.xml',
        'views/menus.xml',
        'views/res_config_settings.xml',
        'views/fleet_vehicle.xml',
        'views/service_type.xml',
        'views/service_history.xml',
        'report/service_history_menu.xml',
        'report/service_hist.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
