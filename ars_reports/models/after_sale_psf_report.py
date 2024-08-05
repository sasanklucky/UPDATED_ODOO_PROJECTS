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
    ro_open_date = fields.Datetime(string="RO Open Date")
    ro_number = fields.Char(string="RO Number")
    ro_close_date = fields.Datetime(string="RO Close Date")
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
    ro_ageing = fields.Integer('Ro Ageing', compute='ro_ageing_compute')

    @api.depends('ro_close_date', 'ro_open_date')
    def ro_ageing_compute(self):
        for record in self:
            if record.ro_open_date and record.ro_close_date:
                start_date = datetime.strptime(record.ro_open_date, '%Y-%m-%d %H:%M:%S')
                end_date = datetime.strptime(record.ro_close_date, '%Y-%m-%d %H:%M:%S')
                delta = end_date - start_date
                record.ro_ageing = delta.days
            else:
                record.ro_ageing = 0

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
        select row_number() over(order by so.id desc) as id,
        initcap(to_char(inv.date_invoice, 'month')) as month,
        inv.company_id as dealer_name_id,
        inv.number as invoice_number, 
        so.appointment_date as ro_open_date,
        inv.origin as ro_number,
        inv.date_invoice as invoice_date,
        inv.create_date as ro_close_date,
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
        where inv.state not in ('draft', 'cancelled') and so.sale_aftersales = 'after_sales'
        and rp.opt_out = 'False' )""" % (
            self._table))

    def export_xls(self, param=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheets = workbook.add_worksheet('AfterSale PSF Report')
        sheets.set_column('C:C', 35)
        sheets.set_column('D:X', 25)
        sheets.set_column('J:J', 35)
        sheets.set_column('V:W', 35)
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True, 'bg_color': '#8f8f8f'})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheets.merge_range(0, 0, 2, 23, 'After-Sales PSF Report', format0)
        sheets.write(3, 0, 'Sl No', format21)
        sheets.write(3, 1, 'Month', format21)
        sheets.write(3, 2, 'Dealer Name', format21)
        sheets.write(3, 3, 'Invoice Date', format21)
        sheets.write(3, 4, 'Invoice Number', format21)
        sheets.write(3, 5, 'RO Open Date', format21)
        sheets.write(3, 6, 'RO Number', format21)
        sheets.write(3, 7, 'RO Close Date', format21)
        sheets.write(3, 8, 'VIN', format21)
        sheets.write(3, 9, 'Customer Name', format21)
        sheets.write(3, 10, 'Customer Mobile', format21)
        sheets.write(3, 11, 'Customer City', format21)
        sheets.write(3, 12, 'Customer Phone', format21)
        sheets.write(3, 13, 'Customer Pan No.', format21)
        sheets.write(3, 14, 'Untaxed Amount', format21)
        sheets.write(3, 15, 'Tax', format21)
        sheets.write(3, 16, 'Total', format21)
        sheets.write(3, 17, 'Service Options', format21)
        sheets.write(3, 18, 'Service Type', format21)
        sheets.write(3, 19, 'Type', format21)
        sheets.write(3, 20, 'Service Advisor', format21)
        sheets.write(3, 21, 'Reg No.', format21)
        sheets.write(3, 22, 'Model', format21)
        sheets.write(3, 23, 'Delivery Date', format21)

        date = str(datetime.now().date())
        dateval = datetime.strptime(date, "%Y-%m-%d")
        date2 = dateval + timedelta(days=-5)
        datetimes = datetime.strftime(dateval, "%Y-%m-%d")
        datetimes2 = datetime.strftime(date2, "%Y-%m-%d")
        records = self.env['after.sale.report'].search([('delivery_date', '>=', datetimes2), ('delivery_date', '<', datetimes)])

        row = 4
        column = 0
        sl = 0
        for record in records:
            sheets.write(row, column, sl + 1, format11)
            sheets.write(row, column + 1, record.month, format11)
            sheets.write(row, column + 2, record.dealer_name_id.name, format11)
            inv_date = datetime.strptime(record.invoice_date, '%Y-%m-%d')
            invoice_date = inv_date.strftime('%d-%m-%Y')
            sheets.write(row, column + 3, invoice_date, format11)
            sheets.write(row, column + 4, record.invoice_number, format11)
            if record.ro_open_date:
                ro_o_date = datetime.strptime(record.ro_open_date, '%Y-%m-%d')
                ro_open_date = ro_o_date.strftime('%d-%m-%Y')
                sheets.write(row, column + 5, ro_open_date, format11)
            sheets.write(row, column + 6, record.ro_number, format11)
            if record.ro_close_date:
                ro_co_date = datetime.strptime(record.ro_close_date, '%Y-%m-%d')
                ro_close_date = ro_co_date.strftime('%d-%m-%Y')
                sheets.write(row, column + 7, ro_close_date, format11)
            sheets.write(row, column + 8, record.vin, format11)
            sheets.write(row, column + 9, record.partner_id.name, format11)
            sheets.write(row, column + 10, record.mobile, format11)
            sheets.write(row, column + 11, record.city, format11)
            sheets.write(row, column + 12, record.phone, format11)
            sheets.write(row, column + 13, record.pan_no, format11)
            sheets.write(row, column + 14, record.amount_untaxed, format11)
            sheets.write(row, column + 15, record.amount_tax, format11)
            sheets.write(row, column + 16, record.amount_total, format11)
            sheets.write(row, column + 17, record.service_options_id.name, format11)
            sheets.write(row, column + 18, record.service_type_id.name, format11)
            sheets.write(row, column + 19, record.doc_type, format11)
            sheets.write(row, column + 20, record.user_id.name, format11)
            sheets.write(row, column + 21, record.reg_no.license_plate, format11)
            sheets.write(row, column + 22, record.model.display_name, format11)
            if record.delivery_date:
                del_date = datetime.strptime(record.delivery_date, '%Y-%m-%d')
                delivery_date = del_date.strftime('%d-%m-%Y')
                sheets.write(row, column + 23, delivery_date, format11)
            sl = sl + 1
            row = row + 1
        workbook.close()
        output.seek(0)
        data = output.read()
        output.close()
        data = base64.encodebytes(data)
        doc_id = self.env['ir.attachment'].create({'datas': data, 'name': 'Aftersale_psf_report_' + str(datetime.now().date()) + '.xls',
                                                   'datas_fname': 'Aftersale_psf_report_' + str(datetime.now().date()) + '.xls',
                                                   })
        print('doc_id', doc_id.datas_fname, doc_id.res_name)
        if param is not None:
            return doc_id
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?id=%s&download=true' % doc_id.id,
                'target': 'current',
            }

