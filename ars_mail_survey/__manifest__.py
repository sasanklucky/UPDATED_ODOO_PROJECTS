{
    'name': "ARS Mail Survey",
    'summary': """
        ARS Mail Survey""",
    'description': """
       
    """,
    'author': "Autochip",
    'website': "www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['product', 'crm','mail', 'sale', 'ars_after_sales', 'account','survey','helpdesk'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/ars_res_partner_views.xml',
        # 'views/ars_after_sale_views.xml',
        # 'views/ars_templates.xml',
        'views/ars_sales_followup.xml',
        'views/ars_post_sales_followup.xml',
        # 'wizard/ars_split_line_item_views.xml',
        'views/res_config_settings.xml',
        'views/followup_spoc_master.xml',
        'views/helpdesk_ticket.xml',
        'views/category.xml',
    ],

    # 'qweb': ['static/src/xml/ars_split_template.xml','static/src/xml/template.xml',],

    'installable': True,
    'application': True,
    'auto_install': False,
}
