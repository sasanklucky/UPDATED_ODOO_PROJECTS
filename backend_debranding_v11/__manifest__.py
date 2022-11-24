# -*- coding: utf-8 -*-

{
    "name": "Debranding Kit",
    'version': '11.1.0.0',
    "description": """This module can be used for Debranding of odoo module """,
    'author': 'Autochip',
    'company': "Autochip",
    "support": "http://www.autochip.in/",
    'category': "Extra Tools",
    "license": "AGPL-3",

    'depends': [
        'web',
        'mail',
        'web_settings_dashboard',
        'portal',

    ],
    'data': [
        'views/data.xml',
        'views/views.xml',
        'views/js.xml',
        'pre_install.yml',
        'views/webclient_templates.xml',
        'security/ir.model.access.csv',

        ],
    'qweb': [
        'static/src/xml/web.xml',
        'static/src/xml/dashbord.xml',

    ],
    'images': ['static/description/main.png'],
    'auto_install': False,
    'installable': True,
    'application': True,

}
