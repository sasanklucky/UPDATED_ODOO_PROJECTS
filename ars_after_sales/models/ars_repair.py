# # -*- coding: utf-8 -*-
#
#
# from odoo import models, fields, api
# from datetime import datetime, timedelta
#
# class ARSMRPOrder(models.Model):
#     _inherit = 'mrp.repair'
#
#     name = fields.Char('Doc No.',default=lambda self: self.env['ir.sequence'].next_by_code('mrp.repair'),copy=False, required=True,states={'confirmed': [('readonly', True)]})
#     regn_no = fields.Char()
#     type = fields.Char()
#     lot_id = fields.Many2one('stock.production.lot', 'VIN',domain="[('product_id','=', product_id)]",help="Products repaired are all belonging to this lot", oldname="prodlot_id")
#     #model = fields.Many2one('product.product', string='Model')
#     product_id = fields.Many2one('product.product', string='Model',readonly=True, required=True, states={'draft': [('readonly', False)]})
#     service_advisor_id = fields.Many2one('resource.resource', 'Service Advisor')
#     delivery_service_advisor_id = fields.Many2one('resource.resource', 'Delivery Service Advisor')
#     appointment = fields.Datetime(string='Appointment Date & Time')
#     delivery = fields.Datetime(string='Delivery Date & Time')
#     kilometer_till = fields.Char()
#     mobile = fields.Char(related='partner_id.mobile')
#     payment_term = fields.Many2one('account.payment.term', string='Payment Terms')
#
#
#     @api.onchange('product_id')
#     def onchange_product_id(self):
#         # self.guarantee_limit = False
#         # self.lot_id = False
#         if self.product_id:
#             self.product_uom = self.product_id.uom_id.id
#
#     @api.onchange('regn_no')
#     def auto_formfill(self):
#         if self.regn_no:
#             stock_detail = self.env['stock.production.lot'].search([('reg_no','=',self.regn_no)])
#             if stock_detail:
#                 location_detail = self.env['stock.quant'].search([('lot_id','=',stock_detail.id)])
#                 if location_detail:
#                     self.location_id = location_detail[-1].location_id.id
#                     self.location_dest_id = location_detail[-1].location_id.id
#                 self.kilometer_till = stock_detail.kilometer_till
#                 self.partner_id = stock_detail.customer_id.id
#                 # self.model = stock_detail.product_id.id
#                 self.product_id = stock_detail.product_id.id
#                 self.lot_id = stock_detail.id
#                 self.product_uom = stock_detail.product_id.uom_id.id
#                 self.guarantee_limit = stock_detail.warranty_validation
#                 self.type = 'Appointment'
#
#
# class ARSMRPOrderLine(models.Model):
#     _inherit = 'mrp.repair.line'
#
#     onhand_qty = fields.Float()
#     delivery_qty = fields.Float()
#     invoice_qty = fields.Float()
#
#
#
#
#
#
#
