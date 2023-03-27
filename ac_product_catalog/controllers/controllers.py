# -*- coding: utf-8 -*-
from odoo import http

# class AcProductCatalog(http.Controller):
#     @http.route('/ac_product_catalog/ac_product_catalog/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ac_product_catalog/ac_product_catalog/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ac_product_catalog.listing', {
#             'root': '/ac_product_catalog/ac_product_catalog',
#             'objects': http.request.env['ac_product_catalog.ac_product_catalog'].search([]),
#         })

#     @http.route('/ac_product_catalog/ac_product_catalog/objects/<model("ac_product_catalog.ac_product_catalog"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ac_product_catalog.object', {
#             'object': obj
#         })