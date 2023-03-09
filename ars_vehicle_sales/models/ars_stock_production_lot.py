from odoo import models, fields,api,_
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class ARS_stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'
    # _rec_name = 'reg_no'



    check_new_lotno = fields.Boolean(default=False)
#     @api.multi
#     def _get_customer(self):
#         for record in self:
#             move_line = self.env['stock.move.line'].search([('lot_name', '=', False), ('lot_id', '=', record.id)])
#             if move_line:
#                 if move_line[-1].picking_id:
#                     record.write({'customer_id' : move_line[-1].picking_id.partner_id.id,'vehicle_status': 'customer'})
#                     record.function_customer_id = move_line[-1].picking_id.partner_id.id
#
#     @api.multi
#     def _get_contact_name(self):
#         for record in self:
#             move_line = self.env['stock.move.line'].search([('lot_name', '=', False), ('lot_id', '=', record.id)])
#             if move_line:
#                 if move_line[-1].picking_id:
#                     if move_line[-1].picking_id.partner_id.child_ids:
#                         record.contact_name = move_line[-1].picking_id.partner_id.child_ids.name
#
#
#     @api.multi
#     def get_years(self):
#         year_list = []
#         for i in range(2014, 2036):
#             year_list.append((i, str(i)))
#         return year_list
#
#
#     active = fields.Boolean(default=True)
#     company_id = fields.Many2one('res.company', 'Company', index=True)
#     function_customer_id = fields.Many2one('res.partner', string='Customer', store=False, compute="_get_customer")
#     function_contact_name = fields.Char(string='Contact Name', store=False, compute="_get_contact_name" )
#     customer_id = fields.Many2one('res.partner')
#     contact_name = fields.Char(string='Contact Name')
#     vehicle_status = fields.Selection([('demo', 'Demo'), ('customer', 'Customer'), ('own', 'Own'), ('new', 'New Vehicle')],'Vehicle Status', select=True)
#     reg_no = fields.Char(string='Regn No.')
#     kilometer_till = fields.Integer(string='Kilometer Till')
#     age = fields.Integer(string='Age', compute = "_age")
#     # prodcution_year = fields.Date(string='Prodcution Year')
#     prodcution_month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
#                                          (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
#                                          (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
#                                         string='Month', )
#     prodcution_year = fields.Selection('get_years', string='Production Year')
#     # model_year = fields.Date(string='Model Year')
#     model_month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
#                                          (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
#                                          (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
#                                         string='Month', )
#     model_year = fields.Selection('get_years', string='Model Year')
#     initial_reg_no = fields.Char(string='Initial Reg.No')
#     service_due = fields.Char(string='Service Due',compute = "_service_due")
#     engine_code = fields.Char(string='Engine Code')
#     engine_number = fields.Char(string='Engine Number')
#     key_serial_number = fields.Char(string='Key Serial Number')
#     categ_id = fields.Many2one('product.category', 'Vehicle Category',related="product_id.product_tmpl_id.categ_id")
#     emission_test_category = fields.Char(string='Emission Test Category')
#     warranty_validation = fields.Datetime(string='Warranty Validation')
#     extented_warranty_no = fields.Char(string='Extented Warranty No')
#     extented_warranty_validation = fields.Datetime(string='Warranty Validation')
#     custumer_ide = fields.One2many('ownership.history','stock_id1')
#     emission_ide = fields.One2many('emission.history', 'stock_id2')
#     insurance_ide = fields.One2many('insurance.history', 'stock_id3')
#     service_ide = fields.One2many('service.history','stock_id4')
#
#     engine_type_code = fields.Char(string='Engine Type Code',related="product_id.product_tmpl_id.engine_type_code")
#     no_of_cylinder = fields.Char(string='No of Cylinder',related="product_id.product_tmpl_id.no_of_cylinder")
#     cylinder_capacity = fields.Char(string='Cylinder Capacity',related="product_id.product_tmpl_id.cylinder_capacity")
#     power_kw = fields.Char(string='Power(KW)',related="product_id.product_tmpl_id.power_kw")
#     power_hp = fields.Char(string='Power(HP)',related="product_id.product_tmpl_id.power_hp")
#     top_speed = fields.Char(string='Top Speed',related="product_id.product_tmpl_id.top_speed")
#     accellaration = fields.Char(string='Acceleration',related="product_id.product_tmpl_id.accellaration")
#     transmission_type_code = fields.Char(string='Transmission Code',related="product_id.product_tmpl_id.transmission_type_code")
#     tyre_details = fields.Char(string='Tyre Details ',related="product_id.product_tmpl_id.tyre_details")
#     no_of_doors = fields.Char(string='No of Doors',related="product_id.product_tmpl_id.no_of_doors")
#     empty_weight = fields.Float(string='Empty Weight',related="product_id.product_tmpl_id.empty_weight")
#     total_weight = fields.Float(string='Total Weight',related="product_id.product_tmpl_id.total_weight")
#     roof_load = fields.Char(string='Roof Load',related="product_id.product_tmpl_id.roof_load")
#     trailer_load = fields.Char(string='Trailer Load',related="product_id.product_tmpl_id.trailer_load")
#     awd = fields.Char(string='AWD',related="product_id.product_tmpl_id.awd")
#     no_of_axeles = fields.Char(string='No of Axeles',related="product_id.product_tmpl_id.no_of_axeles")
#     wheel_base = fields.Char(string='Wheel Base',related="product_id.product_tmpl_id.wheel_base")
#     front_axle_load = fields.Char(string='Front Axle Load',related="product_id.product_tmpl_id.front_axle_load")
#     rear_axle_load = fields.Char(string='Rear Axle Load',related="product_id.product_tmpl_id.rear_axle_load")
#     fuel_type = fields.Selection(string='Fuel Type',related="product_id.product_tmpl_id.fuel_type")
#     # color = fields.Char()
#     car_type = fields.Char(string='Car Type',related="product_id.product_tmpl_id.car_type")
#     seating_capacity = fields.Char(string='Seating Capacity',related="product_id.product_tmpl_id.seating_capacity")
#     engine_capacity = fields.Char(string='Engine Capacity',related="product_id.product_tmpl_id.engine_capacity")
#     city_mileage = fields.Char(string='City Mileage',related="product_id.product_tmpl_id.city_mileage")
#     highway_mileage = fields.Char(string='Highway Mileage',related="product_id.product_tmpl_id.highway_mileage")
#     power_steering = fields.Boolean(string='Power Steering',related="product_id.product_tmpl_id.power_steering")
#     ac = fields.Boolean(string='A/C',related="product_id.product_tmpl_id.ac")
#     steering_adjustment = fields.Boolean(string='Steering Adjustment',related="product_id.product_tmpl_id.steering_adjustment")
#     power_window = fields.Many2one(string='Power Window',related="product_id.product_tmpl_id.power_window")
#     centre_locking = fields.Boolean(string='Centre Locking',related="product_id.product_tmpl_id.centre_locking")

    # _sql_constraints = [
    #     ('reg_no_engine_number_uniq', 'UNIQUE(reg_no, engine_number)', 'Regn No is unique change your Regn No!')
    # ]

    # @api.one
    # @api.constrains('reg_no', 'engine_number')
    # def _check_duplicate_no(self):
    #     if self.date_end < self.date_begin:
    #         raise ValidationError(_('Closing Date cannot be set before Beginning Date.'))


    # ('engine_number_uniq', 'unique (engine_number)', 'Engine No is unique change your Engine No!')
    @api.model
    def create(self, vals):
        # for d in dates:
        #     if not vals.get(d):
        #         vals[d] = dates[d]
        vals.update({'vehicle_status': 'new'})
        res = super(ARS_stock_production_lot, self).create(vals)
        lot_no = vals.get('product_id')
        browse_lot = self.env['product.product'].browse(lot_no)
        browse_lot.lot_id = res.id
        return res

    # @api.multi
    # def write(self, vals):
    #     self.update({'vehicle_status': 'customer'})


#     @api.multi
#     def name_get(self):
#         context = dict(self.env.context)
#         result = []
#         ress = super(ARS_stock_production_lot,self).name_get()
#         if 'active_picking_id' not in context and not 'lotno' in context:
#             if ress:
#                 reg_count = self.env['stock.production.lot'].search([('id', 'in', self.ids),('reg_no','!=', False)])
#                 if len(self) == 8:
#                     if len(reg_count) < 8:
#                         reg_no_count = self.env['stock.production.lot'].search([('reg_no', '!=', False)],limit=8)
#                         self = reg_no_count
#                         ress = super(ARS_stock_production_lot, self).name_get()
#                 for res in ress:
#                     r = list(res)
#                     st_pr_lt = self.browse(int(r[0]))
#                     if st_pr_lt.reg_no:
#                         r[1] = st_pr_lt.reg_no
#                         res_t = tuple(r)
#                         result.append(res_t)
#         if result:
#             ress = result
#         return ress
    
class Picking(models.Model):
    _inherit = 'stock.picking'

    product_template_id = fields.Many2one('product.template', string='Product')
    product_catalog_id = fields.Many2one('product.catalog', string='Catalog Type')

    @api.multi
    def button_validate(self):
        print ('called validate')
        for stock_production_obj in self.move_line_ids:
            if stock_production_obj.lot_id:
                stock_production_obj.lot_id.custumer_ide = [(0, 0, {'custmer_name': self.partner_id.id,
                                                  'date_of_ownership': datetime.now(),
                                                  'address': self.partner_id.city,
                                                  'mobile': self.partner_id.mobile})]

                stock_production_obj.lot_id.check_new_lotno = True
        res = super(Picking, self).button_validate()
        self._cr.commit()
        picking_type = self.picking_type_id
        no_quantities_done = all(
            float_is_zero(move_line.qty_done, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
               lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))

            for line in lines_to_check:
                if not line.move_id.sale_line_id and (line.lot_name or line.lot_id):
                   vals = {'mvariant_id'   : line.product_id.id,
                           'model_id'      : line.product_id.product_tmpl_id.id,
                           'vin_sn'        : line.lot_id and line.lot_id.name or line.lot_name,
                           'license_plate' : '/',
                           'company_id'    : line.move_id.company_id.id,
                           'vehicle_status': 'new',
                           'lot_id'        : line.lot_id and line.lot_id.id,
                           'driver_id' : self.env.user.company_id.partner_id.id
                          }
                   res=self.env['fleet.vehicle'].create(vals)
                   res.custumer_ide = [(0, 0, {'custmer_name': self.partner_id.id,
                                           'date_of_ownership': datetime.now(),
                                           'address': self.partner_id.city,
                                           'mobile': self.partner_id.mobile})]
                elif line.lot_id and line.move_id.sale_line_id:
                    vals = {
                            'vin_no': line.lot_id.id,
                            }
                    line.move_id.sale_line_id.write(vals)
                    self.env['fleet.vehicle'].search([('lot_id','=',line.lot_id.id)]).write({'driver_id': line.move_id.partner_id and line.move_id.partner_id.id, 'vehicle_status':'customer','customer_ids' : [(0, 0, {'custmer_name': self.partner_id.id,
                                           'date_of_ownership': datetime.now(),
                                           'address': self.partner_id.city,
                                           'mobile': self.partner_id.mobile})]})
        return res



    # @api.multi
    # def button_validate(self):
    #     print('called overriden validate')
    #     self.ensure_one()
    #     if not self.move_lines and not self.move_line_ids:
    #         raise UserError(_('Please add some lines to move'))
    #
    #     # If no lots when needed, raise error
    #     picking_type = self.picking_type_id
    #     no_quantities_done = all(
    #         float_is_zero(move_line.qty_done, precision_rounding=move_line.product_uom_id.rounding) for move_line in
    #         self.move_line_ids)
    #     no_reserved_quantities = all(
    #         float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
    #         self.move_line_ids)
    #     if no_reserved_quantities and no_quantities_done:
    #         raise UserError(_(
    #             'You cannot validate a transfer if you have not processed any quantity. You should rather cancel the transfer.'))
    #
    #     if picking_type.use_create_lots or picking_type.use_existing_lots:
    #         lines_to_check = self.move_line_ids
    #         if not no_quantities_done:
    #             lines_to_check = lines_to_check.filtered(
    #                 lambda line: float_compare(line.qty_done, 0,
    #                                            precision_rounding=line.product_uom_id.rounding)
    #             )
    #
    #         for line in lines_to_check:
    #             product = line.product_id
    #             if product and product.tracking != 'none':
    #                 if not line.lot_name and not line.lot_id:
    #                     raise UserError(_('You need to supply a lot/serial number for %s.') % product.display_name)
    #                 elif line.qty_done == 0:
    #                     raise UserError(_(
    #                         'You cannot validate a transfer if you have not processed any quantity for %s.') % product.display_name)
    #
    #     if no_quantities_done:
    #         view = self.env.ref('stock.view_immediate_transfer')
    #         wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
    #         return {
    #             'name': _('Immediate Transfer?'),
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'stock.immediate.transfer',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'target': 'new',
    #             'res_id': wiz.id,
    #             'context': self.env.context,
    #         }
    #
    #     if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
    #         view = self.env.ref('stock.view_overprocessed_transfer')
    #         wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'stock.overprocessed.transfer',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'target': 'new',
    #             'res_id': wiz.id,
    #             'context': self.env.context,
    #         }
    #
    #     # Check backorder should check for other barcodes
    #     if self._check_backorder():
    #         return self.action_generate_backorder_wizard()
    #     self.action_done()
    #     return



    # On click of validate while sale the vehicle create Customer Ownership history
#     @api.multi
#     def button_validate(self):
#         for stock_production_obj in self.move_line_ids:
#             if stock_production_obj.lot_id:
#                 stock_production_obj.lot_id.custumer_ide = [(0, 0, {'custmer_name': self.partner_id.id,
#                                                   'date_of_ownership': datetime.now(),
#                                                   'address': self.partner_id.city,
#                                                   'mobile': self.partner_id.mobile})]
# 
#         return super(ARS_Picking, self).button_validate()


    # by default 'New vehicle' comes in vehicle_status field on create of purchase order
    # @api.multi
    # def _action_done(self):
    #     """ This method is called during a move's `action_done`. It'll actually move a quant from
    #     the source location to the destination location, and unreserve if needed in the source
    #     location.
    #
    #     This method is intended to be called on all the move lines of a move. This method is not
    #     intended to be called when editing a `done` move (that's what the override of `write` here
    #     is done.
    #     """
    #
    #     # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
    #     # be negative and, according to the presence of a picking type or a linked inventory
    #     # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
    #     # the line. It is mandatory in order to free the reservation and correctly apply
    #     # `action_done` on the next move lines.
    #     ml_to_delete = self.env['stock.move.line']
    #     for ml in self:
    #         qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
    #         if qty_done_float_compared > 0:
    #             if ml.product_id.tracking != 'none':
    #                 picking_type_id = ml.move_id.picking_type_id
    #                 if picking_type_id:
    #                     if picking_type_id.use_create_lots:
    #                         # If a picking type is linked, we may have to create a production lot on
    #                         # the fly before assigning it to the move line if the user checked both
    #                         # `use_create_lots` and `use_existing_lots`.
    #                         if ml.lot_name and not ml.lot_id:
    #                             lot = self.env['stock.production.lot'].create(
    #                                 {'name': ml.lot_name, 'product_id': ml.product_id.id}
    #                             )
    #                             ml.write({'lot_id': lot.id})
    #                     elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
    #                         # If the user disabled both `use_create_lots` and `use_existing_lots`
    #                         # checkboxes on the picking type, he's allowed to enter tracked
    #                         # products without a `lot_id`.
    #                         continue
    #                 elif ml.move_id.inventory_id:
    #                     # If an inventory adjustment is linked, the user is allowed to enter
    #                     # tracked products without a `lot_id`.
    #                     continue
    #
    #                 if not ml.lot_id:
    #                     raise UserError(_('You need to supply a lot/serial number for %s.') % ml.product_id.name)
    #         elif qty_done_float_compared < 0:
    #             raise UserError(_('No negative quantities allowed'))
    #         else:
    #             ml_to_delete |= ml
    #     ml_to_delete.unlink()
    #
    #     # Now, we can actually move the quant.
    #     for ml in self - ml_to_delete:
    #         if ml.product_id.type == 'product':
    #             Quant = self.env['stock.quant']
    #             rounding = ml.product_uom_id.rounding
    #
    #             # if this move line is force assigned, unreserve elsewhere if needed
    #             if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty, precision_rounding=rounding) > 0:
    #                 extra_qty = ml.qty_done - ml.product_qty
    #                 ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #             # unreserve what's been reserved
    #             if not ml.location_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
    #                 try:
    #                     Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #                 except UserError:
    #                     Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #
    #             # move what's been actually done
    #             quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
    #             available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #             if available_qty < 0 and ml.lot_id:
    #                 # see if we can compensate the negative quants with some untracked quants
    #                 untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #                 if untracked_qty:
    #                     taken_from_untracked_qty = min(untracked_qty, abs(quantity))
    #                     Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
    #                     Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #             Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
    #     # Reset the reserved quantity as we just moved it to the destination location.
    #     (self - ml_to_delete).with_context(bypass_reservation_update=True).write({'product_uom_qty': 0.00})

