# -*- coding: utf-8 -*-

from odoo import models, fields, api

class rms_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_customer(self, vals):
        print(vals)
        partner = {'name':vals.get('customer_name'),'phone':vals.get('mobile'),'email':vals.get('email')}
        part = self.create(partner)
        model_id = self.env.ref('rms_frontend.default_vehicle').id
        mvariant_id = self.env['product.product'].search([('product_tmpl_id','=',model_id)],limit=1).id
        vahicle_id = self.env['fleet.vehicle'].create({'model_id':model_id,'mvariant_id':mvariant_id,'license_plate':vals.get('regn')})
        sale_data = {'partner_id':part.id,'regn_no':vahicle_id.id,'is_online':True,'template_id':1}
        self.env['sale.order'].create(sale_data)
        return True