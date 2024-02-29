from odoo import models, fields, api
from odoo.tools import datetime
import re


class MailMessageHelpdesk(models.Model):
    _inherit = 'mail.message'

    def remove_html_tags(self,tags):
        clean = re.compile('<.*?>')
        return re.sub(clean, '', tags)

    @api.model
    def create(self, values):
        # print('custom create called mail activity',values)
        res = super(MailMessageHelpdesk, self).create(values)
        if res.model == 'helpdesk.ticket':
            html_text = res.body
            plain_text = self.remove_html_tags(html_text)
            self.env['solution.logs'].create({
                'sol_log': res.res_id,
                'name': plain_text,

            })
        return res


class MailActivityHelpdesk(models.Model):
    _inherit = 'mail.activity'

    @api.model
    def create(self, values):
        # print('custom create called',values)
        res = super(MailActivityHelpdesk, self).create(values)
        if res.res_model == 'helpdesk.ticket':
            html_text = res.note
            plain_text = self.remove_html_tags(html_text)
            self.env['solution.logs'].create({
                'sol_log': res.res_id,
                'activity_type_id': res.activity_type_id.id,
                'name': plain_text


            })
        return res