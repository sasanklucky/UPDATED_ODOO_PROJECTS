import logging
import werkzeug
import json
from odoo import http, _, fields
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo.http import request
import urllib
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home

_logger = logging.getLogger(__name__)
import requests

import passlib.context
import math, random


def generateOTP():
    digits = "0123456789"
    OTP = ""
    for i in range(4):
        OTP += digits[int(math.floor(random.random() * 10))]
    return OTP


from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class OAuthLoginOtp(AuthSignupHome):

    @http.route('/web/login', type='http', auth="public", website=True)
    def web_login(self, *args, **kw):
        _logger.info("Starting web login process")
        if request.httprequest.method == 'POST':
            print(kw)
            request.params['login_success'] = False
            email = kw.get('login')
            password = kw.get('password')
            _logger.info(f"Login attempt for email: {email}")

            try:
                user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                if user:
                    _logger.info("User found, checking credentials.")
                    user.sudo().check_credentials(password)
                    _logger.info("Credentials validated. Generating OTP.")

                    # Check if OTP already exists in the session
                    if 'otp_sent' not in request.session:
                        # Generate OTP and store in user record
                        otp = random.randint(1000, 9999)
                        user.sudo().write({'otp': otp})
                        _logger.info(f"OTP generated: {otp}")

                        # Send OTP and log SMS process
                        try:
                            self.send_otp_via_sms(user.partner_id.mobile, otp)
                            _logger.info("OTP sent successfully.")
                            self.send_otp_via_email(email, otp)
                        except Exception as sms_error:
                            _logger.error(f"Failed to send OTP: {sms_error}")
                            return request.render('web.login', {'error': 'Failed to send OTP. Please try again.'})

                        # Mark OTP as sent in the session
                        request.session['otp_sent'] = True
                    else:
                        _logger.info("OTP already sent, skipping resend.")

                    # Store session details and redirect
                    request.session['user_email'] = email
                    request.session['user_password'] = password
                    _logger.info("Redirecting to OTP verification page.")
                    return request.render('sr_otp_login.otp_verification_template', {'email': email, 'mobile': f"OTP Successfully Send To {'*' * 6}{user.partner_id.mobile[-4:]} & "})
                else:
                    _logger.warning("User not found.")
                    return request.render('odoo_web_login.login', {'error': 'Invalid email or password.'})
            except Exception as login_error:
                _logger.error(f"Error during login: {login_error}")
                return request.render('odoo_web_login.login', {'error': 'Invalid email or password.'})

        _logger.info("Default login flow (GET request).")
        return super(OAuthLoginOtp, self).web_login(*args, **kw)

    def send_otp_via_sms(self, mobile_number, otp):
        try:
            # Search for the active SMS API configuration
            sms_config = request.env['sms.configure'].sudo().search([('active', '=', True)], limit=1)
            if not sms_config:
                _logger.error("No active SMS API configuration found.")
                raise Exception("No active SMS API configuration found.")

            # Build the URL dynamically
            url = sms_config.sms_api
            params = {}

            for param in sms_config.val_ids:
                if param.name == "to":
                    params[param.name] = mobile_number
                elif param.name == "message":
                    params[
                        param.name] = f"Your login OTP is {otp}. It is valid for 5 minutes. Please keep this code confidential. If you didn’t request this code, contact support Autochip India."
                else:
                    params[param.name] = param.value

            # Encode dynamic values (e.g., the message)
            if "message" in params:
                params["message"] = urllib.parse.quote(params["message"])

            # Construct the full URL
            final_url = f"{url}?" + "&".join(f"{key}={value}" for key, value in params.items())

            _logger.info(f"Sending SMS via URL: {final_url}")

            # Send the SMS request
            try:
                response = requests.post(final_url, timeout=10)  # Added timeout to prevent long delays
                response_text = response.text
                status = 'sent' if response.status_code == 200 else 'exception'
                failed_reason = "None" if status == 'sent' else f"Response: {response_text}"
            except requests.exceptions.RequestException as e:
                response_text = str(e)
                status = 'exception'
                failed_reason = response_text

            # Log SMS details and create a record
            try:
                company_id = request.env.user.company_id.id if request.env.user.company_id else None
                _logger.info(f"Creating SMS record for phone: {mobile_number}, company_id: {company_id}")

                sms_record = request.env['sms.record'].sudo().create({
                    'name': "Login OTP",
                    'phone': mobile_number,
                    'date': fields.Datetime.now(),
                    'company_id': company_id,
                    'body': f"Your login OTP is {otp}",
                    'response': response_text,
                    'url': final_url,
                    'stage': status,
                    'failed_reason': failed_reason if status != 'sent' else '',
                })
                _logger.info(f"SMS record created successfully: {sms_record.id}")
            except Exception as record_error:
                _logger.error(f"Error creating SMS record: {record_error}")
                raise Exception("Failed to log SMS record.")

            # If the SMS was not sent successfully, raise an exception
            if status != 'sent':
                raise Exception("Failed to send OTP. Please try again later.")
        except Exception as sms_error:
            _logger.error(f"Error in send_otp_via_sms: {sms_error}")
            # Re-raise the exception to handle it in the caller function
            raise

    def send_otp_via_email(self, email, otp):
        """
        Function to send OTP via email.
        """
        if not email:
            raise ValueError("User email is missing.")

        # Get the default sender email from the Odoo Outgoing Mail Server
        mail_server = request.env['ir.mail_server'].sudo().search([('name', '=', 'OTP Outgoing Mail')], limit=1)
        email_from = mail_server.smtp_user if mail_server and mail_server.smtp_user else "no-reply@example.com" # Default to no-reply if no mail server configured

        subject = "Login OTP For BYD Portal"
        body = f"Your login OTP is {otp}. It is valid for 5 minutes. Please keep this code confidential. If you didn’t request this code, contact support Autochip India."

        # Create the email
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': email,
            'email_from': email_from,
        }

        # Create and send the email
        request.env['mail.mail'].sudo().create(mail_values).send()

    @http.route('/web/resend_otp', type='json', auth="public", website=True)
    def resend_otp(self, **kwargs):
        email = request.session.get('user_email')
        print(email, 'email')
        if not email:
            return {'success': False, 'message': 'Session expired. Please log in again.'}

        user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if not user:
            return {'success': False, 'message': 'User not found.'}

        try:
            otp = random.randint(1000, 9999)
            user.sudo().write({'otp': otp})
            print(otp, 'otp')
            self.send_otp_via_sms(user.partner_id.mobile, otp)
            self.send_otp_via_email(email, otp)
            return {'success': True, 'message': 'OTP sent successfully.'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
            # Log SMS details and create a record


    @http.route('/web/otp_verify', type='http', auth="public", website=True)
    def otp_verify(self, *args, **kw):
        if request.httprequest.method == 'POST':
            qcontext = request.params.copy()
            # Retrieve email and password from the session
            email = request.session.get('user_email')
            # Combine the OTP parts to form the full OTP
            otp_customer = "".join([qcontext.get('otp_one', ''), qcontext.get('otp_two', ''),
                                    qcontext.get('otp_three', ''), qcontext.get('otp_four', '')])

            # Validate the OTP and email fields
            if not email or not otp_customer:
                return request.render('sr_otp_login.otp_verification_template',
                                      {'email': email, 'error': 'Please enter all OTP fields.'})

            # Search for the user
            user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)

            # Verify OTP for the user
            if user and str(user.otp) == otp_customer:
                # Retrieve password from the session
                password = request.session.get('user_password')
                if not password:
                    # Session password is missing (could be due to timeout)
                    return request.render('sr_otp_login.otp_verification_template',
                                          {'email': email, 'error': 'Session expired. Please log in again.'})

                try:
                    # Authenticate the user
                    user.sudo().check_credentials(password)  # Check the password

                    # Create an authenticated session
                    request.session.authenticate(request.db, email, password)

                    # Redirect to main dashboard
                    return request.redirect('/web')

                except Exception as e:
                    # Handle failed authentication due to incorrect credentials or other issues
                    return request.render('sr_otp_login.otp_verification_template',
                                          {'email': email, 'error': 'Authentication failed, please try again.'})
            else:
                # Incorrect OTP
                return request.render('sr_otp_login.otp_verification_template',
                                      {'email': email, 'error': 'Invalid OTP. Please try again.'})

        # If not a POST request, redirect to login
        return request.redirect('/web/login')

    def get_auth_signup_config(self):
        response = super(OAuthLoginOtp, self).get_auth_signup_config()
        company_id = request.env['res.company'].sudo().search([('id', '=', 1)])
        response.update({

            'signup_otp': company_id.use_otp_login,
        })
        return response

    @http.route('/phoneexist', type='http', auth="public", website=True, methods=['GET'], csrf=False)
    def validate_referral_code(self, **kwargs):
        """Controller for validating referral codes"""
        result_dict = {}
        params_keys = list(kwargs.keys())
        phone = kwargs['sendto']
        name = kwargs['name']
        if phone and name:
            partner_ids = request.env['res.users'].sudo().search(['|', ('phone', '=', phone), ('login', '=', name)])
            if partner_ids:
                return "False"
            else:
                return "True"
        return json.dumps(result_dict)

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = {key: qcontext.get(key) for key in ('login', 'name', 'password', 'otp', 'phone')}
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        user_id = request.env['res.users'].sudo().search([('phone', '=', values.get('phone'))])
        if user_id:
            raise UserError(_("Phone number is already registered."))
        if values.get('phone'):
            if len(values.get('phone')) != 10 or not values.get('phone').isdigit():
                raise UserError(_("Not a valid Phone Number."))

        supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

    @http.route('/web/request_otp', type='http', auth='public', website=True, sitemap=False)
    def web_auth_request_otp(self, *args, **kw):

        qcontext = request.params.copy()
        try:
            if qcontext.get('mobile'):
                user_id = request.env['res.users'].sudo().search([('phone', '=', qcontext.get('mobile'))], limit=1)
                if user_id:
                    qcontext.update({'user': user_id.id})
                    otp = generateOTP()
                    company_id = request.env['res.company'].sudo().search([('id', '=', 1)])
                    if company_id and company_id.otp_message:
                        if '%s' not in company_id.otp_message:
                            text = str(company_id.otp_message) + str(otp)
                        else:
                            text = str(company_id.otp_message).replace('%s', otp)
                    else:
                        text = """Dear Customer,
%s is your one time password (OTP). Please enter the OTP to proceed.
Thank you,
Team Seeroo""" % otp

                    data_url = ''

                    try:
                        if company_id and company_id.use_otp_login:
                            data_url = company_id and company_id.otp_message_url or ''
                            phone_key = company_id and str(company_id.phone_key) or ''
                            message_key = company_id and str(company_id.message_key) or ''

                            data_url = str(data_url).replace(phone_key, str("91" + qcontext.get('mobile')))
                            data_url = str(data_url).replace(message_key, str(text))

                        result = requests.post(data_url, timeout=20)
                        qcontext.update({'otp_original': otp})
                        response = request.render('sr_otp_login.verify_otp', qcontext)
                        return response
                    except:
                        response = request.render('sr_otp_login.request_otp', qcontext)
                        return response

                else:
                    try:
                        raise UserError(_('This Mobile number is not registered..'))
                    except UserError as e:
                        qcontext['error'] = e.name or e.value
                        response = request.render('sr_otp_login.request_otp', qcontext)
                        return response

            if qcontext.get('otp_one') and qcontext.get('otp_two') and qcontext.get('otp_three') and qcontext.get(
                    'otp_four'):
                otp_customer = str(
                    qcontext.get('otp_one') + qcontext.get('otp_two') + qcontext.get('otp_three') + qcontext.get(
                        'otp_four'))
                if otp_customer != qcontext.get('otp_original'):
                    try:
                        raise UserError(_('Verification Failed'))
                    except UserError as e:
                        qcontext['error'] = e.name or e.value
                        response = request.render('sr_otp_login.verify_otp', qcontext)
                        return response
                else:
                    user_id = request.env['res.users'].sudo().search([('id', '=', qcontext.get('user'))], limit=1)
                    request.env.cr.execute(
                        "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                        [qcontext.get('user')]
                    )
                    hashed = request.env.cr.fetchone()[0]
                    qcontext.update({'login': user_id.sudo().login,
                                     'name': user_id.sudo().partner_id.name,
                                     'password': hashed + 'mobile_otp_login'})
                    request.params.update(qcontext)
                    return self.web_login(*args, **kw)

        except UserError as e:
            qcontext['error'] = e.name or e.value

        response = request.render('sr_otp_login.request_otp', {})
        return response
