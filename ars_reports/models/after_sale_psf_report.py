import io
import base64
import datetime
from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta


try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AfterSaleReport(models.Model):
    _name = 'after.sale.report'
    _description = 'After Sale Report'
    _auto = False

    month = fields.Char(string="Month")
    dealer_name_id = fields.Many2one('res.company', string="Dealer Name")
    invoice_date = fields.Date(string="Invoice Date")
    invoice_number = fields.Char(string="Invoice Number")
    ro_open_date = fields.Date(string="ro_opendate")
    ro_number = fields.Char(string="RO Number")
    ro_close_date = fields.Date(string="RO Close Date")
    vin = fields.Char(string="VIN")
    partner_id = fields.Many2one('res.partner', string="Customer Name")
    mobile = fields.Char(string="Customer Mobile")
    city = fields.Char(string="Customer City")
    phone = fields.Char(string="Customer Phone")
    pan_no = fields.Char(string="Pan No.")
    amount_untaxed = fields.Float(string="Untaxed Amount")
    amount_tax = fields.Float(string="Tax")
    amount_total = fields.Float(string="Total")
    service_options_id = fields.Many2one('service.options', string="Service Options")
    service_type_id = fields.Many2one('service.type', string="Service Type")
    doc_type = fields.Char(string="Type")
    user_id = fields.Many2one('res.users', string="Service Advisor", track_visibility='onchange')
    reg_no = fields.Many2one('fleet.vehicle', string="Reg No.")
    model = fields.Many2one('product.product', string="Model")
    delivery_date = fields.Date(string="Delivery Date")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
        select row_number() over(order by so.id desc) as id,
        initcap(to_char(inv.date_invoice, 'month')) as month,
        inv.company_id as dealer_name_id,
        inv.number as invoice_number, 
        so.create_date as ro_open_date, 
        inv.origin as ro_number,
        inv.date_invoice as invoice_date,
        inv.date_invoice as ro_close_date,
        inv.vin as vin,
        so.partner_id as partner_id,
        rp.mobile as mobile,
        rp.city as city,
        rp.phone as phone,
        rp.pan_no as pan_no,
        inv.amount_untaxed as amount_untaxed,
        inv.amount_tax as amount_tax,
        inv.amount_total as amount_total,
        so.service_options as service_options_id,
        so.service_type as service_type_id,
        ru.id as user_id,
        so.doc_type as doc_type,
        inv.reg_no as reg_no,
        inv.model as model,
        inv.gate_pass_date as delivery_date
        from account_invoice inv left join sale_order so on so.name = inv.origin
        left join res_partner rp on rp.id = so.partner_id 
        left join res_users ru on ru.id = so.user_id 
        left join res_company rc on ru.company_id = rc.id
	where inv.state not in ('draft', 'cancelled') and so.sale_aftersales = 'after_sales')""" % (
        self._table))       
