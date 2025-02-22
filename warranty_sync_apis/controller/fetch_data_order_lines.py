from odoo import http
from odoo.http import request


class FetchDataOrderLines(http.Controller):
    @http.route(['/warranty_sync_apis/fetch_data/get_fields'], type='json', auth='user', website=True, crsf=False)
    def fetch_data_orders_line(self, **kwargs):
        print(*kwargs.get('model'), 'KRISHNAAAAAAA')
        return [{'customer': 'Customer A', 'percentage': 20,'subtotal': 100,'tax': 10,'taxable_amount': 110}]