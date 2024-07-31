# import notify2
from odoo import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class ARS_stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'
    # _rec_name = 'reg_no'
    check_new_lotno = fields.Boolean(default=False)
    motor_number = fields.Char(string="Motor Number")
    product_catalog = fields.Char(string='Catalog Type', related='product_id.catalog_type.name')
    battery_number = fields.Char('Battery Number')

    @api.model
    def create(self, vals):
        vals.update({'vehicle_status': 'new'})
        res = super(ARS_stock_production_lot, self).create(vals)
        lot_no = vals.get('product_id')
        browse_lot = self.env['product.product'].browse(lot_no)
        browse_lot.lot_id = res.id
        return res

    @api.multi
    def create_missing_vehicle_card(self):
        lot_numbers = self.env['stock.production.lot'].search([])
        fleet_vehicle = self.env['fleet.vehicle']
        for lot_number in lot_numbers:
            if not fleet_vehicle.search([('vin_sn', '=', lot_number.name)]):
                line = self.env['stock.move.line'].search([('lot_id', '=', lot_number.id)], order='id desc', limit=1)
                vals = {'mvariant_id': lot_number.product_id.id,
                        'model_id': lot_number.product_id.product_tmpl_id.id,
                        'vin_sn': lot_number.name,
                        'license_plate': '/',
                        'company_id': line.move_id.company_id.id,
                        'vehicle_status': 'new',
                        'lot_id': line.lot_id and line.lot_id.id,
                        'driver_id': line.move_id.company_id.partner_id.id
                        }
                res = fleet_vehicle.create(vals)


class Picking(models.Model):
    _inherit = 'stock.picking'

    batch_id = fields.Many2one("stock.picking", string="Batch")
    delivery_challan_sequence = fields.Char()
    picking_operations = fields.Char()
    batch_count = fields.Integer(string="Batch Count")
    is_batch = fields.Boolean("Batch Transfer")
    delivery_slip_sequence = fields.Char()
    return_picking_id = fields.Many2one('stock.picking', 'Return Picking')

    def create_vehicle_card(self, vals, location):
        res = {}
        return res

    # @api.multi
    # def button_validate(self):
    #     res = super(Picking, self).button_validate()
    #     self._cr.commit()
    #     picking_type = self.picking_type_id
    #
    #     if self.location_dest_id.usage == 'internal' and self.location_id.usage == 'supplier':
    #         print(self.location_id.usage)
    #     elif self.location_dest_id.usage == 'customer' and self.location_id.usage == 'internal':
    #         for stock_production_obj in self.move_line_ids:
    #             if stock_production_obj.lot_id:
    #                 val = {'custmer_name': self.partner_id.id,'date_of_ownership': datetime.now(),
    #                         'address': self.partner_id.city,'mobile': self.partner_id.mobile}
    #                 stock_production_obj.lot_id.custumer_ide = [(0, 0, )]
    #                 if stock_production_obj.move_id.sale_line_id:
    #                     stock_production_obj.lot_id.check_new_lotno = True
    #         print(self.location_id.usage)
    #     elif self.location_dest_id.usage == 'internal' and self.location_id.usage == 'customer':
    #         print(self.location_id.usage)
    #     elif self.location_dest_id.usage == 'supplier' and self.location_id.usage == 'internal':
    #         print(self.location_id.usage)
    #     no_quantities_done = all(
    #         float_is_zero(move_line.qty_done, precision_rounding=move_line.product_uom_id.rounding) for move_line in
    #         self.move_line_ids)
    #     if picking_type.use_create_lots or picking_type.use_existing_lots:
    #         lines_to_check = self.move_line_ids
    #         if not no_quantities_done:
    #             lines_to_check = lines_to_check.filtered(
    #                 lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
    #         for line in lines_to_check:
    #             if not line.move_id.sale_line_id and (line.lot_name or line.lot_id):
    #                 if self.origin and 'Return' not in self.origin:
    #                     vals = {'mvariant_id': line.product_id.id,
    #                             'model_id': line.product_id.product_tmpl_id.id,
    #                             'vin_sn': line.lot_id and line.lot_id.name or line.lot_name,
    #                             'license_plate': '/',
    #                             'company_id': line.move_id.company_id.id,
    #                             'vehicle_status': 'new',
    #                             'lot_id': line.lot_id and line.lot_id.id,
    #                             'driver_id': self.env.user.company_id.partner_id.id
    #                             }
    #                     vin_sn = line.lot_id.name if line.lot_id else line.lot_name
    #                     if not self.env['fleet.vehicle'].search([('vin_sn', '=', vin_sn)]):
    #                         res = self.env['fleet.vehicle'].create(vals)
    #                         # notification.update('Validated',
    #                         #                     'Vehicle card created')
    #                         # notification.show()
    #                         res.custumer_ide = [(0, 0, {'custmer_name': self.partner_id.id,
    #                                                     'date_of_ownership': datetime.now(),
    #                                                     'address': self.partner_id.city,
    #                                                     'mobile': self.partner_id.mobile})]
    #                 elif self.origin and 'Return' in self.origin:
    #                     vehicles = self.env['fleet.vehicle'].search([('lot_id', '=', line.lot_id.id)])
    #                     for vehicle in vehicles:
    #                         if vehicle.vehicle_status == 'new':
    #                             vehicle.unlink()
    #             elif line.lot_id and line.move_id.sale_line_id:
    #                 vals = {
    #                     'vin_no': line.lot_id.id,
    #                 }
    #                 line.move_id.sale_line_id.write(vals)
    #                 self.env['fleet.vehicle'].search([('lot_id', '=', line.lot_id.id)]).write(
    #                     {'driver_id': line.move_id.partner_id and line.move_id.partner_id.id,
    #                      'vehicle_status': 'customer', 'customer_ids': [(0, 0, {'custmer_name': self.partner_id.id,
    #                                                                             'date_of_ownership': datetime.now(),
    #                                                                             'address': self.partner_id.city,
    #                                                                             'mobile': self.partner_id.mobile})]})
    #     return res
    @api.multi
    def button_validate(self):
        res = super(Picking, self).button_validate()
        self._cr.commit()
        picking_type = self.picking_type_id
        no_quantities_done = all(
            float_is_zero(move_line.qty_done, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
            for line in lines_to_check:
                if self.location_id and self.location_id.usage == 'supplier':
                    if self.origin and 'Return' not in self.origin:
                        vals = {'mvariant_id': line.product_id.id,
                                'model_id': line.product_id.product_tmpl_id.id,
                                'vin_sn': line.lot_id and line.lot_id.name or line.lot_name,
                                'license_plate': '/',
                                'engine_number': line.motor_number,
                                'company_id': line.move_id.company_id.id,
                                'vehicle_status': 'new',
                                'lot_id': line.lot_id and line.lot_id.id,
                                'driver_id': self.env.user.company_id.partner_id.id
                                }
                        vin_sn = line.lot_id.name if line.lot_id else line.lot_name
                        existing_lot_numbers = []
                        if line.lot_id:
                            line.lot_id.write({'motor_number': line.motor_number})
                        if self.env['fleet.vehicle'].search([('vin_sn', '=', vin_sn)]):
                            existing_lot_numbers.extend([vin_sn])
                            print(existing_lot_numbers)
                        else:
                            # sold_by_id = self.env.user.company_id.partner_id
                            res = self.env['fleet.vehicle'].create(vals)
                            # res.custumer_ide = [(0, 0, {'custmer_name': self.partner_id.id,
                            #                            'date_of_ownership': datetime.now(),
                            #                           'address': self.partner_id.city,
                            #                           'mobile': self.partner_id.mobile,
                            #                           'sold_by': sold_by_id.id})]
                    elif self.origin and 'Return' in self.origin:
                        vehicles = self.env['fleet.vehicle'].search([('lot_id', '=', line.lot_id.id)])
                        for vehicle in vehicles:
                            if vehicle.vehicle_status == 'new':
                                vehicle.unlink()
                elif self.location_dest_id and self.location_dest_id.usage == 'customer':
                    for stock_production_obj in self.move_line_ids:
                        if stock_production_obj.lot_id and 'Vehicle' in stock_production_obj.lot_id.product_catalog:
                            stock_production_obj.lot_id.custumer_ide = [(0, 0, {'custmer_name': self.partner_id.id,
                                                                                'date_of_ownership': datetime.now(),
                                                                                'address': self.partner_id.city,
                                                                                'mobile': self.partner_id.mobile})]

                            vals = {'vin_no': line.lot_id.id}
                            line.move_id.sale_line_id.write(vals)
                            vehicle_card = self.env['fleet.vehicle'].search(
                                [('lot_id', '=', stock_production_obj.lot_id.id)])
                            if not vehicle_card:
                                vehicle_card = self.env['fleet.vehicle'].search(
                                    [('vin_sn', '=', stock_production_obj.lot_id.name)])
                            else:
                                stock_production_obj.lot_id.check_new_lotno = True
                            # customer = line.move_id.partner_id if line.move_id.partner_id else self.partner_id
                            # if vehicle_card:
                            #     vehicle_card.write(
                            #         {'driver_id': customer.id, 'vehicle_status': 'customer',
                            #          'lot_id': stock_production_obj.lot_id.id,
                            #          'customer_ids': [(0, 0, {'custmer_name': self.partner_id.id,
                            #                                   'date_of_ownership': datetime.now(),
                            #                                   'address': self.partner_id.city,
                            #                                   'mobile': self.partner_id.mobile})]})
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_template_id = fields.Many2one('product.template', string='Product')
    product_catalog_id = fields.Many2one('product.catalog', string='Catalog Type')

    @api.multi
    @api.onchange('product_catalog_id')
    def onchange_product_based_on_catalog(self):
        if self.product_catalog_id:
            product = self.env['product.template'].sudo().search([('catalog_type', '=', self.product_catalog_id.id)])
            return {'domain': {'product_template_id': [('id', 'in', product.ids)]}}
        else:
            return {'domain': {'product_template_id': [('id', 'in', False)]}}

    @api.multi
    @api.onchange('product_template_id')
    def onchange_product_template_id(self):
        self.product_id = False
        if self.product_template_id and self.product_template_id.attribute_line_ids:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            return {'domain': {'product_id': [('id', 'in', varient_ids.ids)]}}
        else:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            self.product_id = varient_ids.id
            return {'domain': {'product_id': [('id', 'in', False)]}}


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    motor_number = fields.Char(string="Motor Number")
    battery_number = fields.Char(string="Battery Number")
    filter_vin_ids = fields.Many2many('stock.production.lot', compute="_compute_filtered_vin_ids")
    move_id = fields.Many2one('stock.move', string='Stock Move')

    @api.depends('location_id', 'move_id.product_id', 'picking_id.return_picking_id')
    def _compute_filtered_vin_ids(self):
        for rec in self:
            rec.filter_vin_ids = self.env['stock.production.lot']
            company_id = self.env.user.company_id.id

            if rec.location_id and rec.location_id.usage != 'customer' and rec.move_id.product_id:
                stock_quants = self.env['stock.quant'].search([
                    ('location_id', '=', rec.location_id.id),
                    ('company_id', '=', company_id),
                    ('product_id', '=', rec.move_id.product_id.id)
                ])
                rec.filter_vin_ids = stock_quants.mapped('lot_id')

            elif rec.picking_id.return_picking_id and rec.picking_id.origin:
                return_picking = rec.picking_id.return_picking_id
                return_lots = rec.picking_id.origin.split(' ')[2:]
                stock_picking = self.env['stock.picking'].search([('name', 'in', return_lots)]).id
                return_stock_moves = self.env['stock.move'].search([('picking_id', '=', stock_picking)])
                return_stock_move_lines = self.env['stock.move.line'].search(
                    [('move_id', 'in', return_stock_moves.ids)])
                # lot_ids = return_stock_move_lines.mapped('lot_id').ids

                # stock_quants = self.env['stock.quant'].search([
                #     ('location_id', '=', rec.location_id.id),
                #     ('product_id', '=', rec.move_id.product_id.id),
                #     ('lot_id', '=', lot_ids)
                # ])
                rec.filter_vin_ids = return_stock_move_lines.mapped('lot_id')

            else:
                return False

    @api.onchange('lot_id', 'motor_number')
    def _update_motor_number(self):
        if not self.motor_number and self.lot_id:
            self.motor_number = self.lot_id.motor_number
        if not self.lot_id and self.motor_number:
            lot = self.env['stock.production.lot'].search([('motor_number', '=', self.motor_number)], limit=1)
            self.lot_id = lot.id
        #
#     @api.constrains('lot_name', 'lot_id')
#     def lot_name_alphanumeric_constrains(self):
#         for record in self:
#             if record.lot_name:
#                 # len(record.lot_name) == 17
#                 if not record.lot_name.isalnum():

# class StockProductionLot(models.Model):
#     _inherit = 'stock.production.lot'
#
#     @api.constrains('name')
#     def lot_name_alphanumeric_constrains(self):
#         for record in self:
#             # len(record.name)
#             if record.name:
#                 if not record.name.isalnum():
#                     raise ValidationError(_('Please enter valid Lot/Serial Number!'))

#                     raise ValidationError(_('Please enter valid Lot/Serial Number!'))
#             elif record.lot_id:
#                 if not record.lot_id.name.isalnum():
#                     raise ValidationError(_('Please enter valid Lot/Serial Number!'))
