# -*- coding: utf-8 -*-

from odoo import models, fields, api
# from dateitime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date, datetime, timedelta
import datetime
import csv
import io
import base64
import logging
import requests
import json
import odoo.exceptions
import odoo.osv.osv

_logger = logging.getLogger(__name__)


class LiveStreaming(models.Model):
    _inherit = 'live.streaming'


    # @api.model
    # def create(self, values):
    #     res = super(LiveStreaming, self).create(values)
    #     cr = self.env.cr
    #     if not res.sms_status:
    #         cr.execute("""SELECT stage FROM sms_record
    #                                    WHERE  body ~ '\y""" + res.name + """ \y'""")
    #         sms_state = cr.fetchall()
    #         if sms_state:
    #             res.update({'sms_status': sms_state[0](0)})
    #         else:
    #             res.update({'sms_status': ''})
    #     if not res.mail_status:
    #         cr.execute("""SELECT state FROM mail_mail
    #                                    WHERE  body_html ~ '\y""" + res.name + """ \y'""")
    #         mail_state = cr.fetchall()
    #         if mail_state:
    #             res.update({'sms_status': mail_state[0](0)})
    #
    #     return res

# def get_mail_status(self):
#     obj_mail = self.env['mail.mail'].search([])
#     print(obj_mail)
