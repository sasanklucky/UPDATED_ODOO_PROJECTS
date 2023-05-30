{
    "name": "ARS Reports",
	"description": """
		ARS Reports
    """,
    "installable": True,
    "depends": [
        'base','sale','account'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/repair_report.xml',
        'views/retail_report.xml',
        'views/wholesale_report.xml',
    ],
}