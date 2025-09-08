from odoo import models, fields, api, _
import secrets
from datetime import datetime, timedelta
from odoo import tools




class ResUsers(models.Model):
    _inherit = 'res.users'

    web_api_key = fields.Char(string="Web API Key", readonly=True)
    web_api_expiry_time = fields.Datetime(string="Web API Expiry", readonly=1)

    def generate_web_api_key(self, user_id):
        if user_id:
            user = self.browse(user_id)
            api_key = secrets.token_urlsafe(32)
            now = datetime.now()
            expiry_time = now + timedelta(days=1)
            user.sudo().write({
                'web_api_key': api_key,
                'web_api_expiry_time': expiry_time
            })
            return api_key, expiry_time
        else:
            api_key = secrets.token_urlsafe(32)
            expiry_time = datetime.now() + timedelta(days=1)
            self.web_api_key = api_key
            self.web_api_expiry_time = expiry_time
            return self.api_key, self.api_expiry_time


    def generate_web_api_key_for_user(self):
        api_key = secrets.token_urlsafe(32)
        expiry_time = datetime.now() + timedelta(days=1)
        self.web_api_key = api_key
        self.web_api_expiry_time = expiry_time
        return self.web_api_key, self.web_api_expiry_time







