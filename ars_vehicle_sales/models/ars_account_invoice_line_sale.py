from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from lxml import etree
from openerp.osv.orm import setup_modifiers


class ARSAccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    vin_no = fields.Many2one('stock.production.lot', string="VIN")
    """ Product line varient """
    product_varient_ids = fields.Many2many('product.attribute.value', 'account_line_attribute_rel', 'account_id',
                                           'attribute_id', string='Attribute')
    product_template_id = fields.Many2one('product.template', string='Model')

    product_catalog_id = fields.Many2one('product.catalog', string='Product Catalog')

    @api.multi
    @api.onchange('product_template_id')
    def onchange_product_template_id(self):
        self.product_id = False
        if self.product_template_id:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            return {'domain': {'product_id': [('id', 'in', varient_ids.ids)]}}
        else:
            return {'domain': {'product_id': [('id', 'in', False)]}}

    @api.multi
    @api.onchange('product_catalog_id')
    def onchange_product_based_on_catalog(self):
        if self.product_catalog_id:
            product = self.env['product.template'].sudo().search([('catalog_type', '=', self.product_catalog_id.id)])
            return {'domain': {'product_template_id': [('id', 'in', product.ids)]}}
        else:
            return {'domain': {'product_template_id': [('id', 'in', False)]}}


    # @api.multi
    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     if self.product_id:
    #         return {'domain': {'product_varient_ids': [('id', 'in', self.product_id.attribute_value_ids.ids)]}}

    @api.multi
    def get_engcode(self, pro_id, vin_no):
        prot_id = self.env['fleet.vehicle'].search([('mvariant_id', '=', pro_id.id), ('vin_sn', '=', vin_no.name)])
        return prot_id.engine_number

    @api.multi
    def get_vinno(self, pro_id, vin_no):
        prot_id = self.env['fleet.vehicle'].search([('mvariant_id', '=', pro_id.id), ('vin_sn', '=', vin_no.name)])
        return prot_id.vin_sn


class product_attribute_custom(models.Model):
    _inherit = "product.attribute.value"


    @api.multi
    def _variant_name(self, variable_attributes):
        return ", ".join([f"{v.attribute_id.name}:{v.name}" for v in self if v.attribute_id in variable_attributes])


class ARS_Product_Product(models.Model):
    _inherit = "product.product"

    

    lot_id = fields.Many2one('stock.production.lot')
    catalog_type = fields.Many2one('product.catalog', related="product_tmpl_id.catalog_type")

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         vehicle_name = record.attribute_value_ids.mapped('name') if record.attribute_value_ids else ''
    #         result.append((record.id, vehicle_name))
    #     return result

   

    @api.multi
    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '%s' % (name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id', 'attribute_value_ids', 'attribute_line_ids'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            # display only the attributes with multiple possible values on the template
            variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id')
            variant = product.attribute_value_ids._variant_name(variable_attributes)
            print('variant=====================',variant,variable_attributes)
            if variant != '':
                name = variant and "(%s)" % (variant)
            else:
                name = product.product_tmpl_id.name and (
                        variant and "%s (%s)" % (product.product_tmpl_id.name, variant) or product.product_tmpl_id.name
                        ) or False
            sellers = []
            if partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': name,
                              'default_code': s.product_code or product.default_code,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,
                          }
                result.append(_name_get(mydict))
        return result
