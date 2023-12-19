{
    "name": "ARS Reports",
	"description": """
		ARS Reports
    """,
    "installable": True,
    "depends": [
        'base','sale','account','l10n_in','ars_after_sales',
    ],
    "data": [
        'security/ir.model.access.csv',
        'security/ars_report_access.xml',
        'views/repair_report.xml',
        'views/service_history_report.xml',
        'views/service_history_report_template.xml',
        'views/retail_report.xml',
        'views/wholesale_report.xml',
        'views/repair_order_report.xml',
        'views/parts_purchase_report.xml',
        'views/after_sales_retail_report.xml',
        'views/after_sale_report.xml',
        'views/stock_picking.xml',
        'views/purchase_order_document.xml',
        'views/stock_ageing.xml',
        'menu/report_menus.xml',
    ],
}
