# -*- coding: utf-8 -*-
from odoo import http

# class AcVehicleManagement(http.Controller):
#     @http.route('/ac_vehicle_management/ac_vehicle_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ac_vehicle_management/ac_vehicle_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ac_vehicle_management.listing', {
#             'root': '/ac_vehicle_management/ac_vehicle_management',
#             'objects': http.request.env['ac_vehicle_management.ac_vehicle_management'].search([]),
#         })

#     @http.route('/ac_vehicle_management/ac_vehicle_management/objects/<model("ac_vehicle_management.ac_vehicle_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ac_vehicle_management.object', {
#             'object': obj
#         })