# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale(models.Model):
    _inherit = 'sale.order'

    is_online = fields.Boolean()