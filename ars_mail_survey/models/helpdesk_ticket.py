from odoo import models, fields, api
from odoo.tools import datetime
import re


class ComplaintSources(models.Model):
    _name = 'complaint.source'

    name = fields.Char()


class HelpdeskStageInheritStage(models.Model):
    _inherit = 'helpdesk.stage'

    is_close_stage = fields.Boolean('Is Close Stage')


class HelpdeskTicketInheritMail(models.Model):
    _inherit = 'helpdesk.ticket'

    activity_source_id = fields.Many2one('mail.activity', string='Activity Source')
    category_i_id = fields.Many2one('helpdesk_category_i', string="Category I")
    category_ii_id = fields.Many2one('helpdesk_category_ii', string="Category II")
    seller_dealer = fields.Many2one('res.partner')
    source_complaint_id = fields.Many2one('complaint.source')
    date_of_sale = fields.Date('Date Of Sale')
    model = fields.Many2one('product.product')
    milage = fields.Integer('Milage')
    vin_number = fields.Char('VIN Number')
    vehicle_no = fields.Char('Vehicle Number')
    close_date = fields.Date('Close Date ')
    logs = fields.Char()
    sol_ids = fields.One2many('solution.logs', 'sol_log')


    @api.multi
    def update_user_company_info(self):
        for rec in self:
            if not rec.company_id:
                rec.company_id = rec.user_id.company_id

    @api.onchange('category_i_id')
    def _get_category_ii(self):
        self.category_ii_id = False
        if self.category_i_id:
            return {'domain': {'category_ii_id': [('parent_id', '=', self.category_i_id.id)]}}

    @api.onchange('stage_id')
    def close_mail_activity(self):
        for record in self:
            if record.stage_id.sequence == 2:
                # print(record.activity_source_id)
                record.activity_source_id.write({'stages': 'completed'})


class HelpdeskSolutionLines(models.Model):
    _name = 'solution.logs'

    name = fields.Text()
    sol_log = fields.Many2one('helpdesk.ticket')
    activity_type_id = fields.Many2one('mail.activity.type', 'Activity')



