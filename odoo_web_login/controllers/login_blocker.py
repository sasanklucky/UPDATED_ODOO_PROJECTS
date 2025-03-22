from odoo import http
from odoo.http import request, Response
from datetime import datetime, timedelta
from odoo import api, fields, models, _

class CustomLoginController(http.Controller):

    @http.route('/lock_user', type='json', auth='public', methods=['POST'])
    def lock_user(self, login):
        if not login:
            return {'status': 'error', 'message': 'Missing login parameter'}

        user = request.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        if user:
            pass_word_expiry = user.company_id.password_expiration #days in integer formate like 10 or 20 days
            write_date = fields.Datetime.from_string(user.password_write_date)
            today = fields.Datetime.from_string(fields.Datetime.now())
            days_since_last_change = (today - write_date).days
            days_left_to_expiry = max(pass_word_expiry - days_since_last_change, 0)
            total_days_to_back = days_since_last_change + days_left_to_expiry + 1
            computed_for_set_expiry_day = fields.Datetime.to_string(today - timedelta(days=total_days_to_back))
            print(computed_for_set_expiry_day, 'computed_for_set_expiry_day')
            user.sudo().write({
                'active': False,
                'password_write_date': computed_for_set_expiry_day,
            })
            return {'status': 'locked'}

        return {'status': 'not_found'}

    @http.route('/check_user',type='json', auth='public')
    def check_users(self, login):
        if not login:
            return {'status': 'error', 'message': 'Missing login parameter'}

        user = request.env['res.users'].sudo().search([('login', '=', login),('active', 'in', [True, False])], limit=1)
        print(user, 'KRISHNAAAAA')
        if not user:
            # user.sudo().write({'active': False})
            return {'status': 'invalid'}
        elif not user.active:
            return {'status': 'not_present'}

        return {'status': 'found'}

    @http.route('/store_user_ip', type='json', auth="public")
    def store_user_ip(self, login, ip, city, region, country, latitude, longitude):
        user = request.env['res.users'].sudo().search([('login', '=', login),('active', 'in', [True, False])], limit=1) # Get the logged-in user

        request.env['user.ip.log'].sudo().create({
            'user_id': user.id,
            'ip_address': ip,
            'city': city,
            'region': region,
            'country': country,
            'latitude': latitude,
            'longitude': longitude
        })

        return {'status': 'success'}