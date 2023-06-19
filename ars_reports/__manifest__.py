{
    "name": "ARS Reports",
	"description": """
		ARS Reports
    """,
    "installable": True,
    "depends": [
        'base','sale','account','l10n_in',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/repair_report.xml',
        'views/retail_report.xml',
        'views/wholesale_report.xml',
        'views/repair_order_report.xml',
        'views/parts_purchase_report.xml',
    ],
}