from odoo import models, fields, api, _




class WebsiteRawInfo(models.Model):
    _name = "website.raw.info"
    _description = "website requst data capture in this model and delaer response data capture here"

    request_data = fields.Text(string="Website Request Data")
    request_time = fields.Datetime(string="Request Date")
    response_data = fields.Text(string="Response Data")
    response_time = fields.Datetime(string="Response Date")
    lead_status = fields.Char(string="Lead Status")




