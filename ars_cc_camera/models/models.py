# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ARSResource(models.Model):
    _inherit = 'resource.resource'

    ip_address = fields.Many2many('cc.camera', string="IP Address")

class ARSCCCamera(models.Model):
    _name = 'cc.camera'

    name = fields.Char(string="IP Address")
    camera_name = fields.Char(string="Camera Name")
    port_num = fields.Integer(string="Port Number")
    username = fields.Char(string="Username")
    password = fields.Char(string="Password")


