from odoo import models, fields, api
from datetime import datetime
from datetime import timedelta

class customer_history(models.Model):
    _name = 'ownership.history'

    custmer_name = fields.Many2one('res.partner')
    date_of_ownership = fields.Date()
    address = fields.Text()
    mobile = fields.Char()
    sold_by = fields.Many2one('res.partner')
    stock_id1 = fields.Many2one('stock.production.lot','Stock Id')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Fleet Vehicle ID')

class emission_history(models.Model):
    _name = 'emission.history'

    emission_doc_no = fields.Char()
    agency_name = fields.Char()
    emission_start = fields.Date()
    emision_end = fields.Date()
    set_reminder = fields.Date()
    stock_id2 = fields.Many2one('stock.production.lot')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Fleet Vehicle ID')


class insurance_history(models.Model):
    _name = 'insurance.history'

    insurance_doc_no = fields.Char()
    vender_name = fields.Many2one('res.partner')
    insurance_start = fields.Date()
    insurance_end = fields.Date()
    set_reminder = fields.Date()
    stock_id3 = fields.Many2one('stock.production.lot')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Fleet Vehicle ID')


class service_history(models.Model):
    _name = 'service.history'

#     @api.multi
#     def _calculate_service_history(self):
#         for record in self:
#             service_order = self.env['sale.order'].search([('sale_aftersales','=','after_sales'),('regn_no','=',record.reg_no),('partner_id','=',record.customer_id.id),('invoice_status','=','invoiced')])
#             if service_order:
#                 nxt_date = service_order.confirmation_date + timedelta(days=90)
#                 set_reminder = service_order.confirmation_date + timedelta(days=30)
#                 record.write({'order':service_order.id,'servicetype':'First Free Service','next_service_due':nxt_date,'stock_id4':record.id,'set_reminder':set_reminder})
#             


    order = fields.Many2one('sale.order')
    servicetype = fields.Char()
    date = fields.Date()
    mileage = fields.Integer()
    next_serv_due = fields.Date()
    next_service_due = fields.Date()
    set_reminder = fields.Date()
    stock_id4 = fields.Many2one('stock.production.lot')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Fleet Vehicle ID')
class Brand_model(models.Model):
    _name = 'brand.name'

    name = fields.Char(string="Brand Name")





