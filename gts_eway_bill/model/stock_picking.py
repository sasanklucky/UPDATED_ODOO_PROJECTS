import json
import logging
from datetime import datetime
import requests
import base64
import re

from odoo import fields, models, api, _, tools
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)
import math

def geo_query_address(street=None, zip=None, city=None, state=None, country=None):
    if country and ',' in country and (country.endswith(' of') or country.endswith(' of the')):
        # put country qualifier in front, otherwise GMap gives wrong results,
        # e.g. 'Congo, Democratic Republic of the' => 'Democratic Republic of the Congo'
        country = '{1} {0}'.format(*country.split(',', 1))
    return tools.ustr(', '.join(filter(None, [street, ("%s %s" % (zip or '', city or '')).strip(), state, country])))


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    generate_ewaybill = fields.Boolean("E-Way Bill Applicable?", help='Generate E-way Bill?')
    invoices = fields.Many2many('account.invoice','picking_inv_rel','picking_id','invoice_id', string='Invoices')
    supply_type = fields.Selection([('I', 'Inward'),
                                    ('O', 'Outward')], string="Supply Type", tracking=2)
    vehicle_type = fields.Selection([('R', 'Regular'),
                                     ('O', 'ODC')], string="Vehicle Type", tracking=2)
    sub_supply_type = fields.Selection([('1', 'Supply'),
                                        ('2', 'Import'),
                                        ('3', 'Export'),
                                        ('4', 'Job Work'),
                                        ('5', 'For Own Use'),
                                        ('6', 'Job Work Return'),
                                        ('7', 'Sale Return'),
                                        ('8', 'Other'),
                                        ('9', 'SKD/CDK'),
                                        ('10', 'Line Sales'),
                                        ('11', 'Recipient Not Known'),
                                        ('12', 'Exhibiation or Fairs'),
                                        ], string="Sub-supply Type", copy=False, tracking=2)
    transportation_mode = fields.Selection([('1', 'Road'),
                                            ('2', 'Rail'),
                                            ('3', 'Air'),
                                            ('4', 'Ship'),
                                            ], string="Transportation Mode", copy=False, tracking=2)
    transporter_id = fields.Many2one('res.partner', string="Transporter", tracking=2)
    transportation_distance = fields.Integer("Distance (Km)", tracking=2,
                                             help='If entered, we will use this distance')
    trans_id = fields.Char("Transporter ID", tracking=2)
    ewaybill_no = fields.Char("E-Way Bill No.", copy=False, tracking=2)
    vehicle_no = fields.Char("Vehicle No.", tracking=2)
    document_type = fields.Selection([('INV', 'Tax Invoice'),
                                      ('BIL', 'Bill of Supply'),
                                      ('BOE', 'Bill of Entry'),
                                      ('CHL', 'Delivery Challan'),
                                      ('OTH', 'Others')], string="Document Type", copy=False,
                                     tracking=2)
    doc_date = fields.Date("Document Date", tracking=2)
    transporter_doc_no = fields.Char("Transporter Document No.", size=16, tracking=2)
    transportation_doc_date = fields.Date('Transport Document Date', tracking=2)
    consolidate_id = fields.Many2one('consolidate.bill', string="Consolidate Bill", tracking=2)
    sub_type_desc = fields.Text('Sub Type Description', tracking=2)
    bill_status = fields.Selection([('not', 'Not Generated'), ('generate', 'Generated'),
                                    ('cancel', 'Cancel')], string="E-Way Bill Status", default='not',
                                   tracking=2)
    logs_details = fields.Char("Log Details", copy=False, tracking=2)
    consolidate_eway = fields.Char("Consolidate E-Way Bill No.", copy=False, tracking=2)
    cancel_date = fields.Char("E-Way Bill Cancellation Date", copy=False, tracking=2)
    eway_bill_date = fields.Char("E-Way Bill Date", copy=False, tracking=2)
    valid_ebill_date = fields.Char("E-Way Bill ValidUp", copy=False, tracking=2)
    conslidate_ebill_date = fields.Char("Consolidate E-Way Bill Date", copy=False, tracking=2)
    ewaybill_response = fields.Text('E-Way Bill Bill Response')
    ewaybill_print_response = fields.Text('E-Way Bill Print Response')
    from_name = fields.Char('Name')
    street = fields.Char('Street', tracking=2)
    street2 = fields.Char('Street2', tracking=2)
    zip = fields.Char('Pincode', change_default=True, tracking=2)
    city = fields.Char('City/Place', tracking=2)
    state_id = fields.Many2one("res.country.state", string='State', domain="[('country_id.code', '=', 'IN')]",
                               tracking=2)
    vat = fields.Char(string='GSTIN', help="GSTIN Number", tracking=2)
    transaction_type = fields.Selection([('1', 'Regular'),
                                         ('2', 'Bill To - Ship To'),
                                         ('3', 'Bill From - Dispatch From'),
                                         ('4', 'Combination of 2 and 3')], string="Transaction Type", copy=False,
                                        tracking=2, default='1')

    to_name = fields.Char('Name')
    to_street = fields.Char('Street', tracking=2)
    to_street2 = fields.Char('Street2', tracking=2)
    to_zip = fields.Char('Pincode', change_default=True, tracking=2)
    to_city = fields.Char('City/Place', tracking=2)
    to_state_id = fields.Many2one("res.country.state", string='State', domain="[('country_id.code', '=', 'IN')]",
                               tracking=2)
    to_vat = fields.Char(string='GSTIN', help="GSTIN Number", tracking=2)
    sub_supply_type_id = fields.Many2one('sub.supply.type', string='Sub Supply Type')
    sub_supply_type_domain = fields.Char(compute="_compute_sub_supply_type_id_domain", readonly=True, store=False)
    sub_supply_type_code = fields.Char('Sub Supply Type Code', related='sub_supply_type_id.code', readonly=True)
    generate_eway_part_b = fields.Boolean('Generate Part - B', default=False, copy=False)






    # @api.onchange('invoices')
    # def validation_invoice_no(self):
    #     invoice_no_ids = self.env['stock.picking'].search(
    #         [('generate_ewaybill', '=', True), ('ewaybill_no', '!=', False)])
    #     for record in invoice_no_ids:
    #         if self.invoices.ids in [record.invoices.id]:
    #             raise UserError(_('EwayBill already generated for this Invoice_no please select Another'))

        # if self.invoice_no.name:
        #     print("=-=-=->>>>>>>>>>>>>>invoice_no")

    @api.constrains('doc_date')
    def validate_document_date(self):
        if self.doc_date:
            if self.doc_date and datetime.strptime(str(self.doc_date), "%Y-%m-%d").date() > datetime.now().date():
                raise UserError(_('Document Date can not be greater then today!'))
            return True

    @api.constrains('transportation_doc_date')
    def validate_transportation_doc_date(self):
        if self.doc_date and self.transportation_doc_date:
            if not (self.transportation_doc_date >= self.doc_date):
                raise UserError(_('Transport Document Date should be greater than or equal to Document Date!'))
            return True


    def set_status_to_draft(self):
        self.action_cancel()
        self.state = 'draft'

    @api.depends('supply_type')
    def _compute_sub_supply_type_id_domain(self):
        for rec in self:
            domain = []
            if rec.supply_type:
                if rec.supply_type == 'O':
                    domain.append(('code', 'in', ('1', '3', '4', '9', '11', '5', '12', '10', '8')))
                elif rec.supply_type == 'I':
                    domain.append(('code', 'in', ('1', '2', '9', '4', '7', '12', '5', '8')))
            rec.sub_supply_type_domain = json.dumps(domain)

    @api.onchange('supply_type', 'sub_supply_type_id','partner_id','picking_type_id')
    def onchange_generate_ewaybill(self):
        address = self.picking_type_id.warehouse_id.partner_id #warehouse
        contact_address = self.partner_id #contact
        sub_supply = self.sub_supply_type_id.name
        print("000000000000000000000000",address, contact_address, self.supply_type)
        if self.partner_id:
            self.to_name = self.partner_id.name
            self.to_vat = self.partner_id.vat
        if self.picking_type_id:
            self.from_name = self.picking_type_id.warehouse_id.name
            self.vat = self.picking_type_id.warehouse_id.partner_id.vat

        if address and contact_address and self.supply_type == 'O':
            self.from_name = self.picking_type_id.warehouse_id.registered_name
            self.street = address.street
            self.street2 = address.street2
            self.city = address.city
            self.state_id = address.state_id.id
            self.zip = address.zip
            self.vat = address.vat

            self.to_name = contact_address.name
            self.to_street = contact_address.street
            self.to_street2 = contact_address.street2
            self.to_city = contact_address.city
            self.to_state_id = contact_address.state_id.id
            self.to_zip = contact_address.zip
            self.to_vat = contact_address.vat

        if address and contact_address and self.supply_type == 'I':
            self.from_name = contact_address.name
            self.street = contact_address.street
            self.street2 = contact_address.street2
            self.city = contact_address.city
            self.state_id = contact_address.state_id.id
            self.zip = contact_address.zip
            self.vat = contact_address.vat

            self.to_name = self.picking_type_id.warehouse_id.registered_name
            self.to_street = address.street
            self.to_street2 = address.street2
            self.to_city = address.city
            self.to_state_id = address.state_id.id
            self.to_zip = address.zip
            self.to_vat = address.vat

        if address and contact_address and self.supply_type == 'O' and sub_supply == 'Export':
            self.from_name = ''
            self.street = address.street
            self.street2 = address.street2
            self.city = address.city
            self.state_id = address.state_id.id
            self.zip = address.zip
            self.vat = address.vat

            self.to_name = ''
            self.to_street = ''
            self.to_street2 = ''
            self.to_city = ''
            self.to_state_id = ''
            self.to_zip = ''
            self.to_vat = 'URP'

        if address and contact_address and self.supply_type == 'I' and sub_supply == 'Import':
            self.from_name = ''
            self.street = ''
            self.street2 = ''
            self.city = ''
            self.state_id = ''
            self.zip = ''
            self.vat = 'URP'

            self.to_name = ''
            self.to_street = address.street
            self.to_street2 = address.street2
            self.to_city = address.city
            self.to_state_id = address.state_id.id
            self.to_zip = address.zip
            self.to_vat = address.vat

    @api.onchange('transporter_id')
    def _onchange_transporter_id(self):
        if self.transporter_id:
            self.trans_id = self.transporter_id.vat

    def format_date(self, doc_date):
        if doc_date:
            return datetime.strptime(str(doc_date), DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
        else:
            return ''

    def get_configuration(self):
        configuration = self.env['eway.configuration'].search([], limit=1)
        if not configuration:
            raise UserError(_('Eway bill Configuration not found !'))
        return configuration

    def get_eway_bill_details(self):
        configuration = self.get_configuration()
        details_response = configuration.get_eway_details('GetEwayBill', self.ewaybill_no, self.picking_type_id.warehouse_id)
        # print('details_response.json()....------',configuration, details_response.json())
        return details_response.json()

    def print_eway_bill(self):
        Attachment = self.env['ir.attachment']
        configuration = self.get_configuration()
        details_response = self.get_eway_bill_details()
        det_response = details_response
        # Temporary to be able to use Print API
        # det_response['userGstin'] = '09AAFCT8324E1Z9'
        # det_response['fromGstin'] = '09AAFCT8324E1Z9'
        print_response = configuration.print_eway('printewb', det_response)
        attachment_data = {
            'name': 'EwayBill: ' + str(self.origin or '') + ':' + str(self.name),
            'datas': base64.b64encode(print_response),
            'type': 'binary',
            'res_model': 'stock.picking',
            'public':True,
            'res_id': self.id,
        }
        attachment = Attachment.create(attachment_data)
        self.env.user.notify_info(message='E-Way Bill Printed Successfully! Please check '
                                             'the attachments to download the copy.')
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        # return True
        return {
            'type': 'ir.actions.act_url',
            'url': f'{str(base_url)}/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def print_eway_bill_details(self):
        Attachment = self.env['ir.attachment']
        configuration = self.get_configuration()
        details_response = self.get_eway_bill_details()
        det_response = details_response
        # Temporary to be able to use Print API
        # det_response['userGstin'] = '09AAFCT8324E1Z9'
        # det_response['fromGstin'] = '09AAFCT8324E1Z9'
        print_response = configuration.print_eway('printdetailewb', det_response)
        attachment_data = {
            'name': 'Detailed EwayBill: ' + str(self.origin or '') + ':' + str(self.name),
            'datas': base64.b64encode(print_response),
            'type': 'binary',
            'res_model': 'stock.picking',
            'res_id': self.id,
        }
        attachment = Attachment.create(attachment_data)
        print('attachment...', attachment)
        self.env.user.notify_info(message='Detailed EwayBill Printed Successfully! Please check '
                                             'the attachments at the bottom.')
        return True

    def generate_eway(self):
        tax_obj = self.env['account.tax']
        configuration = self.get_configuration()
        # print('-configuration--------->>>>>>>>>>>>>>>>>',configuration,tax_obj)
        if self.ewaybill_no and self.bill_status == 'generate':
            raise UserError(_('You are not allow to Re-generate the Eway bill Again, Please cancel first !'))
        if not self.origin:
            raise UserError(_('Please fill Source Document!'))
        if not self.picking_type_id.warehouse_id:
            raise UserError(_('Warehouse is not set on Picking Operation %s !') % self.picking_type_id.name)
        if not self.picking_type_id.warehouse_id.partner_id:
            raise UserError(_('Address is not set on Warehouse %s !') % self.picking_type_id.warehouse_id.name)
        # if not self.partner_id:
        #     raise UserError(_('Delivery Address is not set %s !') % self.name)
        # if not self.partner_id.street:
        #     raise UserError(_('Street is not set on Delivery Address %s !') % self.partner_id.name)
        # if not self.partner_id.street2:
        #     raise UserError(_('Street2 is not set on Delivery Address %s !') % self.partner_id.name)
        # if not self.partner_id.city:
        #     raise UserError(_('City is not set on Delivery Address %s !') % self.partner_id.name)
        # if not self.partner_id.state_id:
        #     raise UserError(_('State is not set on Delivery Address %s !') % self.partner_id.name)
        # if not self.partner_id.zip:
        #     raise UserError(_('Pincode is not set on Delivery Address %s !') % self.partner_id.name)
        # if not self.partner_id.vat:
        #     raise UserError(_('GSTIN is not set on Delivery Address %s !') % self.partner_id.name)
        port_other_country = self.env['res.country.state'].search([
            ('name', 'ilike', 'OTHER COUNTRIES')], limit=1)
        # print("port_other_country----------------",port_other_country)
        if not self.picking_type_id.warehouse_id.gstin_live:
            raise UserError(_('GSTIN Live is not set on Warehouse %s !') % self.picking_type_id.warehouse_id.name)
        if not self.picking_type_id.warehouse_id.user_name_live:
            raise UserError(_('User Name is not set on Warehouse %s !') % self.picking_type_id.warehouse_id.name)
        if not self.picking_type_id.warehouse_id.ewb_password_live:
            raise UserError(_('Eway Bill Password Name is not set on Warehouse %s !') % self.picking_type_id.warehouse_id.name)
        if not self.picking_type_id.warehouse_id.registered_name:
            raise UserError(_('Registered Name is not set on Warehouse %s !') % self.picking_type_id.warehouse_id.name)
        if self.sub_supply_type_id.name == 'Supply' and self.document_type != 'INV':
            raise UserError(_('Please Select Document Type as  Tax Invoice'))
        if self.sub_supply_type_id.name == 'Job Work' and self.document_type != 'CHL':
            raise UserError(_('Please Select Document Type as Delivery Challan'))
        if not self.invoices:
            raise UserError(_('Please Please enter invoice number'))
        warehouse_details = self.picking_type_id.warehouse_id
        # print("warehouse_details----",warehouse_details)
        amount_untaxed = 0 
        print(self.invoices, 'ppppppppppppp',self.invoices)
        my_data = {
            'supplyType': self.supply_type,
            'subSupplyType': self.sub_supply_type_id.code,
            'subSupplyDesc': self.sub_type_desc or '',
            'docType': self.document_type,
            'docNo': self.name,
            'docDate': self.format_date(self.doc_date),
            'fromGstin': warehouse_details.gstin_live,
            'fromTrdName': self.from_name,
            'fromAddr1': self.street,
            'fromAddr2': self.street2,
            'fromPlace': self.city,
            'fromPincode': int(str(self.zip).replace(' ', '')) if self.zip else '',
            'actFromStateCode': int(self.state_id.l10n_in_tin) if self.state_id.l10n_in_tin else '' ,
            'fromStateCode': int(self.state_id.l10n_in_tin) if self.state_id.l10n_in_tin else '',
            'toGstin': self.to_vat,
            'toTrdName': self.to_name,
            'toAddr1': self.to_street or '',
            'toAddr2': self.to_street2 or '',
            'toPlace': self.to_city or '',
            'toPincode': int(str(self.to_zip).replace(' ', '')) if self.to_zip else '',
            'actToStateCode': int(self.to_state_id.l10n_in_tin) if self.to_state_id.l10n_in_tin else '',
            'toStateCode': int(self.to_state_id.l10n_in_tin) if self.to_state_id.l10n_in_tin else '',
            'transactionType': int(self.transaction_type),
            'transporterId': self.trans_id or '',
            'transporterName': self.transporter_id.name or '',
            'transDocNo': self.transporter_doc_no or '',
            'transMode': self.transportation_mode or '',
            'transDistance': str(int(self.transportation_distance)) or '0',
            'transDocDate': self.format_date(self.transportation_doc_date) or '',
            'vehicleNo': self.vehicle_no or '',
            'vehicleType': self.vehicle_type or ''
        }

        order_dic = {
            'supplyType': self.supply_type,
            'subSupplyType': self.sub_supply_type_id.code,
            'subSupplyDesc': self.sub_type_desc or '',
            'docType': self.document_type,
            # 'docNo': self.origin,invoice_no
            'docDate': self.format_date(self.doc_date),
            'transactionType': int(self.transaction_type),
            # 'fromGstin': configuration.gstin_live,
            'fromGstin': warehouse_details.gstin_live,
            # 'fromGstin': '05AAACG1539P1ZH',
            'fromTrdName': self.from_name,
            'fromAddr1': self.street,
            'fromAddr2': self.street2,
            'fromPlace': self.city,
            'fromPincode': int(str(self.zip).replace(' ', '')) if self.zip else '',
            'actFromStateCode': self.state_id.l10n_in_tin,
            'fromStateCode': self.state_id.l10n_in_tin,
            # 'dispatchFromGSTIN': '06AACCD5777E1ZN',
            'dispatchFromGSTIN': self.vat,
            'dispatchFromTradeName': self.picking_type_id.warehouse_id.partner_id.name,
            'toGstin': self.to_vat,
            # 'toGstin': '02EHFPS5910D2Z0',
            'toTrdName': self.to_name,
            'toAddr1': self.to_street or '',
            'toAddr2': self.to_street2 or '',
            'toPlace': self.to_city or '',
            'toPincode': int(str(self.to_zip).replace(' ', '')) if self.to_zip else '',
            'actToStateCode': self.to_state_id.l10n_in_tin,
            'toStateCode': self.to_state_id.l10n_in_tin,
            # 'shipToGSTIN': '02EHFPS5910D2Z0',
            'shipToGSTIN': self.partner_id.vat or '',
            'shipToTradeName': self.partner_id.name,
            'transporterId': self.trans_id or '',
            'transporterName': self.transporter_id.name or '',
        }
        # print("order_dic----",order_dic)
        inv_no = ''
        for move in self.invoices:
            if inv_no == '':
                inv_no += move.display_name
            else:
                inv_no += ","+move.display_name
        order_dic.update({
            'docNo': inv_no,
        })

        if self.generate_eway_part_b:
            order_dic.update({
                'transDocNo': self.transporter_doc_no or '',
                'transMode': self.transportation_mode,
                'transDocDate': self.format_date(self.transportation_doc_date) or '',
                'vehicleNo': self.vehicle_no or '',
                'vehicleType': self.vehicle_type,
            })
            # print("order_dic-----generate_eway_part_b-------",order_dic)
        company_currency_id = self.company_id.currency_id
        line_data = []
        total_cgst = total_igst = total_sgst = total_cess = total_cess_non_advol = 0.0
        if self.move_lines:
            for line in self.move_lines:
                if not line.product_uom.uom_mapping_id:
                    raise UserError(_('Eway Code is not set on UOM "%s" ') % (line.product_uom.name))
                if not line.product_price > 0:
                    raise UserError(_('Unit Price is 0 for product "%s" ') % (line.product_id.name))
                if not line.product_id.l10n_in_hsn_code:
                    raise UserError(_('HSN CODE is blank for product "%s" ') % (line.product_id.name))
                if not line.quantity_done > 0:
                    raise UserError(_('Done Qty should be greater than zero for product %s ') % (line.product_id.name))
                line_dic = {
                    'productName': line.product_id.name,
                    'productDesc': line.name,
                    'hsnCode': int(line.product_id.l10n_in_hsn_code)if line.product_id.l10n_in_hsn_code else '',
                    'quantity': int(line.quantity_done),
                    'qtyUnit': line.product_uom.uom_mapping_id.code,
                }
                cgst_rate = sgst_rate = igst_rate = cess_rate = cess_non_advol = 0.0
                if self.document_type in ('INV', 'BIL', 'BOE'):
                    product_price = line.product_price
                    print("product_price",product_price)
                    balance_taxes_res = line.tax_id.compute_all(
                        product_price,
                        currency=company_currency_id,
                        quantity=line.product_uom_qty,
                        product=line.product_id,
                        partner=self.partner_id,
                        # is_refund=False,
                        # handle_price_include=True,
                    )
                    print("balance_taxes_res",balance_taxes_res)
                    # print('balance_taxes_res..', balance_taxes_res)
                    for tax_dict in balance_taxes_res.get('taxes', []):
                        # print('tax_dict...', tax_dict)
                        tax = tax_obj.browse(tax_dict.get('id'))
                        if 'IGST' in tax_dict.get('name') or tax.name.startswith('IGST'):
                            igst_rate = tax.amount
                            print("igst====",tax_dict.get('amount'))
                            total_igst += tax_dict.get('amount', 0.0)
                        elif 'CGST' in tax_dict.get('name') or tax.name.startswith('CGST'):
                            cgst_rate = tax.amount
                            total_cgst += tax_dict.get('amount', 0.0)
                        elif 'SGST' in tax_dict.get('name') or tax.name.startswith('SGST'):
                            sgst_rate = tax.amount
                            total_sgst += tax_dict.get('amount', 0.0)
                        elif 'CESS' in tax_dict.get('name') or tax.name.startswith('CESS'):
                            cess_rate = tax.amount
                            total_cess += tax_dict.get('amount', 0.0)
                    cess_non_advol = line.cess_non_advol
                    total_cess_non_advol += int(cess_non_advol) if cess_non_advol else 0
                line_dic.update({
                    'cgstRate': cgst_rate,
                    'sgstRate': sgst_rate,
                    'igstRate': igst_rate,
                    'cessRate': cess_rate,
                    'cessNonAdvol': int(cess_non_advol) if cess_non_advol else 0,
                    'taxableAmount': line.product_price * line.quantity_done,
                })
                amount_untaxed += line.product_price * line.quantity_done
                line_data.append(line_dic)
        # print("line_data-------------------------------",line_data)

        my_data.update({
            'itemList': line_data,
            'cgstValue': total_cgst,
            'sgstValue': total_sgst,
            'igstValue': total_igst,
            'totalValue': amount_untaxed,
            'otherValue': 0,
            'cessValue': total_cess,
            'cessNonAdvolValue': total_cess_non_advol,
            'totInvValue': amount_untaxed + total_cgst + total_sgst + total_igst + total_cess +
                           total_cess_non_advol,
        })

        order_dic.update({
            'itemList': line_data,
            'cgstValue': total_cgst,
            'sgstValue': total_sgst,
            'igstValue': total_igst,
            'totalValue': amount_untaxed,
            'otherValue': 0,
            'cessValue': total_cess,
            'cessNonAdvolValue': total_cess_non_advol,
            'totInvValue': amount_untaxed + total_cgst + total_sgst + total_igst + total_cess +
                           total_cess_non_advol,
        })

        # Distance Calculation
        if self.transportation_distance > 0:
            my_data.update({'transDistance': str(int(self.transportation_distance))})
        else:
            if configuration.distance_key and self.company_id.partner_id.zip and self.partner_id.zip:
                url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins="\
                      + self.company_id.partner_id.zip + "&destinations=" + self.partner_id.zip + \
                      "&key=" + configuration.distance_key
                try:
                    response = requests.get(url, timeout=20.000).json()
                    print('response....', response)
                    if (response['status'] == 'OK'):
                        result = response.get('rows')
                        print('result...', result)
                        if result:
                            elements_list = response.get('rows')[0].get('elements')
                            if elements_list:
                                pre_final_list = elements_list[0]
                                if (pre_final_list.get('status') == 'OK'):
                                    final_list = (pre_final_list.get('distance')).get('value')
                                    if final_list > 1:
                                        distance_km = round(final_list * 0.001)
                                        # print('distance_km...', distance_km)
                                        my_data.update({'transDistance': str(int(distance_km))})
                                        self.transportation_distance = distance_km
                        else:
                            raise Warning(_('Invalid JSon for the Distance:\n%s') % result)
                    else:
                        raise Warning(_('Distance Error :%s could not be generated') % response)
                except Exception as e:
                    _logger.info("Exception in fetching Distance: %s", e.args)
            else:
                raise UserError(_('Invalid configuration for the Distance API'))
        # for Outward
        if self.supply_type == 'O':
            if self.document_type == 'BIL':
                if self.sub_supply_type_id.code == '9':
                    my_data.update({
                        'actToStateCode': port_other_country.code,
                        'toStateCode': port_other_country.code
                    })
            if self.sub_supply_type_id.code == '3':
                my_data.update({
                    'actToStateCode': port_other_country.code,
                    'toStateCode': port_other_country.code
                })

        print("my data ooooooo",my_data)
        print("inayat json dic",order_dic)
        data_base64 = json.dumps(my_data)
        print("")
        print("-=-=-=-=-=-",data_base64)
        # print('data_base64...-------------', data_base64)
        response = configuration.generate_eway(self.picking_type_id.warehouse_id,data_base64,'GENEWAYBILL')
        response_json = response.json()
        print("response_json",response_json)
        # print('Generate response...', response_json)
        if response_json.get('status_code', '') == 200 or 'ewayBillNo' in response_json:
            print("response_json.get('ewayBillNo')",response_json.get('ewayBillNo'))
            print("response_json.get('ewayBillDate')",response_json.get('ewayBillDate'))
            print("response_json.get('validUpto')",response_json.get('validUpto'))
            self.ewaybill_no = response_json.get('ewayBillNo')
            self.eway_bill_date = response_json.get('ewayBillDate')
            self.valid_ebill_date = response_json.get('validUpto')
            self.bill_status = 'generate'
            self.logs_details = ""
            self.cancel_date = ''
            self.message_post(body=_("Eway Bill is generated : '" + str(self.ewaybill_no) +
                "', Eway Bill Date: '" + str(self.eway_bill_date) + "', Valid Upto: '"
                + str(self.valid_ebill_date)))
            if response_json.get('alert'):
                self.message_post(body=_("Eway Bill Alert : '" + str(response_json.get('alert'))))
            self.env.user.notify_info(message='EwayBill Generated Successfully!')
            # Print and attach
            self.print_eway_bill()
        elif response_json.get('error').get('error_cd') == 'GSP102' or response_json.get('error').get('message') == 'eInvoice AuthToken not found or expired. Please call Authenticate API on IRP: 1':
            if configuration.active_production:
                configuration.access_token_live = False
                configuration.access_date_live = False
            else:
                configuration.access_token_staging = False
                configuration.access_date_staging = False
            configuration.handle_auth_token()
        else:
            self.env['response.json'].create({
                'name':self.name,
                'json':data_base64,
                'response':response_json
            })
            self.logs_details = response_json.get('error', {}).get('message', '')
            self.env.user.notify_info(message=response_json.get('error', {}).get('message'))
        return True

    @api.onchange("picking_type_id")
    def _compute_auto_address(self):
        if self.picking_type_id:

            if self.picking_type_id.warehouse_id.partner_id.street:
                self.street = self.picking_type_id.warehouse_id.partner_id.street

            if self.picking_type_id.warehouse_id.partner_id.street2:
                self.street2 = self.picking_type_id.warehouse_id.partner_id.street2

            if self.picking_type_id.warehouse_id.partner_id.city:
                self.city = self.picking_type_id.warehouse_id.partner_id.city

            if self.picking_type_id.warehouse_id.partner_id.state_id:
                self.state_id = self.picking_type_id.warehouse_id.partner_id.state_id

            if self.picking_type_id.warehouse_id.partner_id.zip:
                self.zip = self.picking_type_id.warehouse_id.partner_id.zip

    @api.onchange('partner_id')
    def ship_address(self):
        print('working')

        if self.partner_id:
            print('partner_id.shipping_id', self.partner_id)

            if self.partner_id.street:
                self.to_street = self.partner_id.street

            if self.partner_id.street2:
                self.to_street2 = self.partner_id.street2

            if self.partner_id.city:
                self.to_city = self.partner_id.city

            if self.partner_id.state_id:
                self.to_state_id = self.partner_id.state_id

            if self.partner_id.zip:
                self.to_zip = self.partner_id.zip


class ResponseJson(models.Model):
    _name = "response.json"

    name = fields.Char("Request")
    json = fields.Text("Json")
    response = fields.Text("Response")

