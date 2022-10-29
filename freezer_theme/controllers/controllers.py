# -*- coding: utf-8 -*-
from odoo import http

class FreezerTheme(http.Controller):
    @http.route('/bulestar_freezer  ', auth='public')
    def index(self, **kw):
        return "Hello, world"

#     @http.route('/freezer_theme/freezer_theme/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('freezer_theme.listing', {
#             'root': '/freezer_theme/freezer_theme',
#             'objects': http.request.env['freezer_theme.freezer_theme'].search([]),
#         })

#     @http.route('/freezer_theme/freezer_theme/objects/<model("freezer_theme.freezer_theme"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('freezer_theme.object', {
#             'object': obj
#         })