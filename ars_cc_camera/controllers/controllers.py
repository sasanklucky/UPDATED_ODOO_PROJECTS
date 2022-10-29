# -*- coding: utf-8 -*-
from odoo import http

# class ArsCcCamera(http.Controller):
#     @http.route('/ars_cc_camera/ars_cc_camera/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ars_cc_camera/ars_cc_camera/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ars_cc_camera.listing', {
#             'root': '/ars_cc_camera/ars_cc_camera',
#             'objects': http.request.env['ars_cc_camera.ars_cc_camera'].search([]),
#         })

#     @http.route('/ars_cc_camera/ars_cc_camera/objects/<model("ars_cc_camera.ars_cc_camera"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ars_cc_camera.object', {
#             'object': obj
#         })