# -*- coding: utf-8 -*-
from odoo import http

# class AcPartsPurchase(http.Controller):
#     @http.route('/ac_parts_purchase/ac_parts_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ac_parts_purchase/ac_parts_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ac_parts_purchase.listing', {
#             'root': '/ac_parts_purchase/ac_parts_purchase',
#             'objects': http.request.env['ac_parts_purchase.ac_parts_purchase'].search([]),
#         })

#     @http.route('/ac_parts_purchase/ac_parts_purchase/objects/<model("ac_parts_purchase.ac_parts_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ac_parts_purchase.object', {
#             'object': obj
#         })