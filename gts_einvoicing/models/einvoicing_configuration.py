from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
import requests
import json
import logging
import re

_logger = logging.getLogger('E-Invoicing')


class EInvoicing(models.Model):
    _name = 'einvoicing.configuration'
    _rec_name = 'testing'

    def user_company_domain(self):
        return [('id', '=', self.env.user.company_id.id)]

    def user_company(self):
        return self.env.user.company_id.id

    testing = fields.Selection([('t', 'Testing'), ('p', 'Production')], string="Url Type")
    base_url = fields.Char('Url')
    active = fields.Boolean("Active", default=True)
    active_production = fields.Boolean("Production?", default=False)
    asp_id = fields.Char(string='ASP-ID')
    asp_password = fields.Char(string='ASP Password')
    eway_url_staging = fields.Char("Eway URL(Staging)", tracking=2,
                                   default='http://gstsandbox.charteredinfo.com/eivital/dec/v1.04/auth?')
    print_url_live = fields.Char("Eway Print URL(Live)", tracking=2,
                                help="Eway Print URL", default='https://einvapi.charteredinfo.com/eivital/dec/v1.04/auth?')


    company_id = fields.Many2one("res.company",string="Company",domain=user_company_domain,default=user_company)

    # @api.constrains('company_id')
    # def onchange_company_id(self):
    #     active_ids = self.env['einvoicing.configuration'].search([('company_id', '=', self.env.user.company_id.id)])
    #     if not len(active_ids) == 1:
    #         raise UserError(_(f'Configuration already created for this company {self.env.user.company_id.name}'))
    #     return True


    @api.multi
    def handle_einvoicing_auth_token(self):
        warehouse1 = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id),('configure_einvoice', '=', True)])
        for warehouse in warehouse1:
            if not self.testing:
                raise UserError(_('Please Select Url Type'))
            if not self.asp_id:
                raise UserError(_('Please Enter ASP-ID'))
            if not self.asp_password:
                raise UserError(_('Please Enter ASP Password'))
            if not warehouse.gst_no:
                raise UserError(_('Please Enter Registered GSTIN'))
            if not warehouse.user_name:
                raise UserError(_('Please Enter Registered User Name'))
            if not warehouse.user_password:
                raise UserError(_('Please Enter User Password'))
            aspid = self.asp_id
            asppass = self.asp_password
            if self.testing == 't':
                url = self.eway_url_staging + '&aspid=' + aspid + '&password=' + asppass + '&Gstin=' + warehouse.gst_no + '&user_name=' + warehouse.user_name + '&eInvPwd=' + warehouse.user_password
                url = str(url)
            if self.testing == 'p':
                url = self.print_url_live + '&aspid=' + aspid + '&password=' + asppass + '&Gstin=' + warehouse.gst_no + '&user_name=' + warehouse.user_name + '&eInvPwd=' + warehouse.user_password
                url = str(url)
            _logger.info("======auth URL-=====%s ",url)
            response = requests.get(url)
            if response.status_code == 400:
                rec = response.content
                rec_dict = json.loads(rec.decode('utf-8'))
                if rec_dict:
                    error_dict = rec_dict.get('ErrorDetails')
                    raise UserError(_("Error Code:-"+error_dict[0].get('ErrorCode', '')+'  '+ error_dict[0].get('ErrorMessage', '')))
            else:
                res = response.content
                res_dict = json.loads(res.decode('utf-8'))
                if 'error' in res_dict:
                    raise UserError(_("Error Code:-"+res_dict['error'].get('error_cd', '')+'  '+ res_dict['error'].get('message', '')))
                auth_token = res_dict['Data'].get('AuthToken')
                token_epiry = res_dict['Data'].get('TokenExpiry')
                dt = str(token_epiry)
                res1 = dt.replace('T', ' ')
                time = datetime.strptime(res1, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
                time1 = datetime.strptime(time, '%d/%m/%Y %H:%M:%S')
                _logger.info("======auth URL respoise-=====%s,%s ", response,response.content)
                print("--1-1-1-11-1-11-1-11-",warehouse)
                warehouse.write({
                'auth_token': auth_token,
                'expire_date': time1  # datetime.now()
                })
        return True





    


