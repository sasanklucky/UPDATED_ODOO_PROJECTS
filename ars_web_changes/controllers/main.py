from odoo import http
from odoo.http import request
import werkzeug
from odoo.addons.web.controllers.main import Home


class LoginHome(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        print(self, "\n", redirect, kw)
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return werkzeug.utils.redirect('/')
        return super(LoginHome, self).web_login(redirect, **kw)
