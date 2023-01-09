from odoo import models, fields, api,_
from datetime import datetime
import time


class ResCompany(models.Model):
    _inherit = "res.company"
    _description = "Company master"

    is_child = fields.Boolean()
    is_parent = fields.Boolean()
    connection_type = fields.Selection([('internal', 'Internal'),('external', 'External')])
    internal_url = fields.Char()
    external_url = fields.Char()
    company_code = fields.Char()
    db_name = fields.Char()
    port = fields.Char()
    host = fields.Char()
    db_user_name = fields.Char()
    db_password = fields.Char()
    