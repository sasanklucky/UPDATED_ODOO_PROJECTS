from odoo import models, fields, api,_
from odoo.exceptions import UserError
from datetime import date
from lxml import etree
from openerp.osv.orm import setup_modifiers


class ARSAccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    vin_no = fields.Many2one('stock.production.lot', string="VIN")
    """ Product line varient """
    product_varient_ids = fields.Many2many('product.attribute.value','account_line_attribute_rel','account_id','attribute_id',string='Attribute')
    product_template_id = fields.Many2one('product.template',string='Model')

    @api.multi
    @api.onchange('product_template_id')
    def onchange_product_template_id(self):
        self.product_id=False
        if self.product_template_id:
            varient_ids = self.env['product.product'].sudo().search([('product_tmpl_id','=',self.product_template_id.id)])
            return {'domain': {'product_id': [('id', 'in', varient_ids.ids)]}}
        else:
            return {'domain': {'product_id': [('id', 'in', False)]}}


    
    # @api.multi
    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     if self.product_id:
    #         return {'domain': {'product_varient_ids': [('id', 'in', self.product_id.attribute_value_ids.ids)]}}


    @api.multi
    def get_engcode(self,pro_id,vin_no):
        prot_id = self.env['fleet.vehicle'].search([('mvariant_id', '=',pro_id.id),('vin_sn', '=',vin_no.name)])
        return prot_id.engine_number

    @api.multi
    def get_vinno(self, pro_id, vin_no):
        prot_id = self.env['fleet.vehicle'].search([('mvariant_id', '=', pro_id.id), ('vin_sn', '=', vin_no.name)])
        return prot_id.vin_sn

class ARS_Product_Product(models.Model):
    _inherit = "product.product"

    lot_id = fields.Many2one('stock.production.lot')

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         vehicle_name = record.name if record.name else ''
    #         result.append((record.id, vehicle_name))
    #     return result


