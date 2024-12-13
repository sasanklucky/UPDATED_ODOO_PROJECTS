# -*- coding: utf-8 -*-

from odoo import models, fields, api


class customer_history(models.Model):
    _name = 'ownership.history'

    custmer_name = fields.Many2one('res.partner')
    date_of_ownership = fields.Date()
    delivery_date = fields.Date()
    address = fields.Text()
    mobile = fields.Char()
    sold_by = fields.Many2one('res.partner')
    stock_id1 = fields.Many2one('stock.production.lot', 'Stock Id')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Fleet Vehicle ID')


class service_history(models.Model):
    _name = 'service.history'

    order = fields.Many2one('sale.order')
    servicetype = fields.Char(compute="_compute_servicetype")
    date = fields.Date()
    mileage = fields.Integer()
    next_serv_due = fields.Date()
    next_service_due = fields.Date()
    set_reminder = fields.Date()
    closed_date = fields.Date(string="Closed Date")
    stock_id4 = fields.Many2one('stock.production.lot')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Fleet Vehicle ID')

    @api.multi
    def _compute_servicetype(self):
        for record in self:
            if record.sudo().order.service_type:
                record.servicetype = record.order.sudo().service_type.name
            if record.service_type_name:
                record.servicetype = record.service_type_name

    @api.multi
    def _compute_mileage(self):
        for mileage in self:
            if mileage.order.sudo().mileage_in:
                mileage.mileage = mileage.order.sudo().mileage_in
            if mileage.mileage_in:
                mileage.mileage = mileage.mileage_in
