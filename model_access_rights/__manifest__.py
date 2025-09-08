
{
    'name': 'Hide Create|Delete|Archive|Export Options - Model Wise',
    'version': '11.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Hide module features for user groups.""",
    'description': """Can restrict create, update, delete, archive/unarchive, 
     export in different models to user groups.""",
    'author': 'Auto Chip PVT LTD.',
    'company': 'Auto Chip PVT LTD.',
    'maintainer': 'Auto Chip PVT LTD.',
    'website': "",
    'depends': ['base_setup', 'mail','base'],
    'data': [
        'security/model_access_rights_groups.xml',
        'security/ir.model.access.csv',
        'views/access_right_views.xml',
        'views/assets.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
