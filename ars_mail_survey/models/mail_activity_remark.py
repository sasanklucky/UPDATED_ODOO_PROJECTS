from odoo import fields, models


class MailActivityRemark(models.Model):
    _name = 'mail.activity.remark'
    _description = "Table For Mail Activity Remark"

    activity_id = fields.Many2one('mail.activity', string="Mail Activity")
    date = fields.Datetime(string="Date")
    remark = fields.Char(string="Remark")


