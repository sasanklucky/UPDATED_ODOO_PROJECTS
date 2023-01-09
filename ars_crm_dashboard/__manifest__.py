{
    'name': "ARS CRM Dashbord",

    'summary': """ARS CRM Dashbord - """,

    'author': "Autochip india pvt ltd",
    'website': "http://www.autochip.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web','crm'],

    # always loaded
    'data': [
        'views/ars_crm_dashboard.xml'
    ],
    'qweb': [
            'static/src/xml/*.xml'
            ],
}