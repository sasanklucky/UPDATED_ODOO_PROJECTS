from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ARSStockReturnPickings(models.TransientModel):
    _inherit = 'stock.return.picking'

    picking_id = fields.Many2one('stock.picking', string='Picking')
    # @api.multi
    # def _create_returns(self):
    #     res = super(ARSStockReturnPickings, self)._create_returns()
    #     picking_record = self.env['stock.picking'].sudo().search([('id', '=', self.picking_id.id)])
    #     # print(picking_record,'picking_record')
    #     # print(picking_record.move_lines,'move_lines')
    #     pickings = picking_record.move_lines
    #     for record in pickings:
    #         # print(record)
    #         # print(record.move_line_ids,'Enter into move_line_ids')
    #         move_line_ids = record.move_line_ids
    #         for move in move_line_ids:
    #             # print(move)
    #             vin = move.lot_id.name
    #             # print(vin,'vin_number')
    #             fleet_vehicle = self.env['fleet.vehicle'].sudo().search([('vin_sn','=',vin)])
    #             # print(fleet_vehicle,'fleet_vehicle')
    #             # print(fleet_vehicle.service_type_sequence,'service_type_sequence')
    #             return_services = self.env['service.type'].search([('sequence','=',fleet_vehicle.service_type_sequence)])
    #             # print(return_services, 'return_services')
    #             if fleet_vehicle.service_type_sequence != 0:
    #                 raise ValidationError(f" Already you have done {return_services.name} ! "
    #                                               f"You can not return the vehicle.")
    #     return res

    # picking_id = fields.Many2one('stock.picking', string='Picking')
    # @api.multi
    # def _create_returns(self):
    #     print('return started')
    #     res = super(ARSStockReturnPickings, self)._create_returns()
    #     picking_record = self.env['stock.picking'].sudo().search([('id', '=', self.picking_id.id)])
    #     print(picking_record,'picking_record')
    #     print(picking_record.origin)
    #     sales_order = self.env['sale.order'].sudo().search([('name','=',picking_record.origin)])
    #     print(sales_order,'sales_order')
    #     return_services = self.env['service.type'].search([('id','=',sales_order.service_type.id)])
    #     print(return_services,'return_services')
    #     print(return_services.sequence,'sequence')
    #     if return_services.sequence != 0 :
    #         raise ValidationError(f" Already you have done {return_services.name} !"
    #                               f"You can not return it.")
    #     return res





