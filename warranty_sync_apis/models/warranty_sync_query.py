from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db, _, exceptions
import re
from datetime import datetime, timedelta
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval

from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm
import logging

_logger = logging.getLogger(__name__)
import contextlib
# from odoo import models, fields, api, SUPERUSER_ID, _
# from odoo.exceptions import ValidationError
# from odoo.sql_db import sql_db
from datetime import datetime, timedelta
# DEFAULT_DATE_TIME_FORMATE = '%Y-%m-%d %H:%M:%S'



class WarrentySaleOrderLineInheritSync(models.Model):
    _inherit = "sale.order.line"

    child_db = fields.Char()
    child_warrenty_id_ref = fields.Char(string='Parent Reference')
    sync_to_parent = fields.Boolean(string="Synced to Parent", default=False)
    Warranty_sync_reject = fields.Boolean('')
    # warrant_split_line_ids = fields.One2many("warranty.split.line.item", "order_line_to_split_id", string="Line Items Split", ondelete='cascade')
    # Many/many field to link sale.order.line with warranty.split.line.item
    warranty_split_partner_ids = fields.Many2many(
        'warranty.split.line.item',  # Target model
        'sale_order_line_warranty_split_rel',  # Relation table name
        'sale_order_line_id',  # Column for this model's ID (sale.order.line)
        'warranty_split_line_item_id',  # Column for the target model's ID (warranty.split.line.item)
        string='Warranty Split Partners'
    )

    @api.model
    def fetch_data_orders_line(self, **kwargs):
        order_lines = self.env['sale.order.line'].browse(kwargs.get('selected_ids'))
        print(self.env.context, 'contextcontextcontext')
        context_lib = self.env.context
        data = []
        product_price = self.env['product.template']
        purchase_partner_price = self.env['product.supplierinfo']
        customers = self.env['res.partner'].search([('customer', '=', True)])  # Fetch all customers

        for line in order_lines:
            warranty_partner_id = line.customer_split
            partner = line.order_id.partner_id
            unit_price = 0
            purchase_partner_info = None
            if context_lib.get('default_split_price_by') == 'do_split_sale_price':
                unit_price = [v for product_pri in product_price.search_read([('id', '=', line.product_template_id.id)],['list_price']) for k, v in product_pri.items() if k == 'list_price']
            elif context_lib.get('default_split_price_by') == 'do_split_purchase_price':
                # purchase_partner_info = purchase_partner_price.search_read([('name', '=', warranty_partner_id.id)])
                pr_unit_price = product_price.search_read([('id', '=', line.product_template_id.id)], ['seller_ids'])
                purchase_partner_info = purchase_partner_price.search_read([('id', 'in', pr_unit_price[0].get('seller_ids'))], ['name', 'product_templ_id', 'price'])
                unit_price =[price for price in [v if v == line.price_unit else 0 for i in purchase_partner_info for k, v in i.items() if k == 'price'] if price!=0]
            print(unit_price)
            part1, perc1, part2, perc2, totals = self.calculate_percentage(unit_price[0], line.ars_warranty_price)
            print(part1, perc1, part2, perc2)
            split_data = [
                {
                    'sale_order_line': line.product_id.name,
                    'line_id': line.id,
                    'product_id': line.product_id.id,
                    'customer_id': warranty_partner_id.id if warranty_partner_id else False,
                    'customer_name': warranty_partner_id.name if warranty_partner_id else '',
                    'percentage': f"{perc1}%",
                    'subtotal': part1,
                    'tax': line.tax_id.name,
                    'tax_ids': [tax.id for tax in line.tax_id],
                    'taxable_amount': self.calculate_tax(part1, line.tax_id.name),
                    'customers_list': [{'id': c.id, 'name': c.name} for c in customers],  # Send as dicts
                    'category_id': line.category.id,
                    'totals' : totals
                },
                {
                    'sale_order_line': line.product_id.name,
                    'product_id': line.product_id.id,
                    'line_id': line.id,
                    'customer_id': partner.id if partner else False,
                    'customer_name': partner.name if partner else '',
                    'percentage': f"{perc2}%",
                    'subtotal': part2,
                    'tax': line.tax_id.name,
                    'tax_ids': [tax.id for tax in line.tax_id],
                    'taxable_amount': self.calculate_tax(part2, line.tax_id.name),
                    'customers_list': [{'id': c.id, 'name': c.name} for c in customers],  # Send as dicts
                    'category_id': self.env['order.line.category'].search([('name', '=', 'Customer')], limit=1).id,
                    'totals': totals
                },
            ]
            data.extend(split_data)

        return data

    @staticmethod
    def calculate_percentage(total, part1):
        part2 = total - part1  # Calculate the second part
        perc1 = round((part1 / total) * 100, 2)
        perc2 = round((part2 / total) * 100, 2)
        totals = total
        return round(part1,2), round(perc1,2), round(part2,2), round(perc2, 2), round(totals)

    @staticmethod
    def calculate_tax(base_amount, tax_string):
        """
        Calculate IGST or CGST & SGST based on the given tax string.

        :param base_amount: The taxable amount.
        :param tax_string: Tax type and percentage (e.g., "GST 18%" or "IGST 18%").
        :return: Dictionary with tax details.
        """
        # Extract tax type (GST or IGST) and percentage
        match = re.match(r'(\w+)\s*(\d+)%', tax_string)
        if not match:
            return {"Error": "Invalid tax format. Use 'GST 18%' or 'IGST 18%'"}

        tax_type, tax_rate = match.groups()
        tax_rate = float(tax_rate)

        if tax_type.upper() == "IGST":
            # Apply IGST
            igst_amount = (tax_rate * base_amount) / 100
            return round(igst_amount,2)

        elif tax_type.upper() == "GST":
            # Apply CGST & SGST (each half of GST)
            cgst_sgst_rate = tax_rate / 2
            cgst_amount = (cgst_sgst_rate * base_amount) / 100
            sgst_amount = (cgst_sgst_rate * base_amount) / 100
            return round(cgst_amount + sgst_amount, 2)
        else:
            return 0

    @api.model
    def create_data_orders_line(self, grouped_data):
        warranty_split_model = self.env['warranty.split.line.item']

        for sale_order_line, records in grouped_data.items():
            for record in records:
                vals = {
                    'order_line_to_split_id': record.get('line_id'),  # Link to sale.order.line
                    'product_id': record.get('product_id'),
                    'category': record.get('category_id'),
                    'discount': record.get('percentage'),  # Assuming 'percentage' is quantity
                    'customer_split_id': record.get('customer_id'),
                    'price_unit': record.get('subtotal'),
                    'tax_amount': record.get('taxable_amount'),
                    'tax_id': [(6, 0, [int(record.get('tax_ids'))])] if record.get('tax_ids') else False,
                    # Handling tax_id Many2many
                }
                # Create the record in warranty.split.line.item
                warranty_split_record = warranty_split_model.create(vals)
                sale_order_line = self.env['sale.order.line'].browse(record.get('line_id'))
                sale_order_line.write({
                    'warranty_split_partner_ids': [(4, warranty_split_record.id)]
                })

        return True

class WarrantySplitLineItmes(models.Model):
    _name = 'warranty.split.line.item'

    order_line_to_split_id = fields.Many2one("sale.order.line", string="Sale Order Line To Split", ondelete='cascade')
    product_id = fields.Many2one("product.product", string="Product")
    category = fields.Many2one('order.line.category', string="Category")
    quantity = fields.Float(string="Quantity")
    discount = fields.Float(string="Discount(%)")
    tax_id = fields.Many2many("account.tax", string="Taxes")
    price_unit = fields.Float(string="Unit Price")
    tax_amount = fields.Float(string="Tax Price")
    customer_split_id = fields.Many2one("res.partner", string="Customer")


class ArsSaleWarrantyAlignmentWizardInherit(models.TransientModel):
    _inherit = 'ars.sale.warranty.alignment.wizard'

    # split_percentage = fields.Float(string="Split Percentage", help="Enter the percentage to split the amount to customer")
    split_line_amount = fields.Selection([('do_split_sale_price', 'Split with sale price.'), ('do_split_purchase_price', 'Split with purchase price.')], string="Split Line Amount", default='do_split_sale_price' ,required=True)

    def set_alignment(self):
        res = super(ArsSaleWarrantyAlignmentWizardInherit, self).set_alignment()
        if self.split_line_amount == 'do_split_sale_price' or self.split_line_amount == 'do_split_purchase_price':
            print(self.split_line_amount, 'self.split_line_amount11')
            if self.split_line_amount == 'do_split_sale_price':
                for ol in self.warranty_id.order_lines:
                    if ol.category and ol.category.name.lower() == 'warranty':
                        if ol.apr_action == 'approved' and ol.ars_warranty_price != ol.price_unit:
                            list_price = self.env['product.template'].search([('id', '=', ol.product_template_id.id)], limit=1)
                            if list_price:
                                ol.price_unit = list_price.list_price
                            else:
                                raise ValidationError(_(f"{list_price.name} product doesn't existed."))

            filtered_order_line_ids = self.warranty_id.order_lines.filtered(lambda line: line.apr_action == 'approved' and line.ars_warranty_price != line.price_unit).ids
            if len(filtered_order_line_ids) >= 1:
                action = self.env.ref('warranty_sync_apis.action_warranty_split_line').read()[0]
                action.update({'domain': [('id', 'in', filtered_order_line_ids)],
                               'context': {
                                   'default_split_price_by': self.split_line_amount,  # Passing the split percentage
                                   'custom_flag': True,  # Example of adding a custom flag
                               },
                               })
                return action
        else:
            return res

class ArsSaleWarrentySync(models.Model):
    _inherit = "ars.sale.warranty"

    sync_warranty = fields.Boolean(string='Sync', default=False)
    child_warrenty_id_ref = fields.Char(string='Child ID Reference')
    child_warrenty_ref = fields.Char(string='Child Reference')
    # child_warrenty_ref_tree = fields.Char(string='Child Reference')
    child_db = fields.Char()
    order_id_ref = fields.Char(string='Child Service Document ref')
    # test_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)
    hide_sync = fields.Boolean(string='Sync', store=True, compute='_compute_hide_sync')
    # hide_sync = fields.Boolean(string='Sync', compute='hide_sync_status')
    sync_log_details_ids = fields.One2many('warrenty_sync_log', 'warrenty_record', string='Log')
    reject_reason = fields.Char('Rejected Reason')
    any_line_rejected = fields.Boolean(string="Any Line Rejected", compute='_compute_any_line_rejected')
    sync_count = fields.Integer('Count', default=0)
    Warranty_sync_reject = fields.Boolean('', compute='_compute_any_line_rejected')
    reject_date = fields.Date()
    hide_sync_lines = fields.Boolean(string="Hide Sync", default=False)
    claim_id = fields.Many2one('warranty.claim.config', 'Claim Type')
    # order_date = fields.Datetime(related='order_id.confirmation_date')
    order_date = fields.Date(store=True, compute='_compute_order_date')
    closure_date = fields.Date('Date of Closure')
    confirmation_date = fields.Date('Order Confirmation Date')
    model_name = fields.Char(string="Model", related='model_id.name', store=True)
    child_warrenty_ref_form = fields.Char()

    file_attachment_id = fields.Many2many('ir.attachment')
    # file_attachment = fields.Binary()

    @api.depends('order_id.confirmation_date')
    def _compute_order_date(self):
        for record in self:
            record.order_date = record.order_id.confirmation_date if record.order_id else ''


    @api.depends('order_lines.apr_action')
    def _compute_any_line_rejected(self):
        for record in self:
            record.any_line_rejected = any(line.apr_action in ['re_submit', 'reject']  for line in record.order_lines)

            record.Warranty_sync_reject = record.any_line_rejected

    @api.multi
    def action_approve_lines(self):
        """
        Approve all lines and update the warranty state to 'processed' if all lines are approved.
        """
        for line in self.order_lines:
            if line.apr_action == 'reject':
                raise ValidationError("You cannot approve, lines that have already been rejected.")


        if self.child_warrenty_ref:
            all_approved = True
            for line in self.order_lines:
                if line.apr_action != 'approved':
                    line.apr_action = 'approved'

            for line in self.order_lines:
                if line.apr_action != 'approved':
                    all_approved = False
                    break

            if all_approved:
                self.write({'state': 'processed', 'parent_sync': True})

        # if self.child_warrenty_ref:
        #     all_approved = True
        #     for line in self.order_lines:
        #         line.apr_action = 'approved'
        #         if line.apr_action != 'approved':
        #             all_approved = False
        #
        #     if all_approved:
        #         self.write({'state': 'processed', 'parent_sync': True})

    @api.multi
    def action_open_reject_wizard(self):
        for line in self.order_lines:
            if line.apr_action == 'approved':
                raise ValidationError("You cannot reject, lines that have already been approved.")

        return {
            'name': 'Reject Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'reject.lines.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('warranty_sync_apis.view_reject_lines_wizard_form').id,
            'target': 'new',
            'context': {'active_ids': self.ids},
        }

    @api.depends('state', 'sync_count', 'Warranty_sync_reject', 'order_lines')
    def _compute_hide_sync(self):
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('warranty_sync_apis.warrenty_company_type')

        for record in self:
            # Set hide_sync based on conditions
            if record.Warranty_sync_reject:
                if record.sync_count < 2:
                    record.hide_sync = False
                else:
                    record.hide_sync = True
            else:
                if child == 'is_child_company' and record.state == 'draft' and not record.sync_warranty:
                    if record.sync_count < 2:
                        record.hide_sync = False
                    else:
                        record.hide_sync = True
                else:
                    record.hide_sync = True


    @api.multi
    def call_warrenty_sync(self):
        for record in self:
            if record.reject_date and record.Warranty_sync_reject:
                reject_date_dt = fields.Date.from_string(record.reject_date)
                today_date = fields.Date.context_today(self)
                today_date_dt = fields.Date.from_string(today_date)

                days_difference = today_date_dt - reject_date_dt

                if days_difference.days > 2:
                    raise ValidationError(_("Unable to claim after 48hrs of Re-Submission."))


            record.hide_sync = True
            record.Warranty_sync_reject = False
            record.sync_warranty = False


            # Set apr_action to False for all order_lines
            all_lines_apr_action_false = True
            for line in record.order_lines:
                line.apr_action = False
                if line.apr_action:
                    all_lines_apr_action_false = False

            # If sync_warranty is False and all order_lines have apr_action = False, change state to 'draft'
            if not record.sync_warranty and all_lines_apr_action_false:
                record.state = 'draft'

            self.sync_warranty_to_parent(record)


    # @api.depends('state')
    # def hide_sync_status(self):
    #     param = self.env['ir.config_parameter'].sudo()
    #     child = param.get_param('warranty_sync_apis.warrenty_company_type')
    #     print("child====", child)
    #     for record in self:
    #         if child == 'is_child_company' and record.state == 'draft' and not record.sync_warranty:
    #             record.hide_sync = False
    #         else:
    #             record.hide_sync = True

       # ////////////


    # @api.depends('state')
    # def _compute_css(self):state
    #     for record in self:
    #         print('state------------called',record.state)
    #         if record.state == 'done':
    #             record.test_css = '<style>.o_form_button_edit {display: none !important;}</style>'
    #         else:
    #             record.test_css = False
    # update False value to sync_warranty if no value is passed

    @api.multi
    def write(self, vals):
        if 'sync_warranty' not in vals:
            vals['sync_warranty'] = False
        res = super(ArsSaleWarrentySync, self).write(vals)
        return res

    @api.model
    def _cron_warernty_sync_to_parent(self):
        # Find one record that needs to be synced
        record_to_sync = self.env['ars.sale.warranty'].search([('sync_warranty', '=', False), ('state', '=', 'draft')],
                                                              limit=1)

        if record_to_sync:
            record_to_sync.call_warrenty_sync()

    # @api.multi
    # def write(self, vals):
    #     res = super(ArsSaleWarrentySync, self).write(vals)
    #
    #     # Check if sync_warranty is set to True in vals
    #     if 'sync_warranty' in vals and vals.get('sync_warranty'):
    #         # Ensure state is moved to draft when sync_warranty is True
    #         self.sudo().write({'state': 'draft'})
    #
    #     return res

    # @api.model
    # def _cron_warernty_sync_to_parent(self):
    #     call = self.env['ars.sale.warranty'].sync_warranty_to_parent(False)

    # /////////////////////////


    # (query warranty)

    @api.model
    def sync_warranty_to_parent(self, current_warrenty_record):
        """ Sync warranty record to parent DB using raw SQL queries """
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('warranty_sync_apis.warrenty_company_type')
        print(f"child: {child}")
        check_warrenty_sync = param.get_param('warranty_sync_apis.enable_sync_to_parent')
        print(f"check_warrenty_sync: {check_warrenty_sync}")

        if child == 'is_child_company' and check_warrenty_sync == 'yes':
            print(f"Rchild: {child}")
            database = param.get_param('warranty_sync_apis.warrenty_sync_db')
            print(f"database: {database}")
            child_database = self._cr.dbname
            print(f"child_database: {child_database}")
            db = sql_db.db_connect(f"{database}")
            print(f"db: {db}")
            print(f"database: {database}")

            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                print(f"env: {env}")
                warrenty_records = False

                if current_warrenty_record:
                    warrenty_records = [current_warrenty_record]  # Handle this record only
                    print("111111111", current_warrenty_record)
                else:
                    # SQL query to fetch records where sync_warranty is False and state is draft
                    query = """
                                    SELECT * FROM ars_sale_warranty 
                                    WHERE sync_warranty = FALSE AND state = 'draft' 
                                    ORDER BY id ASC
                                    LIMIT 1
                                """
                    cr.execute(query)
                    warrenty_records = cr.fetchall()
                    print("==1==", warrenty_records)

                # warrenty_records = [current_warrenty_record] if current_warrenty_record else self.env[
                #     'ars.sale.warranty'].sudo().search([('sync_warranty', '=', False), ('state', '=', 'draft')], order='id asc')
                # print(f"warrenty_records: {warrenty_records}")

                for rec in warrenty_records:
                    print("rec=====", rec)
                    # if rec.state != 'draft':
                    #     print(f"Record {rec.id} is not in draft state; skipping sync.")
                    #     continue
                    stop_sync = False
                    failure_message = None

                    sync_log_dict = {
                        'warrenty_record': rec.id,
                        'warrenty_sequence': rec.name,
                        'status': 200,
                    }

                    print("33333", sync_log_dict)

                    # Check if the warranty already exists in parent DB
                    cr.execute("""
                                    SELECT id FROM ars_sale_warranty 
                                    WHERE child_warrenty_id_ref = %s AND child_db = %s 
                                    ORDER BY id DESC
                                    LIMIT 1
                                """, (str(rec.id), child_database))
                    exist_in_parent = cr.fetchone()
                    print(exist_in_parent,'exist_in_parent')

                    if not exist_in_parent:
                        customer = False
                        reg_record = False
                        country = False
                        model_id = False
                        # # if exist_in_parent:
                        print("company===", rec.company_id.partner_id.mobile)
                        if rec.partner_id:
                            # customer
                            customer = env['res.partner'].sudo().search([('name', '=', rec.partner_id.name)],
                                                                        order='id desc', limit=1)
                            if not customer:
                                data_dict = {
                                    # 'customer_code':rec.partner_id.name if rec.partner_id.name else '',
                                    # 'customer_code':rec.partner_id.customer_code if rec.partner_id.customer_code else '',
                                    'name': rec.partner_id.name if rec.partner_id else '',
                                    'mobile': rec.partner_id.mobile if rec.partner_id.mobile else '',
                                    'email': rec.partner_id.email if rec.partner_id.email else '',
                                    'street': rec.partner_id.street if rec.partner_id.street else '',
                                    'street2': rec.partner_id.street2 if rec.partner_id.street2 else '',
                                    'city': rec.partner_id.city if rec.partner_id.city else '',
                                    'state_id': country.state if country else False,
                                    'zip': rec.partner_id.zip if rec.partner_id.zip else '',
                                    'country_id': country if country else False,
                                    'pan_no': rec.partner_id.pan_no if rec.partner_id.pan_no else '',
                                    'vat': rec.partner_id.vat if rec.partner_id.vat else '',
                                    'function': rec.partner_id.function if rec.partner_id.function else '',
                                    'phone': rec.partner_id.phone if rec.partner_id.phone else '',
                                    'website': rec.partner_id.website if rec.partner_id.website else '',
                                    'lang': rec.partner_id.lang if rec.partner_id.lang else '',
                                }
                                customer = env['res.partner'].sudo().create(data_dict)
                                sync_log_dict[
                                    'sync_message'] = 'Customer is not present in Parent.New Customer Created.'
                                # sync_log_dict['payload'] = {'warrenty_sequence': rec.name, 'db': child_database,'values': data_dict}
                                sync_log_dict['payload'] = {'Customer': rec.partner_id.name,'values': data_dict}
                                sync_log_dict['sequence'] = {rec.name, }
                                record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True

                                failure_message = sync_log_dict
                                if stop_sync:
                                    # Format sync_log_dict to a readable string
                                    formatted_message = (
                                        f"Log: \n\nWarranty Sequence: {failure_message.get('sequence')} \n Customer: {failure_message.get('payload')}"
                                        f"\n Sync Message:{failure_message.get('sync_message')}")
                                    raise ValidationError(formatted_message)
                                break

                        # model_id
                        if rec.model_id:
                            model_id = env['product.product'].sudo().search(
                                [('name', '=', rec.model_id.name), ('default_code', '=', rec.model_id.default_code)],
                                order='id desc', limit=1)
                            if not model_id:
                                data_dict = {
                                    'default_code': rec.model_id.default_code if rec.model_id.default_code else '',
                                    'active': rec.model_id.active if rec.model_id.active else '',
                                    'product_tmpl_id': rec.model_id.product_tmpl_id.id if rec.model_id.product_tmpl_id else False,
                                    'barcode': rec.model_id.barcode if rec.model_id.barcode else False,
                                    'volume': rec.model_id.volume if rec.model_id.volume else '',
                                    'weight': rec.model_id.weight if rec.model_id.weight else '',
                                    'activity_date_deadline': rec.model_id.activity_date_deadline if rec.model_id.activity_date_deadline else '',
                                }
                                msg = 'Failure. Model ID is not present in Parent.'
                                # if not line_data.product_id.default_code:
                                #     msg = 'Failure. Model code is not set.'
                                sync_log_dict['sync_message'] = msg
                                # sync_log_dict['payload'] = {'warrenty_sequence': rec.name, 'db': child_database,
                                #                             'values': data_dict}
                                sync_log_dict['payload'] = {'Model':rec.model_id.name,'values': data_dict}
                                sync_log_dict['sequence'] = {rec.name, }
                                record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True

                                failure_message = sync_log_dict
                                if stop_sync:
                                    # Format sync_log_dict to a readable string
                                    formatted_message = (
                                        f"Log: \n\nWarranty Sequence: {failure_message.get('sequence')} \n Model: {failure_message.get('payload')}"
                                        f"\n Sync Message:{failure_message.get('sync_message')}")
                                    raise ValidationError(formatted_message)

                                break

                        # Reg No
                        if rec.regn_no:
                            reg_record = env['fleet.vehicle'].sudo().search(
                                # [('active', '=', rec.regn_no.active)], order='id desc',
                                [('vin_sn', '=', rec.regn_no.vin_sn)], order='id desc',
                                # [('name', '=', rec.regn_no.name), ('active', '=', rec.regn_no.active)], order='id desc',
                                limit=1)
                            if not reg_record:
                                data_dict = {
                                    'name': rec.regn_no.name if rec.regn_no.name else '',
                                    'license_plate': rec.regn_no.license_plate if rec.regn_no.license_plate else '',
                                    'active': rec.regn_no.active if rec.regn_no.active else False,
                                    'vin_sn': rec.regn_no.vin_sn if rec.regn_no.vin_sn else '',
                                    'location': rec.regn_no.location if rec.regn_no.location else '',
                                    'lot_id': rec.regn_no.lot_id if rec.regn_no.lot_id else False,
                                    'vehicle_status': rec.regn_no.vehicle_status if rec.regn_no.vehicle_status else '',
                                    # 'production_year':rec.regn_no.production_year if rec.regn_no.production_year else '',
                                    'model_month': rec.regn_no.model_month if rec.regn_no.model_month else '',
                                    'engine_code': rec.regn_no.engine_code if rec.regn_no.engine_code else '',
                                    'engine_number': rec.regn_no.engine_number if rec.regn_no.engine_number else '',
                                    'key_serial_number': rec.regn_no.key_serial_number if rec.regn_no.key_serial_number else '',
                                    'model_id': rec.regn_no.model_id if rec.regn_no.model_id else False,
                                    # 'driver_id':rec.regn_no.activity_date_deadline if rec.regn_no.activity_date_deadline else '',
                                }
                                sync_log_dict['sync_message'] = 'Failure. REG No is not present in Parent.'
                                # sync_log_dict['payload'] = {'warrenty_sequence': rec.name, 'db': child_database, 'values': data_dict}
                                sync_log_dict['payload'] = {'Reg No':rec.regn_no.name, 'values': data_dict}
                                sync_log_dict['sequence'] = {rec.name, }
                                record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True

                                failure_message = sync_log_dict
                                if stop_sync:
                                    # Format sync_log_dict to a readable string
                                    formatted_message = (
                                        f"Log: \n\nWarranty Sequence: {failure_message.get('sequence')} \n Reg NO: {failure_message.get('payload')}"
                                        f"\n Sync Message:{failure_message.get('sync_message')}")
                                    raise ValidationError(formatted_message)

                                break

                        if env.registry.get('warranty.claim.config'):
                            k = env['warranty.claim.config'].sudo().search(
                                [('warranty_claim_list', '=', rec.claim_id.warranty_claim_list)], limit=1).id
                        else:
                            query = """
                                SELECT id FROM warranty_claim_config 
                                WHERE warranty_claim_list = %s 
                                LIMIT 1
                            """
                            params = (rec.claim_id.warranty_claim_list,)

                            env.cr.execute(query, params)
                            result = env.cr.fetchone()
                            k = result[0] if result else None

                        attachments = []
                        attachment_Obj = env['ir.attachment'].sudo()
                        for doc in rec.file_attachment_id:
                            attachment = attachment_Obj.create({
                                'name': doc.name,
                                'datas': doc.datas,
                                'datas_fname': doc.name,
                                'res_model': rec._name,
                                'res_id': rec.id,
                                'type': 'binary',
                            })
                            attachments.append(attachment.id)

                        order_line_list = []
                        # Preparing warrenty data
                        # seq = env['ir.sequence'].sudo().search([('code','=','sale.order'),('active','=',True)],limit=1)
                        # code = f"{seq.prefix}" + f"{seq.number_next_actual}"
                        # print("seq===================",seq,code)

                        data = {
                            'name': rec.name,
                            'partner_id': customer.id if customer else False,
                            'regn_no': reg_record.id if reg_record else False,
                            'model_id': model_id.id if model_id else False,
                            'vin_no': rec.vin_no if rec.vin_no else False,
                            'order_id_ref': rec.order_id.name if rec.order_id else '',
                            'child_warrenty_id_ref': rec.id,
                            'child_db': child_database,
                            'child_warrenty_ref': f"{rec.order_id.company_id.name}-{rec.name}" if rec.order_id.company_id else f"{rec.name}",
                            'child_warrenty_ref_tree': f"{rec.order_id.company_id.name}" if rec.order_id.company_id else f"{rec.order_id.company_id}",
                            'confirmation_date': rec.order_id.confirmation_date,
                            'claim_id' : k,
                            'order_date' : rec.order_date,
                            # 'file_attachment': rec.file_attachment,
                            'file_attachment_id': [(6, 0, attachments)],
                        }

                        print('file_attachment_id', data)
                        # preparing order_lines data
                        for line_data in rec.order_lines:
                            print("line_data=====", line_data)
                            product_data = env['product.product'].sudo().search(
                                [('name', '=', line_data.product_id.name),
                                 ('default_code', '=', line_data.product_id.default_code)], order='id desc', limit=1)
                            product_uom = env['product.uom'].sudo().search([('name', '=', line_data.product_uom.name)],
                                                                           order='id desc', limit=1)


                            if not product_data or not line_data.product_id.default_code:
                                data_dict = {
                                    'default_code': line_data.product_id.default_code if line_data.product_id.default_code else '',
                                    'active': line_data.product_id.active if line_data.product_id.active else '',
                                    'product_tmpl_id': line_data.product_id.product_tmpl_id.id if line_data.product_id.product_tmpl_id else False,
                                    'barcode': line_data.product_id.barcode if line_data.product_id.barcode else False,
                                    'volume': line_data.product_id.volume if line_data.product_id.volume else 0,
                                    'weight': line_data.product_id.weight if line_data.product_id.weight else 0,
                                    'activity_date_deadline': line_data.product_id.activity_date_deadline if line_data.product_id.activity_date_deadline else None,
                                }
                                msg = 'Failure. Product is not present in Parent.'
                                if not line_data.product_id.default_code:
                                    msg = 'Failure. Product code is not set.'
                                sync_log_dict['sync_message'] = msg
                                # sync_log_dict['payload'] = {'warrenty_sequence': rec.name,'db': child_database,
                                #                             'values': data_dict}
                                sync_log_dict['payload'] = {'Product':line_data.product_id.name, 'values':data_dict}
                                sync_log_dict['sequence'] = {rec.name,}
                                record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True

                                failure_message =sync_log_dict
                                if stop_sync:
                                    # Format sync_log_dict to a readable string
                                    formatted_message = (f"Log: \n\nWarranty Sequence: {failure_message.get('sequence')} \n Product: {failure_message.get('payload')}"
                                                         f"\n Sync Message:{failure_message.get('sync_message')}")
                                    raise ValidationError(formatted_message)
                                break

                            if not product_uom and line_data.product_uom.name:
                                data_dict = {
                                    'name': line_data.product_uom.name if line_data.product_uom.name else '',
                                    'factor': line_data.product_uom.factor.id if line_data.product_uom.factor else False,
                                    'rounding': line_data.product_uom.rounding if line_data.product_uom.rounding else False,
                                    'active': line_data.product_uom.active if line_data.product_uom.active else False,
                                    'uom_type': line_data.product_uom.uom_type if line_data.product_uom.uom_type else False,
                                }
                                sync_log_dict['sync_message'] = 'Failure.Product unit is not present in Parent.'
                                # sync_log_dict['payload'] = {'warrenty_sequence': rec.name, 'db': child_database,
                                #                             'values': data_dict}
                                sync_log_dict['payload'] = {'product': line_data.product_uom.name,'values': data_dict}
                                sync_log_dict['sequence'] = {rec.name}
                                record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True

                                failure_message = sync_log_dict
                                if stop_sync:
                                    # Format sync_log_dict to a readable string
                                    formatted_message = (
                                        f"Log: \n\nWarranty Sequence: {failure_message.get('sequence')} \n Product: {failure_message.get('payload')}"
                                        f"\n Sync Message:{failure_message.get('sync_message')}")
                                    raise ValidationError(formatted_message)
                                break

                            parent_tax_data = False
                            if line_data.tax_id:
                                current_child_tax_data = self.env['account.tax'].sudo().search(
                                    [('id', 'in', line_data.tax_id.ids)])
                                print("env.user=====", env.user)
                                print("env.company_id.id=====", env.user.company_id,
                                      current_child_tax_data.mapped('name'))
                                parent_company = rec.order_id.company_id
                                print("parent_company====", parent_company)
                                parent_tax_data = env['account.tax'].sudo().search(
                                    [('name', 'in', current_child_tax_data.mapped('name')),
                                     ('type_tax_use', '=', 'sale')])
                                print("parent_tax_data=====", parent_tax_data)
                                if not parent_tax_data:
                                    data_dict = {
                                        'name': current_child_tax_data.name if current_child_tax_data.name else '',
                                        'type_tax_use': current_child_tax_data.type_tax_use if current_child_tax_data.type_tax_use else False,
                                        'company_id': parent_company.id if parent_company else False,
                                        'active': True,
                                        'description': current_child_tax_data.name if current_child_tax_data.name else '',
                                        'python_compute': current_child_tax_data.mapped(
                                            'python_applicable') if current_child_tax_data else False,
                                        'python_applicable': current_child_tax_data.name if current_child_tax_data.name else False,
                                    }
                                    sync_log_dict['sync_message'] = 'Failure.Tax is not present in Parent.'
                                    # sync_log_dict['payload'] = {'warrenty_sequence': rec.name, 'db': child_database,
                                    #                             'values': data_dict}
                                    sync_log_dict['payload'] = {'values': data_dict}
                                    sync_log_dict['sequence'] = {rec.name}
                                    record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                                    stop_sync = True

                                    failure_message = sync_log_dict
                                    if stop_sync:
                                        # Format sync_log_dict to a readable string
                                        formatted_message = (
                                            f"Log: \n\nWarranty Sequence: {failure_message.get('sequence')} \n Product: {failure_message.get('payload')}"
                                            f"\n Sync Message:{failure_message.get('sync_message')}")
                                        raise ValidationError(formatted_message)
                                    break
                            # if stop_sync:
                            #     # Raise a validation error with the failure message
                            #     raise ValidationError(sync_log_dict)

                            one2many_data = {
                                'name': line_data.name,
                                'product_catalog_id': line_data.product_catalog_id.id if line_data.product_catalog_id.id else False,
                                'product_id': product_data.id if product_data else line_data.product_id.id,
                                # 'order_id':rec.id,
                                'product_uom_qty': line_data.product_uom_qty if line_data.product_uom_qty else False,
                                'product_uom': product_uom.id if product_uom else line_data.product_uom.id,
                                'ars_std_price': line_data.price_unit if line_data.price_unit else 0,
                                # 'ars_std_price': line_data.ars_std_price if line_data.ars_std_price else 0,
                                'ars_warranty_price': line_data.ars_warranty_price if line_data.ars_warranty_price else 0,
                                'discount': line_data.discount if line_data.discount else 0,
                                'wrn_price_subtotal': line_data.wrn_price_subtotal if line_data.wrn_price_subtotal else 0,
                                'apr_action': line_data.apr_action if line_data.apr_action else False,
                                'child_warrenty_id_ref': line_data.id,
                                'child_db': child_database,
                                # 'tax_id': [(6, 0, line_data.tax_id.ids)] if line_data.tax_id else [(6, 0, [])]
                            }
                            if line_data.tax_id:
                                one2many_data['tax_id'] = [(6, 0, parent_tax_data.ids)]
                            else:
                                one2many_data['tax_id'] = [(6, 0, [])]
                            order_line_list.append((0, 0, one2many_data))
                        if order_line_list:
                            data['order_lines'] = order_line_list
                            print('order lines to update', order_line_list, data['order_lines'])
                            print('order lines to000', data['order_lines'])

                        print("----data prepared-------", data)
                        print("----stop sync-------", stop_sync)
                        """ Insert new records """

                        if data and not stop_sync:
                            print("--------------------Create----------------------------")
                            new_recordds = env['ars.sale.warranty'].sudo().create(data)
                            print("new_recordds===", new_recordds)
                            # seq.number_next_actual = seq.number_next_actual+1
                            sync_log_dict['sync_message'] = 'Success.Warranty synced to Parent.'
                            sync_log_dict['payload'] = {'warrenty_sequence': rec.name, 'db': child_database,
                                                        'values': data}

                            print("sync_log_dict====", sync_log_dict)
                            if new_recordds:
                                rec.sudo().write({'sync_warranty': True,
                                                  'sync_count': rec.sync_count + 1,
                                                  # 'claim_id' : rec.claim_id.warranty_claim_list,
                                                  })
                            record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                            print("record_set===", record_set)
                            print("Created new records-----", new_recordds)
                            sync_successful = True

                    elif rec.Warranty_sync_reject <= 1:

                        attachments = []
                        attachment_Obj = env['ir.attachment'].sudo()
                        for doc in rec.file_attachment_id:
                            attachment = attachment_Obj.create({
                                'name': doc.name,
                                'datas': doc.datas,
                                'datas_fname': doc.name,
                                'res_model': rec._name,
                                'res_id': rec.id,
                                'type': 'binary',
                            })
                            attachments.append(attachment.id)

                        exist_in_parent = env['ars.sale.warranty'].sudo().search(
                            [('child_warrenty_id_ref', '=', str(rec.id)),
                             ('child_db', '=', child_database)],
                            limit=1, order='id desc')

                        if exist_in_parent.order_lines:
                            exist_in_parent.order_lines.sudo().unlink()

                            order_line_list = []
                            for line_data in rec.order_lines:
                                product_data = env['product.product'].sudo().search(
                                    [('name', '=', line_data.product_id.name),
                                     ('default_code', '=', line_data.product_id.default_code)],
                                    order='id desc', limit=1
                                )
                                product_uom = env['product.uom'].sudo().search(
                                    [('name', '=', line_data.product_uom.name)],
                                    order='id desc', limit=1
                                )

                                print(f"Child line product: {line_data.product_id.id} - {line_data.product_id.name}")
                                print(f"Parent order lines: {exist_in_parent.order_lines.mapped('product_id.id')}")

                                # Search for matching parent order line by comparing product IDs
                                parent_order_line = exist_in_parent.order_lines.filtered(
                                    lambda l: l.product_id.id == line_data.product_id.id and
                                              l.product_uom_qty == line_data.product_uom_qty and
                                              l.product_uom.id == line_data.product_uom.id
                                )

                                if parent_order_line:
                                    print(f"Updating parent order line {parent_order_line} with child line {line_data.id}")
                                    write_status = parent_order_line[0].sudo().write({
                                        'product_uom_qty': line_data.product_uom_qty if line_data.product_uom_qty else 0,
                                        'ars_std_price': line_data.price_unit if line_data.price_unit else 0,
                                        'ars_warranty_price': line_data.ars_warranty_price if line_data.ars_warranty_price else 0,
                                        'discount': line_data.discount if line_data.discount else 0,
                                        'wrn_price_subtotal': line_data.wrn_price_subtotal if line_data.wrn_price_subtotal else 0,
                                        'apr_action': False,
                                        # 'tax_id': [(6, 0, line_data.tax_id.ids)] if line_data.tax_id else [(6, 0, [])]
                                    })
                                    # order_line_list.append((0, 0, write_status))
                                    print(f"New order line model prepared for parent sync: {write_status}")

                                else:
                                    one2many_data = {
                                        'name': line_data.name,
                                        'product_catalog_id': line_data.product_catalog_id.id if line_data.product_catalog_id.id else False,
                                        'product_id': product_data.id if product_data else line_data.product_id.id,
                                        'product_uom_qty': line_data.product_uom_qty if line_data.product_uom_qty else False,
                                        'product_uom': product_uom.id if product_uom else line_data.product_uom.id,
                                        'ars_std_price': line_data.price_unit if line_data.price_unit else 0,
                                        'ars_warranty_price': line_data.ars_warranty_price if line_data.ars_warranty_price else 0,
                                        'discount': line_data.discount if line_data.discount else 0,
                                        'wrn_price_subtotal': line_data.wrn_price_subtotal if line_data.wrn_price_subtotal else 0,
                                        'apr_action': line_data.apr_action if line_data.apr_action else False,
                                        'child_warrenty_id_ref': line_data.id,
                                        'child_db': child_database,
                                        # 'tax_id': [(6, 0, line_data.tax_id.ids)] if line_data.tax_id else [(6, 0, [])]
                                    }
                                    order_line_list.append((0, 0, one2many_data))
                                    print(f"New order line prepared for parent sync: {one2many_data}")

                                    # If there are new order lines to add to the parent, write them

                            if order_line_list:
                                write_status = exist_in_parent.sudo().write({'order_lines': order_line_list,
                                                                             'file_attachment_id': [(6, 0, attachments)],
                                                                             })

                                if write_status:
                                    print(f"New order lines synced to parent.", order_line_list)
                                    sync_log_dict['sync_message'] = 'Success.Warranty synced to Parent.'
                                    sync_log_dict['payload'] = {'warrenty_sequence': rec.name, 'db': child_database,
                                                                'values': order_line_list}
                                    self.env['warrenty_sync_log'].sudo().create(sync_log_dict)

                                    print(f"Sync log created: {sync_log_dict}")

                                    # Update child warranty record
                                    rec.sudo().write({'sync_warranty': True, 'sync_count': rec.sync_count + 1})

                            else:
                                print("Record already present in parent DB.")
                                sync_log_dict['status'] = 500
                                sync_log_dict['sync_message'] = 'Failure.Record already synced to parent.'
                                sync_log_dict['payload'] = {'warrenty_sequence': rec.name, 'db': child_database, }
                                record_set = self.env['warrenty_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True
                                print("log updated0----", record_set)

                # if not sync_successful:
                #     raise ValidationError("The record(s) did not sync to the parent database.")