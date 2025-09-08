# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PartsPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New' and 'purchase_type' in vals and vals.get('purchase_type') == 'after_sales':
            vals['name'] = self.env['ir.sequence'].next_by_code('parts.purchase.order') or 'New'
        # elif vals.get('name', 'New') == 'New':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
        return super(PartsPurchaseOrder, self).create(vals)
