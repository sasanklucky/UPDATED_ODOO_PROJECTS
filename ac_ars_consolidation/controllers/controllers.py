# -*- coding: utf-8 -*-
from odoo import http

# class AcArsConsolidation(http.Controller):
#     @http.route('/ac_ars_consolidation/ac_ars_consolidation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ac_ars_consolidation/ac_ars_consolidation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ac_ars_consolidation.listing', {
#             'root': '/ac_ars_consolidation/ac_ars_consolidation',
#             'objects': http.request.env['ac_ars_consolidation.ac_ars_consolidation'].search([]),
#         })

#     @http.route('/ac_ars_consolidation/ac_ars_consolidation/objects/<model("ac_ars_consolidation.ac_ars_consolidation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ac_ars_consolidation.object', {
#             'object': obj
#         })