import io
import base64
import datetime
from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


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
    product_template_id = fields.Many2one('product.template')
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
        invl.product_template_id,
        inv.gate_pass_date as delivery_date,
        rp.street as delivery_address1,
        rp.street2 as delivery_address2
        from  account_invoice inv
        left join account_invoice_line invl on invl.invoice_id = inv.id
        left join sale_order so on inv.order_id=so.id
        left join res_partner rp on rp.id = so.partner_id
        left join stock_production_lot lot on invl.vin_no = lot.id
        where inv.type='out_invoice'  and inv.state not in ('draft', 'cancel')and 
        inv.ars_invoice_type = 'vehicle' and invl.vin_no is not null)
        """ % (self._table))

    def export_xls(self, param=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheets = workbook.add_worksheet('PSF RSA Report')
        sheets.set_column('D:R', 30)
        sheets.set_column('H:H', 35)
        sheets.set_column('S:T', 38)
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True, 'bg_color': '#8f8f8f'})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format12 = workbook.add_format({'font_size': 10, 'align': 'center', 'text_wrap': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheets.merge_range(0, 0, 2, 23, 'PSF RSA Report ', format0)
        sheets.write(3, 0, 'Sl No', format21)
        sheets.write(3, 1, 'Month', format21)
        sheets.write(3, 2, 'Year', format21)
        sheets.write(3, 3, 'Dealer Name', format21)
        sheets.write(3, 4, 'Invoice Date', format21)
        sheets.write(3, 5, 'Invoice Number', format21)
        sheets.write(3, 6, 'Sales Person', format21)
        sheets.write(3, 7, 'Customer Name', format21)
        sheets.write(3, 8, 'Customer Mobile', format21)
        sheets.write(3, 9, 'Customer City', format21)
        sheets.write(3, 10, 'Customer Phone', format21)
        sheets.write(3, 11, 'Customer Pan No.', format21)
        sheets.write(3, 12, 'VIN', format21)
        sheets.write(3, 13, 'Model', format21)
        sheets.write(3, 14, 'Untaxed Amount', format21)
        sheets.write(3, 15, 'Tax', format21)
        sheets.write(3, 16, 'Total', format21)
        sheets.write(3, 17, 'Delivery Date', format21)
        sheets.write(3, 18, 'Delivery Address 1', format21)
        sheets.write(3, 19, 'Delivery Address 2', format21)

        date = str(datetime.now().date())
        dateval = datetime.strptime(date, "%Y-%m-%d")

        datetimes = datetime.strftime(dateval, "%Y-%m-%d")
        records = self.env['vehicle.sale.psf.report'].search([('product_template_id.rsa', '=', 'yes'),
                                                              ('delivery_date', '=', datetimes)])

        row = 4
        column = 0
        sl = 0
        for record in records:
            sheets.write(row, column, sl + 1, format11)
            sheets.write(row, column + 1, record.month, format11)
            sheets.write(row, column + 2, record.year, format11)
            sheets.write(row, column + 3, record.dealer_name_id.name, format12)
            sheets.write(row, column + 4, record.invoice_date, format11)
            sheets.write(row, column + 5, record.invoice_number, format11)
            sheets.write(row, column + 6, record.user_id.name, format12)
            sheets.write(row, column + 7, record.partner_id.name, format11)
            sheets.write(row, column + 8, record.mobile, format11)
            sheets.write(row, column + 9, record.city, format11)
            sheets.write(row, column + 10, record.phone, format11)
            sheets.write(row, column + 11, record.pan_no, format11)
            sheets.write(row, column + 12, record.vin, format11)
            sheets.write(row, column + 13, record.product_template_id.name, format11)
            sheets.write(row, column + 14, record.amount_untaxed, format11)
            sheets.write(row, column + 15, record.amount_tax, format11)
            sheets.write(row, column + 16, record.amount_total, format11)
            sheets.write(row, column + 17, record.delivery_date, format11)
            sheets.write(row, column + 18, record.delivery_address1, format12)
            sheets.write(row, column + 19, record.delivery_address2, format12)

            sl = sl + 1
            row = row + 1
        workbook.close()
        output.seek(0)
        if records:
            data = output.read()
            output.close()
            data = base64.encodebytes(data)
            doc_id = self.env['ir.attachment'].create({'datas': data, 'name': 'Rsa_psf_report_' + str(datetime.now().date()) + '.xls',
                                                       'datas_fname': 'Rsa_psf_report_' + str(datetime.now().date()) + '.xls',
                                                       })
            if param is not None:
                return doc_id
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/content/?id=%s&download=true' % doc_id.id,
                    'target': 'current',
                }
        else:
            False

    def send_psf_rsa_mail(self):
        rsa_attachment, template = False, False
        records = self.env['automation.email.conf'].search([])
        for record in records:
            if record.psf_rsa_report:
                if record.report_template_id:
                    template = record.report_template_id
                    template.attachment_ids = [(5,)]
                    rsa_attachment = self.export_xls(param=True)
                    users = record.mail_list_ids
                    template.attachment_ids = [(4, rsa_attachment.id)] if rsa_attachment else False
                    template.send_mail(self.id, email_values={'recipient_ids': [(4, user.id) for user in users],
                                                              }, force_send=True)
                else:
                    mail_values = {
                        'subject': record.mail_subject,
                        'body_html': record.mail_template,
                        'recipient_ids': [(4, user.id) for user in record.mail_list_ids]
                    }
                    mail_obj = self.env['mail.mail'].create(mail_values)
                    if record.psf_rsa_report:
                        rsa_attachment = self.export_xls(param=True)
                    mail_obj.write({'attachment_ids': [(4, rsa_attachment.id)] if rsa_attachment else False})
                    mail_obj.send()

    def export_xls_weekly(self, param=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheets = workbook.add_worksheet('Vehicle-Sale PSF Report')
        sheets.set_column('D:R', 30)
        sheets.set_column('H:H', 35)
        sheets.set_column('S:T', 38)
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True, 'bg_color': '#8f8f8f'})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format12 = workbook.add_format({'font_size': 10, 'align': 'center', 'text_wrap': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheets.merge_range(0, 0, 2, 23, 'Vehicle-Sale PSF Report ', format0)
        sheets.write(3, 0, 'Sl No', format21)
        sheets.write(3, 1, 'Month', format21)
        sheets.write(3, 2, 'Year', format21)
        sheets.write(3, 3, 'Dealer Name', format21)
        sheets.write(3, 4, 'Invoice Date', format21)
        sheets.write(3, 5, 'Invoice Number', format21)
        sheets.write(3, 6, 'Sales Person', format21)
        sheets.write(3, 7, 'Customer Name', format21)
        sheets.write(3, 8, 'Customer Mobile', format21)
        sheets.write(3, 9, 'Customer City', format21)
        sheets.write(3, 10, 'Customer Phone', format21)
        sheets.write(3, 11, 'Customer Pan No.', format21)
        sheets.write(3, 12, 'VIN', format21)
        sheets.write(3, 13, 'Model', format21)
        sheets.write(3, 14, 'Untaxed Amount', format21)
        sheets.write(3, 15, 'Tax', format21)
        sheets.write(3, 16, 'Total', format21)
        sheets.write(3, 17, 'Delivery Date', format21)
        sheets.write(3, 18, 'Delivery Address 1', format21)
        sheets.write(3, 19, 'Delivery Address 2', format21)

        date = str(datetime.now().date())
        dateval = datetime.strptime(date, "%Y-%m-%d")
        date2 = dateval + timedelta(days=-5)
        datetimes = datetime.strftime(dateval, "%Y-%m-%d")
        datetimes2 = datetime.strftime(date2, "%Y-%m-%d")
        records = self.env['vehicle.sale.psf.report'].search([('invoice_date', '>=', datetimes2), ('invoice_date', '<', datetimes)])

        row = 4
        column = 0
        sl = 0
        for record in records:
            sheets.write(row, column, sl + 1, format11)
            sheets.write(row, column + 1, record.month, format11)
            sheets.write(row, column + 2, record.year, format11)
            sheets.write(row, column + 3, record.dealer_name_id.name, format12)
            sheets.write(row, column + 4, record.invoice_date, format11)
            sheets.write(row, column + 5, record.invoice_number, format11)
            sheets.write(row, column + 6, record.user_id.name, format12)
            sheets.write(row, column + 7, record.partner_id.name, format11)
            sheets.write(row, column + 8, record.mobile, format11)
            sheets.write(row, column + 9, record.city, format11)
            sheets.write(row, column + 10, record.phone, format11)
            sheets.write(row, column + 11, record.pan_no, format11)
            sheets.write(row, column + 12, record.vin, format11)
            sheets.write(row, column + 13, record.product_template_id.name, format11)
            sheets.write(row, column + 14, record.amount_untaxed, format11)
            sheets.write(row, column + 15, record.amount_tax, format11)
            sheets.write(row, column + 16, record.amount_total, format11)
            sheets.write(row, column + 17, record.delivery_date, format11)
            sheets.write(row, column + 18, record.delivery_address1, format12)
            sheets.write(row, column + 19, record.delivery_address2, format12)

            sl = sl + 1
            row = row + 1
        workbook.close()
        output.seek(0)
        if records:
            data = output.read()
            output.close()
            data = base64.encodebytes(data)
            doc_id = self.env['ir.attachment'].create({'datas': data, 'name': 'Vehicle_sale_psf_report_' + str(datetime.now().date()) + '.xls',
                                                       'datas_fname': 'Vehicle_sale_psf_report_' + str(datetime.now().date()) + '.xls',
                                                       })
            if param is not None:
                return doc_id
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/content/?id=%s&download=true' % doc_id.id,
                    'target': 'current',
                }
        else:
            False
