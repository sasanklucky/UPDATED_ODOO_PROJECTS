{
    'name': 'Customer Field Restrict',
    'version': '1.0',
    'summary': 'Adding Restriction on customer field after it convert to new quotation',
    "author": "Autochip",
    'depends': ['base','crm','sale','ars_vehicle_sales'],
    'data': [
            'views/restrict_customer_edit.xml',
            'views/add_varient.xml'
    ],
    'installable': True,
    'application': True,
}