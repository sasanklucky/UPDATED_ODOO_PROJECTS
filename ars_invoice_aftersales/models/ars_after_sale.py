from email.policy import default

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError, ValidationError


class ARS_After_sale_order(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('so', 'SO Preparation'),
        ('sent', 'Quotation Sent'),
        ('to_approve', 'To Approve'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def action_convert(self):
        self.write({'state': 'so'})
        self.write({'stages':'repair_order'})
        if self.sale_aftersales == 'after_sales':
            self.create_warranty_order()
            if self.mileage_in == 0:
                raise ValidationError('Please enter the Kilometer')
            vehicle = self.env['service.setup.manual'].search([('model_id','=',self.fleet_vin_no.model_id.id),
                                                               ('service_type','=',self.service_type.id)])
            if vehicle:
                if self.fleet_vin_no.customer_ids:
                    customer_ids_fleet = self.fleet_vin_no.customer_ids[-1]  # selecting the last record of one2many field customer_ids
                    if customer_ids_fleet.date_of_ownership:
                        date_ownership = fields.Date.from_string(customer_ids_fleet.date_of_ownership)  # assigning the value of date of ownership to a varaible
                        current_date = date.today()
                        days_diff = (current_date - date_ownership).days
                        if days_diff > vehicle.days:
                            raise ValidationError(f'{vehicle.service_type.name} Days Have Already Exhausted')
                        if self.mileage_in > vehicle.kms:
                            raise ValidationError(f'{vehicle.service_type.name} Kilometers Have Already Exhausted')
                    else:
                        raise ValidationError('Date Of Ownership is not Present')
                else:
                    raise ValidationError('Date of Ownership is not Present')
        return {
            'name': _('Sale Message'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.message',
            'view_id': self.env.ref('ars_after_sales.view_sale_message').id,
            'target': 'new',
        }
        # param = self.env['ir.config_parameter'].sudo().get_param('ars_after_sales.sale_text')
        # self.call_sale_message(param)
        # print(f'self.call_sale_message{param}', self.call_sale_message(param))


    def create_warranty_order(self):
        for od in self:
            line_ids = []
            warnVals = {}
            vendors = {}
            for ol in od.order_line:
                if ol.category and ol.category.name == 'Warranty':
                    if ol.customer_split and ol.customer_split.id not in vendors:
                        vendors[ol.customer_split.id] = [ol.id]
                    elif ol.customer_split and ol.customer_split.id in vendors:
                        vendors[ol.customer_split.id].append(ol.id)
            print('vendors', vendors)
            warranty_ids = self.env['ars.sale.warranty'].search_read([('order_id', '=', od.id)],
                                                                     fields=['partner_id', 'order_id'])

            for wr in warranty_ids:
                if wr.get('partner_id')[0] not in vendors.keys():
                    vendors[wr.get('partner_id')[0]] = []

            for v in vendors.keys():
                warranty_ids = self.env['ars.sale.warranty'].search([('order_id', '=', od.id), ('partner_id', '=', v)])

                # If a warranty exists and it's in draft state, just update it
                # if warranty_ids and all(w.state == 'draft_process' for w in warranty_ids):
                if warranty_ids and all(w.state == 'draft'for w in warranty_ids):
                    warnVals = {
                        'partner_id': v,
                        'regn_no': od.regn_no.id if od.regn_no else False,
                        'model_id': od.model.id if od.model else False,
                        'vin_no': od.vin_no or '',
                        'order_id': od.id,
                        'order_lines': [(6, 0, vendors.get(v))]
                    }
                    warranty_ids.write(warnVals)
                    print(f'Updated warranty for vendor {v} in draft state: {warnVals}')
                    continue

                if warranty_ids and any(w.state in ['inprocess', 'processed'] for w in warranty_ids):
                    print(f'Skipping creation for vendor {v} as there are existing warranties in-process or processed.')
                    continue

                warnVals = {'partner_id': v,
                            'regn_no': od.regn_no and od.regn_no.id,
                            'model_id': od.model and od.model.id,
                            'vin_no': od.vin_no or '',
                            'order_id': od.id,
                            'order_lines': [(6, 0, vendors.get(v))]}

                if not vendors.get(v):
                    warnVals.update({'state': 'cancel'})

                if warnVals:
                    if not warranty_ids:
                        warnVals['name'] = self.env['ir.sequence'].next_by_code('warranty_claims')
                        self.env['ars.sale.warranty'].create(warnVals)
                        print('999999', warnVals, not warranty_ids)
                    else:
                        warranty_ids.write(warnVals)
        return True

    @api.multi
    def write(self, vals):

        # existing_order_lines = {line.id: line for line in self.order_line}

        if 'order_line' in vals:

            for order in self:
                # Search for existing warranties that meet the specific conditions
                existing_warranties_draft = self.env['ars.sale.warranty'].search([
                    ('order_id', '=', order.id),
                    ('state', '=', 'draft_process'),
                    # ('sync_count', '=', 1),
                    ('Warranty_sync_reject', '=', False)
                ])

                if existing_warranties_draft:
                    raise ValidationError(
                        "Waiting for TM Approval."
                    )

            if 'order_line' in vals:
                for order in self:
                    existing_warranties = self.env['ars.sale.warranty'].search([
                        ('order_id', '=', order.id)
                    ])

                    modified_order_line_ids = set()
                    for command in vals.get('order_line', []):
                        if command[0] == 1:
                            modified_order_line_ids.add(command[1])

                    for warranty in existing_warranties:

                        modified_order_lines = warranty.order_lines.filtered(
                            lambda line: line.id in modified_order_line_ids
                        )

                        approved_modified_order_lines = modified_order_lines.filtered(
                            lambda line: line.apr_action == 'approved'
                        )

                        if approved_modified_order_lines and not warranty.Warranty_sync_reject:
                            raise ValidationError(
                                "Claim is already Approved."
                            )

                        non_approved_modified_order_lines = modified_order_lines.filtered(
                            lambda line: line.apr_action != 'approved'
                        )

                        if non_approved_modified_order_lines and warranty.Warranty_sync_reject:
                            continue


        res = super(ARS_After_sale_order, self).write(vals)

        # Check if order lines are being updated (new line is added)
        if 'order_line' in vals:
            for order in self:
                vendors = {}
                existing_order_line_ids = set()

                # Collect new order lines that are associated with 'Warranty' category
                for ol in order.order_line:
                    if ol.category and ol.category.name == 'Warranty':
                        if ol.customer_split:
                            vendor_id = ol.customer_split.id
                            if vendor_id not in vendors:
                                vendors[vendor_id] = []
                            vendors[vendor_id].append(ol.id)

                existing_warranties = self.env['ars.sale.warranty'].search([
                    ('order_id', '=', order.id),
                    ('state', 'in', ['re_submit', 'inprocess', 'processed', 'done'])
                ])
                for warranty in existing_warranties:
                    existing_order_line_ids.update(warranty.order_lines.ids)

                draft_warranties = self.env['ars.sale.warranty'].search([
                    ('order_id', '=', order.id),
                    ('state', '=', 'draft')
                ])

                for vendor_id, order_line_ids in vendors.items():
                    # Filter new order lines that are not already associated with existing warranties
                    new_order_line_ids = [ol_id for ol_id in order_line_ids
                                          if ol_id not in existing_order_line_ids and
                                          self.env['sale.order.line'].browse(ol_id).apr_action not in ['approved',
                                                                                                       'reject']
                                          # self.env['sale.order.line'].browse(ol_id).apr_action != 'approved'
                                          ]
                    if draft_warranties:
                        # Add new order lines to existing draft warranties
                        for draft_warranty in draft_warranties:
                            # Update existing draft warranty with new order lines
                            draft_warranty.order_lines = [(4, ol_id) for ol_id in new_order_line_ids]
                            print(
                                f'Updated draft warranty {draft_warranty.id} with new order lines: {new_order_line_ids}')
                        continue

                    if new_order_line_ids:
                        warnVals = {
                            'partner_id': vendor_id,
                            'regn_no': order.regn_no.id if order.regn_no else False,
                            'model_id': order.model.id if order.model else False,
                            'vin_no': order.vin_no or '',
                            'order_id': order.id,
                            'order_lines': [(6, 0, new_order_line_ids)],  # Only add new order lines
                        }

                        # If no vendors found for a partner, cancel the warranty
                        if not new_order_line_ids:
                            warnVals.update({'state': 'cancel'})

                            # Create a new warranty record with a sequence number
                        warnVals['name'] = self.env['ir.sequence'].next_by_code('warranty_claims')
                        self.env['ars.sale.warranty'].create(warnVals)
                        print(f'Created new warranty record: {warnVals}')
                    else:
                        print(f'Skipping creation: No new order lines for partner {vendor_id}')

                    # After handling warranty, update warranty states if needed
            self.update_warranty_state_on_order_line_change()

        return res


    def update_warranty_state_on_order_line_change(self):
        print('Starting update_warranty_state_on_order_line_change')
        for order in self:
            service_order_lines = order.order_line.filtered(lambda line: line.category.name == 'Warranty')
            print('SERVICE STATE:', service_order_lines)

            warranty_ids = self.env['ars.sale.warranty'].search(
                [('order_id', '=', order.id), ('state', '=', 're_submit')]
            )
            print('WARRANTY IDS:', warranty_ids)

            if warranty_ids:
                for warranty in warranty_ids:
                    if warranty.sync_count == 1:
                        # Update hide_sync to False when sync_count is 1
                        warranty.write({
                            'hide_sync': False
                        })
                    print(f'Updated warranty {warranty.id} to draft and hide_sync set to False.')
                    print('warranty state:', warranty.state, 'hide_sync:', warranty.hide_sync)
            else:
                print('No warranties found in process.')

        return True

    @api.multi
    def action_cancel(self):
        res = super(ARS_After_sale_order, self).action_cancel()

        for order in self:
            warranties = self.env['ars.sale.warranty'].search([('order_id', '=', order.id)])

            for warranty in warranties:
                warranty.write({'hide_sync': True})
                print(f'Updated warranty {warranty.id} - hide_sync set to True.')

        return res

    @api.multi
    def action_split(self):
        action = ''
        if len(self.order_line.ids) >= 1:
            action = self.env.ref('ars_invoice_aftersales.action_split_line').read()[0]
            action.update({'domain': [('id', 'in', self.order_line.ids)]})
        return action

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            count = 0
            invoice = None
            # Handling after-sales scenario
            if order.sale_aftersales == 'after_sales' and not order.counter_parts:
                for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):

                    # Skip if no quantity to invoice
                    if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue
                    # if not line.warranty_split_partner_ids:
                    # Search for an existing draft invoice for the order and customer
                    invoice = inv_obj.search([('origin', '=', order.name),
                                              ('partner_id', '=', line.customer_split.id),
                                              ('state', '=', 'draft')], limit=1)

                    inv_data = order.with_context(
                        {'customer_split': line.customer_split.id, 'count_line': count})._prepare_invoice()
                    count += 1

                    if invoice:
                        # Reference invoices update
                        invoice_ref = inv_obj.search([('origin', '=', order.name),
                                                      ('cust_invoice_type', '!=', invoice.cust_invoice_type)])
                        if invoice_ref:
                            for ref_inv in invoice_ref:
                                invoice.write({'invoice_reference': ref_inv.id})
                                ref_inv.write({'invoice_reference': invoice.id})

                        # Check if product already exists in the invoice line
                        invoice_line = invoice.invoice_line_ids.filtered(
                            lambda x: x.product_id.id == line.product_id.id)

                        if invoice_line:
                            # If product exists, update the quantity
                            new_qty = invoice_line.quantity + line.qty_to_invoice
                            invoice_line.write({'quantity': new_qty})
                        else:
                            # Otherwise, create a new invoice line
                            line.invoice_line_create(invoice.id, line.qty_to_invoice)

                        # Adjust for refunds if necessary
                        if invoice.amount_untaxed < 0:
                            invoice.type = 'out_refund'
                            for inv_line in invoice.invoice_line_ids:
                                inv_line.quantity = -inv_line.quantity

                        # Force recalculation of taxes
                        invoice.compute_taxes()
                        invoice.message_post_with_view('mail.message_origin_link',
                                                       values={'self': invoice, 'origin': order},
                                                       subtype_id=self.env.ref('mail.mt_note').id)
                        invoices[invoice.id] = invoice
                    else:
                        # Create a new invoice if no draft invoice is found
                        if not order.counter_parts:
                            if line.category.name.lower() == 'warranty':
                                inv_data.update({'cust_invoice_type': 'warranty'})
                            elif line.category.name.lower() == 'customer':
                                inv_data.update({'cust_invoice_type': 'customer'})
                            elif line.category.name.lower() == 'insurance':
                                inv_data.update({'cust_invoice_type': 'insurance'})

                        invoice = inv_obj.create(inv_data)
                        invoices[invoice.id] = invoice
                        line.invoice_line_create(invoice.id, line.qty_to_invoice)

                    # Update invoice with additional information
                    invoice.write({
                        'mobile': order.mobile,
                        'email': order.email,
                        'reg_no': order.regn_no.id,
                        'vin': order.vin_no,
                        'model': order.model.id,
                        'kilometer': order.mileage_in,
                        'doc_type': order.doc_type,
                        'appointment_date': order.appointment_date,
                        'delivery_service_advisor': order.delivery_service_advisor.id,
                        'delivery_date': order.delivery_date,
                        'service_options': order.service_options.id,
                        'service_type': order.service_type.id
                    })
                    # if invoice:
                    # Ensure additional fields are set correctly
                    for inv_line in invoice.invoice_line_ids:
                        inv_line._set_additional_fields(invoice)

                    # Force computation of taxes
                    invoice.compute_taxes()

                # Update order status
                order.invoice_status = "invoiced"
                return [inv.id for inv in invoices.values()]

            elif order.sale_aftersales != 'after_sales' or order.counter_parts:
                res = super(ARS_After_sale_order, self).action_invoice_create(grouped=False, final=False)
                rest = inv_obj.browse(res)
                rest.write({
                    'mobile': order.mobile,
                    'email': order.email,
                    'reg_no': order.regn_no.id,
                    'vin': order.vin_no,
                    'model': order.model.id,
                    'kilometer': order.mileage_in,
                    'doc_type': order.doc_type,
                    'appointment_date': order.appointment_date,
                    'delivery_date': order.delivery_date,
                })
                # Update invoice lines with product_template_id
                for order_line in order.order_line:
                    invoice = rest.invoice_line_ids.filtered(lambda x: x.product_id.id == order_line.product_id.id)
                    for inv_s in invoice:
                        inv_s.product_template_id = order_line.product_template_id.id

                return [inv.id for inv in invoices.values()]

            else:
                res = super(ARS_After_sale_order, self).action_invoice_create(grouped=False, final=False)
                return res

    # @api.multi
    # def action_invoice_create(self, grouped=False, final=False):
    #     # print("-------invoice create---------------")
    #     # import pdb
    #     # pdb.set_trace()
    #     """
    #     Create the invoice associated to the SO.
    #     :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
    #                     (partner_invoice_id, currency)
    #     :param final: if True, refunds will be generated if necessary
    #     :returns: list of created invoices
    #     """
    #
    #     inv_obj = self.env['account.invoice']
    #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #     invoices = {}
    #     references = {}
    #     for order in self:
    #         # self.env.cr.execute("""select
    #         #                         distinct(sl.customer_split)
    #         #                         from sale_order_line sl
    #         #                         where sl.order_id = %s""", (order.id,))
    #         # all_data = self.env.cr.dictfetchall()
    #         # for data in all_data:
    #         group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
    #         warranty_invoice, customer_invoice = None, None
    #         if order.sale_aftersales == 'after_sales' and not order.counter_parts:
    #             # res = super(ARS_After_sale_order, self).action_invoice_create(grouped=False, final=False)
    #             # print("--------after sales-----------")
    #             # for data in all_data:
    #             count = 0
    #             for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
    #
    #                 # if float_is_zero(line.qty_to_invoice, precision_digits=precision):
    #                 #     continue
    #                 # if line.customer_split.id == data.get('customer_split'):
    #
    #                 invoice = inv_obj.search([('origin', '=', order.name), ('partner_id', '=', line.customer_split.id)],
    #                                          limit=1)
    #                 # inv_data = order.with_context(
    #                 #     {'customer_split': line.customer_split.id, 'count_line': count})._prepare_invoice()
    #                 # print('inv_data', inv_data)
    #                 # if invoice and invoice.state == 'draft':
    #                 #     invoice = None
    #                 # count += 1
    #                 if invoice and invoice.state == 'draft':
    #                     invoice_ref = inv_obj.search([('origin', '=', order.name),
    #                                                   ('cust_invoice_type', '!=', invoice.cust_invoice_type)])
    #                     if invoice_ref:
    #                         for ref_inv in invoice_ref:
    #                             invoice.write({'invoice_reference': ref_inv.id})
    #                             ref_inv.write({'invoice_reference': invoice.id})
    #                     products = invoice.invoice_line_ids.mapped('product_id').ids
    #                     if line.product_id.id not in products:
    #                         if line.qty_to_invoice > 0:
    #                             line.invoice_line_create(invoice.id, line.qty_to_invoice)
    #                         if invoice.amount_untaxed < 0:
    #                             invoice.type = 'out_refund'
    #                             for line in invoice.invoice_line_ids:
    #                                 line.quantity = -line.quantity
    #                         # Use additional field helper function (for account extensions)
    #                         for line in invoice.invoice_line_ids:
    #                             line._set_additional_fields(invoice)
    #                         # Necessary to force computation of taxes. In account_invoice, they are triggered
    #                         # by onchanges, which are not triggered when doing a create.
    #                         invoice.compute_taxes()
    #                         invoice.message_post_with_view('mail.message_origin_link',
    #                                                        values={'self': invoice, 'origin': order},
    #                                                        subtype_id=self.env.ref('mail.mt_note').id)
    #                     # else:
    #                         # inv_data = order.with_context({'customer_split': line.customer_split.id, 'count_line': count})._prepare_invoice()
    #                         # invoice = inv_obj.create(inv_data)
    #                         # invoices[invoice.id] = invoice
    #                     invoices[invoice.id] = invoice
    #                 else:
    #                     # print("invoice created----")
    #                     inv_data = order.with_context(
    #                         {'customer_split': line.customer_split.id, 'count_line': count})._prepare_invoice()
    #                     count += 1
    #                     if order.counter_parts == False:
    #                         if line.category.name.lower() == 'warranty':
    #                             inv_data.update({'cust_invoice_type': 'warranty'})
    #                             # print('warranty check')
    #                         elif line.category.name.lower() == 'customer':
    #                             inv_data.update({'cust_invoice_type': 'customer'})
    #                         elif line.category.name.lower() == 'insurance':
    #                             inv_data.update({'cust_invoice_type': 'insurance'})
    #                     invoice = inv_obj.create(inv_data)
    #                     invoices[invoice.id] = invoice
    #                     #                         references[invoice] = order
    #                     # invoices[group_key] = invoice
    #                     if line.qty_to_invoice > 0:
    #                         line.invoice_line_create(invoice.id, line.qty_to_invoice)
    #                 invoice.write({'mobile': order.mobile, 'email': order.email,
    #                                'reg_no': order.regn_no.id, 'vin': order.vin_no,
    #                                'model': order.model.id, 'kilometer': order.mileage_in,
    #                                'doc_type': order.doc_type, 'appointment_date': order.appointment_date,
    #                                'delivery_service_advisor': order.delivery_service_advisor.id,
    #                                'delivery_date': order.delivery_date, 'service_options': order.service_options.id,
    #                                'service_type': order.service_type.id})
    #             #                     elif group_key in invoices:
    #             #                         vals = {}
    #             #                         if order.name not in invoices[group_key].origin.split(', '):
    #             #                             vals['origin'] = invoices[group_key].origin + ', ' + order.name
    #             #                         if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(
    #             #                                 ', ') and order.client_order_ref != invoices[group_key].name:
    #             #                             vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
    #             #                         invoices[group_key].write(vals)
    #
    #             #                     if references.get(invoices.get(group_key)):
    #             #                         if order not in references[invoices[group_key]]:
    #             #                             references[invoice] = references[invoice] | order
    #             #
    #             #                     invoices[group_key] = invoice
    #
    #             #                 if not invoices:
    #             #                     raise UserError(_('There is no invoiceable line.'))
    #             #
    #             #                 for invoice in invoices.values():
    #             #                     if not invoice.invoice_line_ids:
    #             #                         raise UserError(_('There is no invoiceable line.'))
    #             #                     # If invoice is negative, do a refund invoice instead
    #             #                     if invoice.amount_untaxed < 0:
    #             #                         invoice.type = 'out_refund'
    #             #                         for line in invoice.invoice_line_ids:
    #             #                             line.quantity = -line.quantity
    #             #                     # Use additional field helper function (for account extensions)
    #             for line1 in invoice.invoice_line_ids:
    #                 line1._set_additional_fields(invoice)
    #             # Necessary to force computation of taxes. In account_invoice, they are triggered
    #             # by onchanges, which are not triggered when doing a create.
    #             invoice.compute_taxes()
    #             # invoice.message_post_with_view('mail.message_origin_link',
    #             #        values={'self': invoice, 'origin': order.name},
    #             #        subtype_id=self.env.ref('mail.mt_note').id)
    #             order.invoice_status = "invoiced"
    #             return [inv.id for inv in invoices.values()]
    #
    #         if order.sale_aftersales != 'after_sales' or order.counter_parts:
    #             res = super(ARS_After_sale_order, self).action_invoice_create(grouped=False, final=False)
    #             rest = inv_obj.browse(res)
    #             rest.write({'mobile': order.mobile, 'email': order.email,
    #                         'reg_no': order.regn_no.license_plate, 'vin': order.vin_no,
    #                         'model': order.model, 'kilometer': order.mileage_in,
    #                         'doc_type': order.doc_type, 'appointment_date': order.appointment_date,
    #                         'delivery_date': order.delivery_date,
    #                         })
    #
    #             for order_line in order.order_line:
    #                 invoice = rest.invoice_line_ids.filtered(lambda x: x.product_id.id == order_line.product_id.id)
    #                 # invoice.product_template_id = order_line.product_template_id.id
    #                 for inv_s in invoice:
    #                     inv_s.product_template_id = order_line.product_template_id.id
    #             return [inv.id for inv in invoices.values()]

                # 'product_template_id':order.order_line.product_template_id.id

                # """ Update Product attribute from sale order lie to account invoice lines """
                # query = f"""INSERT INTO account_line_attribute_rel (account_id, attribute_id) VALUES ({str(rest.invoice_line_ids.ids)[1:-1]},{str(order.order_line.product_varient_ids.ids)[1:-1]});"""
                # self._cr.execute(query)
                # return res

            # if order.sale_aftersales != 'after_sales':
            #     for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
            #         if float_is_zero(line.qty_to_invoice, precision_digits=precision):
            #             continue
            #         if group_key not in invoices:
            #             inv_data = order._prepare_invoice()
            #             invoice = inv_obj.create(inv_data)
            #             references[invoice] = order
            #             invoices[group_key] = invoice
            #         elif group_key in invoices:
            #             vals = {}
            #             if order.name not in invoices[group_key].origin.split(', '):
            #                 vals['origin'] = invoices[group_key].origin + ', ' + order.name
            #             if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(
            #                     ', ') and order.client_order_ref != invoices[group_key].name:
            #                 vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
            #             invoices[group_key].write(vals)
            #         if line.qty_to_invoice > 0:
            #             line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
            #         elif line.qty_to_invoice < 0 and final:
            #             line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
            #
            #     if references.get(invoices.get(group_key)):
            #         if order not in references[invoices[group_key]]:
            #             references[invoice] = references[invoice] | order

    @api.multi
    def _prepare_invoice(self):
        context = self.env.context
        res = super(ARS_After_sale_order, self)._prepare_invoice()
        if context.get('customer_split'):
            res['partner_id'] = context.get('customer_split')
            res['partner_shipping_id'] = context.get('customer_split')
        return res

    # @api.multi
    # @api.onchange('order_line')
    # def orderLine_Change(self):
    #     res = {}
    #     for ol in self.order_line:
    #         if ol.category and ol.category.name.lower() == 'warranty':
    #            seller_ids = [sl.name.id for sl in ol.product_id.seller_ids]
    #            res = {'domain': {'customer_split': [('id', 'in', seller_ids)]}}


class ARS_sale_order_line(models.Model):
    _inherit = "sale.order.line"

    # @api.model
    # def _default_customer_split(self):
    #     for customer in self:
    #         customer.customer_split = customer.order_id.partner_id.id

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    if invoice_line.invoice_id.type == 'out_invoice':
                        if invoice_line.split_type == 'split':
                            qty_invoiced = invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                        else:
                            qty_invoiced += invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                    elif invoice_line.invoice_id.type == 'out_refund':
                        qty_invoiced -= invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
            line.qty_invoiced = qty_invoiced


    """ Product line varient """
    product_varient_ids = fields.Many2many('product.attribute.value', 'order_line_attribute_rel', 'order_id',
                                           'attribute_id', string='Attribute')
    product_template_id = fields.Many2one('product.template', string='Product')

    @api.multi
    @api.onchange('product_catalog_id')
    def onchange_product_based_on_catalog(self):
        if self.product_catalog_id:
            product = self.env['product.template'].sudo().search([('catalog_type', '=', self.product_catalog_id.id)])
            return {'domain': {'product_template_id': [('id', 'in', product.ids)]}}
        else:
            return {'domain': {'product_template_id': [('id', 'in', False)]}}

    @api.multi
    @api.onchange('product_template_id')
    def onchange_product_template_id(self):
        self.product_id = False
        if self.product_template_id and self.product_template_id.attribute_line_ids:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            return {'domain': {'product_id': [('id', 'in', varient_ids.ids)]}}
        else:
            varient_ids = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_template_id.id)])
            self.product_id = varient_ids.id
            self.customer_split = self.order_id.partner_id.id
            return {'domain': {'product_id': [('id', 'in', False)]}}

    # @api.multi
    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     self.product_varient_ids=False
    #     if self.product_id:
    #         return {'domain': {'product_varient_ids': [('id', 'in', self.product_id.attribute_value_ids.ids)]}}

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(ARS_sale_order_line, self).product_id_change()
        self.category = self.env['order.line.category'].search([('name', '=', 'Customer')])
        self.customer_split = self.env.context.get(
            'partner_id') if 'partner_id' in self.env.context else self.order_id.partner_id.id
        # res.update({'customer_split':self.env.context.get('partner_id')})
        print('res5453453', res, self.price_unit)
        self.update({'ars_warranty_price': self.price_unit,
                     'ars_std_price': self.price_unit})
        return res

    @api.one
    def _get_customer_invoice_count(self):
        count = 1
        if self.order_id:
            if self.customer_split:
                inv_obj = self.env['account.invoice']
                invoice = inv_obj.search(
                    [('origin', '=', self.order_id.name), ('partner_id', '=', self.customer_split.id)])
                count = len(invoice)
        self.split_type = count

    @api.one
    def _filter_partner(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.category and line.category.name.lower() == 'warranty':
                line.cust_filter_ids = [sl.name.id for sl in self.product_id.seller_ids]
            elif self.category and self.category.name.lower() == 'customer':
                line.cust_filter_ids = self.env['res.partner'].search([('customer', '=', True)])
            elif self.category and self.category.name.lower() == 'insurance':
                line.cust_filter_ids = self.env['res.partner'].search([('customer', '=', True)])
            else:
                line.cust_filter_ids = self.env['res.partner'].search([])


    customer_split = fields.Many2one('res.partner', string="Customer", readonly=False)
    split_type = fields.Integer(compute='_get_customer_invoice_count', default=1)
    cust_filter_ids = fields.Many2many('res.partner', compute='_filter_partner', string='Customer Filter')


    # amount tax total
    order_amount_total = fields.Monetary(
        string="Total With Tax",
        compute="_compute_total_with_tax",
        store=True,
        currency_field="currency_id"
    )

    @api.depends('price_unit', 'tax_id', 'product_uom_qty', 'discount')
    def _compute_total_with_tax(self):
        for line in self:
            tax_amount = 0.0
            subtotal = 0.0
            discounted_price = 0.0
            print("KRISHNA11143", line.tax_id)
            if line.tax_id:
                # Adjust the price for the discount
                discounted_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

                # Compute taxes based on the discounted price
                taxes = line.tax_id.compute_all(
                    discounted_price,
                    currency=line.order_id.currency_id,
                    quantity=line.product_uom_qty,
                    product=line.product_id,
                    partner=line.order_id.partner_id
                )

                tax_amount = sum(t['amount'] for t in taxes['taxes'])  # Tax total
                # print('tax_amount', tax_amount)
                subtotal = taxes['total_excluded']
                # print(subtotal, 'subtotal')
            else:
                taxes = line.tax_id.compute_all(
                    price_unit=line.price_unit,
                    currency=line.order_id.currency_id,
                    quantity=line.product_uom_qty,
                    product=line.product_id,
                    partner=line.order_id.partner_id
                )
                print(taxes, 'Sasank ')
                # tax_amount = sum([t['amount'] for t in taxes['taxes'] if t])  # Tax total
                # # print('tax_amount', tax_amount)
                # subtotal = taxes['total_excluded']
            line.price_subtotal = subtotal
            line.amount_tax = tax_amount
            line.order_amount_total = subtotal + tax_amount
            # print('line.order_amount_total', line.order_amount_total)

    # is_visible = fields.Boolean()

    @api.depends('order_line.price_subtotal', 'order_line.tax_id', 'order_line.discount')
    def _compute_amounts(self):
        for order in self:
            total_tax_included = total_tax_excluded = 0.0

            for line in order.order_line:
                total_tax_included += line.price_subtotal + line.amount_tax
                total_tax_excluded += line.price_subtotal

            # Update fields
            order.amount_untaxed = total_tax_excluded
            order.amount_tax = total_tax_included - total_tax_excluded
            order.amount_total = total_tax_included
            # print('order.amount_total', order.amount_total,order.amount_tax, order.amount_untaxed)

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """ Create an invoice line. The quantity to invoice can be positive (invoice) or negative (refund).
            :param invoice_id: integer
            :param qty: float quantity to invoice
            :returns recordset of account.invoice.line created
        """
        invoice_lines = self.env['account.invoice.line']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.order_id.sale_aftersales == 'after_sales' and not self.order_id.counter_parts:
                invoice = self.env['account.invoice'].browse(invoice_id)
                if invoice.partner_id == line.customer_split:
                    vals = line._prepare_invoice_line(qty=qty)
                    line_obj = self.env['account.invoice.line'].search(
                        [('invoice_id', '=', invoice_id), ('product_id', '=', vals.get('product_id'))])
                    if not line_obj:
                        vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                        invoice_lines |= self.env['account.invoice.line'].create(vals)
            else:
                if not float_is_zero(qty, precision_digits=precision):
                    vals = line._prepare_invoice_line(qty=qty)
                    vin_details = self.env['fleet.vehicle'].search([('mvariant_id', '=', self.product_id.id)])
                    vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                    invoice_lines |= self.env['account.invoice.line'].create(vals)
        return invoice_lines

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(ARS_sale_order_line, self)._prepare_invoice_line(qty)
        res.update({'vin_no': self.vin_no.id, 'product_template_id': self.product_template_id.id,
                    'product_catalog_id': self.product_catalog_id.id, 'category': self.category.id})
        return res


class ARS_account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)

            self.price_subtotal = taxes['total_excluded'] if taxes else self.quantity * price
            self.price_total = taxes['total_included'] if taxes else self.price_subtotal

            sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
            self.price_subtotal_signed = self.price_subtotal * sign
        else:
            # print('SASANK')
            taxes = self.invoice_line_tax_ids.compute_all(self.price_unit, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)

            self.price_subtotal = taxes['total_excluded'] if taxes else self.quantity * price
            self.price_total = taxes['total_included'] if taxes else self.price_subtotal

            sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
            self.price_subtotal_signed = self.price_subtotal * sign
        # if self.split_type == 'split':
        #     self.price_subtotal = price_subtotal_signed = self.split_amount
        # else:
        #     self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        # self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        # if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
        #     price_subtotal_signed = self.invoice_id.currency_id.with_context(
        #         date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed,
        #                                                                 self.invoice_id.company_id.currency_id)
        # sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        # self.price_subtotal_signed = price_subtotal_signed * sign

    split_amount = fields.Float('Split Amount')
    split_type = fields.Char('Split Type')
    category = fields.Many2one('order.line.category', string="Category")


class ARS_split_invoice(models.Model):
    _name = "split.invoice"

    @api.multi
    @api.onchange('customer')
    def split_customer(self):
        record_ids = self._context.get('active_ids')
        customers = self.env['sale.order.line'].browse(record_ids[0])
        self.customer = customers.order_id.partner_id.id

    @api.multi
    @api.onchange('amount')
    def split_amount(self):
        record_ids = self._context.get('active_ids')
        records = self.env['sale.order.line'].browse(record_ids)
        total_price = 0
        for record in records:
            total_price += record.price_subtotal
        self.amount = total_price

    @api.multi
    @api.onchange('percentage')
    def split_percentage(self):
        record_ids = self._context.get('active_ids')
        records = self.env['sale.order.line'].browse(record_ids)
        self.percentage = '100%'

    @api.multi
    @api.onchange('tax')
    def split_tax(self):
        record_ids = self._context.get('active_ids')
        taxes = self.env['sale.order.line'].browse(record_ids[0])
        self.tax = taxes.order_id.tax_id.id

    @api.multi
    @api.onchange('tax_amount')
    def split_taxamount(self):
        record_ids = self._context.get('active_ids')
        untax = self.env['sale.order.line'].browse(record_ids[0])
        self.customer = untax.order_id.order_amount_total

    customer = fields.Many2one('res.partner')
    percentage = fields.Char()
    amount = fields.Char()
    tax = fields.Char()
    tax_amount = fields.Char()

    @api.multi
    def action_draft_invoice(self):
        self.customer
        account = self.env['account.invoice']
        return


class AccountInvoice_inherit(models.Model):
    _inherit = "account.invoice"

    # invoice_reference = fields.Many2one('account.invoice', string='Invoice Reference')
    # cust_invoice_type = fields.Selection([('warranty', 'Warranty Invoice'),
    #                                       ('customer', 'Customer Invoice'),
    #                                       ('insurance', 'Insurance Invoice')], string='Type')

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice_inherit, self).action_invoice_open()
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        warranty_ids = self.env['ars.sale.warranty'].search(
            [('order_id.name', '=', self.origin), ('partner_id', '=', self.partner_id.id)])
        for wr in warranty_ids:
            # if wr.state in ('draft', 'inprocess'):
            #     raise UserError(_('Some of warranty claims are in Draft/In-Process state. Please check and proceed.'))
            # else:
            self._cr.execute("update ars_sale_warranty set state='done' where id =" + str(wr.id))
        if not self.invoice_line_ids:
            raise UserError(_(
                'Not allowed to confirm an order without invoice lines'))


        # inv_obj = self.env['account.invoice']
        # rest = inv_obj.browse(res)
        for order in self:
            for vin in order.invoice_line_ids.mapped('vin_no'):
                vehicle_card = self.env['fleet.vehicle'].search([('lot_id', '=', vin.id)])
                if not order.gate_pass_date:
                    order.gate_pass_date = datetime.now()
                if not vehicle_card:
                    vehicle_card = self.env['fleet.vehicle'].search([('vin_sn', '=', vin.name)])
                if vehicle_card and not order.partner_id.is_dealer:
                    vehicle_card.write(
                        {'driver_id': order.partner_id.id, 'vehicle_status': 'customer',
                         'lot_id': vin.id,
                         # 'customer_ids': [(0, 0, {'custmer_name': order.partner_id.id,
                         #                          'date_of_ownership': order.date_invoice,
                         #                          'delivery_date': order.gate_pass_date,
                         #                          'address': order.partner_id.city,
                         #                          'sold_by': self.env.user.company_id.partner_id.id,
                         #                          'mobile': order.partner_id.mobile})]
                         })
                    #commented this code in staging_05_06_24 because vehicle history its not present in branch
                    if vehicle_card.service_type_sequence == 0:
                        if vehicle_card.customer_ids:
                            if vehicle_card.service_type_sequence == 0:
                                service_typ = self.env['service.type'].search([('sequence', '=', vehicle_card.service_type_sequence)], limit=1)
                                for v in vehicle_card.service_ids:
                                    if v.service_type_name == service_typ.name:
                                        k = self.env['service.history'].search([('id', '=', v.id), ('vehicle_id', '=', vehicle_card.id)])
                                        next_ser_typ = vehicle_card.service_type_sequence + 1
                                        next = self.env['service.type'].search([('sequence', '=', next_ser_typ)], limit=1)

                                        remainder = self.env.user.company_id.next_service_remainder
                                        nxt_due = self.env.user.company_id.next_service_due
                                        remainder_value = int(remainder) if isinstance(remainder, str) else remainder

                                        service_manual = {
                                            days.id: {
                                                'next_service': int(days.days) if isinstance(days.days, str) else days.days,
                                                'service_remainder': (int(days.days) if isinstance(days.days,
                                                                                                   str) else days.days) - remainder_value
                                            }
                                            for days in self.env['service.setup.manual'].search(
                                                [('service_type', '=', next.id), ('model_id', '=', vehicle_card.model_id.id)],
                                                limit=1)
                                        }

                                        next_services = [values['next_service'] for values in service_manual.values()]
                                        service_remainders = [values['service_remainder'] for values in service_manual.values()]
                                        next_service_due = datetime.now().date() + timedelta(
                                            days=int(next_services[0] if next_services else nxt_due))
                                        set_reminder = datetime.now().date() + timedelta(
                                            days=int(service_remainders[0] if service_remainders else remainder))
                                        k.write({
                                            'next_service_due': next_service_due,
                                            'set_reminder': set_reminder
                                        })
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice_inherit, self).line_get_convert(line, part)
        if line.get('invoice_id'):
            invoice = self.env['account.invoice'].browse(int(line.get('invoice_id')))
            for inv_ln in invoice.invoice_line_ids:
                if inv_ln.split_type == 'split':
                    res['debit'] = 0.0
                    res['credit'] = 0.0
        return res

    @api.multi
    def action_print_customer_invoice(self):
        if self.cust_invoice_type == 'warranty' and not self.invoice_reference:
            data = self.env.ref('ars_after_sales.account_warranty_customer_invoices').with_context(doc=self, context={'warranty_cus': True}).report_action(
                self)
            return data
        else:
            if self.invoice_reference:
                data = self.env.ref('ars_after_sales.account_warranty_customer_invoices').with_context(doc=self.invoice_reference, context={
                    'warranty_cus': True}).report_action(
                    self)
                return data
            else:
                raise ValidationError("Please take a print out from the print 'Invoice'")

