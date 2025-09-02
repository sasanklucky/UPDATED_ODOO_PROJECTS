from odoo import models, fields, api

class CRMLead(models.Model):
    _inherit = 'crm.lead'

    model_varient_product_id = fields.Many2one(
        'product.product',
        string="Model Variant",
        domain="[('product_tmpl_id', '=', model_id)]",
        # Remove the states parameter for Odoo 11 compatibility
        # readonly=True will be handled differently
    )
    auto_filled_variant = fields.Boolean(string="Auto-filled Variant", default=False)

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """
        Set domain for variants when model changes and clear variant if model changes
        """
        if self.model_id:
            # Clear variant when model changes
            self.model_varient_product_id = False
            return {
                'domain': {
                    'model_varient_product_id': [('product_tmpl_id', '=', self.model_id.id)]
                }
            }
        return {}

class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.multi
    def action_apply(self):
        # Run the original conversion first - FIXED THE TYPO HERE
        res = super(Lead2OpportunityPartner, self).action_apply()

        # Leads that were converted (the wizard is opened on these)
        leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))

        for lead in leads:
            # Only process if lead is converted to opportunity
            if lead.type == 'opportunity':
                line = lead.vehicle_line[:1]  # Take first line
                if line:
                    # Try to find product variant from various possible field names
                    product = getattr(line, 'product_id', False) \
                              or getattr(line, 'variant_id', False) \
                              or getattr(line, 'product_variant_id', False)

                    # If we found a product variant, set it on the opportunity
                    if product and product.product_tmpl_id:
                        lead.write({
                            'model_id': product.product_tmpl_id.id,
                            'model_varient_product_id': product.id,
                            'auto_filled_variant': True  # Mark as auto-filled
                        })
                    else:
                        # Fallback to text/name fields if your line stores labels instead of M2O
                        name = getattr(line, 'variant', False) or getattr(line, 'name', False)
                        if name:
                            # Try to find product by name
                            product = self.env['product.product'].search([
                                ('name', 'ilike', name)
                            ], limit=1)
                            if product:
                                lead.write({
                                    'model_id': product.product_tmpl_id.id,
                                    'model_varient_product_id': product.id,
                                    'auto_filled_variant': True  # Mark as auto-filled
                                })
                            else:
                                # Just set the name as text if product not found
                                lead.write({'model_varient': name})

        return res