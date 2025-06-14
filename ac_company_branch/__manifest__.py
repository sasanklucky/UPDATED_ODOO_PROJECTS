# -*- coding: utf-8 -*-
{
    'name': "ARS Company Branch",
    'summary': """
        ARS Company Branch""",
    'description': """
        
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','web', 'product', 'crm', 'sale', 'sale_stock', 'stock_account', 'web_m2x_options',
                'ars_vehicle_sales', 'account', 'website', 'sale_crm', 'hr', 'sale_timesheet', 'web_notify',
                'l10n_in_sale', 'fleet', 'mail', 'auth_signup', 'purchase_requisition', 'ars_after_sales',
                'purchase', 'purchase_requisition', 'stock', 'stock_account', 'contacts', 'ars_invoice_aftersales'],
    'data': [

        # 'security/ir.model.access.csv',
        # 'security/security.xml',
        # 'views/ars_company_branch_master.xml',
        # 'views/ars_company_branch.xml',

    ],
    'qweb': [
        'static/src/xml/SwitchBranchMenu.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
