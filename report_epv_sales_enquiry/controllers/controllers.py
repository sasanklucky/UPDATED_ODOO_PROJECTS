# -*- coding: utf-8 -*-
from odoo import http

# class ReportEpvSalesEnquiry(http.Controller):
#     @http.route('/report_epv_sales_enquiry/report_epv_sales_enquiry/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_epv_sales_enquiry/report_epv_sales_enquiry/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_epv_sales_enquiry.listing', {
#             'root': '/report_epv_sales_enquiry/report_epv_sales_enquiry',
#             'objects': http.request.env['report_epv_sales_enquiry.report_epv_sales_enquiry'].search([]),
#         })

#     @http.route('/report_epv_sales_enquiry/report_epv_sales_enquiry/objects/<model("report_epv_sales_enquiry.report_epv_sales_enquiry"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_epv_sales_enquiry.object', {
#             'object': obj
#         })