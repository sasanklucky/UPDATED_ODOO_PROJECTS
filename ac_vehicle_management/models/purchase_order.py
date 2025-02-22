from odoo import models, fields, api


class PartsPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New' and 'purchase_type' in vals and vals.get('purchase_type') == 'vehicle':
            vals['name'] = self.env['ir.sequence'].next_by_code('vehicle.purchase.order') or '/'
        # elif vals.get('name', 'New') == 'New':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
        return super(PartsPurchaseOrder, self).create(vals)


class ProductVehicleSaleForm(models.Model):
    _inherit = 'product.template'

    certificate_number = fields.Char('Certificate No')
    horn_level = fields.Char('Horn Level')

class CrmSequence(models.Model):
    _inherit = 'crm.lead'

    crm_sequence = fields.Char(string="Sequence reference", readonly=True, copy=False)
    source_reference = fields.Char(string="Source reference", readonly=True, copy=False)

    @api.model
    def create(self, vals):
        # Create the lead first to get the lead ID
        lead = super(CrmSequence, self).create(vals)

        # Fetch the dealer code from the user's company
        user = self.env.user
        dealer_code = user.company_id.dealer_code if user.company_id.dealer_code else 'N/A'

        # Assign the sequence
        lead.crm_sequence = 'ENQ/{}/{}'.format(dealer_code, lead.id)

        return lead