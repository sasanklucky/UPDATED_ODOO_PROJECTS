from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ARSStockReturnPickings(models.TransientModel):
    _inherit = 'stock.return.picking'

    picking_id = fields.Many2one('stock.picking', string='Picking')

    @api.multi
    def _create_returns(self):
        res = super(ARSStockReturnPickings, self)._create_returns()
        picking_record = self.env['stock.picking'].sudo().search([('id', '=', self.picking_id.id)])
        sale_order = self.env['sale.order'].sudo().search([('id', '=', picking_record.sale_id.id)])
        if sale_order.sale_type == 'vehicle':
            print('NEED TO RETURN --------->')
            pickings = picking_record.move_lines
            for record in pickings:
                move_line_ids = record.move_line_ids
                for move in move_line_ids:
                    vin = move.lot_id.name
                    fleet_vehicle = self.env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin)])
                    return_services = self.env['service.type'].search(
                        [('sequence', '=', fleet_vehicle.service_type_sequence)])
                    if fleet_vehicle.service_type_sequence != 0:
                        raise ValidationError(f" Already you have done {return_services.name} ! "
                                              f"You can not return the vehicle.")
        else:
            _logger.info("Non-vehicle return — proceeding normally.")
        return res

