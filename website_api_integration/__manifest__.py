# -*- coding: utf-8 -*-
{
    'name': "Website API Lead Creation",
    'summary': """Website API Lead Creation""",
    'description': """
       Get the data from Website Team stored the requested data consolidation db, then create the lead for respective dealer
    """,
    'author': "Autochip India",
    'website': "https://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','ac_ars_consolidation'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/source_data.xml',
        'views/website_data.xml',
        'views/res_users.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
