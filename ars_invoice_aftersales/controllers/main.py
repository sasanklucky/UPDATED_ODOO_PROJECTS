from odoo import http
from odoo.http import request


class Split(http.Controller):
    @http.route(['/ars_invoice_aftersales/split/get_fields'], type='json', auth="user", website=True, csrf=False)
    def split_invoice(self, **kwargs):
        partners = ''
        selected_id = 0
        selected_ids = []
        price_subtotal = 0
        line_datas_id = False
        customer_name = ''
        partners = '<select  class="form-control select_class">'
        if kwargs.get('res_ids') and kwargs.get('model') == 'sale.order.line':
            if kwargs.get('selected_ids'):
                line_datas = request.env['sale.order.line'].browse(kwargs.get('selected_ids'))
                line_datas_id = line_datas.ids
                for line_data in line_datas:
                    customer_name = line_data.order_id.partner_id.name
                    price_subtotal += line_data.price_subtotal
            partner_obj = request.env['res.partner'].search([('customer','=',True)])
            for partner in partner_obj:
                if customer_name == partner.name:
                    partners += '<option selected value='+str(partner.id)+'>' + partner.name + '</option>'
                elif partner:
                    partners += '<option value='+str(partner.id)+'>' + partner.name if partner.name else 'Unknown' + '</option>'
            partners += '</select>'

        return [{'customers': partners, 'customer_name': customer_name,'price_subtotal':price_subtotal,'line_ids':line_datas_id,'order_id':line_datas[0].order_id.id}]

    @http.route(['/ars_invoice_aftersales/split/get_data'], type='json', auth="user", website=True, csrf=False)
    def split_invoice_data(self, **kwargs):
        partners = ''
        order_id = ''
        inv_obj = request.env['account.invoice']
        if kwargs.get('res_ids') and kwargs.get('customers') and kwargs.get('amt'):
            res_ids = kwargs.get('res_ids')
            res_id = res_ids.split(',')
            customers = kwargs.get('customers')
            amt = kwargs.get('amt')
            percent = kwargs.get('per')
            ir_property_obj = request.env['ir.property']
            if kwargs.get('order'):
                order_id = request.env['sale.order'].browse(int(kwargs.get('order')))
            # account_id = order_id.partner_id.property_account_receivable.id
            for index, customer in enumerate(customers):
                if order_id:
                    invoice = inv_obj.search([('origin', '=', order_id.name), ('partner_id', '=', int(customer))])
                lines = []
                line_data = {}
                if percent[index]:
                    percent_value = percent[index].split('%')
                for re_id in res_id:
                    res = request.env['sale.order.line'].browse(int(re_id))
                    line_data = {'product_id': res.product_id.id,
                                 'name': res.name,
                                 'quantity': res.product_uom_qty,
                                 'price_unit': res.price_unit,
                                 'sale_line_ids': [(6, 0, [res.id])],
                                 'account_analytic_id': order_id.analytic_account_id.id or False,
                                 'account_id': 1,
                                 'invoice_line_tax_ids': [[6, 0, res.tax_id.ids]],
                                 'price_subtotal': ((int(percent_value[0]) * res.price_subtotal) / 100) if res.price_subtotal > 0 else 0,
                                 'split_amount': ((int(percent_value[0]) * res.price_subtotal) / 100) if res.price_subtotal > 0 else 0,
                                 'split_type': 'split'
                                 }
                    invoice_line = [0, 0, line_data]
                    lines.append(invoice_line)
                vals = {
                    'partner_id':int(customer),
                    'account_id': 1,
                    'invoice_line_ids':lines,
                    'origin':order_id.name
                }
                request.env['account.invoice'].create(vals)
        # action = {'type': 'ir.actions.act_window_close'}

        return {'status':True}
