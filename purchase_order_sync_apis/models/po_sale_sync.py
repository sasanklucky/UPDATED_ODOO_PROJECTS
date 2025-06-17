from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db, _
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm


class StockBackorderConfirmationInherit(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process_cancel_backorder(self):
        # check if parent company has back order against the purchase record
        # check_val = self.check_parent_back_order(self)
        # print("check_val===",check_val)
        # if check_val:
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('purchase_order_sync_apis.po_company_type')
        database = param.get_param('purchase_order_sync_apis.parent_db_name')
        current_picking_id = self._context.get('current_picking_id')
        print("current_picking_id====", current_picking_id, self._context)
        if child == 'is_child_company' and database and current_picking_id:
            print("database=====", database, child)
            db = sql_db.db_connect(f"{database}")
            child_database = self._cr.dbname
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                # fetch stock_picking ref
                pick_id = self.env['stock.picking'].sudo().search([('id', '=', int(current_picking_id))],
                                                                  order='id desc', limit=1).origin
                print("pick_id====", pick_id)
                purchase_id = self.env['purchase.order'].sudo().search([('name', '=', pick_id)], order='id desc',
                                                                       limit=1)
                print("purchase_id=====", purchase_id)
                if purchase_id:
                    sale_in_parent = env['sale.order'].sudo().search(
                        [('child_po_id_ref', '=', str(purchase_id.id)), ('child_db', '=', child_database)])
                    print("sale_in_parent=====", sale_in_parent)
                    if sale_in_parent:
                        picking_parent = env['stock.picking'].sudo().search(
                            [('sale_id', '=', sale_in_parent.id), ('state', 'not in', ['done', 'cancel'])],
                            order='id desc', limit=1)
                        print("picking_parent=====", picking_parent)
                        if picking_parent:
                            raise UserError(
                                _('You cannot Validate as back order has been created in parent.Create a back order to avoid it.'))
        # return
        self._process(cancel_backorder=True)

    # def check_parent_back_order(self):
    #     print("inside check back order---")
    #                 return True


class PurchaseOrderLineInheritSync(models.Model):
    _inherit = "purchase.order.line"
    _description = "Purchase Order Line"

    parent_db = fields.Char()
    parent_sale_id_ref = fields.Char(string='Parent Reference')


class PurchaseOrderInheritSync(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    sync_po = fields.Boolean(string='Sync')
    parent_sale_id_ref = fields.Char(string='Parent Reference')
    child_db = fields.Char()
    parent_db = fields.Char()
    test_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)
    hide_sync = fields.Boolean(string='Sync', compute='hide_sync_status')
    sync_log_details_ids = fields.One2many('po_sync_log', 'purchase_record', string='Log')

    @api.depends('state')
    def hide_sync_status(self):
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('purchase_order_sync_apis.po_company_type')
        print("child====", child)
        for record in self:
            if child == 'is_child_company' and record.state == 'purchase':
                record.hide_sync = False
            else:
                record.hide_sync = True

    @api.multi
    def call_po_sync(self):
        self.sync_po_to_parent(self)

    @api.depends('state')
    def _compute_css(self):
        for record in self:
            print('state------------called', record.state)
            if record.state == 'done':
                record.test_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                record.test_css = False

    # @api.multi
    # def unlink(self):
    #     for record in self:
    #         param = self.env['ir.config_parameter'].sudo()
    #         database = param.get_param('purchase_order_sync_apis.parent_db_name')
    #         self.unlink_so_from_parent(database,record.id)
    #     return super(PurchaseOrderInheritSync, self).unlink()

    # update False value to sync_po if no value is passed
    @api.multi
    def write(self, vals):
        if 'sync_po' not in vals:
            vals['sync_po'] = False
        res = super(PurchaseOrderInheritSync, self).write(vals)
        return res

    # Delete Sale order from parent if purchase order is deleted from child
    # @api.multi
    # def unlink_so_from_parent(self,parent_db_name,child_id):
    #     # unlink po from parent db
    #     try:
    #         param = self.env['ir.config_parameter'].sudo()
    #         child = param.get_param('purchase_order_sync_apis.po_company_type')
    #         check_enable_po_sync = param.get_param('purchase_order_sync_apis.enable_po_sync')
    #         if child == 'is_child_company' and check_enable_po_sync == 'yes':
    #             # print("database=====",parent_db_name)
    #             db = sql_db.db_connect(f"{parent_db_name}")
    #             # child_database = param.get_param('purchase_order_sync_apis.child_parent_db_name')
    #             child_database = self._cr.dbname
    #             with contextlib.closing(db.cursor()) as cr:
    #                 cr.autocommit(True)
    #                 env = api.Environment(cr, SUPERUSER_ID, {})
    #                 exist_in_parent = env['sale.order'].sudo().search([('child_po_id_ref','=',str(child_id)),('child_db','=',child_database)])
    #                 print("exist_in_parent=====",exist_in_parent)
    #                 if exist_in_parent:
    #                     exist_in_parent.unlink()
    #     except Exception as e:
    #         raise ValidationError(e)

    @api.model
    def _cron_sync_po_to_so_in_parent(self):
        call = self.env['purchase.order'].sync_po_to_parent(False)

    @api.model
    def sync_po_to_parent(self, current_po_record):
        """ connect to parent db set up in general settings """
        # try:
        param = self.env['ir.config_parameter'].sudo()
        print("param..........",param)
        child = param.get_param('purchase_order_sync_apis.po_company_type')
        check_po_sync = param.get_param('purchase_order_sync_apis.enable_po_sync')
        print("child---", child, check_po_sync)
        if child == 'is_child_company' and check_po_sync == 'yes':
            database = param.get_param('purchase_order_sync_apis.parent_db_name')
            print("database=====", database)
            db = sql_db.db_connect(f"{database}")
            # child_database = param.get_param('purchase_order_sync_apis.child_parent_db_name')
            child_database = self._cr.dbname
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                # import pdb
                # pdb.set_trace()
                # getting child data as sellf represent child db env
                po_records = False
                if current_po_record:
                    po_records = current_po_record
                else:
                    po_records = self.env['purchase.order'].sudo().search(
                        [('sync_po', '=', False), ('state', '=', 'purchase')], order='id asc')
                    print("==1==", po_records)

                # looped child po datas
                for rec in po_records:
                    print("rec=====", rec)
                    stop_sync = False
                    sync_log_dict = {
                        'purchase_record': rec.id,
                        'purchase_sequence': rec.name,
                        'status': 200,
                    }
                    # parent record env
                    sale_quotation = env['sale.order'].sudo()
                    exist_in_parent = sale_quotation.search(
                        [('child_po_id_ref', '=', str(rec.id)), ('child_db', '=', child_database)],
                        limit=1,
                        order='id desc')
                    # company = env['res.company'].sudo().search([('dealer_code','=',rec.company_id.dealer_code)],order='id desc',limit=1)
                    print("purchase order=====", exist_in_parent)
                    if not exist_in_parent:
                        customer = False
                        payment_term_id = False
                        country = False
                        currency = False
                        fiscal_position_id = False
                        picking_type_id = False
                        payment_term_id = False
                        incoterm_id = False
                        requisition_id = False
                        # # if exist_in_parent:
                        print("company===", rec.company_id.partner_id.mobile)
                        if rec.company_id.partner_id:
                            customer = env['res.partner'].sudo().search(
                                [('is_dealer', '=', True), ('dealer_code', '=', rec.company_id.partner_id.dealer_code)],
                                order='id desc', limit=1)

                            if not customer:
                                data_dict = {
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
                                    # 'title':title.id if title else False,
                                    'lang': rec.partner_id.lang if rec.partner_id.lang else '',
                                }
                                # customer = env['res.partner'].sudo().create(data_dict)
                                sync_log_dict['sync_message'] = 'Failure.Customer is not present in Parent.'
                                sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database,
                                                            'values': data_dict}
                                record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True
                                break

                        print("customer===", customer)
                        if rec.fiscal_position_id:
                            fiscal_position_id = env['account.fiscal.position'].sudo().search(
                                [('name', '=', rec.fiscal_position_id.name)], order='id desc', limit=1)
                            if not fiscal_position_id:
                                data_dict = {
                                    'name': rec.fiscal_position_id.name if rec.fiscal_position_id else '',
                                    'active': rec.fiscal_position_id.active,
                                    'company_id': rec.company_id.id if rec.company_id else False,
                                    'currency_id': currency.id if currency else False,
                                    'country_id': country.id if country else False,
                                    'auto_apply': rec.fiscal_position_id.auto_apply,
                                    'vat_required': rec.fiscal_position_id.vat_required,
                                    'zip_from': rec.fiscal_position_id.zip_from,
                                    'zip_to': rec.fiscal_position_id.zip_to,
                                    'note': rec.fiscal_position_id.note,
                                }
                                # fiscal_position_id = env['account.fiscal.position'].sudo().create(data_dict)
                                sync_log_dict['sync_message'] = 'Failure.Fiscal position is not present in Parent.'
                                sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database,
                                                            'values': data_dict}
                                record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True
                                break

                        # payment terms
                        if rec.payment_term_id:
                            payment_term_id = env['account.payment.term'].sudo().search(
                                [('name', '=', rec.payment_term_id.name),
                                 ('company_id', '=', rec.payment_term_id.company_id.id),
                                 ('active', '=', rec.payment_term_id.active)], order='id desc', limit=1)
                            if not payment_term_id:
                                data_dict = {
                                    'name': rec.payment_term_id.name if rec.payment_term_id else '',
                                    'active': rec.payment_term_id.active if rec.payment_term_id else False,
                                    'note': rec.payment_term_id.note if rec.payment_term_id.note else '',
                                    'company_id': rec.payment_term_id.company_id.id if rec.payment_term_id.company_id else rec.company_id.id,
                                    'sequence': rec.payment_term_id.sequence.id if rec.payment_term_id.sequence else False,
                                }
                                # payment_term_id = env['account.payment.term'].sudo().create(data_dict)
                                sync_log_dict['sync_message'] = 'Failure.Payment Term is not present in Parent.'
                                sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database,
                                                            'values': data_dict}
                                record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True
                                break
                        # -------------------------------------------------------------------------------
                        if rec.purchase_type:
                            team_id = env['crm.team'].sudo().search([('team_type', 'ilike', rec.purchase_type)],
                                                                    limit=1)
                            warehouse = env['stock.warehouse'].sudo().search(
                                [('ars_type', '=', rec.purchase_type)], limit=1)
                        else:
                            # For vehicle orders, explicitly check the product category
                            is_vehicle_order = any(
                                line.product_id.categ_id.is_vehicle_category or
                                'vehicle' in (line.product_id.name or '').lower()
                                for line in rec.order_line
                            )

                            if is_vehicle_order:
                                warehouse = env['stock.warehouse'].sudo().search(
                                    [('code', '=', 'VEH')], limit=1)
                                if not warehouse:
                                    warehouse = env['stock.warehouse'].sudo().search(
                                        [('name', 'ilike', 'Vehicle')], limit=1)
                            else:
                                warehouse = env['stock.warehouse'].sudo().search(
                                    [('code', '=', 'WH')], limit=1)

                            team_id = env['crm.team'].sudo().search(
                                [('name', 'ilike', 'Sales')], limit=1)

                        # Add validation
                        if not warehouse:
                            sync_log_dict['sync_message'] = 'Warning: No warehouse found, using default'
                            warehouse = env['stock.warehouse'].sudo().search([], limit=1)
                            if not warehouse:
                                sync_log_dict['sync_message'] = 'Error: No warehouses configured!'
                                record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                                continue



                        pricelist_id = env['product.pricelist'].sudo().search(
                            [('name', '=', customer.property_product_pricelist.name)], order='id desc', limit=1)
                        print("---------------------data--------", customer, team_id, pricelist_id, warehouse,
                              rec.company_id.partner_id, env.user.company_id, env.user.company_id)  # "currency_id"
                        order_line_list = []
                        # import pdb
                        # pdb.set_trace()
                        # Sale order data formatted with minimum required fields
                        catalog_data = env['product.catalog'].sudo().search(
                            [('code', '=', rec.product_catalog_id.code)], order='id desc', limit=1)
                        counter_parts = False
                        sale_type = False
                        if rec.purchase_type == 'after_sales':
                            seq = env['ir.sequence'].sudo().search(
                                [('code', '=', 'parts.sale.quotation'), ('active', '=', True)],
                                limit=1)
                            counter_parts = True
                            sale_type = 'parts'
                            sale_aftersales = 'aftersales'
                        else:
                            seq = env['ir.sequence'].sudo().search([('code', '=', 'sale.order'), ('active', '=', True)],
                                                                   limit=1)
                            counter_parts = False
                            sale_type = 'vehicle'  # Explicitly set to vehicle
                            sale_aftersales = 'sales'  # Required for vehicle sales filter
                        addr = customer.address_get(['delivery', 'invoice', 'workshop_billing', 'workshop_shipping'])
                        code = f"{seq.prefix}" + f"{seq.number_next_actual}"
                        print("seq===================", seq, code)
                        current_time = fields.Datetime.from_string(fields.Datetime.now())
                        # Ensure warehouse is properly set on the sale order
                        data = {
                            'name': code,
                            'partner_id': customer.id if customer else False,
                            'sale_type': sale_type,
                            'sale_aftersales': sale_aftersales,
                            'counter_parts': counter_parts,
                            'mobile': customer.mobile if customer.mobile else '',
                            'email': customer.email if customer.email else '',
                            'partner_invoice_id': addr['workshop_billing'] if rec.purchase_type == 'after_sales' else
                            addr['invoice'],
                            'partner_shipping_id': addr['workshop_shipping'] if rec.purchase_type == 'after_sales' else
                            addr['delivery'],
                            'pricelist_id': pricelist_id.id if pricelist_id else False,
                            'user_id': customer.user_id.id if customer.user_id else False,
                            'payment_term_id': payment_term_id.id if payment_term_id else False,
                            'warehouse_id': warehouse.id if warehouse else False,  # This is critical
                            'picking_policy': 'direct',
                            'team_id': customer.team_id.id if customer.team_id else team_id.id,
                            'date_order': current_time,
                            'fiscal_position_id': fiscal_position_id.id if fiscal_position_id else False,
                            'product_catalog_id': catalog_data.id if catalog_data else False,
                            'child_po_id_ref': rec.id,
                            'child_db': child_database,
                            "parent_db": database,
                            'child_po_ref': f"{rec.company_id.name}-{rec.name}",
                            "note": rec.notes,
                        }
                        print("warehouse_id: warehouse.id.......", data['warehouse_id'])
                        for line_data in rec.order_line:
                            print("line_data=====", line_data)
                            if rec.purchase_type == 'after_sales':
                                # ('name', '=', line_data.product_id.product_tmpl_id.name),
                                template_data = env['product.template'].sudo().search(
                                    [('default_code', '=', line_data.product_id.default_code)], order='id desc',
                                    limit=1)
                            else:
                                template_data = env['product.template'].sudo().search(
                                    [('name', '=', line_data.product_id.product_tmpl_id.name)], order='id desc',
                                    limit=1)
                            # ('name', '=', line_data.product_id.name),
                            product_data = env['product.product'].sudo().search(
                                [('default_code', '=', line_data.product_id.default_code)], order='id desc', limit=1)
                            if product_data:
                                template_data = product_data.product_tmpl_id
                            product_uom = env['product.uom'].sudo().search([('name', '=', line_data.product_uom.name)],
                                                                           order='id desc', limit=1)
                            catalog_data = env['product.catalog'].sudo().search(
                                [('code', '=', line_data.product_catalog_id.code)], order='id desc', limit=1)
                            if not template_data:
                                data_dict = {
                                    'name': line_data.product_id.product_tmpl_id.name if line_data.product_id.product_tmpl_id.name else '',
                                    'sequence': line_data.product_id.product_tmpl_id.sequence if line_data.product_id.product_tmpl_id.sequence else '',
                                    'description': line_data.product_id.product_tmpl_id.description if line_data.product_id.product_tmpl_id.description else '',
                                    'description_purchase': line_data.product_id.product_tmpl_id.description_purchase if line_data.product_id.product_tmpl_id.description_purchase else '',
                                    'description_sale': line_data.product_id.product_tmpl_id.description_sale if line_data.product_id.product_tmpl_id.description_sale else '',
                                    'type': line_data.product_id.product_tmpl_id.type if line_data.product_id.product_tmpl_id.type else '',
                                    'rental': line_data.product_id.product_tmpl_id.rental if line_data.product_id.product_tmpl_id.rental else '',
                                    'list_price': line_data.product_id.product_tmpl_id.list_price if line_data.product_id.product_tmpl_id.list_price else '',
                                    'volume': line_data.product_id.product_tmpl_id.volume if line_data.product_id.product_tmpl_id.volume else '',
                                    'weight': line_data.product_id.product_tmpl_id.weight if line_data.product_id.product_tmpl_id.weight else '',
                                    'sale_ok': line_data.product_id.product_tmpl_id.sale_ok if line_data.product_id.product_tmpl_id.sale_ok else '',
                                    'purchase_ok': line_data.product_id.product_tmpl_id.purchase_ok if line_data.product_id.product_tmpl_id.purchase_ok else '',
                                    'active': line_data.product_id.product_tmpl_id.active if line_data.product_id.product_tmpl_id.active else '',
                                    'default_code': line_data.product_id.product_tmpl_id.default_code if line_data.product_id.product_tmpl_id.default_code else '',
                                    'activity_date_deadline': line_data.product_id.product_tmpl_id.activity_date_deadline if line_data.product_id.product_tmpl_id.activity_date_deadline else '',
                                    'sale_delay': line_data.product_id.product_tmpl_id.sale_delay if line_data.product_id.product_tmpl_id.sale_delay else '',
                                    'tracking': line_data.product_id.product_tmpl_id.tracking if line_data.product_id.product_tmpl_id.tracking else '',
                                    'list_price': line_data.product_id.product_tmpl_id.list_price if line_data.product_id.product_tmpl_id.list_price else 0,

                                }
                                # template_data = env['product.template'].sudo().create(data_dict)
                                sync_log_dict['sync_message'] = 'Failure.Product Template is not present in Parent.'
                                sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database,
                                                            'values': data_dict}
                                record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True
                                break

                            if not product_data or not line_data.product_id.default_code:
                                data_dict = {
                                    'default_code': line_data.product_id.default_code if line_data.product_id.default_code else '',
                                    'active': line_data.product_id.active if line_data.product_id.active else '',
                                    'product_tmpl_id': line_data.product_id.product_tmpl_id.id if line_data.product_id.product_tmpl_id else False,
                                    'barcode': line_data.product_id.barcode if line_data.product_id.barcode else False,
                                    'volume': line_data.product_id.volume if line_data.product_id.volume else '',
                                    'weight': line_data.product_id.weight if line_data.product_id.weight else '',
                                    'activity_date_deadline': line_data.product_id.activity_date_deadline if line_data.product_id.activity_date_deadline else '',
                                }
                                # product_data = env['product.product'].sudo().create(data_dict)
                                msg = 'Failure. Product is not present in Parent.'
                                if not line_data.product_id.default_code:
                                    msg = 'Failure. Product code is not set.'
                                sync_log_dict['sync_message'] = msg
                                sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database,
                                                            'values': data_dict}
                                record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True
                                break

                            if not product_uom and line_data.product_uom.name:
                                data_dict = {
                                    'name': line_data.product_uom.name if line_data.product_uom.name else '',
                                    'factor': line_data.product_uom.factor.id if line_data.product_uom.factor else False,
                                    'rounding': line_data.product_uom.rounding if line_data.product_uom.rounding else '',
                                    'active': line_data.product_uom.active if line_data.product_uom.active else '',
                                    'uom_type': line_data.product_uom.uom_type if line_data.product_uom.uom_type else '',
                                }
                                # product_uom = env['product.uom'].sudo().create(data_dict)
                                sync_log_dict['sync_message'] = 'Failure.Product unit is not present in Parent.'
                                sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database,
                                                            'values': data_dict}
                                record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                                stop_sync = True
                                break

                            parent_tax_data = False
                            if line_data.taxes_id:
                                current_child_tax_data = self.env['account.tax'].sudo().search(
                                    [('id', 'in', line_data.taxes_id.ids)])
                                print("env.user=====", env.user)
                                print("env.company_id.id=====", env.user.company_id,
                                      current_child_tax_data.mapped('name'))
                                data_set = env['sale.order'].sudo().search([], order='id desc', limit=1)
                                parent_company = data_set.company_id
                                print("parent_company====", parent_company)
                                parent_tax_data = env['account.tax'].sudo().search(
                                    [('name', 'in', current_child_tax_data.mapped('name')),
                                     ('type_tax_use', '=', 'sale'), ('company_id', '=', parent_company.id)])
                                print("parent_tax_data=====", parent_tax_data)
                                if not parent_tax_data:
                                    data_dict = {
                                        'name': current_child_tax_data.name if current_child_tax_data.name else '',
                                        'type_tax_use': current_child_tax_data.type_tax_use if current_child_tax_data.type_tax_use else False,
                                        'company_id': parent_company.id if parent_company else '',
                                        'active': True,
                                        'description': current_child_tax_data.name if current_child_tax_data.name else '',
                                        'python_compute': current_child_tax_data.mapped(
                                            'python_applicable') if current_child_tax_data else '',
                                        'python_applicable': current_child_tax_data.name if current_child_tax_data.name else '',
                                    }
                                    sync_log_dict['sync_message'] = 'Failure.Tax is not present in Parent.'
                                    sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database,
                                                                'values': data_dict}
                                    record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                                    stop_sync = True
                                    break

                            one2many_data = {
                                'name': line_data.name,
                                'product_catalog_id': catalog_data.id if catalog_data else False,
                                'product_template_id': template_data.id if template_data else False,
                                'product_id': product_data.id if product_data else line_data.product_id.id,
                                'order_id': rec.id,

                                'product_uom_qty': line_data.product_qty if line_data.product_qty else False,
                                'product_uom': product_uom.id if product_uom else line_data.product_uom.id,
                                'price_unit': product_data.lst_price if product_data.lst_price else product_data.standard_price,
                                'child_po_id_ref': line_data.id,
                                'child_db': child_database,
                                'warehouse_id': warehouse.id if warehouse else False,
                            }
                            # 'tax_id':[(6, 0, parent_tax_data.ids if parent_tax_data else False)],
                            print("One2many data", one2many_data)
                            print("line_data.taxes_id====", )
                            if line_data.taxes_id:
                                one2many_data['tax_id'] = [(6, 0, parent_tax_data.ids)]
                            else:
                                one2many_data['tax_id'] = [(6, 0, [])]
                            order_line_list.append((0, 0, one2many_data))
                        if order_line_list:
                            data['order_line'] = order_line_list
                        print("----data prepared-------", data)
                        print("----stop sync-------", stop_sync)
                        """ Insert new records """
                        if data and not stop_sync:
                            print("Selected Warehouse:", warehouse.name, "ID:", warehouse.id)
                            print("Warehouse Out Type:",
                                  warehouse.out_type_id.name if warehouse.out_type_id else "None")
                            print("Selected data:",data)
                            print("--------------------Create----------------------------")
                            new_recordds = env['sale.order'].sudo().create(data)
                            print("new_recordds===", new_recordds)
                            seq.number_next_actual = seq.number_next_actual + 1
                            sync_log_dict['sync_message'] = 'Success.Purchase order synced to Parent.'
                            sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database,
                                                        'values': data}
                            print("sync_log_dict====", sync_log_dict)
                            record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                            print("record_set===", record_set)
                            if new_recordds:
                                warehouse_id_pick_type_id_to_line = new_recordds.warehouse_id.in_type_id.id
                                cr.execute(
                                    "SELECT value FROM ir_config_parameter WHERE key = 'eg_sale_multi_warehouse.default_vehicle_wh_id' LIMIT 1")
                                vehicle_wh_id = cr.fetchone()

                                vehicle_wh_id = vehicle_wh_id[0] if vehicle_wh_id else None
                                print("vehicle_wh_id",vehicle_wh_id)

                                # param_ims_wh_id = env['ir.config_parameter'].sudo()
                                # print("param...record",param_ims_wh_id)
                                # default_warehouse_id = param_ims_wh_id.get_param('eg_sale_multi_warehouse.default_vehicle_wh_id')
                                default_warehouse_id = vehicle_wh_id
                                print("default_warehouse_id...record", default_warehouse_id)
                                if default_warehouse_id:
                                    warehouse_id_warehouse_id_to_line = int(default_warehouse_id)
                                    print("warehouse_id_warehousesssss_id_to_lin", warehouse_id_warehouse_id_to_line)

                                rec.sudo().write({'sync_po': True, 'state': 'done'})
                                for pr_data in data['order_line']:
                                    data_list = pr_data[2]
                                    records = new_recordds.order_line.filtered(
                                        lambda x: x.product_id.id == data_list['product_id'])
                                    cr.execute(f"""
                                        UPDATE sale_order 
                                        SET sale_type = '{data['sale_type']}',
                                            counter_parts = {data['counter_parts']},
                                            sale_aftersales = '{data['sale_aftersales']}'
                                        WHERE id = {new_recordds.id};
                                    """)


                                    for record in records:
                                        cr.execute(f"""
                                            UPDATE sale_order_line
                                            SET product_catalog_id = {data_list['product_catalog_id']} ,
                                                product_template_id = {data_list['product_template_id']},
                                                picking_type_id = {warehouse_id_pick_type_id_to_line},
                                                warehousesssss_id = {warehouse_id_warehouse_id_to_line}
                                            WHERE id ={record.id} ;
                                        """)
                                        # print("record.....record",record.picking_type_id.name)
                            print("Created new records-----", new_recordds)
                    else:
                        print("Record already present in parent DB.")
                        sync_log_dict['status'] = 500
                        sync_log_dict['sync_message'] = 'Failure.Record already synced to parent.'
                        sync_log_dict['payload'] = {'purchase_sequence': rec.name, 'db': child_database, }
                        record_set = self.env['po_sync_log'].sudo().create(sync_log_dict)
                        stop_sync = True
                        print("log updated0----", record_set)

        # except Exception as e:
        #     raise ValidationError(e)
