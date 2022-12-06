# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm
from odoo import models, fields, api, _
from lxml import etree
from openerp.osv.orm import setup_modifiers


class ARS_product_vehicle(models.Model):
    _inherit = 'product.template'

    def _get_default_category_id(self):
        if self._context.get('params'):
            action_id = self._context.get('params').get('action')
            act_browse = self.env['ir.actions.act_window'].browse(int(action_id))
            category = False
            if act_browse.name == 'Models':
                category = self.env['product.category'].search([('name', '=', 'Vehicle')], limit=1)

            if act_browse.name == 'Model Variants':
                category = self.env['product.category'].search([('name', '=', 'Vehicle')], limit=1)

            if act_browse.name == 'Parts':
                category = self.env['product.category'].search([('name', '=', 'Parts')], limit=1)

            if act_browse.name == 'Accessories':
                category = self.env['product.category'].search([('name', '=', 'Accessories')], limit=1)

            if act_browse.name == 'Labors':
                category = self.env['product.category'].search([('name', '=', 'Labor')], limit=1)

            if category:
                return category.id

    def _get_default_catalog_id(self):
        if self._context.get('params'):
            action_id = self._context.get('params').get('action')
            act_browse = self.env['ir.actions.act_window'].browse(int(action_id))
            category = False
            if act_browse.name == 'Models':
                category = self.env['product.catalog'].search([('name', '=', 'Vehicle')], limit=1)

            if act_browse.name == 'Model Variants':
                category = self.env['product.catalog'].search([('name', '=', 'Vehicle')], limit=1)

            if act_browse.name == 'Parts':
                category = self.env['product.catalog'].search([('name', '=', 'Parts')], limit=1)

            if act_browse.name == 'Accessories':
                category = self.env['product.catalog'].search([('name', '=', 'Accessories')], limit=1)

            if act_browse.name == 'Labors':
                category = self.env['product.catalog'].search([('name', '=', 'Labor')], limit=1)

            if act_browse.name == 'Other Products':
                # category = self.env.ref('ars_vehicle_sales.product_catalog_other_products')
                category = self.env['product.catalog'].search([('name', '=', 'Other Products')], limit=1)

            if category:
                return category.id

    @api.multi
    @api.depends('product_variant_ids.sales_count')
    def _sales_count(self):
        for product in self:
            product.sales_count = sum([p.sales_count for p in product.product_variant_ids])
            if product.sales_count != 0:
                self.sales_count = product.sales_count

    @api.multi
    def _purchase_count(self):
        for template in self:
            template.purchase_count = sum([p.purchase_count for p in template.product_variant_ids])
            if template.purchase_count != 0:
                self.purchase_count = template.purchase_count

    categ_id = fields.Many2one(
        'product.category', 'Internal Category',
        change_default=True, default=_get_default_category_id,
        required=True, help="Select category for the current product")
    sales_count = fields.Integer(compute='_sales_count', string='# Sales')
    purchase_count = fields.Integer(compute='_purchase_count', string='# Purchases')
    catalog_type = fields.Many2one('product.catalog', default=_get_default_catalog_id, required=True,
                                   string="Catalog Type")
    brand_name = fields.Many2one('brand.name')
    engine_type_code = fields.Char(string='Engine Type Code')
    no_of_cylinder = fields.Char(string='No of Cylinder')
    cylinder_capacity = fields.Char(string='Cylinder Capacity')
    power_kw = fields.Char(string='Power(KW)')
    power_hp = fields.Char(string='Power(HP)')
    top_speed = fields.Char(string='Top Speed')
    accellaration = fields.Char(string='Acceleration')
    transmission_type_code = fields.Char(string='Transmission Code')
    tyre_details = fields.Char(string='Tyre Details ')
    no_of_doors = fields.Char(string='No of Doors')
    empty_weight = fields.Float(string='Empty Weight')
    total_weight = fields.Float(string='Total Weight')
    roof_load = fields.Char(string='Roof Load')
    trailer_load = fields.Char(string='Trailer Load')
    awd = fields.Char(string='AWD')
    no_of_axeles = fields.Char(string='No of Axeles')
    wheel_base = fields.Char(string='Wheel Base')
    tyre_details = fields.Char(string='Tyre Details')
    front_axle_load = fields.Char(string='Front Axle Load')
    rear_axle_load = fields.Char(string='Rear Axle Load')
    fuel_type = fields.Selection([('petrol', 'Petrol'), ('diesel', 'Diesel')], 'Fuel Type')
    # color = fields.Char()
    car_type = fields.Char(string='Car Type')
    seating_capacity = fields.Char(string='Seating Capacity')
    engine_capacity = fields.Char(string="Engine Capacity")
    city_mileage = fields.Char(string="City Mileage")
    highway_mileage = fields.Char(string="Highway Mileage")
    power_steering = fields.Boolean(string="Power Steering")
    ac = fields.Boolean(string="A/C")
    steering_adjustment = fields.Boolean(string="Steering Adjustment")
    power_window = fields.Many2one('power.window', 'Power Window', index=True)
    centre_locking = fields.Boolean(string="Centre Locking")
    description = fields.Text()
    brand_id = fields.Many2one('fleet.vehicle.model.brand', 'Make', help='Make of the vehicle')
    brand_logo = fields.Binary('Brand Logo', related="brand_id.image_medium", store=False)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        con = self.env.context
        res = super(ARS_product_vehicle, self).fields_view_get(view_id, view_type, toolbar, submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            catalog = self._get_default_catalog_id()
            category = self.env['product.catalog'].browse(catalog)
            # if self.sales_count != 0 and doc.xpath("//field[@name='catalog_type']"):
            #     node = doc.xpath("//field[@name='catalog_type']")
            #     node.set('readonly', '1')
            #     setup_modifiers(node, res['fields']['catalog_type'])
            if category.name == 'Vehicle':
                for node in doc.xpath("//label[@string='Product Name']"):
                    node.set('string', 'Model Name')
                for node in doc.xpath("//field[@placeholder='Product Name']"):
                    node.set('placeholder', 'Model Name')
                for node in doc.xpath("//field[@name='default_code']"):
                    node.set('string', 'Model Code')
                for node in doc.xpath("//field[@name='tracking']"):
                    node.set('readonly', '1')
                    setup_modifiers(node, res['fields']['tracking'])
            else:
                for node in doc.xpath("//field[@name='brand_id']"):
                    node.set('invisible', '1')
                    setup_modifiers(node, res['fields']['brand_id'])
                for node in doc.xpath("//field[@name='brand_logo']"):
                    node.set('invisible', '1')
                    setup_modifiers(node, res['fields']['brand_logo'])
        res['arch'] = etree.tostring(doc)
        return res

    # @api.multi
    # @api.onchange('tracking')
    # def tracking_set(self):
    #     res = {}
    #     if self.catalog_type.name == 'Vehicle':
    #         if self.tracking == 'lot' or self.tracking == 'none':
    #             res['warning'] = {
    #                 'title': _('Warning'),
    #                 'message': _(
    #                     'U can not select.')
    #             }
    #         return res

    @api.model
    def create(self, vals):
        res = {}
        res = super(ARS_product_vehicle, self).create(vals)
        type = vals.get('catalog_type')
        catalog_vehicle = self.env['product.catalog'].browse(type).name
        if catalog_vehicle == 'Vehicle':
            if vals.get('tracking') == 'lot' or vals.get('tracking') == 'none':
                raise UserError(_('U can not select by lots & no tracking'))

        return res

    @api.multi
    def write(self, vals):
        res = {}
        val = super(ARS_product_vehicle, self).write(vals)
        if self.catalog_type.name == 'Vehicle':
            if vals.get('tracking') == 'lot' or vals.get('tracking') == 'none':
                raise UserError(_('U can not select by lots & no tracking'))
            # else:
            #     return super(ARS_product_vehicle, self).write(vals)
        return val


class ARS_product_product(models.Model):
    _inherit = 'product.product'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        con = self.env.context
        res = super(ARS_product_product, self).fields_view_get(view_id, view_type, toolbar, submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            catalog = self.product_tmpl_id._get_default_catalog_id()
            category = self.env['product.catalog'].browse(catalog)
            if category.name == 'Vehicle':
                for node in doc.xpath("//label[@string='Product Name']"):
                    node.set('string', 'Model Name')
                for node in doc.xpath("//field[@placeholder='Product Name']"):
                    node.set('placeholder', 'Model Name')
                for node in doc.xpath("//field[@name='default_code']"):
                    node.set('string', 'Model Code')
                for node in doc.xpath("//field[@name='tracking']"):
                    node.set('readonly', '1')
                    setup_modifiers(node, res['fields']['tracking'])
        res['arch'] = etree.tostring(doc)
        return res


class ARS_product_Catalog(models.Model):
    _name = 'product.catalog'

    name = fields.Char()


class PowerWindow(models.Model):
    _name = 'power.window'
    _description = 'Model Power Window'

    name = fields.Char()
    product_id = fields.Many2one('product.template', string="Product", readonly=True)


class ARS_Sale_ResUsers(models.Model):
    _inherit = 'res.users'

    salesperson = fields.Boolean()


class ARS_ProductChangeQuantity(models.TransientModel):
    _inherit = "stock.change.product.qty"
    _description = "Change Product Quantity"

    # Update quantity on hand - should take 1 quantity
    @api.multi
    @api.onchange('new_quantity')
    def quantity_change(self):
        if self.product_tmpl_id.catalog_type.name == 'Vehicle':
            if self.new_quantity > 1:
                raise UserError(_('It can not be take more than one quantity'))

    @api.multi
    @api.onchange('location_id')
    def location_change(self):
        product = self.product_tmpl_id.categ_id.id
        locat = self.env['stock.fixed.putaway.strat'].search([('category_id', '=', product)])
        if locat:
            self.location_id = locat.fixed_location_id
        else:
            self.location_id = self.env.ref('stock.stock_location_stock').id

    # def change_product_qty(self):
    #     res = super(ARS_ProductChangeQuantity, self).change_product_qty()
    #     fleet_veh_obj = self.env['fleet.vehicle']
    #     fleet_veh_obj = fleet_veh_obj.create({
    #         'model_id': self.product_tmpl_id.id,
    #         'mvariant_id': self.product_id.id,
    #         'vin_sn': self.lot_id.name,
    #         'license_plate': '/',
    #         'vehicle_status': 'new',
    #         'driver_id': self.env.user.company_id.partner_id.id,
    #         'lot_id': self.lot_id and self.lot_id.id,

    #     })
