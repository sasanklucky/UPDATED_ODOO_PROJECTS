# -*- coding: utf-8 -*-
from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db, _
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool
import contextlib
from ast import literal_eval
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm


class ARSConsolidation(models.Model):
    _name = 'ars.consolidation.setup'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    dealer_name = fields.Char(string="Dealer Name", required=True)
    dealer_code = fields.Char(string="Dealer Code", required=True)
    db_name = fields.Char(string="DB Name", required=True)
    url_ip = fields.Char()
    user_name = fields.Char()
    password = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company')
    partner_id = fields.Many2one('res.partner')
    update_log_ids = fields.One2many("ars.consolidation.logs", "dealer_setup_id", copy=False, string="")

    def update_dealer_vehicle_card_details(self):
        view_id = self.env.ref("ac_ars_consolidation.dealer_vehicle_card_fetch_data_form")
        return {
            'name': _('Fetch Vehicle Card Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'vehiclecard.fetch.wizard',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'context': {'default_dealer_setup_id': self.id}
        }

    def fetch_ownership_history_details(self):
        print("fetch_ownership_history_detailsfetch_ownership_history_detailsfetch_ownership_history_details")
        try:
            database = self.db_name
            db = sql_db.db_connect(f"{database}")
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                dealer_vehicle_cards = env['fleet.vehicle'].sudo().search([])
                if not dealer_vehicle_cards:
                    self.env['ars.consolidation.logs'].sudo().create({
                        'status': 'exception',
                        'updated_on': datetime.now(),
                        'exception_reason': "No vehicle cards found in dealer database",
                        'db_name': self.db_name,
                        'is_updated': False,
                        'dealer_setup_id': self.id
                    })
                    return
                for dealer_vehicle_card in dealer_vehicle_cards:
                    try:
                        if dealer_vehicle_card:
                            consolidate_vehicle_card = self.env['fleet.vehicle'].sudo().search([('vin_sn', '=', dealer_vehicle_card.vin_sn)], limit=1)
                            if consolidate_vehicle_card:
                                dealer_ownerships = dealer_vehicle_card.customer_ids
                                for ownership in dealer_ownerships:
                                    owner = self.env['res.partner'].sudo().search([
                                        '|', '|',
                                        ('email', '=', ownership.custmer_name.email),
                                        ('mobile', '=', ownership.custmer_name.mobile),
                                        ('customer_code', '=', ownership.custmer_name.customer_code)
                                    ], limit=1)
                                    if not owner:
                                        owner_vals = {
                                            'name': ownership.custmer_name.name,
                                            'email': ownership.custmer_name.email,
                                            'city': ownership.custmer_name.city,
                                            'street': ownership.custmer_name.street,
                                            'mobile': ownership.custmer_name.mobile,
                                            'customer_code': ownership.custmer_name.customer_code or f"{database}_{ownership.custmer_name.id}"
                                        }
                                        owner = self.env['res.partner'].sudo().create(owner_vals)
                                    existing_ownership_history = self.env['ownership.history'].sudo().search([
                                        ('vehicle_id', '=', consolidate_vehicle_card.id),
                                        ('custmer_name', '=', owner.id),
                                        ('date_of_ownership', '=', ownership.date_of_ownership)
                                    ], limit=1)
                                    if not existing_ownership_history:
                                        dealer_code = env.user.company_id.dealer_code
                                        company_id = self.env['res.company'].sudo().search(
                                            [('dealer_code', '=', dealer_code)], limit=1
                                        )
                                        ownership_vals = {
                                            'custmer_name': owner.id,
                                            'date_of_ownership': ownership.date_of_ownership,
                                            'address': ownership.address,
                                            'mobile': ownership.mobile,
                                            'sold_by': company_id.partner_id.id,
                                            'vehicle_id': consolidate_vehicle_card.id
                                        }
                                        consolidate_ownership_history = self.env['ownership.history'].sudo().create(ownership_vals)
                            else:
                                self.env['ars.consolidation.logs'].sudo().create({
                                    'status': 'pending',
                                    'updated_on': datetime.now(),
                                    'exception_reason': "Vehicle Card not found in Consolidation Database",
                                    'db_name': self.db_name,
                                    'dealer_vehicle_card_id': str(dealer_vehicle_card.id),
                                    'vin_no': dealer_vehicle_card.vin_sn,
                                    'is_updated': False,
                                    'dealer_setup_id': self.id
                                })

                    except Exception as e:
                        self.env['ars.consolidation.logs'].sudo().create({
                            'status': 'exception',
                            'updated_on': datetime.now(),
                            'exception_reason': f"Error processing vehicle card {dealer_vehicle_card.vin_sn}: {str(e)}",
                            'db_name': self.db_name,
                            'dealer_vehicle_card_id': str(dealer_vehicle_card.id),
                            'vin_no': dealer_vehicle_card.vin_sn,
                            'is_updated': False,
                            'dealer_setup_id': self.id
                        })

        except Exception as e:
            self.env['ars.consolidation.logs'].sudo().create({
                'status': 'exception',
                'updated_on': datetime.now(),
                'exception_reason': f"Database connection error: {str(e)}",
                'db_name': self.db_name,
                'is_updated': False,
                'dealer_setup_id': self.id
            })

    def fetch_missing_ownership_history_details(self):
        print("fetch_missing_ownership_history_details")
        try:
            database = self.db_name
            db = sql_db.db_connect(f"{database}")
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                # pending_logs = self.update_log_ids.search([('is_updated', '=', False)])
                # if not pending_logs:
                #     self.env['ars.consolidation.logs'].sudo().create({
                #         'status': 'info',
                #         'updated_on': datetime.now(),
                #         'exception_reason': "No pending ownership history logs found",
                #         'db_name': self.db_name,
                #         'is_updated': False,
                #         'dealer_setup_id': self.id
                #     })
                #     return

                for log_record in self.update_log_ids.search([('is_updated', '=', False)]):
                    try:
                        dealer_vehicle_card = env['fleet.vehicle'].sudo().browse(int(log_record.dealer_vehicle_card_id))
                        if dealer_vehicle_card:
                            consolidate_vehicle_card = self.env['fleet.vehicle'].sudo().search(
                                [('vin_sn', '=', dealer_vehicle_card.vin_sn)], limit=1)

                            if consolidate_vehicle_card:
                                for ownership in dealer_vehicle_card.customer_ids:
                                    owner = self.env['res.partner'].sudo().search([
                                        '|', '|',
                                        ('email', '=', ownership.custmer_name.email),
                                        ('mobile', '=', ownership.custmer_name.mobile),
                                        ('customer_code', '=', ownership.custmer_name.customer_code)
                                    ], limit=1)
                                    if not owner:
                                        owner_vals = {
                                            'name': ownership.custmer_name.name,
                                            'email': ownership.custmer_name.email,
                                            'city': ownership.custmer_name.city,
                                            'street': ownership.custmer_name.street,
                                            'mobile': ownership.custmer_name.mobile,
                                            'customer_code': ownership.custmer_name.customer_code or f"{database}_{ownership.custmer_name.id}"
                                        }
                                        owner = self.env['res.partner'].sudo().create(owner_vals)

                                    existing_ownership_history = self.env['ownership.history'].sudo().search([
                                        ('vehicle_id', '=', consolidate_vehicle_card.id),
                                        ('custmer_name', '=', owner.id),
                                        ('date_of_ownership', '=', ownership.date_of_ownership)
                                    ], limit=1)

                                    if not existing_ownership_history:
                                        dealer_code = env.user.company_id.dealer_code
                                        company_id = self.env['res.company'].sudo().search(
                                            [('dealer_code', '=', dealer_code or self.dealer_code)], limit=1)

                                        ownership_vals = {
                                            'custmer_name': owner.id,
                                            'date_of_ownership': ownership.date_of_ownership,
                                            'address': ownership.address,
                                            'mobile': ownership.mobile,
                                            'sold_by': company_id.partner_id.id,
                                            'vehicle_id': consolidate_vehicle_card.id
                                        }
                                        consolidate_ownership_history = self.env['ownership.history'].sudo().create(
                                            ownership_vals)

                                log_record.sudo().write({
                                    'status': 'updated',
                                    'updated_on': datetime.now(),
                                    'is_updated': True
                                })
                            else:
                                log_record.sudo().write({
                                    'status': 'pending',
                                    'updated_on': datetime.now(),
                                    'exception_reason': "Vehicle Card not found in Consolidation Database",
                                    'is_updated': False
                                })

                    except Exception as e:
                        log_record.sudo().write({
                            'status': 'exception',
                            'updated_on': datetime.now(),
                            'exception_reason': f"Error processing vehicle card {log_record.vin_no}: {str(e)}",
                            'is_updated': False
                        })
        except Exception as e:
            self.env['ars.consolidation.logs'].sudo().create({
                'status': 'exception',
                'updated_on': datetime.now(),
                'exception_reason': f"Database connection error: {str(e)}",
                'db_name': self.db_name,
                'is_updated': False,
                'dealer_setup_id': self.id
            })

    def fetch_missing_vehicle_service_history_details(self):
        print("fetch_missing_vehicle_service_history_details")
        try:
            database = self.db_name
            db = sql_db.db_connect(f"{database}")
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                for log_record in self.update_log_ids.search([('is_updated', '=', False)]):
                    try:
                        dealer_vehicle_card = env['fleet.vehicle'].sudo().browse(int(log_record.dealer_vehicle_card_id))
                        if dealer_vehicle_card:
                            consolidate_vehicle_card = self.env['fleet.vehicle'].sudo().search(
                                [('vin_sn', '=', dealer_vehicle_card.vin_sn)])
                            if consolidate_vehicle_card:
                                for service in dealer_vehicle_card.service_ids:
                                    existing_service_history = self.env['service.history'].sudo().search([
                                        ('vehicle_id', '=', consolidate_vehicle_card.id),
                                        ('ro_number', '=', service.ro_number),
                                        ('date', '=', service.date)
                                    ], limit=1)
                                    if not existing_service_history:
                                        vals = {
                                            'vehicle_id': consolidate_vehicle_card.id,
                                            'ro_number': service.ro_number or service.order.name,
                                            'servicetype': service.servicetype,
                                            'date': service.date,
                                            'service_type_name': service.servicetype,
                                            'mileage': service.mileage,
                                            'mileage_in': service.mileage,
                                            'service_code': service.service_code,
                                            'dealer_db_name': service.dealer_db_name or self.db_name,
                                            'next_service_due': service.next_service_due,
                                            'set_reminder': service.set_reminder,
                                            'dealer_id': self.id
                                        }
                                        consolidate_service_history = self.env['service.history'].sudo().create(vals)
                                        print(existing_service_history, 'existing_service_history')
                                    service.sudo().write({'cons_service_history_id': consolidate_service_history.id})

                                log_record.sudo().write({
                                    'status': 'updated',
                                    'is_updated': True,
                                    'updated_on': datetime.now(),
                                })
                            else:
                                log_record.sudo().write({
                                    'status': 'pending',
                                    'updated_on': datetime.now(),
                                    'exception_reason': "Vehicle Card not found in Consolidation Database",
                                    'is_updated': False
                                })
                    except Exception as e:
                        log_record.sudo().write({
                            'status': 'exception',
                            'updated_on': datetime.now(),
                            'exception_reason': f"Error processing vehicle card {log_record.vin_no}: {str(e)}",
                            'is_updated': False,
                        })

        except Exception as e:
            self.env['ars.consolidation.logs'].sudo().create({
                'status': 'exception',
                'updated_on': datetime.now(),
                'exception_reason': f"Database connection error: {str(e)}",
                'db_name': self.db_name,
                'is_updated': False,
                'dealer_setup_id': self.id
            })

    def fetch_vehicle_service_history_details(self):
        try:
            database = self.db_name
            db = sql_db.db_connect(f"{database}")
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                # Fetch all vehicle cards from the dealer's database
                dealer_vehicle_cards = env['fleet.vehicle'].sudo().search([])
                if not dealer_vehicle_cards:
                    self.env['ars.consolidation.logs'].sudo().create({
                        'status': 'exception',
                        'updated_on': datetime.now(),
                        'exception_reason': "No vehicle cards found in dealer database",
                        'db_name': self.db_name,
                        'is_updated': False,
                        'dealer_setup_id': self.id
                    })
                    return
                for dealer_vehicle_card in dealer_vehicle_cards:
                    try:
                        if dealer_vehicle_card:
                            consolidate_vehicle_card = self.env['fleet.vehicle'].sudo().search(
                                [('vin_sn', '=', dealer_vehicle_card.vin_sn)])
                            if consolidate_vehicle_card:
                                customer = self.env['res.partner'].sudo().search(
                                    ['|', '|', ('email', '=', dealer_vehicle_card.driver_id.email),
                                     ('mobile', '=', dealer_vehicle_card.driver_id.mobile),
                                     ('customer_code', '=', dealer_vehicle_card.driver_id.customer_code)], limit=1)
                                if not customer:
                                    customer_vals = {
                                        'name': dealer_vehicle_card.driver_id.name,
                                        'mobile': dealer_vehicle_card.driver_id.mobile if dealer_vehicle_card.driver_id.mobile else None,
                                        'is_dealer': False,
                                        'email': dealer_vehicle_card.driver_id.email if dealer_vehicle_card.driver_id.email else None,
                                        'city': dealer_vehicle_card.driver_id.city if dealer_vehicle_card.driver_id.city else None,
                                        'customer_code': dealer_vehicle_card.driver_id.customer_code if dealer_vehicle_card.driver_id.customer_code else f"{database}_{dealer_vehicle_card.driver_id.id}"
                                    }
                                    new_customer = self.env['res.partner'].sudo().create(customer_vals)
                                    consolidate_vehicle_card.write({'driver_id': new_customer.id})

                                for service in dealer_vehicle_card.service_ids:
                                    existing_service_history = self.env['service.history'].sudo().search([
                                        ('vehicle_id', '=', consolidate_vehicle_card.id),
                                        ('ro_number', '=', service.ro_number),
                                        ('date', '=', service.date)
                                    ], limit=1)
                                    print(existing_service_history, 'existing_service_history')
                                    if not existing_service_history:
                                        vals = {
                                            'vehicle_id': consolidate_vehicle_card.id,
                                            'ro_id': service.order.id,
                                            'ro_number': service.ro_number or service.order.name,
                                            'servicetype': service.servicetype,
                                            'date': service.date,
                                            'service_type_name': service.servicetype,
                                            'mileage': service.mileage,
                                            'mileage_in': service.mileage,
                                            'service_code': service.service_code,
                                            'dealer_db_name': service.dealer_db_name or self.db_name,
                                            'next_service_due': service.next_service_due,
                                            'set_reminder': service.set_reminder,
                                            'dealer_id': self.id
                                        }
                                        consolidate_service_history = self.env['service.history'].sudo().create(vals)
                                        service.sudo().write(
                                            {'cons_service_history_id': consolidate_service_history.id})
                            else:
                                self.env['ars.consolidation.logs'].sudo().create({
                                    'status': 'pending',
                                    'updated_on': datetime.now(),
                                    'exception_reason': "Vehicle Card not found in Consolidation Database",
                                    'db_name': self.db_name,
                                    'dealer_vehicle_card_id': str(dealer_vehicle_card.id),
                                    'vin_no': dealer_vehicle_card.vin_sn,
                                    'is_updated': False,
                                    'dealer_setup_id': self.id
                                })
                    except Exception as e:
                        self.env['ars.consolidation.logs'].sudo().create({
                            'status': 'exception',
                            'updated_on': datetime.now(),
                            'exception_reason': f"Error processing vehicle card {dealer_vehicle_card.vin_sn}: {str(e)}",
                            'db_name': self.db_name,
                            'dealer_vehicle_card_id': str(dealer_vehicle_card.id),
                            'vin_no': dealer_vehicle_card.vin_sn,
                            'is_updated': False,
                            'dealer_setup_id': self.id
                        })
        except Exception as e:
            self.env['ars.consolidation.logs'].sudo().create({
                'status': 'exception',
                'updated_on': datetime.now(),
                'exception_reason': f"Database connection error: {str(e)}",
                'db_name': self.db_name,
                'is_updated': False,
                'dealer_setup_id': self.id
            })

    @api.multi
    def establish_connection(self):
        model = 'fleet.vehicle'
        vehicles = self.connection_establish_to_parent_db(model)

    @api.model
    def create_vehicle(self):
        fleet_vehicle = self.env['fleet.vehicle'].sudo()
        fleet_vehicle.create()

    @api.model
    def get_data_from_parent_model(self, model):
        fields = []
        if model:
            res_fields = self.env['ir.model.fields'].search([('model', '=', model)])
            for field in res_fields:
                fields.append(field.name)
            return fields

    @api.model
    def create_method(self, model, vals):
        if model:
            model_obj = self.env[f'{model}'].sudo()

    @api.model
    def search_method(self, model, domain, obj):
        if model:
            model_obj = self.env[f'{model}'].sudo()
            con_obj = model_obj.search(domain)
            if not con_obj:
                if model == 'res.partner':
                    self.create_method()
            return model_obj
        else:
            return False

    @api.model
    def get_product_record(self, model_code):
        if model_code:
            FIELDS = ['']
            product_model = self.env['product.product'].sudo()
            prod_obj = product_model.search([('default_code', '=', model_code)])
            if prod_obj:
                return prod_obj
            else:
                return False
        else:
            return False

    @api.model
    def get_lot_number_record(self, vin, lot_data):
        print(self._cr.dbname)
        try:
            with api.Environment.manage():
                # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
                new_cr = self.pool.cursor()
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                if vin:
                    FIELDS = ['']
                    vin_obj = self.env['stock.production.lot'].sudo()
                    vin_no = vin_obj.search([('name', '=', vin)])
                    if vin_no:
                        new_cr.close()
                        return vin_no
                    else:
                        # for token in self.env['live.stream.token'].search([('state', '=', 'valid')]):
                        if not lot_data['product_id'] or not lot_data['name']:
                            new_cr.close()
                            return False
                        else:
                            if lot_data['product_id'] and lot_data['name']:
                                vin_no = vin_obj.create(lot_data)
                                new_cr.close()
                                return vin_no
                else:
                    new_cr.close()
                    return False
        except Exception as e:
            new_cr.close()
            print(e)

    @api.model
    def update_service_history(self, data):
        try:
            with api.Environment.manage():
                # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
                new_cr = self.pool.cursor()
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                if data:
                    service_his_obj = self.env['service.history'].sudo()
                    history_id = service_his_obj.search(
                        [('ro_number', '=', data['ro_number']), ('dealer_id', '=', self.id)])
                    if history_id:
                        new_cr.close()
                        return history_id
                    else:
                        history_id = service_his_obj.create(data)
                        new_cr.close()
                        return history_id
                else:
                    new_cr.close()
                    return False
        except Exception as e:
            new_cr.close()
            print(e)

    @api.model
    def update_ownership_history(self, data):
        try:
            with api.Environment.manage():
                # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
                new_cr = self.pool.cursor()
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                if data:
                    owner_ship_his_obj = self.env['ownership.history'].sudo()
                    history_id = owner_ship_his_obj.search(
                        [('custmer_name', '=', data['custmer_name']), ('dealer_id', '=', self.id)])
                    if history_id:
                        new_cr.close()
                        return history_id
                    else:
                        history_id = owner_ship_his_obj.create(data)
                        new_cr.close()
                        return history_id
                else:
                    new_cr.close()
                    return False
        except Exception as e:
            new_cr.close()
            print(e)

    @api.model
    def get_company(self, dealer_code):
        if dealer_code:
            company_obj = self.env['res.company'].sudo()
            company_id = company_obj.search([('dealer_code', '=', dealer_code)])
            if company_id:
                return company_id
            else:
                return False
        else:
            return False

    @api.model
    def get_country_details(self, code):
        company_obj = self.env['res.country'].sudo()
        if code:
            company_id = company_obj.search([('code', '=', code)])
            if company_id:
                return company_id
            else:
                return False
        else:
            company_id = company_obj.search([('code', '=', 'IN')])
            return company_id

    @api.model
    def get_customer_details(self, data):
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            new_cr.autocommit(True)
            self = self.with_env(self.env(cr=new_cr))
            if data['mobile'] and data['name']:
                partner_obj = self.env['res.partner'].sudo()
                partner_id = partner_obj.search([('mobile', '=', data['mobile']), ('name', '=', data['name'])])
                if partner_id:
                    new_cr.close()
                    return partner_id
                else:
                    partner_id = partner_obj.create(data)
                    new_cr.close()
                    return partner_id
            else:
                new_cr.close()
                return False

    @api.model
    def get_vehicle_details(self, vehicles):
        res = []
        # model = 'fleet.vehicle'
        # vehicles = self.connection_establish_to_parent_db(model)
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            new_cr.autocommit(True)
            self = self.with_env(self.env(cr=new_cr))
            fleet_vehicle = self.env['fleet.vehicle'].sudo()
            for vehicle in vehicles:
                vehicle_id = fleet_vehicle.search([('vin_sn', '=', vehicle['vin_sn'])])
                if vehicle_id:
                    new_cr.close()
                    return vehicle_id
                else:
                    vehicle_id = fleet_vehicle.create(vehicle)
                    new_cr.close()
                    return vehicle_id
            new_cr.close()
            return res

    @api.model
    def connection_establish_to_parent_db(self, model, domain=[]):
        try:
            database = self.db_name
            db = sql_db.db_connect(f"{database}")
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                res_model = env[f"{model}"].sudo()
                datas = res_model.search(domain)
                vehicle_list = []
                if model == 'fleet.vehicle':
                    for data in datas:
                        try:
                            lot_no_data, cus_data, vals = {}, {}, {}
                            company_id = self.get_company(data.company_id.dealer_code)
                            prod_variant_id = self.get_product_record(data.mvariant_id.default_code)
                            lot_no_data = {'name': data.vin_sn, 'motor_number': data.engine_number,
                                           'product_catalog': 'Vehicle',
                                           'product_id': prod_variant_id.id if prod_variant_id else False,
                                           # 'company_id': company_id.id if company_id else False
                                           }
                            vin_sn = self.get_lot_number_record(data.vin_sn, lot_no_data)
                            country_id = self.get_country_details(data.driver_id.country_id.code)
                            if data.driver_id:
                                cus_data = {'name': data.driver_id.name, 'mobile': data.driver_id.mobile,
                                            'email': data.driver_id.email, 'street': data.driver_id.street,
                                            'street2': data.driver_id.street2, 'city': data.driver_id.city,
                                            'country_id': country_id.id
                                            }
                            else:
                                cus_data = {}
                            customer = self.get_customer_details(cus_data)
                            vals = {'mvariant_id': prod_variant_id.id if prod_variant_id else False,
                                    'model_id': prod_variant_id.product_tmpl_id.id if prod_variant_id else False,
                                    'vin_sn': data.vin_sn,
                                    'license_plate': data.license_plate,
                                    'engine_number': data.engine_number,
                                    'company_id': company_id.id if company_id else False,
                                    'vehicle_status': data.vehicle_status,
                                    'driver_id': customer.id if customer else False,
                                    }
                            if prod_variant_id and data.vin_sn and company_id and customer:
                                vehicle_id = self.get_vehicle_details([vals])
                                if vehicle_id:
                                    for history in data.service_ids:
                                        his_data = {'ro_number': history.order.name, 'ro_id': history.order.id,
                                                    'dealer_id': self.id, 'servicetype': history.servicetype,
                                                    'date': history.date, 'mileage': history.mileage,
                                                    'next_service_due': history.next_service_due,
                                                    'set_reminder': history.set_reminder,
                                                    'vehicle_id': vehicle_id.id
                                                    }
                                        service_history = self.update_service_history(his_data)
                                    for ownerships in data.customer_ids:
                                        if ownerships.custmer_name:
                                            cus_data = {'name': ownerships.custmer_name.name,
                                                        'mobile': ownerships.custmer_name.mobile,
                                                        'email': ownerships.custmer_name.email,
                                                        'street': ownerships.custmer_name.street,
                                                        'street2': ownerships.custmer_name.street2,
                                                        'city': ownerships.custmer_name.city,
                                                        'country_id': country_id.id
                                                        }
                                            custmr_name = self.get_customer_details(cus_data)
                                            if custmr_name:
                                                ownership_data = {'custmer_name': custmr_name.id,
                                                                  'date_of_ownership': ownerships.date_of_ownership,
                                                                  'address': ownerships.custmer_name.city,
                                                                  'mobile': ownerships.custmer_name.mobile,
                                                                  'vehicle_id': vehicle_id.id
                                                                  }
                                                self.update_ownership_history(ownership_data)
                                    vehicle_list.append(vehicle_id)
                        except Exception as e:
                            print(e)
                            continue
                    return vehicle_list
        except Exception as e:
            print(e)
