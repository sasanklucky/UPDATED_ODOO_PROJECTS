# -*- encoding: utf-8 -*-

{
    'name': 'GST E-Invoicing with Eway Bill',
    'version': '11.0.0.1',
    'category': 'Integration',
    'description': """
        module to allow E-Invoicing integration with Taxpro
        Documentation, gst e-invoice , e-invoice, odoo gst einvoice, einvoice for gst, how can generate e invoice in odoo,
        want to generate e-invoice , einvoice for odoo 13, for odoo 15, india gst, gst in odoo, invoice in odoo, elecronc invoice in odoo,
        odoo gst, gst einvoice, invoice in odoo, gst invoice, e-invoice , invoice odoo, invoice in odoo, odoo gst , gst, einvoice, einvoice with irn,
        qr code, odoo 14, community, odoo 15, odoo form view, tree view , odoo e generation , generated e invoice, hiow e invoice works in odoo,
        generate odoo einvoice, einvoice generated,einvoice, invoice, INVOICE,E-INVOICE, e-invoice, invoice odoo,
        odoo invoice, E-invoice, e-invoice, inv, gst, e-invoice
    """,
    'live_test_url': 'https://www.youtube.com/watch?v=bM6eU7l1LIM',
    'author': 'Geo Technosoft',
    'sequence': 1,
    'website': 'https://www.geotechnosoft.com',
    # 'depends': ['account', 'stock','ars_after_sales'],
    'depends': ['account', 'stock', 'ac_product_catalog'],
    'data': [
        'security/ir.model.access.csv',
        'security/e_invoice_group.xml',
        'reports/invoice_report.xml',
        'reports/credit_note_report.xml',
        'data/uom_data.xml',
        'data/res_country_state_data.xml',
        'wizard/cancel_einvoice.xml',
        'wizard/cancel_eway.xml',
        'views/einvoicing_configuration.xml',
        'views/account_invoice.xml',
        'views/after_sales_invoice.xml',
        'views/stock_warehouse.xml',
    ],
    'application': True,
    'installable': True,
    'images': ['static/description/banner.png'],
    'price': 49.00,
    'currency': 'USD',
    'license': 'OPL-1',
}
