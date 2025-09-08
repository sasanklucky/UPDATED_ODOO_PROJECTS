# -*- coding: utf-8 -*-

import base64

from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.tools import consteq

class InteritCustomerPortal(CustomerPortal):
    @http.route(['/my/orders/<int:order>'], type='http', auth="public", website=True)
    def portal_order_page(self, order=None, access_token=None, **kw):
        try:
            order_sudo = self._order_check_access(order, access_token=access_token)
        except AccessError:
            return request.redirect('/my')

        values = self._order_get_page_view_values(order_sudo, access_token, **kw)
        if order_sudo.sudo().sale_aftersales == 'sales':
            return request.render("ars_vehicle_sales.ars_portal_order_page", values)
        else:
            return request.render("ars_after_sales.ars_portal_aftersales_page", values)

    @http.route(['/my/orders/pdf/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_report(self, order_id, access_token=None, **kw):
        try:
            order_sudo = self._order_check_access(order_id, access_token)
            if order_sudo.sudo().sale_aftersales == 'sales':
                order_sale = request.env.ref('sale.action_report_saleorder')
            else:
                order_sale = request.env.ref('ars_after_sales.estimate_order')
        except AccessError:
            return request.redirect('/my')

        pdf = order_sale.sudo().render_qweb_pdf([order_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

class InteritPortalAccount(CustomerPortal):

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, **kw):
        try:
            invoice_sudo = self._invoice_check_access(invoice_id, access_token)
            invoice_sudo_one = self._invoice_check_access_one(invoice_sudo, access_token)
            # origin_name = request.env['account.invoice'].sudo().browse(invoice_id)

        except AccessError:
            return request.redirect('/my')

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        if invoice_sudo_one == 'sales':
            return request.render("ars_vehicle_sales.ars_portal_invoice_page", values)
        else:
            return request.render("ars_after_sales.ars_portal_aftersales_page", values)

    @http.route(['/my/invoices/pdf/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_report(self, invoice_id, access_token=None, **kw):
        try:
            invoice_sudo = self._invoice_check_access(invoice_id, access_token)
        except AccessError:
            return request.redirect('/my')

        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref('ars_vehicle_sales.before_sales_invoice').sudo().render_qweb_pdf([invoice_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    def _invoice_check_access_one(self, invoice_id, access_token=None):
        origin_sudo = request.env['sale.order'].sudo().search([('name', '=', invoice_id.sudo().origin)])
        try:
            origin_sudo.check_access_rights('read')
            origin_sudo.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(origin_sudo.access_token, access_token):
                raise
        return origin_sudo.sale_aftersales

# class Ac-ars(http.Controller):
#     @http.route('/ac-ars/ac-ars/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ac-ars/ac-ars/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ac-ars.listing', {
#             'root': '/ac-ars/ac-ars',
#             'objects': http.request.env['ac-ars.ac-ars'].search([]),
#         })

#     @http.route('/ac-ars/ac-ars/objects/<model("ac-ars.ac-ars"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ac-ars.object', {
#             'object': obj
#         })