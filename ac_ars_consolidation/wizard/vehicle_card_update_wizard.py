from email.policy import default
from math import trunc

from odoo import models, fields, api, registry, SUPERUSER_ID, sql_db, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date, datetime, time, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import contextlib
import logging
from odoo.sql_db import db_connect

class FetchDataDealerVehicleCard(models.TransientModel):
    _name = "vehiclecard.fetch.wizard"

    dealer_setup_id = fields.Many2one("ars.consolidation.setup", required=True, readonly=True)
    is_service_enable = fields.Boolean(string="Fetch Service History", default=False)
    is_ownership_enable = fields.Boolean(string="Fetch Ownership History", default=False)
    is_wholesale_enable = fields.Boolean(string="Fetch Wholesale History", default=False)
    is_insurance_enable = fields.Boolean(string="Fetch Insurance History", default=False)
    is_emission_enable = fields.Boolean(string="Fetch Emission History", default=False)


    is_update_vehicle_card = fields.Boolean(string="Update Vehicle Card", default=False)
    is_update_vehicle_card_compare = fields.Boolean(string="Update Vehicle Card With Comparison",default=False)


    def fetch_vehicle_from_the_dealer(self):
        print("fetch_vehicle_from_the_dealer")
        if self.is_service_enable and self.is_update_vehicle_card:
            self.dealer_setup_id.fetch_vehicle_service_history_details()
        if self.is_ownership_enable and self.is_update_vehicle_card:
            self.dealer_setup_id.fetch_ownership_history_details()
        # if self.is_insurance_enable and self.is_update_vehicle_card:
        #     self.dealer_setup_id.fetch_insurance_history_details()
        # if self.is_emission_enable and self.is_update_vehicle_card:
        #     self.dealer_setup_id.fetch_emission_history_details()
        # if self.is_wholesale_enable and self.is_update_vehicle_card:
        #     self.dealer_setup_id.fetch_wholesale_history_details()




    def fetch_missing_vehicle_details(self):
        print("fetch_missing_vehicle_details")
        if self.is_service_enable and self.is_update_vehicle_card_compare:
            self.dealer_setup_id.fetch_missing_vehicle_service_history_details()
        if self.is_ownership_enable and self.is_update_vehicle_card_compare:
            self.dealer_setup_id.fetch_missing_ownership_history_details()
        # if self.is_insurance_enable and self.is_update_vehicle_card_compare:
        #     self.dealer_setup_id.fetch_missing_vehicle_insurance_history_details()
        # if self.is_emission_enable and self.is_update_vehicle_card_compare:
        #         self.dealer_setup_id.fetch_missing_vehicle_emission_history_details()
        # if self.is_wholesale_enable and self.is_update_vehicle_card_compare:
        #         self.dealer_setup_id.fetch_missing_vehicle_wholesale_history_details()

