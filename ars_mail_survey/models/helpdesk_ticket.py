from odoo import models, fields, api


class ComplaintSources(models.Model):
    _name = 'complaint.source'

    name = fields.Char()

class HelpdeskTicket(models.Model):
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

    @api.onchange('category_i_id')
    def _get_category_ii(self):
        self.category_ii_id = False
        if self.category_i_id:
            return {'domain': {'category_ii_id': [('parent_id', '=', self.category_i_id.id)]}}

    @api.onchange('stage_id')
    def close_mail_activity(self):
        for record in self:
            if record.stage_id.sequence == 2:
                print(record.activity_source_id)
                record.activity_source_id.write({'stages': 'completed'})
