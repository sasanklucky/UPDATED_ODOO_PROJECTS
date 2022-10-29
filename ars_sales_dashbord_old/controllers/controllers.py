# -*- coding: utf-8 -*-
from odoo import http

# class JavaTest(http.Controller):
#     @http.route('/ars_sales_dashbord/ars_sales_dashbord/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ars_sales_dashbord/ars_sales_dashbord/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ars_sales_dashbord.listing', {
#             'root': '/ars_sales_dashbord/ars_sales_dashbord',
#             'objects': http.request.env['ars_sales_dashbord.ars_sales_dashbord'].search([]),
#         })

#     @http.route('/ars_sales_dashbord/ars_sales_dashbord/objects/<model("ars_sales_dashbord.ars_sales_dashbord"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ars_sales_dashbord.object', {
#             'object': obj
#         })