# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class PartsPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New' and 'purchase_type' in vals and vals.get('purchase_type') == 'after_sales':
            # vals['name'] = self.env['ir.sequence'].next_by_code('parts.purchase.order') or 'New'
        # elif vals.get('name', 'New') == 'New':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
            seq = self.env['ir.sequence'].search([
                ('code', '=', 'parts.purchase.order'),
                ('company_id','=',vals['company_id']),
                ('branch', '=', vals['branch_id'])
            ],limit=1)
            if seq:
                vals['name'] = seq.next_by_id()
            else:
                raise UserError(f"Please create a sequence for branch {self.branch_id.name}")
        return super(PartsPurchaseOrder, self).create(vals)
