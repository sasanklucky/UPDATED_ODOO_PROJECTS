# -*- coding: utf-8 -*-
{
    'name': "ARS Sales Dashbord",

    'summary': """ARS Sales Dashbord - """,

    'description': """
        The "dashboard" is often displayed on a web page 
        which is linked to a database that allows the report to be constantly updated
    """,

    'author': "Autochip india pvt ltd",
    'website': "http://www.autochip.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['product','crm','sale','ars_vehicle_sales','account','website','sale_crm','hr','sale_timesheet','base','web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/classes_link.xml',
        'views/ars_dashbord.xml',
        'views/ars_dashbord_view.xml',
        'views/ars_sales.xml',

    ],
    'qweb': [
            # 'static/src/xml/headee_file.xml',
            'static/src/xml/ars_crm_dashbord_header.xml',
            ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}