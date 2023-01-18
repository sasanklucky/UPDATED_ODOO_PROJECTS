from odoo import models, fields, api,_
from datetime import datetime
import time


class ParentChildConfiguration(models.Model):
    _name = "parent.child.configuration"
    _description = "Parent Child Configuration"


    connection_type = fields.Selection([('internal', 'Internal'),('external', 'External')])
    child_id = fields.Many2one('res.company', string='Child Comapny', domain=[('parent_id','!=',False)])
    # internal_url = fields.Char()
    external_url = fields.Char()
    db_name = fields.Char()