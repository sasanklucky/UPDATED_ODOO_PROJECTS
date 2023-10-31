import json
import requests
import datetime
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class EbillCancel(models.TransientModel):
    _name = 'einvoice.cancel'

    cancel_reason = fields.Selection(
        [('1', 'Duplicate'), ('2', 'Data Entry Mistake'), ('3', 'Order Cancelled'), ('4', 'Others')],
        string='Cancel Reason')
    desc = fields.Text('Description')

    def generate_einvoice(self):
        active_id = self.env.context.get('active_id')
        order = self.env['account.invoice'].browse(active_id)
        delivery = self.env['stock.picking'].search([('origin', '=', order.origin)], limit=1)
        if delivery:
            warehouse = delivery.picking_type_id.warehouse_id
            return warehouse
        if not delivery:
            so_delivery = self.env['sale.order'].search([('name', '=', order.origin)], limit=1)
            if so_delivery:
                so_warehouse = so_delivery.warehouse_id
                return so_warehouse
            else:
                warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', order.company_id.id), ('configure_einvoice', '=', True)], limit=1)
                return warehouse

    @api.multi
    def cancel_einvoicing(self):
        active_id = self.env.context.get('active_id')
        print('active_id', active_id)

        order = self.env['account.invoice'].browse(active_id)
        print('order', order)
        date1 = datetime.strptime(str(order.date_invoice), '%Y-%m-%d').strftime('%d/%m/%Y')
        einvoicing = self.env['einvoicing.configuration'].search([], limit=1)
        delivery = self.env['stock.picking'].search([('origin', '=', order.origin)], limit=1)
        warehouses = delivery.picking_type_id.warehouse_id
        # warehouse = self.env['stock.warehouse'].search([],limit=1)
        warehouse = self.generate_einvoice()
        data = einvoicing.handle_einvoicing_auth_token()
        print('data', data)

        # if not delivery:
        #     raise UserError(_('No picking Found !'))
        if not order.irn_no:
            raise UserError(_('Please Create E-Invoice First'))
        if not einvoicing:
            raise UserError(_('No Configurations details found in the system for E-Invoicing.'))
        if not warehouse.auth_token:
            raise UserError(_('Please Check Auth Token in warehouse configuration is Expired or Null.'))
        if not einvoicing.testing:
            raise UserError(_('Please Set Url Type in E-Invoicing Configuration.'))
        if not einvoicing.asp_id:
            raise UserError(_('Please Enter ASP-ID in E-Invoicing Configurations.'))
        if not einvoicing.asp_password:
            raise UserError(_('Please Enter ASP Password in E-Invoicing Configurations.'))
        if not warehouse.gst_no:
            raise UserError(_('Please Enter Registered GSTIN in warehouse Configurations.'))
        if not warehouse.user_password:
            raise UserError(_('Please Enter User Password in warehouse Configurations.'))
        if not warehouse.user_name:
            raise UserError(_('Please Enter User Name in Warehouse Configurations.'))
        data = {
            "Irn": order.irn_no,
            "CnlRsn": self.cancel_reason,
            "CnlRem": self.desc
        }
        try:
            if einvoicing.testing == 't':
                url = 'https://gstsandbox.charteredinfo.com/eicore/dec/v1.03/Invoice/Cancel?aspid=' + einvoicing.asp_id + '&password=' + einvoicing.asp_password + '&Gstin=' + warehouse.gst_no + '&eInvPwd=' + warehouse.user_password + '&AuthToken=' + warehouse.auth_token + '&user_name=' + warehouse.user_name
                url = str(url)
            if einvoicing.testing == 'p':
                url = 'https://api.taxprogsp.co.in/eicore/dec/v1.03/Invoice/Cancel?aspid=' + einvoicing.asp_id + '&password=' + einvoicing.asp_password + '&Gstin=' + warehouse.gst_no + '&eInvPwd=' + warehouse.user_password + '&AuthToken=' + warehouse.auth_token + '&user_name=' + warehouse.user_name
                url = str(url)
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            response = requests.post(url, data=json.dumps(data), headers=headers)
            res = response.content
            print(res)
            order.write({'exception_reason': res})
            res_dict = json.loads(res.decode('utf-8'))
            if res_dict.get('Status') == '1':
                a = res_dict['Data']
                n = json.loads(a)
                dt = n['CancelDate']
                order.write({'irn_cancel_date': dt})
                order.write({'way_bill_status': 'cancel'})
                self.env.user.notify_info(message='IRN Number Cancel Successfully !')
            if res_dict.get('Status') == '0':
                order.write({'exception_reason': res_dict})
                order.write({'e_invoice_status': 'exception'})
                raise UserError(_(res_dict.get('ErrorDetails')))
        except Exception as e:
            print(e)
            order.write({'exception_reason': e})
            order.write({'e_invoice_status': 'exception'})
