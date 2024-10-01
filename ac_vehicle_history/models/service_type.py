from odoo import models, fields, api, _
from datetime import datetime
import logging
import json

_logger = logging.getLogger(__name__)


class ServiceType(models.Model):
    _inherit = "service.type"

    sequence = fields.Integer(string="Sequence", default=0)
    code = fields.Char("code", required=1)

class ServiceHistory(models.Model):
    _inherit = "service.history"


    cons_service_history_id = fields.Integer('Consolidate Service History Id')
    service_type_name = fields.Char(string="Service Type Name")
    mileage_in = fields.Integer(string="Mileage")
    service_code = fields.Char(string="Service Code")
    dealer_db_name = fields.Char("Dealer DB Name", required=True)

