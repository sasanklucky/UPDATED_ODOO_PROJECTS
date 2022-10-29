# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import requests
import json
_logger = logging.getLogger(__name__)


class planner_cander_event(models.Model):
    _inherit = 'calendar.event'

    event_type = fields.Char()
    token = fields.Char("Tocken String")
    url = fields.Char("Video URL")

    @api.multi
    def push_ccip(self, ip, bay_num_ip_id):
        res = {}
        cr = self._cr
        cam_obj = self.env['cc.camera']
        cam = cam_obj.browse(bay_num_ip_id[0])
        cr.execute("select username, password from cc_camera where id in" + str(cam.id))
        cam_dict = cr.dictfetchall()
        if cam_dict:
            cam_dict = cam_dict[0]
        username = cam_dict.get('username')
        password = cam_dict.get('password')
        url = "http://122.174.176.81:85/camera/geturl"
        querystring = {
            "ip1": str(ip[0]),
            "username1": str(username),
            "password1": str(password),
            "ip2": str(ip[1]),
            "username2": str(username),
            "password2": str(password),
            "ip3": str(ip[2]),
            "username3": str(username),
            "password3": str(password)
        }

        response = requests.request("POST", url, params=querystring)
        _logger.error('After Post URL.........: %s', response.text)
        if response.text:
            response = json.loads(response.text)
            if response.get('status') == True:
                cr.execute("update calendar_event set token='" + str(response.get('token')) + "', url='" + str(
                    response.get('url')) + "' where id =" + str(self.id))
                # res.update({'token': response.get('token'), 'url': response.get('url')})
                # if response.get("status") != 200 and response.get("message") != 'Success':
                #     raise osv.except_osv(_('Warning'), _(response.get("message") + 'From Business Connect'))

        return res

    @api.multi
    def close_ccip(self, event_token):
        res = {}
        cr = self._cr
        url = "http://192.168.1.8:85/stop"
        querystring = event_token
        response = requests.request("POST", url, params=querystring)
        return res