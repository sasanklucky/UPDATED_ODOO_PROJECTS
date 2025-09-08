# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ARSModel(models.Model):
    _inherit = 'product.template'

    name = fields.Char()
    engine_type_code = fields.Char(string='Engine Type Code')
    no_of_cylinder = fields.Char(string='No of Cylinder')
    cylinder_capacity = fields.Char(string='Cylinder Capacity')
    power_kw = fields.Char(string='Power(KW)')
    power_hp = fields.Char(string='Power(HP)')
    top_speed = fields.Char(string='Top Speed')
    accellaration = fields.Char(string='Acceleration')
    transmission_type_code = fields.Char(string='Transmission Type Code')
    tyre_details = fields.Char(string='Tyre Details ')
    no_of_doors = fields.Char(string='No of Doors')
    empty_weight = fields.Float(string='Empty Weight')
    total_weight = fields.Float(string='Total Weight')
    roof_load = fields.Char(string='Roof Load')
    trailer_load = fields.Char(string='Trailer Load')
    awd = fields.Char(string='AWD')
    no_of_axeles = fields.Char(string='No of Axeles')
    wheel_base = fields.Char(string='Wheel Base')
    tyre_details = fields.Char(string='Tyre Details')
    front_axle_load = fields.Char(string='Front Axle Load')
    rear_axle_load = fields.Char(string='Rear Axle Load')
    description_form22 = fields.Text(
        'Form-22 Description', translate=True,
        help="The Form-22 Certificate Description")


# class website_module(models.Model)
#     _inherit='website.menu'
#
#     @api.model
#     def create(self,vals):
#         res = super(website_module, self).create(vals)
#         return res

