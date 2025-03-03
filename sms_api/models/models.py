# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import requests
import re

import json


class sms_records(models.Model):
    _name = 'sms.record'
    name = fields.Char(string="Customer Name")
    phone = fields.Char(string="Phone Number")
    date = fields.Datetime(string="Date")
    # token = fields.Many2one('live.streaming')
    company_id = fields.Many2one('res.company', "Company")
    failed_reason = fields.Char()
    body = fields.Html()
    response = fields.Html()
    url = fields.Text()
    stage = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('exception', 'Delivery Failed'),
        ('cancel', 'Cancelled'),
        ('not_found', 'Not Found')])

    @api.multi
    def sent_an_sms(self):
        company = self.company_id.id
        phone = self.phone
        name = self.name
        url_decode = self.url
        pattern = "^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$"
        if re.match(pattern, self.phone):
            domain = [('company_id', '=', company), ('active', '=', True)]
            sms_api = self.env['sms.configure'].search(domain)
            if sms_api:
                values = sms_api.sent_sms(phone, name, url_decode)
                self.body = values.get('body')
                self.response = values.get('response')
                self.stage = 'sent'
                return True
            else:
                sms_api = self.env['sms.configure'].search([('active', '=', True), ('sms_global', '=', True)], limit=1)
                if sms_api:
                    values = sms_api.sent_sms(phone, name, url_decode)
                    self.body = values.get('body')
                    self.response = values.get('response')
                    self.stage = 'sent'
                    return True
                else:
                    self.stage = 'not_found'
                    return False
        else:
            self.stage = 'exception'
            self.failed_reason = "***Invalid Number***"
            return False
    
    @api.multi
    def sent_whatsapp_message(self, company, phone, name, reg_no, ls_url):
        pattern = "^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$"
        try:
            if re.match(pattern, self.phone):
                url = 'https://hooks.imiconnect.in/events/EMDDSABHQY'
                headers = {"key": "902430dc-e034-11e9-9e4e-025282c394f2", "Content-Type": "application/json"}
                payload = {'Temp_Name': 'svc_servicebay', 'corr_id': company.dealer_code, 'msisdn': phone}
                params = [name, reg_no, ls_url]
                payload.update({"params": params})
                req_payload = json.dumps(payload)
                print("Whatsapp Payload\n", req_payload)
                x = requests.post(url=url, data=req_payload, headers=headers)
                print("Response", x.text)
                return True
            else:
                print("***Invalid Number***")
                return False
        except Exception as e:
            print("Exception While send WhatsApp Message\n", e)
            return False


class sms_api(models.Model):
    _name = 'sms.configure'

    name = fields.Char()
    phone = fields.Char()
    active = fields.Boolean()
    rest_api = fields.Boolean()
    message = fields.Text()
    sms_api = fields.Text()
    company_id = fields.Many2one('res.company', "Company")
    val_ids = fields.One2many('sms.configure.line', 'values_id')
    sms_global = fields.Boolean()

    def sent_sms(self, phone, name, url_decode):
        print(self.sms_api)
        vals = {}
        message = self.message
        company = self.company_id
        message = message.replace('customer_name', name)
        message = message.replace('url_decode', url_decode)
        url = self.sms_api
        if self.val_ids:
            for params in self.val_ids:
                if params.value == 'phone':
                    url = url + "&" + params.name + "=" + phone
                elif params.value == 'message':
                    url = url + "&" + params.name + "=" + message
                else:
                    url = url + "&" + params.name + "=" + params.value
            print(url)
        response = self.api_call(url)
        if name and phone and url_decode:
            vals.update({"body": url, "response": response.text})
        return vals

    def api_call(self, url):
        if url:
            try:
                if self.rest_api:
                    response = requests.request("POST", url, params={})
                    print(response.text)
                else:
                    response = requests.get(url, params={})
                    print(response.text)
            except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema,
                    requests.exceptions.Timeout, requests.exceptions.HTTPError) as error:
                response = error
        return response

    def get_mail_status(self):
        cr = self.env.cr
        live_streaming_id = self.env['live.streaming'].search([])
        for li in live_streaming_id:
            vals = {}
            if not li.sms_status and li.name:
                token = '\y' + li.name + '\y'
                cr.execute("""SELECT stage FROM sms_record
                                    WHERE  body ~ '""" + str(token) + """'""")
                sms_state = cr.fetchall()
                if sms_state and sms_state[0]:
                    li.write({'sms_status': str(sms_state[0][0])})
            if not li.mail_status and li.name:
                token = '\y' + li.name + '\y'
                cr.execute("""SELECT state FROM mail_mail
                                    WHERE  body_html ~ '""" + str(token) + """'""")
                mail_state = cr.fetchall()
                if mail_state and mail_state[0]:
                    li.write({'mail_status': str(mail_state[0][0])})


class sms_api(models.Model):
    _name = 'sms.configure.line'
    name = fields.Char()
    value = fields.Char()
    values_id = fields.Many2one('sms.configure')
    # @api.onchange('active','company_id')
    # def check_sms_gate_way(self):
    #     if self.active == True and self.company_id:
    #         domain = [('active','=',True),('company_id','=',self.company_id.id)]
    #         sms_cofig= self.env['sms.configure'].search(domain)
    #         for sms_con in sms_cofig:
    #             # if sms_con.id != self.id:
    #                 sms_con.active = False

