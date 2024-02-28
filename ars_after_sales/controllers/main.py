#-*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import ensure_db, login_and_redirect
import werkzeug.utils
import webbrowser
from odoo.addons.website.controllers.main import Website
import json
from odoo.exceptions import UserError

import re
import simplejson
import odoo
from odoo.addons import auth_signup

class Ac_ars(http.Controller):
    @http.route(['/web/logins'], type='http', auth='none', website=True)
    def get_web_customlogins(self, **post):
        ensure_db()
        db = post.get('db')
        user = post.get('login')
        passwd = post.get('password')
        login_and_redirect(db, user, passwd)
        return werkzeug.utils.redirect("/service_planner")




    @http.route(['/web/customlogin1'], type='http', auth='none', website=True)
    def get_web_customlogin(self, **post):
        db = request.session.db
        request.session.logout(keep_db=True)
        user = post.get('login')
        users = user.replace("autochip","@autochip")
        passwd = post.get('password')
        # passwd = 'a'
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = "%s/web/session/authenticate" % base_url
        session_id = request.session.sid
        url = '/web/logins?csrf_token=%s&login=%s&password=%s&db=%s'%(session_id, users, passwd, db)
        return werkzeug.utils.redirect(url)



    @http.route(['/warranty_stage_value'], type='json', auth="user", website=True, csrf=False)
    def warranty_stage(self, **post):
        sale_id = post.get('data')
        sale_obj = request.env['sale.order'].browse(sale_id)
        warranty_stage = []
        approved_count = 0
        reject_count = 0
        hold_count = 0
        re_submission_count = 0
        war_approved = {}
        war_reject = {}
        war_hold = {}
        war_re_submission = {}
        for line_id in sale_obj.order_line:
            if line_id.apr_action:
                if line_id.apr_action == 'approved':
                    approved_count += 1
                elif line_id.apr_action == 'reject':
                    reject_count += 1
                elif line_id.apr_action == 'hold':
                    hold_count += 1
                elif line_id.apr_action == 're_submission':
                    re_submission_count += 1
        if approved_count:
            war_approved.update({'colors': '#00FF00', 'approved_count': approved_count, 'stages': 'Approved'})
            warranty_stage.append(war_approved)
        if reject_count:
            war_reject.update({'colors': '#DB3838', 'reject_count': reject_count, 'stages': 'Reject'})
            warranty_stage.append(war_reject)
        if hold_count:
            war_hold.update({'colors': '#1E90FF', 'hold_count': hold_count, 'stages': 'Hold'})
            warranty_stage.append(war_hold)
        if re_submission_count:
            war_re_submission.update({'colors': '#C37373', 're_submission_count': re_submission_count, 'stages': 'Re Submission'})
            warranty_stage.append(war_re_submission)

        data = {'sale_line': warranty_stage}
        return data

    # @http.route(['/WarrantyClaims/<int:warranty_id>/<int:user_id>'], type='http', auth='none', website=True)
    # def Redirect_to_Claims(self, warranty_id, user_id, **post):
    #
    #
    #     return werkzeug.utils.redirect("/service_planner")




class ARSLogin(Website):

    @http.route(website=True, auth="public")
    def web_login(self, redirect=None, *args, **kw):
        if not redirect:
            redirect = '/service_planner'
        r = super(ARSLogin, self).web_login(redirect=redirect, *args, **kw)
        return r


    @http.route(['/service_planner'], type='http', auth="user", website=True)
    def service_planner(self, **kwargs):
        land_category = request.env['landing.setting'].search([('landing_user', '=', request.env.user.id)])
        if land_category:
            redirect = land_category.sudo().landing_link.sudo().url
            return werkzeug.utils.redirect(redirect)
        else:
            home = '/'
            return werkzeug.utils.redirect(home)

    @http.route(['/WarrantyClaim/<int:id>'], type='http', auth="user", website=True)
    def warranty_claims(self, id, **kwargs):
        if id:
           vals = {'warranty': request.env['ars.sale.warranty'].browse(id)}
           return request.render("ars_after_sales.warranty_claim", vals)
        return True
        # if land_category:
        #     redirect = land_category.sudo().landing_link.sudo().url
        #     return werkzeug.utils.redirect(redirect)
        # else:
        #     home = '/'
        #     return werkzeug.utils.redirect(home)



    @http.route(['/Warranty-Claim/Update'], type='json', auth="user", website=True, csrf=False)
    def warrantyclaim_update(self, db_id, warranty_id, vals, **post):
        # print('warrantyclaim_update',db_id, warranty_id, vals)
        request.env['sale.order.line'].browse(int(db_id)).write(vals)
        warranty = request.env['ars.sale.warranty'].browse(warranty_id)
        vals.get('comment') and warranty.message_post(body=vals.get('comment'))
        warranty.write({})
        return True


# ====================================== Sign UP Page ====================================================

class AuthSignupHome(auth_signup.controllers.main.AuthSignupHome):

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = {key: qcontext.get(key) for key in ('login', 'name', 'password')}
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        # lead = self.Enquiry_Create(values)
        request.env.cr.commit()

    # def Enquiry_Create(self, values):
    #     # Check and insert values from the form on the model <model>
    #     import time
    #     CrmLead = request.env['crm.lead']
    #     crmvals = {'partner_id': values.get('parent_id', ''),
    #                'email_from': values.get('email'),
    #                'phone': values.get('phone'),
    #                'name': values.get('property_name'),
    #                'activity_date_deadline': time.strftime('%Y-%m-%d'),
    #                'type': 'opportunity',
    #                'partner_name': values.get('property_name'),
    #                'post': simplejson.dumps(values)
    #                }
    #     if values.get('plan'):
    #         stage = request.env['crm.stage'].search([('name', '=', 'Provisioning')])
    #         stage and crmvals.update({'stage_id': stage[0].id})
    #
    #     crmvals.update(CrmLead._onchange_partner_id_values(values.get('parent_id')))
    #     crmvals.update({'contact_name': values.get('name'), })
    #     if not values.get('lead'):
    #         lead = CrmLead.sudo().create(crmvals)
    #     else:
    #         lead = CrmLead.browse(values.get('lead'))
    #         lead.sudo().write(crmvals)
    #
    #     return lead.id


