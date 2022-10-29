from odoo import models, fields, api,_
from odoo.exceptions import UserError
from datetime import date
from lxml import etree
from openerp.osv.orm import setup_modifiers


class ARSAccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    vin_no = fields.Many2one('stock.production.lot', string="VIN")


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


