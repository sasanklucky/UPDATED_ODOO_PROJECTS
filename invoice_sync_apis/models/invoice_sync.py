from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db, _
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm


class AccountInvoiceLineInheritSync(models.Model):
    _inherit = "account.invoice.line"
    _description = "Account Invoice Line"

    child_db = fields.Char()
    child_invoice_id_ref = fields.Char(string='Parent Reference')


class AccountInvoiceInheritSync(models.Model):
    _inherit = "account.invoice"
    _description = "Account Invoice"

    sync_invoice  = fields.Boolean(string='Sync')
    child_invoice_id_ref = fields.Char(string='Child ID Reference')
    child_db = fields.Char()
    child_invoice_ref = fields.Char(string='Child Reference')
    # test_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)
    hide_sync  = fields.Boolean(string='Sync', compute='hide_sync_status')
    invoice_sync_log_ids = fields.One2many('invoice_sync_log','invoice_record', string='Log')

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False
        warning = {}
        domain = {}
        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
        print('partner value is========',p)
        type = self.type
        if p:
            rec_account = p.property_account_receivable_id
            pay_account = p.property_account_payable_id
            print('partner value is cuma========',rec_account,pay_account)

            if not rec_account and not pay_account and not self.child_invoice_ref:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('in_invoice', 'in_refund'):
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term_id.id
            else:
                account_id = rec_account.id
                payment_term_id = p.property_payment_term_id.id

            delivery_partner_id = self.get_delivery_partner_id()
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=delivery_partner_id)

            # If partner has no warning, check its company
            if p.invoice_warn == 'no-message' and p.parent_id:
                p = p.parent_id
            if p.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                    p = p.parent_id
                warning = {
                    'title': _("Warning for %s") % p.name,
                    'message': p.invoice_warn_msg
                    }
                if p.invoice_warn == 'block':
                    self.partner_id = False

        self.account_id = account_id
        self.payment_term_id = payment_term_id
        self.date_due = False
        self.fiscal_position_id = fiscal_position

        if type in ('in_invoice', 'out_refund'):
            bank_ids = p.commercial_partner_id.bank_ids
            bank_id = bank_ids[0].id if bank_ids else False
            self.partner_bank_id = bank_id
            domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}

        res = {}
        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        return res

    @api.depends('state')
    def hide_sync_status(self):
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('invoice_sync_apis.invoice_company_type')
        print("child====",child)
        for record in self:
            if child == 'is_child_company' and record.sync_invoice == False and record.state != 'draft':
                record.hide_sync = False
            elif record.state == 'draft':
                record.hide_sync = True
            else:
                record.hide_sync = True

    @api.multi
    def call_invoice_sync(self):
        self._call_sync_invoice_to_parent(self)

    # @api.depends('state')
    # def _compute_css(self):
    #     for record in self:
    #         print('state------------called',record.state)
    #         if record.state == 'done':
    #             record.test_css = '<style>.o_form_button_edit {display: none !important;}</style>'
    #         else:
    #             record.test_css = False

    @api.multi
    def write(self, vals):
        if 'sync_invoice' not in vals:
            vals['sync_invoice'] = False
        res =  super(AccountInvoiceInheritSync, self).write(vals)
        return res

    @api.model
    def _cron_sync_invoice_to_parent(self):
        call = self.env['account.invoice']._call_sync_invoice_to_parent(False)
    
    @api.model
    def _call_sync_invoice_to_parent(self,current_invoice_record):
        """ connect to parent db set up in general settings """
        # try:
        param = self.env['ir.config_parameter'].sudo()
        child = param.get_param('invoice_sync_apis.invoice_company_type')
        check_invoice_sync = param.get_param('invoice_sync_apis.enable_invoice_sync')
        print("child---",child,check_invoice_sync)
        if child == 'is_child_company' and check_invoice_sync == 'yes':
            database = param.get_param('invoice_sync_apis.invoice_parent_db')
            print("database=====",database)
            db = sql_db.db_connect(f"{database}")
            child_database = self._cr.dbname
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                #getting child data as sellf represent child db env
                invoice_records = False
                if current_invoice_record:
                    invoice_records = current_invoice_record
                else:
                    invoice_records = self.env['account.invoice'].sudo().search([('sync_invoice','=',False),('state','in', ['open','paid'])],order='id asc')
                    print("==1==",invoice_records)
                
                # looped child po datas
                for rec in invoice_records:
                    print("rec=====",rec)
                    stop_sync = False
                    sync_log_dict = {
                        'invoice_record':rec.id,
                        'invoice_sequence':rec.name,
                        'status':200,
                    }
                    # parent record env
                    invoice_record_set = env['account.invoice'].sudo()
                    exist_in_parent = invoice_record_set.search([('child_invoice_id_ref','=',str(rec.id)),('child_db','=',child_database)],limit=1, order='id desc')
                    print("acccount invoice=====",exist_in_parent)
                    if not exist_in_parent:
                        customer = False
                        payment_term_id= False
                        country= False
                        currency= False
                        fiscal_position_id= False
                        account_journal_id= False
                        payment_term_id= False
                        account_id= False
                        cash_rounding_id = False
                        line_vin_no=False
                        # # if exist_in_parent:
                        # Currency
                        if rec.currency_id:
                            currency = env['res.currency'].sudo().search([('name','=',rec.currency_id.name),('symbol','=',rec.currency_id.symbol)],order='id desc',limit=1)
                            if not currency:
                                data_dict = {
                                    'name':rec.currency_id.name if rec.currency_id else '',
                                    'symbol':rec.currency_id.symbol if rec.currency_id else False,
                                    'rounding':rec.currency_id.rounding if rec.currency_id.rounding else False,
                                    'active':rec.currency_id.active if rec.currency_id.active else '',
                                    'position':rec.currency_id.position if rec.currency_id.position else '',
                                    'currency_unit_label':rec.currency_id.currency_unit_label if rec.currency_id.currency_unit_label else '',
                                    'currency_subunit_label':rec.currency_id.currency_subunit_label if rec.currency_id.currency_subunit_label else '',
                                    }
                                sync_log_dict['sync_message'] = 'Failure.Currency is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break
                        # company
                        if rec.company_id:
                            company = env['res.company'].sudo().search([('dealer_code','=',rec.company_id.dealer_code)],order='id desc',limit=1)
                            data_dict = {'company_name':rec.company_id.name,
                                         'dealer_code':rec.company_id.dealer_code,
                                         }
                            if not company:
                                sync_log_dict['sync_message'] = 'Failure.Company is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break
                            
                        print("company===",rec.company_id.partner_id.mobile)
                        # customer
                        
                        if rec.partner_id:
                            customer = env['res.partner'].sudo().search([('customer_code','=',rec.partner_id.customer_code)],order='id desc',limit=1)
                        
                            if not customer:
                                data_dict = {
                                    'customer_code':rec.partner_id.customer_code if rec.partner_id.customer_code else '',
                                    'name':rec.partner_id.name if rec.partner_id else '',
                                    'mobile':rec.partner_id.mobile if rec.partner_id.mobile else '',
                                    'email':rec.partner_id.email if rec.partner_id.email else '',
                                    'street':rec.partner_id.street if rec.partner_id.street else '',
                                    'street2':rec.partner_id.street2 if rec.partner_id.street2 else '',
                                    'city':rec.partner_id.city if rec.partner_id.city else '',
                                    'state_id':country.state if country else False,
                                    'zip':rec.partner_id.zip if rec.partner_id.zip else '',
                                    'country_id':country if country else False,
                                    'pan_no':rec.partner_id.pan_no if rec.partner_id.pan_no else '',
                                    'vat':rec.partner_id.vat if rec.partner_id.vat else '',
                                    'function':rec.partner_id.function if rec.partner_id.function else '',
                                    'phone':rec.partner_id.phone if rec.partner_id.phone else '',
                                    'website':rec.partner_id.website if rec.partner_id.website else '',
                                    'lang':rec.partner_id.lang if rec.partner_id.lang else '',
                                }
                                customer = env['res.partner'].sudo().create(data_dict)
                                sync_log_dict['sync_message'] = 'Customer is not present in Parent.New Customer Created.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                # stop_sync =True
                                # break
                        
                        print("customer===",customer)
                        if rec.fiscal_position_id:
                            fiscal_position_id = env['account.fiscal.position'].sudo().search([('name','=',rec.fiscal_position_id.name)],order='id desc',limit=1)
                            if not fiscal_position_id:
                                data_dict = {
                                    'name':rec.fiscal_position_id.name if rec.fiscal_position_id else '',
                                    'active':rec.fiscal_position_id.active,
                                    'company_id':rec.company_id.id if rec.company_id else False,
                                    'currency_id':currency.id if currency else False,
                                    'country_id':country.id if country else False,
                                    'auto_apply':rec.fiscal_position_id.auto_apply,
                                    'vat_required':rec.fiscal_position_id.vat_required,
                                    'zip_from':rec.fiscal_position_id.zip_from,
                                    'zip_to':rec.fiscal_position_id.zip_to,
                                    'note':rec.fiscal_position_id.note,
                                }
                                sync_log_dict['sync_message'] = 'Failure.Fiscal position is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break
                        
                        # payment terms
                        if rec.payment_term_id:
                            payment_term_id = env['account.payment.term'].sudo().search([('name','=',rec.payment_term_id.name),('company_id','=',rec.payment_term_id.company_id.id),('active','=',rec.payment_term_id.active)],order='id desc',limit=1)
                            if not payment_term_id:
                                data_dict = {
                                    'name':rec.payment_term_id.name if rec.payment_term_id else '',
                                    'active':rec.payment_term_id.active if rec.payment_term_id else False,
                                    'note':rec.payment_term_id.note if rec.payment_term_id.note else '',
                                    'company_id':rec.payment_term_id.company_id.id if rec.payment_term_id.company_id else rec.company_id.id,
                                    'sequence':rec.payment_term_id.sequence.id if rec.payment_term_id.sequence else False,
                                    }
                                sync_log_dict['sync_message'] = 'Failure.Payment Term is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break
                        # cash rounding
                        if rec.cash_rounding_id:
                            cash_rounding_id = env['account.cash.rounding'].sudo().search([('name','=',rec.cash_rounding_id.name)],order='id desc',limit=1)
                            if not cash_rounding_id:
                                data_dict = {
                                    'name':rec.cash_rounding_id.name if rec.cash_rounding_id else '',
                                    'rounding':rec.cash_rounding_id.rounding if rec.cash_rounding_id else False,
                                    'strategy':rec.cash_rounding_id.strategy if rec.cash_rounding_id.strategy else '',
                                    'rounding_method':rec.cash_rounding_id.rounding_method if rec.cash_rounding_id.rounding_method else ''
                                    }
                                sync_log_dict['sync_message'] = 'Failure.Account Cash rounding is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break
                        
                        # Account journal
                        if rec.journal_id:
                            account_journal_id = env['account.journal'].sudo().search([('name','=',rec.journal_id.name),('code','=',rec.journal_id.code),('active','=',rec.journal_id.active)],order='id desc',limit=1)
                            if not account_journal_id:
                                data_dict = {
                                    'name':rec.journal_id.name if rec.journal_id else '',
                                    'code':rec.journal_id.code if rec.journal_id else False,
                                    'active':rec.journal_id.active if rec.journal_id.active else False,
                                    'type':rec.journal_id.type if rec.journal_id.type else ''
                                    }
                                sync_log_dict['sync_message'] = 'Failure.journal is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break
                        
                        # Account Account
                        if rec.account_id:
                            account_id = env['account.account'].sudo().search([('name','=',rec.account_id.name),('code','=',rec.account_id.code)],order='id desc',limit=1)
                            if not account_id:
                                data_dict = {
                                    'name':rec.account_id.name if rec.account_id else '',
                                    'code':rec.account_id.code if rec.account_id else False,
                                    'deprecated':rec.account_id.deprecated if rec.account_id.deprecated else False,
                                    'internal_type':rec.account_id.internal_type if rec.account_id.internal_type else '',
                                    'note':rec.account_id.note if rec.account_id.note else ''
                                    }
                                sync_log_dict['sync_message'] = 'Failure.Account is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break
                        
                        #-------------------------------------------------------------------------------
                        pricelist_id = env['product.pricelist'].sudo().search([('name','=',customer.property_product_pricelist.name)],order='id desc',limit=1)
                        warehouse = env['stock.warehouse'].sudo().sudo().search([('code','=','VEH')],limit=1)
                        invoice_line_list = []
                        # Invoice data formatted with minimum required fields
                        # seq = env['ir.sequence'].sudo().search([('code','=','account.invoice'),('active','=',True)],limit=1)
                        # code = f"{seq.prefix}" + f"{seq.number_next_actual}"
                        # print("seq===================",seq,code)
                        data = {
                                'name':rec.name if rec.name else '',
                                'partner_id':customer.id if customer else False,
                                'partner_shipping_id':customer.id if customer else False,
                                'mobile':customer.mobile if customer.mobile else '',
                                'email':customer.email if customer.email else '',
                                'cash_rounding_id':cash_rounding_id.id if cash_rounding_id else False,
                                'pricelist_id':pricelist_id.id if pricelist_id else False,
                                'date_invoice':rec.date_invoice if rec.date_invoice else '',
                                'gate_pass_date':rec.gate_pass_date if rec.gate_pass_date else '',
                                'date_due':rec.date_due if rec.date_due else '',
                                'user_id':customer.user_id.id if customer.user_id else False,
                                'payment_term_id':payment_term_id.id if payment_term_id else False,
                                'currency_id':currency.id if currency else False,
                                'fiscal_position_id':fiscal_position_id.id if fiscal_position_id else False,
                                'journal_id':account_journal_id.id if account_journal_id else False,
                                'account_id':account_id.id if account_id else False,
                                'company_id':company.id if company else False,
                                'comment':rec.comment if rec.comment else '',
                                'amount_total':rec.amount_total if rec.amount_total else '',
                                'amount_untaxed':rec.amount_untaxed if rec.amount_untaxed else '',
                                'amount_tax':rec.amount_tax if rec.amount_tax else '',
                                'child_invoice_id_ref':rec.id,
                                'child_db':child_database,
                                "parent_db":database,
                                'child_invoice_ref':f"{rec.company_id.name}-{rec.number}",
                                # "note":rec.note,
                                
                            }
                        for line_data in rec.invoice_line_ids:
                            print("line_data=====",line_data)
                            template_data = env['product.template'].sudo().search([('name','=',line_data.product_id.product_tmpl_id.name)],order='id desc',limit=1)
                            product_data = env['product.product'].sudo().search([('name','=',line_data.product_id.name),('default_code','=',line_data.product_id.default_code)],order='id desc',limit=1)
                            product_uom = env['product.uom'].sudo().search([('name','=',line_data.uom_id.name)],order='id desc',limit=1)
                            catalog_data = env['product.catalog'].sudo().search([('code','=',line_data.product_catalog_id.code)],order='id desc',limit=1)
                                   
                            if not template_data:
                                data_dict = {
                                    'name':line_data.product_id.product_tmpl_id.name if line_data.product_id.product_tmpl_id.name else '',
                                    'sequence':line_data.product_id.product_tmpl_id.sequence if line_data.product_id.product_tmpl_id.sequence else '',
                                    'description':line_data.product_id.product_tmpl_id.description if line_data.product_id.product_tmpl_id.description else '',
                                    'description_purchase':line_data.product_id.product_tmpl_id.description_purchase if line_data.product_id.product_tmpl_id.description_purchase else '',
                                    # 'description_sale':line_data.product_id.product_tmpl_id.description_sale if line_data.product_id.product_tmpl_id.description_sale else '',
                                    'type':line_data.product_id.product_tmpl_id.type if line_data.product_id.product_tmpl_id.type else '',
                                    'rental':line_data.product_id.product_tmpl_id.rental if line_data.product_id.product_tmpl_id.rental else '',
                                    'volume':line_data.product_id.product_tmpl_id.volume if line_data.product_id.product_tmpl_id.volume else '',
                                    'weight':line_data.product_id.product_tmpl_id.weight if line_data.product_id.product_tmpl_id.weight else '',
                                    # 'sale_ok':line_data.product_id.product_tmpl_id.sale_ok if line_data.product_id.product_tmpl_id.sale_ok else '',
                                    'purchase_ok':line_data.product_id.product_tmpl_id.purchase_ok if line_data.product_id.product_tmpl_id.purchase_ok else '',
                                    'active':line_data.product_id.product_tmpl_id.active if line_data.product_id.product_tmpl_id.active else '',
                                    'default_code':line_data.product_id.product_tmpl_id.default_code if line_data.product_id.product_tmpl_id.default_code else '',
                                    'activity_date_deadline':line_data.product_id.product_tmpl_id.activity_date_deadline if line_data.product_id.product_tmpl_id.activity_date_deadline else '',
                                    # 'sale_delay':line_data.product_id.product_tmpl_id.sale_delay if line_data.product_id.product_tmpl_id.sale_delay else '',
                                    'tracking':line_data.product_id.product_tmpl_id.tracking if line_data.product_id.product_tmpl_id.tracking else '',
                                    'list_price':line_data.product_id.product_tmpl_id.list_price if line_data.product_id.product_tmpl_id.list_price else 0,

                                }
                                sync_log_dict['sync_message'] = 'Failure.Product Template is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break

                            if not product_data or not line_data.product_id.default_code:
                                data_dict = {
                                    'default_code':line_data.product_id.default_code if line_data.product_id.default_code else '',
                                    'active':line_data.product_id.active if line_data.product_id.active else '',
                                    'product_tmpl_id':line_data.product_id.product_tmpl_id.id if line_data.product_id.product_tmpl_id else False,
                                    'barcode':line_data.product_id.barcode if line_data.product_id.barcode else False,
                                    'volume':line_data.product_id.volume if line_data.product_id.volume else '',
                                    'weight':line_data.product_id.weight if line_data.product_id.weight else '',
                                    'activity_date_deadline':line_data.product_id.activity_date_deadline if line_data.product_id.activity_date_deadline else '',
                                }
                                msg = 'Failure. Product is not present in Parent.'
                                if not line_data.product_id.default_code:
                                    msg = 'Failure. Product code is not set.'
                                sync_log_dict['sync_message'] = msg
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break
                            
                            if not product_uom and line_data.uom_id.name:
                                data_dict = {
                                    'name':line_data.uom_id.name if line_data.uom_id.name else '',
                                    'factor':line_data.uom_id.factor.id if line_data.uom_id.factor else False,
                                    'rounding':line_data.uom_id.rounding if line_data.uom_id.rounding else '',
                                    'active':line_data.uom_id.active if line_data.uom_id.active else '',
                                    'uom_type':line_data.uom_id.uom_type if line_data.uom_id.uom_type else '',
                                }
                                sync_log_dict['sync_message'] = 'Failure.Product unit is not present in Parent.'
                                sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                stop_sync =True
                                break

                            parent_tax_data =False
                            if line_data.invoice_line_tax_ids:
                                current_child_tax_data = self.env['account.tax'].sudo().search([('id','in',line_data.invoice_line_tax_ids.ids)])
                                print("env.user=====",env.user)
                                print("env.company_id.id=====",env.user.company_id,current_child_tax_data.mapped('name'))
                                data_set = env['account.invoice'].sudo().search([('company_id','!=',False)],order='id desc', limit=1)
                                parent_company = data_set.company_id if data_set.company_id else company
                                print("parent_company====",parent_company)
                                print("current_child_tax_data.mapped('name')-------",current_child_tax_data.mapped('name'))
                                print("current_child_tax_data.mapped('type_tax_use')-------",current_child_tax_data.mapped('type_tax_use'))
                                parent_tax_data = env['account.tax'].sudo().search([('name','in',current_child_tax_data.mapped('name')),('type_tax_use','in',current_child_tax_data.mapped('type_tax_use')),('company_id','=',parent_company.id)])
                                print("parent_tax_data=====",parent_tax_data)
                                if not parent_tax_data:
                                    data_dict = {
                                        'name':current_child_tax_data.mapped('name') if current_child_tax_data else '',
                                        'type_tax_use':current_child_tax_data.mapped('type_tax_use') if current_child_tax_data else False,
                                        'company_id':parent_company.id if parent_company else '',
                                        'active':True,
                                        'description':current_child_tax_data.mapped('description') if current_child_tax_data else '',
                                        'python_compute':current_child_tax_data.mapped('python_compute') if current_child_tax_data else '',
                                        'python_applicable':current_child_tax_data.mapped('python_applicable') if current_child_tax_data else '',
                                    }
                                    sync_log_dict['sync_message'] = 'Failure.Tax is not present in Parent.'
                                    sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                    record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                    stop_sync =True
                                    break
                            
                            # Account Account
                            if line_data.account_id:
                                line_account_id = env['account.account'].sudo().search([('name','=',line_data.account_id.name),('code','=',line_data.account_id.code)],order='id desc',limit=1)
                                if not line_account_id:
                                    data_dict = {
                                        'name':line_data.account_id.name if line_data.account_id else '',
                                        'code':line_data.account_id.code if line_data.account_id else False,
                                        'deprecated':line_data.account_id.deprecated if line_data.account_id.deprecated else False,
                                        'internal_type':line_data.account_id.internal_type if line_data.account_id.internal_type else '',
                                        'note':line_data.account_id.note if line_data.account_id.note else ''
                                        }
                                    sync_log_dict['sync_message'] = 'Failure.Account is not present in Parent.'
                                    sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                    record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                    stop_sync =True
                                    break
                            
                            # Vim No
                            if line_data.vin_no:
                                line_vin_no = env['stock.production.lot'].sudo().search([('name','=',line_data.vin_no.name)],order='id desc',limit=1)
                                if not line_vin_no:
                                    data_dict = {
                                        'name':line_data.vin_no.name if line_data.vin_no else '',
                                        'active':line_data.vin_no.active if line_data.vin_no else False,
                                        }
                                    sync_log_dict['sync_message'] = 'Failure.Vin is not present in Parent.'
                                    sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data_dict}
                                    record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                                    stop_sync =True
                                    break

                            one2many_data ={
                                            'name':line_data.name,
                                            'product_catalog_id':catalog_data.id if catalog_data else False,
                                            'product_template_id':template_data.id if template_data else False,
                                            'product_id':product_data.id if product_data else line_data.product_id.id,
                                            'invoice_id':rec.id,
                                            'quantity':line_data.quantity if line_data.quantity else False,
                                            'uom_id':product_uom.id if product_uom else line_data.product_uom.id,
                                            'price_unit':line_data.price_unit if line_data.price_unit else 0,
                                            'price_subtotal':line_data.price_subtotal if line_data.price_subtotal else 0,
                                            'discount':line_data.discount if line_data.discount else 0,
                                            'account_id':line_account_id.id if line_account_id else False,
                                            'vin_no':line_vin_no.id if line_vin_no else False,
                                            'child_invoice_id_ref':line_data.id,
                                            'child_db':child_database
                                        }
                            print("line_data.taxes_id====",)
                            if line_data.invoice_line_tax_ids:
                                one2many_data['invoice_line_tax_ids'] = [(6, 0, parent_tax_data.ids)]
                            else:
                                one2many_data['invoice_line_tax_ids'] = [(6, 0, [])]
                            invoice_line_list.append((0,0,one2many_data ))
                        if invoice_line_list:
                            data['invoice_line_ids'] = invoice_line_list
                        print("----data prepared-------",data)
                        print("----stop sync-------",stop_sync)
                        
                        """ Preparing data for tax_line_ids """
                        # for tax in tax_line_ids:
                        
                        
                        if data and not stop_sync:
                            print("--------------------Create----------------------------")
                            new_recordds = env['account.invoice'].sudo().create(data)
                            print("new_recordds===",new_recordds)
                            # seq.number_next_actual = seq.number_next_actual+1
                            sync_log_dict['sync_message'] = 'Success.Invoice synced to Parent.'
                            sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,'values':data}
                            print("sync_log_dict====",sync_log_dict)
                            record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                            print("record_set===",record_set)
                            if new_recordds:
                                rec.sudo().write({'sync_invoice':  True})
                            print("Created new records-----",new_recordds)
                    else:
                        print("Record already present in parent DB.")
                        sync_log_dict['status'] = 500
                        sync_log_dict['sync_message'] = 'Failure.Record already synced to parent.'
                        sync_log_dict['payload'] = {'invoice_sequence':rec.name,'db':child_database,}
                        record_set = self.env['invoice_sync_log'].sudo().create(sync_log_dict)
                        stop_sync =True
                        print("log updated0----",record_set)
                        
    
        # except Exception as e:
        #     raise ValidationError(e)

