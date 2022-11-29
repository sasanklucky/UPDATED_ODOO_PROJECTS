from odoo import models, fields, api,_
from datetime import datetime
import time


class StatusDashboard(models.Model):
    _name = "cre.dashboard"
    _description = "Status Dashboard"


    name = fields.Char()

