from odoo import models, fields, api,exceptions, _

class Customerfieldrestrict(models.Model):
    _inherit = 'crm.lead'

    has_quotation = fields.Boolean(
        string="Has Quotation", compute="_compute_has_quotation"
    )

    def _compute_has_quotation(self):
        for lead in self:
            count = self.env['sale.order'].search_count([
                ('opportunity_id', '=', lead.id),
                ('state', 'in', ['draft', 'sent'])
            ])
            lead.has_quotation = bool(count)

    def write(self, vals):
        for lead in self:
            if lead.type == 'opportunity' and 'mobile' in vals:
                raise exceptions.UserError(_("You cannot change the mobile number for an opportunity."))
        return super(Customerfieldrestrict, self).write(vals)
