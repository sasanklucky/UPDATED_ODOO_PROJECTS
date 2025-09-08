from odoo import fields, models, api, _
import requests
import json
import datetime
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import base64
from num2words import num2words
import logging

_logger = logging.getLogger("_____")

class BranchAccountTax(models.Model):
    _inherit = 'account.tax'

    tcs_add_on_tax = fields.Boolean(string="TCS Add On Tax Amount")
    tcs_amt_percentage = fields.Float(digits=(16, 4), default=0.0, tracking=True, string="TCS Amount % [Apply Only On E-Invoice]")