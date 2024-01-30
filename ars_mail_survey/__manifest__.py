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
        'security/mail_activity_security.xml',
	'security/ars_security_access.xml',
        # 'views/ars_res_partner_views.xml',
        # 'views/ars_after_sale_views.xml',
        # 'views/ars_templates.xml',
        'data/mail_activity_server_action.xml',
	'views/ars_mail_activity_form_view.xml',
        'views/ars_sales_followup.xml',
        'views/ars_post_sales_followup.xml',
        'views/ars_mail_activity_type_views.xml',
        # 'wizard/ars_split_line_item_views.xml',
	'wizard/sale_wiz.xml',
        'wizard/service_wiz.xml',
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
