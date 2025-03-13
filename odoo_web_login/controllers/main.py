# -*- encoding: utf-8 -*-
##############################################################################
#
#    Samples module for Odoo Web Login Screen
#    Copyright (C) 2017- XUBI.ME (http://www.xubi.me)
#    @author binhnguyenxuan (https://www.linkedin.com/in/binhnguyenxuan)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#    
#
##############################################################################

import ast
from http.client import responses
from pyexpat.errors import messages

from odoo.addons.web.controllers.main import Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import pytz
import datetime
import logging
import requests
from odoo import http
from odoo.http import request
_logger = logging.getLogger(__name__)


def set_background():
    param_obj = request.env['ir.config_parameter'].sudo()
    request.params['disable_footer'] = ast.literal_eval(param_obj.get_param('login_form_disable_footer')) or False
    request.params['disable_database_manager'] = ast.literal_eval(
        param_obj.get_param('login_form_disable_database_manager')) or False

    change_background = ast.literal_eval(param_obj.get_param('login_form_change_background_by_hour')) or False
    if change_background:
        config_login_timezone = param_obj.get_param('login_form_change_background_timezone')
        tz = config_login_timezone and pytz.timezone(config_login_timezone) or pytz.utc
        current_hour = datetime.datetime.now(tz=tz).hour or 10

        if (current_hour >= 0 and current_hour < 3) or (current_hour >= 18 and current_hour < 24):  # Night
            request.params['background_src'] = param_obj.get_param('login_form_background_night') or ''
        elif current_hour >= 3 and current_hour < 7:  # Dawn
            request.params['background_src'] = param_obj.get_param('login_form_background_dawn') or ''
        elif current_hour >= 7 and current_hour < 16:  # Day
            request.params['background_src'] = param_obj.get_param('login_form_background_day') or ''
        else:  # Dusk
            request.params['background_src'] = param_obj.get_param('login_form_background_dusk') or ''
    else:
        request.params['background_src'] = param_obj.get_param('login_form_background_default') or ''


#----------------------------------------------------------
# Odoo Web web Controllers
#----------------------------------------------------------
class LoginHome(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        set_background()
        recaptcha_response = kw.get('g-recaptcha-response')
        secret_key = "6LeRC_EqAAAAAB6Nz_mJSychKq9rIizkSyERVrju"  # Replace with your actual secret key

        # Verify reCAPTCHA
        if recaptcha_response:
            response = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={'secret': secret_key, 'response': recaptcha_response}
            ).json()
            print(response, recaptcha_response)
            # If reCAPTCHA is invalid, return an error message
            if not response.get("success"):
                return request.render("web.login", {
                    'error': "Invalid CAPTCHA. Please try again."
                })
        return super(LoginHome, self).web_login(redirect, **kw)


class AuthSignupHomeInherit(AuthSignupHome):

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        set_background()
        return super(AuthSignupHomeInherit, self).web_auth_reset_password(*args, **kw)

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        set_background()
        return super(AuthSignupHomeInherit, self).web_auth_signup(*args, **kw)

    @http.route("/get_password_instruction_messages", type="json", auth="public")
    def get_password_instruction(self):
        company = request.env.user.company_id
        instructions = {
            "password_lower": company.password_lower if company.password_lower else '',
            "password_upper": company.password_upper if company.password_upper else '',
            "password_numeric": company.password_numeric if company.password_numeric else '',
            "password_special": company.password_special if company.password_special else '',
            "password_length": company.password_length if company.password_length else '',
        }
        return instructions