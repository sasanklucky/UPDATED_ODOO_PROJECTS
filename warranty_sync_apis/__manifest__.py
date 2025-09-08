# -*- coding: utf-8 -*-
{
    'name': "Warranty Sync API",
    'summary': """
        Warranty Sync API""",
    'description': """
       Warranty Sync API
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['ars_after_sales'],
    'data': [
             'data/ir_cron.xml',
             'security/ir.model.access.csv',
             'views/res_config.xml',
             'views/warrenty.xml',
             'views/sync_log.xml',
             'views/warranty_lines_split.xml',
             'views/warranty_menu_item.xml',
             'views/line_items_dialog_js.xml',
             'wizard/sync_check_wizard.xml',
    ],
    'qweb':[
        'static/src/xml/dailog_box_template.xml',
        'static/src/xml/split_line_item.xml'
    ],
   'installable': True,
   'application': True,
   'auto_install': False,
}