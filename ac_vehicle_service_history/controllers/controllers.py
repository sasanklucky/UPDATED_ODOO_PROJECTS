# -*- coding: utf-8 -*-
from odoo import http

# class AcVehicleServiceHistory(http.Controller):
#     @http.route('/ac_vehicle_service_history/ac_vehicle_service_history/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ac_vehicle_service_history/ac_vehicle_service_history/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ac_vehicle_service_history.listing', {
#             'root': '/ac_vehicle_service_history/ac_vehicle_service_history',
#             'objects': http.request.env['ac_vehicle_service_history.ac_vehicle_service_history'].search([]),
#         })

#     @http.route('/ac_vehicle_service_history/ac_vehicle_service_history/objects/<model("ac_vehicle_service_history.ac_vehicle_service_history"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ac_vehicle_service_history.object', {
#             'object': obj
#         })