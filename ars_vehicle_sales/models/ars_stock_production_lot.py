from odoo import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class ARS_stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'
    # _rec_name = 'reg_no'
    check_new_lotno = fields.Boolean(default=False)

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


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        print('called validate')
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
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))

            for line in lines_to_check:
                if not line.move_id.sale_line_id and (line.lot_name or line.lot_id):
                    vals = {'mvariant_id': line.product_id.id,
                            'model_id': line.product_id.product_tmpl_id.id,
                            'vin_sn': line.lot_id and line.lot_id.name or line.lot_name,
                            'license_plate': '/',
                            'company_id': line.move_id.company_id.id,
                            'vehicle_status': 'new',
                            'lot_id': line.lot_id and line.lot_id.id,
                            'driver_id': self.env.user.company_id.partner_id.id
                            }
                    res = self.env['fleet.vehicle'].create(vals)
                    res.custumer_ide = [(0, 0, {'custmer_name': self.partner_id.id,
                                                'date_of_ownership': datetime.now(),
                                                'address': self.partner_id.city,
                                                'mobile': self.partner_id.mobile})]
                elif line.lot_id and line.move_id.sale_line_id:
                    vals = {
                        'vin_no': line.lot_id.id,
                    }
                    line.move_id.sale_line_id.write(vals)
                    self.env['fleet.vehicle'].search([('lot_id', '=', line.lot_id.id)]).write(
                        {'driver_id': line.move_id.partner_id and line.move_id.partner_id.id,
                         'vehicle_status': 'customer', 'customer_ids': [(0, 0, {'custmer_name': self.partner_id.id,
                                                                                'date_of_ownership': datetime.now(),
                                                                                'address': self.partner_id.city,
                                                                                'mobile': self.partner_id.mobile})]})
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
        if self.product_template_id:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            return {'domain': {'product_id': [('id', 'in', varient_ids.ids)]}}
        else:
            return {'domain': {'product_id': [('id', 'in', False)]}}


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.constrains('lot_name', 'lot_id')
    def lot_name_alphanumeric_constrains(self):
        for record in self:
            if record.lot_name:
                # len(record.lot_name) == 17
                if not record.lot_name.isalnum():
                    raise ValidationError(_('Please enter valid Lot/Serial Number!'))
            elif record.lot_id:
                if not record.lot_id.name.isalnum():
                    raise ValidationError(_('Please enter valid Lot/Serial Number!'))


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.constrains('name')
    def lot_name_alphanumeric_constrains(self):
        for record in self:
            # len(record.name)
            if record.name:
                if not record.name.isalnum():
                    raise ValidationError(_('Please enter valid Lot/Serial Number!'))
