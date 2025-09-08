# -*- coding: utf-8 -*-
from odoo import http

# class ArsTheme(http.Controller):
#     @http.route('/ars_theme/ars_theme/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ars_theme/ars_theme/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ars_theme.listing', {
#             'root': '/ars_theme/ars_theme',
#             'objects': http.request.env['ars_theme.ars_theme'].search([]),
#         })

#     @http.route('/ars_theme/ars_theme/objects/<model("ars_theme.ars_theme"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ars_theme.object', {
#             'object': obj
#         })