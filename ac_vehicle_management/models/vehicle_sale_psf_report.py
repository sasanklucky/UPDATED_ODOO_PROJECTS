from odoo import models, fields, api, tools, _


class VehicleSalePsfReport(models.Model):
    _name = 'vehicle.sale.psf.report'
    _description = 'After Sale Report'
    _auto = False

    month = fields.Char(string="Month")
    year = fields.Char(string="Year")
    dealer_name_id = fields.Many2one('res.company', string="Dealer Name")
    invoice_date = fields.Date(string="Invoice Date")
    invoice_number = fields.Char(string="Invoice Number")
    user_id = fields.Many2one('res.users', 'Sales Person')
    # ro_open_date = fields.Date(string="ro_opendate")
    # ro_number = fields.Char(string="RO Number")
    # ro_close_date = fields.Date(string="RO Close Date")

    partner_id = fields.Many2one('res.partner', string="Customer Name")
    mobile = fields.Char(string="Customer Mobile")
    city = fields.Char(string="Customer City")
    phone = fields.Char(string="Customer Phone")
    pan_no = fields.Char(string="Pan No.")
    vin = fields.Char(string="VIN")
    model = fields.Char(string="Model")
    amount_untaxed = fields.Float(string="Untaxed Amount")
    amount_tax = fields.Float(string="Tax")
    amount_total = fields.Float(string="Total")
    # service_options_id = fields.Many2one('service.options', string="Service Options")
    # service_type_id = fields.Many2one('service.type', string="Service Type")
    # doc_type = fields.Char(string="Type")
    # user_id = fields.Many2one('res.users', string="Service Advisor", track_visibility='onchange')
    # reg_no = fields.Many2one('fleet.vehicle', string="Reg No.")

    delivery_date = fields.Date(string="Delivery Date")
    delivery_address1 = fields.Char(string="Delivery Address 1")
    delivery_address2 = fields.Char(string="Delivery Address 2")

    @api.model_cr
    def init(self):
        print(self)
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
        select row_number() over(order by inv.id desc) as id,
        initcap(to_char(inv.date_invoice, 'month'))  as month,
        CAST(extract(year from inv.date_invoice) AS INTEGER) as year,
        inv.company_id as dealer_name_id,
        inv.number as invoice_number, 
        inv.date_invoice as invoice_date,
        so.partner_id as partner_id,
        so.user_id as user_id,
        rp.mobile as mobile,
        rp.city as city,
        rp.phone as phone,
        rp.pan_no as pan_no,
        invl.vin_no as vin_no,
        lot.name as vin,
        inv.amount_untaxed as amount_untaxed,
        inv.amount_tax as amount_tax,
        inv.amount_total as amount_total,
        invl.name as model,
        inv.gate_pass_date as delivery_date,
        rp.street as delivery_address1,
        rp.street2 as delivery_address2
        from  account_invoice inv
        left join account_invoice_line invl on invl.invoice_id = inv.id
        left join sale_order so on inv.order_id=so.id
        left join res_partner rp on rp.id = so.partner_id
        left join stock_production_lot lot on invl.vin_no = lot.id
        where inv.type='out_invoice'  and inv.state not in ('draft', 'cancelled')and 
        inv.ars_invoice_type = 'vehicle' and invl.vin_no is not null)
        """ % (self._table))
