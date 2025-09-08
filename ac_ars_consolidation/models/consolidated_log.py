# -*- coding: utf-8 -*-
import time
import psycopg2
import contextlib
from datetime import datetime
from ast import literal_eval
from psycopg2 import pool
from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm


class ARSConsolidationLogs(models.Model):
    _name = 'ars.consolidation.logs'


    name = fields.Char()
    status = fields.Selection([('updated', 'Updated'), ('pending', 'Pending'), ('exception', 'Exception')])
    updated_on = fields.Datetime('Updated On')
    exception_reason = fields.Text("Exception")
    db_name = fields.Char(string="DB Name")
    dealer_vehicle_card_id = fields.Char(string="Vehicle Card Id")
    vin_no = fields.Char(string="VIN Number")
    is_updated = fields.Boolean(string="Updated", default=False)
    # active= fields.Booelan(string="Active", default=False)
    dealer_setup_id = fields.Many2one("ars.consolidation.setup", string="Dealer Setup", ondelete='cascade', index=True, copy=False, readonly=True)

