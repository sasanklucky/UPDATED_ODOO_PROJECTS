from odoo import models, fields, api, _


class CrmLostReasonChild(models.Model):
    _name = 'crm.lost.reason.child'

    name = fields.Char('Crm Lost Reason Child')
    parent_lost_reason = fields.Many2one('crm.lost.reason')


class CrmLeadLostWizardInherit(models.TransientModel):
    _inherit = 'crm.lead.lost'

    child_lost_reason = fields.Many2one('crm.lost.reason.child')
    check_sales_ids = fields.Text('Message', default='')

    @api.model
    def default_get(self, fields):
        res = super(CrmLeadLostWizardInherit, self).default_get(fields)
        lead_id = self._context.get('default_lead_id')
        if lead_id:
            lead = self.env['crm.lead'].browse(lead_id)
            sale_orders = self.env['sale.order'].search([
                ('opportunity_id', '=', lead.id)
            ])
            if sale_orders:
                res['check_sales_ids'] = (
                        "Warning: This lead has linked quotations/sale orders:\n" +
                        "\n".join("- %s (%s)" % (so.name, so.state) for so in sale_orders)
                )
        return res

class CrmLeadChildLost(models.Model):
    _inherit = 'crm.lead'

    child_lost_reason = fields.Many2one('crm.lost.reason.child',track_visibility='onchange')