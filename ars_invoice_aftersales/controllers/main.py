from odoo import http
from odoo.http import request


class Split(http.Controller):
    @http.route(['/ars_invoice_aftersales/split/get_fields'], type='json', auth="user", website=True, csrf=False)
    def split_invoice(self, **kwargs):
        partners = ''
        selected_id = 0
        selected_ids = []
        price_subtotal = 0
        tax_id = 0
        order_amount_total = 0
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
                    tax_id = line_data.tax_id.name
                    order_amount_total = line_data.order_amount_total
            partner_obj = request.env['res.partner'].search([('customer','=',True)])
            for partner in partner_obj:
                if customer_name == partner.name:
                    partners += '<option selected value='+str(partner.id)+'>' + partner.name + '</option>'
                elif partner:
                    partners += '<option value='+str(partner.id)+'>' + partner.name if partner.name else 'Unknown' + '</option>'
            partners += '</select>'

        return [{'customers': partners, 'customer_name': customer_name,'price_subtotal':price_subtotal,'line_ids':line_datas_id,'tax_id':tax_id,'order_amount_total':order_amount_total,'order_id':line_datas[0].order_id.id}]

    @http.route(['/ars_invoice_aftersales/split/get_data'], type='json', auth="user", website=True, csrf=False)
    def split_invoice_data(self, **kwargs):
        partners = ''
        order_id = ''
        inv_obj = request.env['account.invoice']
        invoice_ids = []
        if kwargs.get('res_ids') and kwargs.get('customers') and kwargs.get('amt') and kwargs.get('tax') and kwargs.get('taxamount'):
            res_ids = kwargs.get('res_ids')
            res_id = res_ids.split(',')
            customers = kwargs.get('customers')
            amt = kwargs.get('amt')
            percent = kwargs.get('per')
            tax = kwargs.get('tax')
            taxamount = kwargs.get('taxamount')
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
                    #Chnages by Krishna
                    ir_property_obj = request.env['ir.property']
                    account_idd = False
                    if res.product_id.id:
                        account_idd = order_id.fiscal_position_id.map_account(
                            res.product_id.property_account_income_id or res.product_id.categ_id.property_account_income_categ_id).id
                    if not account_idd:
                        inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                        account_idd = order_id.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
                    #this above part added we using 'account_idd' in line_data
                    line_data = {'product_catalog_id': res.product_catalog_id.id,
                                 'product_template_id': res.product_template_id.id,
                                 'product_id': res.product_id.id,
                                 'name': res.name,
                                 # 'picking_type_id': res.picking_type_id.id,
                                 'quantity': res.product_uom_qty,
                                 'price_unit': res.price_unit,
                                 'uom_id': res.product_uom.id,
                                 # 'product_uom': product_id.uom_id.id,
                                 'discount': float(100 - float(percent_value[0])),
                                 'sale_line_ids': [(6, 0, [res.id])],
                                 'account_analytic_id': order_id.analytic_account_id.id or False,
                                 'account_id': account_idd,
                                 'invoice_line_tax_ids': [[6, 0, res.tax_id.ids]],
                                 'price_subtotal': ((float(percent_value[0]) * res.price_subtotal) / 100) if res.price_subtotal > 0 else 0,
                                 'split_amount': ((float(percent_value[0]) * res.price_subtotal) / 100) if res.price_subtotal > 0 else 0,
                                 'split_type': 'split'
                                 }
                    invoice_line = [0, 0, line_data]
                    lines.append(invoice_line)
                vals = {
                    'partner_id': int(customer),
                    # Chnages by Krishna below line changed the values
                    'account_id': order_id.partner_id.property_account_receivable_id.id,
                    'invoice_line_ids': lines,
                    'origin': order_id.name,
                    'order_id': order_id.id,
                    'mobile': request.env['res.partner'].search([('id', '=', int(customer))]).mobile,
                    'email': request.env['res.partner'].search([('id', '=', int(customer))]).email,
                    # Vehicle-Details
                    'reg_no': order_id.regn_no.id,
                    'vin': order_id.vin_no,
                    'product_id': order_id.vehicle_model.id,
                    'model': order_id.model.id,
                    'kilometer': order_id.mileage_in,
                    'appointment_date': order_id.appointment_date,
                    'delivery_service_advisor': order_id.delivery_service_advisor.id,
                    'delivery_date': order_id.delivery_date,
                    'payment_term_id': order_id.payment_term_id.id,
                    'fiscal_position_id': order_id.fiscal_position_id.id,
                    'service_type': order_id.service_type.id,
                    'service_options': order_id.service_options.id,
                }
                context = {'type': 'out_invoice', 'journal_type': 'sale', 'default_ars_invoice_type': 'after_sales'}
                created_invoice = request.env['account.invoice'].with_context(context).create(vals)
                invoice_ids.append(created_invoice.id)

        if not invoice_ids:
            return {'status': False, 'error': 'No invoices were created.'}

        return {
            'status': True,
            'invoice_ids': invoice_ids,
        }



        # action = {'type': 'ir.actions.act_window_close'}

        # return {'status':True}
