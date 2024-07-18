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
    _name = 'vehicle.sale.rsa.report'
    _description = 'Vehicle Sale RSA Report'
    _auto = False
    _table = 'vehicle_sale_rsa_report'

    product_template_id = fields.Many2one('product.template', string='ID Product', )
    brand_name = fields.Char('Brand (Client Name)')
    policy_number = fields.Char('Policy Number')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    customer_name = fields.Many2one('res.partner', string='Customer Name')
    model_type = fields.Many2one('product.template', string='Model Type')
    reg_no = fields.Char(string=' Reg No')
    # RegDate
    selling_dealer_code = fields.Char('Selling Dealer Code')
    dealer_name = fields.Char('Dealer Name')
    dealer_address = fields.Char('Dealer Address')
    dealer_address1 = fields.Char('Dealer Address1')
    dealer_city = fields.Char('Dealer City')
    dealer_state = fields.Many2one('res.country.state', string='Dealer State', )  # use .name
    dealer_pin = fields.Char('Dealer Pin')
    dealer_mobile = fields.Char('Dealer Mobile')
    dealer_email = fields.Char('Dealer Mail')
    vin_number = fields.Char('VIN Number')
    color_id = fields.Char('Color')

    # FuelType
    # DateofSharing

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW {self._table} as (
                select row_number() over(order by inv.id desc) as id,
                    invline.product_template_id,
                    brand_name.name AS brand_name,
                    inv.number AS policy_number,
                    inv.date_invoice AS start_date,
                    (inv.date_invoice + INTERVAL '6 years')::date AS end_date,
                    inv.partner_id AS customer_name,
                    invline.product_template_id AS Model_Type,
                    dealer.dealer_code AS selling_dealer_code,
                    dealer.name AS dealer_name,
                    rp.street AS dealer_address,
                    rp.street2 AS dealer_address1,
                    rp.city AS dealer_city,
                    rp.state_id AS dealer_state,
                    rp.zip AS dealer_pin,
                    rp.mobile AS dealer_mobile,
                    rp.email AS dealer_email,
                    lot.name as vin_number,
                    fv.initial_reg_no as reg_no,
                    prod_attrs.Exterior_Color  as color_id
                from 
                    account_invoice inv
                left join 
                    account_invoice_line invline ON invline.invoice_id = inv.id
                left join 
                    product_template pt ON pt.id = invline.product_template_id
                left join 
                    stock_production_lot lot on invline.vin_no = lot.id
                left join
                    fleet_vehicle fv on fv.lot_id = invline.vin_no
                left join 
                    fleet_vehicle_model_brand brand_name ON brand_name.id = pt.brand_id
                left join 
                    res_company AS dealer ON dealer.id = invline.company_id
                left join 
                    res_partner AS rp ON rp.id = dealer.partner_id
                left join 
                     product_product as pp on pp.id = invline.product_id
                left join (SELECT * FROM crosstab(
                    'select inv.id as inv_id ,
                    CASE WHEN attr.name LIKE ''_xt%'' THEN ''Exterior Color'' ELSE ''Interior Color'' END AS attr,
                       attr_val.name AS attrs_val
                       from account_invoice inv
                       left join account_invoice_line lines on inv.id = lines.invoice_id
                       left join product_product pp on lines.product_id = pp.id    
                       left join product_template pt on pp.product_tmpl_id = pt.id
                       left join product_catalog cat on pt.catalog_type= cat.id
                       left join product_attribute_value_product_product_rel attr_rel on pp.id = attr_rel.product_product_id
                       left join product_attribute_value attr_val on attr_rel.product_attribute_value_id = attr_val.id
                       left join product_attribute attr on attr_val.attribute_id = attr.id
                          ORDER BY inv.id',
                     'SELECT DISTINCT CASE WHEN attr.name LIKE ''_xt%'' THEN ''Exterior Color'' ELSE ''Interior Color'' END AS attr 
                     FROM product_attribute_value attr_val
                     LEFT JOIN product_attribute attr ON attr_val.attribute_id = attr.id'
                    ) AS newtable (inv_id INT, Exterior_Color VARCHAR, Interior_Color VARCHAR)) as prod_attrs on prod_attrs.inv_id = inv.id
                where 
                    inv.id = invline.invoice_id
                    and inv.type='out_invoice'
                    and inv.ars_invoice_type = 'vehicle' 
                    and invline.vin_no IS NOT NULL 
                    and inv.state not in ('draft', 'cancel')
                 and pt.rsa = 'yes')
                """)

    def export_xls_rsa(self, param=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, )
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
        sheets.merge_range(0, 0, 2, 21, 'RSA Report ', format0)
        sheets.write(3, 0, 'Sl No.', format21)
        sheets.write(3, 1, 'ID Product', format21)
        sheets.write(3, 2, 'Client Name', format21)
        sheets.write(3, 3, 'Policy Number', format21)
        sheets.write(3, 4, 'Start Date', format21)
        sheets.write(3, 5, 'End Date', format21)
        sheets.write(3, 6, 'Customer Name', format21)
        sheets.write(3, 7, 'Model Type', format21)
        sheets.write(3, 8, 'Reg. No.', format21)
        sheets.write(3, 9, 'Selling Dealer Code', format21)
        sheets.write(3, 10, 'Dealer Name', format21)
        sheets.write(3, 11, 'Dealer Address', format21)
        sheets.write(3, 12, 'Dealer City', format21)
        sheets.write(3, 13, 'Dealer State', format21)
        sheets.write(3, 14, 'Dealer Pin', format21)
        sheets.write(3, 15, 'Dealer Mobile', format21)
        sheets.write(3, 16, 'Dealer Mail', format21)
        sheets.write(3, 17, 'VIN Number', format21)
        sheets.write(3, 18, 'Color', format21)
        sheets.write(3, 19, 'Fuel Type', format21)
        sheets.write(3, 20, 'Date of Sharing', format21)

        date = str(datetime.now().date())
        dateval = datetime.strptime(date, "%Y-%m-%d")

        datetimes = datetime.strftime(dateval, "%Y-%m-%d")
        records = self.env['vehicle.sale.rsa.report'].search([('product_template_id.rsa', '=', 'yes'),
                                                              ('start_date', '=', datetimes)])
        print(len(records))
        row = 4
        column = 0
        sl = 0
        for record in records:
            start_date = datetime.strptime(record.start_date, "%Y-%m-%d").strftime(
                '%d/%m/%Y') if record.start_date else ''
            end_date = datetime.strptime(record.end_date, "%Y-%m-%d").strftime('%d/%m/%Y') if record.end_date else ''
            sheets.write(row, column, sl + 1, format11)
            sheets.write(row, column + 1, record.product_template_id.name, format11)
            sheets.write(row, column + 2, record.brand_name, format11)
            sheets.write(row, column + 3, record.policy_number, format12)
            sheets.write(row, column + 4, start_date, format11)
            sheets.write(row, column + 5, end_date, format11)
            sheets.write(row, column + 6, record.customer_name.name, format12)
            sheets.write(row, column + 7, record.model_type.name, format11)
            sheets.write(row, column + 8, record.reg_no if record.reg_no else '', format11)
            sheets.write(row, column + 9, record.selling_dealer_code, format11)
            sheets.write(row, column + 10, record.dealer_name, format11)
            sheets.write(row, column + 11, str(record.dealer_address + record.dealer_address1), format11)
            sheets.write(row, column + 12, record.dealer_city, format11)
            sheets.write(row, column + 13, record.dealer_state.name, format11)
            sheets.write(row, column + 14, record.dealer_pin, format11)
            sheets.write(row, column + 15, record.dealer_mobile, format11)
            sheets.write(row, column + 16, record.dealer_email, format11)
            sheets.write(row, column + 17, record.vin_number, format11)
            sheets.write(row, column + 18, record.color_id, format12)
            sheets.write(row, column + 19, 'EV', format12)
            sheets.write(row, column + 20, str(datetime.now().strftime('%d/%m/%Y')), format12)

            sl = sl + 1
            row = row + 1
        workbook.close()
        output.seek(0)
        if records:
            data = output.read()
            output.close()
            data = base64.encodebytes(data)
            doc_id = self.env['ir.attachment'].create(
                {'datas': data, 'name': 'RSA Activation Request' + str(datetime.now().strftime('%d/%m/%Y')) + '.xls',
                 'datas_fname': 'RSA Activation Request' + str(datetime.now().strftime('%d/%m/%Y')) + '.xls',
                 })
            print((doc_id.id), "HELOOO")
            if param is not None:
                return doc_id
            else:
                print('RETu')
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                return {
                    'name': 'RSA REPORT',
                    'type': 'ir.actions.act_url',
                    'url': '/web/content/?id=%s&download=true' % doc_id.id,
                    'target': 'self',
                }
        else:
            False

    def send_rsa_mail(self):
        rsa_attachment, template = False, False
        records = self.env['automation.email.conf'].search([])
        for record in records:
            if record.psf_rsa_report:
                if record.report_template_id:
                    template = record.report_template_id
                    template.attachment_ids = [(5,)]
                    rsa_attachment = self.export_xls_rsa(param=True)
                    print(rsa_attachment, 'rsa_attachment')
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
