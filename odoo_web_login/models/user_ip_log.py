from odoo import models, fields, api

class UserIPLog(models.Model):
    _name = 'user.ip.log'
    _description = 'User IP & Location Log'

    user_id = fields.Many2one('res.users', string="User", required=True)
    ip_address = fields.Char(string="IP Address", required=True)
    city = fields.Char(string="City")
    region = fields.Char(string="Region")
    country = fields.Char(string="Country")
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")
    login_time = fields.Datetime(string="Login Time", default=fields.Datetime.now)

