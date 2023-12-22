from odoo import models, fields, api, _


class CrmLostReasonChild(models.Model):
    _name = 'crm.lost.reason.child'

    name = fields.Char('Crm Lost Reason Child')
    parent_lost_reason = fields.Many2one('crm.lost.reason')


class CrmLeadLostWizardInherit(models.TransientModel):
    _inherit = 'crm.lead.lost'

    child_lost_reason = fields.Many2one('crm.lost.reason.child')


class CrmLeadChildLost(models.Model):
    _inherit = 'crm.lead'

    child_lost_reason = fields.Many2one('crm.lost.reason.child',track_visibility='onchange')