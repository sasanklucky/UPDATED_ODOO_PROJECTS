from odoo import models, fields, api, _, SUPERUSER_ID, sql_db
from odoo.exceptions import UserError, ValidationError
import contextlib
import logging
import psycopg2

_logger = logging.getLogger(__name__)


class FleetVehicles(models.Model):
    _inherit = 'fleet.vehicle'
    _description = 'Information on a vehicle'

    @api.multi
    def update_customer_ownership(self):
        ownership_history = []
        for rec in self:
            history = False
            if rec.vehicle_status == 'customer':
                if rec.vin_sn:
                    lot_Obj = self.env['stock.production.lot']
                    lot_id = rec.lot_id if rec.lot_id else lot_Obj.sudo().search([('name', '=', rec.vin_sn)],
                                                                                 order='id desc', limit=1)
                    sale_line = self.env['sale.order.line'].search([('vin_no', '=', lot_id.id)])
                    if sale_line:
                        for record in rec.customer_ids:
                            history = False
                            for sale in sale_line:
                                _logger.info(
                                    f"Sale line for update owner history for {sale.vin_no.name} with {sale.order_id.partner_id.name}")
                                if sale.order_id.partner_id == rec.driver_id and not sale.order_id.partner_id.supplier and record.custmer_name == sale.order_id.partner_id:
                                    for invoice in sale.order_id.invoice_ids:
                                        if invoice.date_invoice == record.date_of_ownership:
                                            history = True
                    elif len(rec.customer_ids) > 1:
                        owner = rec.customer_ids.sorted(key=lambda r: r.id, reverse=True)
                        i = 0
                        while owner[-1] != owner[i]:
                            owner[i].sudo().unlink()
                            i += 1
                    if len(rec.customer_ids) == 0:
                        for sale in sale_line:
                            if sale.order_id.partner_id == rec.driver_id and not sale.order_id.partner_id.supplier:
                                for invoice in sale.order_id.invoice_ids:
                                    if invoice.state not in ['draft', 'cancel']:
                                        ownership_history.append([0, 0, {'custmer_name': sale.order_id.partner_id.id,
                                                                         'order': sale.order_id.id,
                                                                         'date_of_ownership': invoice.date_invoice,
                                                                         'address': sale.order_id.partner_id.city,
                                                                         'mobile': sale.order_id.partner_id.mobile,
                                                                         'sold_by': sale.order_id.company_id.partner_id.id}])
                        rec.customer_ids = ownership_history
        return super(FleetVehicles, self).update_customer_ownership()


class SyncServiceUpdate(models.TransientModel):
    _name = "sync.service.update"
    _description = "Sync Service Update"

    service_hist = fields.Boolean(string='Fetch Service History')
    ownership_hist = fields.Boolean(string='Fetch Ownership History')
    wholesales_hist = fields.Boolean(string='Fetch Wholesale History')
    consolidation_data = fields.Text(string="Consolidation Data")
    sync_line_ids = fields.One2many(
        'sync.service.update.line',
        'sync_service_id',
        string="Consolidated Dealers"
    )
    mode = fields.Selection([
        ('ims', 'IMS'),
        ('dms', 'DMS')
    ], string="Mode", default='dms')

    @api.onchange('mode')
    def _onchange_mode(self):
        if self.mode == 'ims':
            self.service_hist = False
            self.wholesales_hist = True
            self.ownership_hist = False
        else:
            self.service_hist = True
            self.wholesales_hist = True
            self.ownership_hist = True


    vehicle_sync_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    is_current_db = fields.Char(default=lambda self: self.env.cr.dbname)
    cons_db = fields.Char(string='Consolidation DB', compute='_compute_cons_db')
    show_consolidated_dealers = fields.Boolean(string='Show Dealers Section', compute="_compute_dealer_visibility")
    hide_dealer_group = fields.Boolean(string='Hide Dealer Group', compute="_compute_dealer_visibility")
    hide_service_fields = fields.Boolean(string="Hide Service & Ownership", compute="_compute_service_visibility")

    @api.depends('mode')
    def _compute_service_visibility(self):
        for rec in self:
            current_db = rec.env.cr.dbname
            cons_db = rec._get_consolidation_db()

            # Hide fields only if in consolidation and mode is IMS
            rec.hide_service_fields = current_db == cons_db and rec.mode == 'ims'

    @api.depends()
    def _compute_cons_db(self):
        cons_db_name = self._get_consolidation_db()
        for rec in self:
            rec.cons_db = cons_db_name

    @api.depends('mode')
    def _compute_dealer_visibility(self):
        for rec in self:
            current_db = rec.env.cr.dbname
            cons_db = rec._get_consolidation_db()
            rec.show_consolidated_dealers = current_db == cons_db
            # rec.hide_dealer_group = rec.mode == 'ims' and current_db == cons_db
            if not rec.show_consolidated_dealers:
                rec.hide_dealer_group = True
            elif rec.mode == 'ims':
                rec.hide_dealer_group = True
            else:
                rec.hide_dealer_group = False

    def _get_consolidation_db(self):
        return self.env['ir.config_parameter'].sudo().get_param('ac_vehicle_history.consolidate_db_name')

    def compare_with_vehicle_card_data(self, vehicle_synced, cons_ownership_history):
        customer = vehicle_synced.driver_id
        for rec in cons_ownership_history:
            if customer and rec:
                if (customer.name != rec.custmer_name.name) or (customer.mobile != rec.mobile):
                    raise ValidationError(
                        f"Wrong data detected regarding ownership history !!\n"
                        f"Vehicle Customer name: {customer.name} and Mobile: {customer.mobile} "
                        f"does not match with \n ownership history customer name: {rec.custmer_name.name} and Mobile: {rec.mobile}.\n"
                        "Please correct the data before proceeding.")
        return True


    def sync_update_comparison_action(self):
        # Clear previous unmatched records
        self.env['unmatched.record'].search([]).unlink()
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        print("cons......", cons_db_name)
        if self._cr.dbname == cons_db_name:
            vehicle_synced = self.env['fleet.vehicle'].sudo().search([
                ('id', '=', self.vehicle_sync_id.id)
            ])
            print(vehicle_synced, 'vehicle_synced===>')

            if self.mode == 'ims':
                if self.wholesales_hist:
                    _logger.info(
                        f"Wholesale is not started yet")
            else:
                selected_records = self.sync_line_ids.filtered(lambda var: var.select_dealers)
                no_unmatched_dealers = []
                for dealer in selected_records:
                    try:
                        db = sql_db.db_connect(f"{dealer.db_name}")
                        with contextlib.closing(db.cursor()) as cr:
                            cr.autocommit(True)
                            env = api.Environment(cr, SUPERUSER_ID, {})
                            dealer_vehicle_card = env['fleet.vehicle'].sudo().search([
                                ('vin_sn', '=', vehicle_synced.vin_sn)
                            ])
                            print(dealer_vehicle_card, 'dealer_vehicle_card')
                            if not dealer_vehicle_card:
                                raise ValidationError(
                                    f"Vehicle with VIN {vehicle_synced.vin_sn} not found in dealer database {dealer.db_name}")
                            if dealer_vehicle_card and vehicle_synced:
                                print('Start to Fetch')
                                update_vehicle_status_service = vehicle_synced.vehicle_status in ('customer', 'new', 'demo', 'own') and dealer_vehicle_card.vehicle_status in ('customer', 'new', 'demo', 'own')
                                both_vehicle_status = vehicle_synced.vehicle_status == 'customer' and dealer_vehicle_card.vehicle_status == 'customer'
                                # if self.service_hist and not update_vehicle_status_service:
                                #     print('not woking')
                                #     raise ValidationError(
                                #         f"Vehicle synchronization is not allowed for Vehicle status {vehicle_synced.vehicle_status} only customer vehicles can be synchronized")
                                if self.ownership_hist and not both_vehicle_status:
                                    print('problem')
                                    raise ValidationError(
                                        f"Vehicle synchronization is not allowed for Vehicle status {vehicle_synced.vehicle_status} only customer vehicles can be synchronized")

                                unmatched_found = False
                                if self.service_hist and update_vehicle_status_service:
                                    cons_history = self.env['service.history'].sudo().search([
                                        ('vehicle_id', '=', self.vehicle_sync_id.id)
                                    ])

                                    dealer_history = env['service.history'].sudo().search([
                                        ('vehicle_id', '=', dealer_vehicle_card.id)
                                    ])

                                    # Compare RO numbers
                                    cons_ros = {rec.ro_number for rec in cons_history}
                                    dealer_ros = {rec.ro_number for rec in dealer_history}

                                    missing_in_dealer = cons_ros - dealer_ros
                                    print(missing_in_dealer)
                                    missing_in_cons = dealer_ros - cons_ros
                                    print(missing_in_cons)

                                    if missing_in_dealer or missing_in_cons:
                                        unmatched_found = True

                                    # Create unmatched records
                                    for ro in missing_in_dealer:
                                        self.env['unmatched.record'].create({
                                            'conso_db': cons_db_name,
                                            'dealer_db': dealer.db_name,
                                            'ro_reference': ro,
                                            'status': 'missing_in_dealer',
                                            'dealer_name': dealer.dealer_name,
                                        })

                                    for ro in missing_in_cons:
                                        self.env['unmatched.record'].create({
                                            'conso_db': cons_db_name,
                                            'dealer_db': dealer.db_name,
                                            'ro_reference': ro,
                                            'status': 'missing_in_cons',
                                            'dealer_name': dealer.dealer_name,
                                        })
                                if self.ownership_hist and both_vehicle_status :
                                    print('<========ownership history =======>')
                                    cons_ownership_history = self.env['ownership.history'].sudo().search([
                                        ('vehicle_id', '=', self.vehicle_sync_id.id)
                                    ])
                                    self.compare_with_vehicle_card_data(vehicle_synced, cons_ownership_history)
                                    print('========fun calling =========')
                                    dealer_ownership_history = env['ownership.history'].sudo().search([
                                        ('vehicle_id', '=', dealer_vehicle_card.id)
                                    ])

                                    cons_owner = {
                                        (
                                            rec.custmer_name.name if rec.custmer_name else '',
                                            rec.date_of_ownership,
                                            rec.sold_by.name if rec.sold_by else ''
                                        )
                                        for rec in cons_ownership_history
                                    }
                                    print(cons_owner, 'consolidation ownership history ')

                                    dealer_owner = {
                                        (
                                            rec.custmer_name.name if rec.custmer_name else '',
                                            rec.date_of_ownership,
                                            rec.sold_by.name if rec.sold_by else ''
                                        )
                                        for rec in dealer_ownership_history
                                    }
                                    print(dealer_owner, 'dealer ownership history')

                                    missing_in_dealer = cons_owner - dealer_owner
                                    print(missing_in_dealer, ' dealer ownership-->')
                                    missing_in_cons = dealer_owner - cons_owner
                                    print(missing_in_cons, 'cons ownership<---')

                                    if missing_in_dealer or missing_in_cons:
                                        unmatched_found = True

                                    for dealer_rec in missing_in_dealer:
                                        self.env['unmatched.record'].create({
                                            'conso_db': cons_db_name,
                                            'dealer_db': dealer.db_name,
                                            'customer_ownership_name': dealer_rec[0],
                                            'date_of_ownership': dealer_rec[1],
                                            'status': 'missing_in_dealer',
                                            'dealer_name': dealer.dealer_name,
                                            'vin_sn': dealer_vehicle_card.vin_sn
                                        })

                                    for cons_rec in missing_in_cons:
                                        self.env['unmatched.record'].create({
                                            'conso_db': cons_db_name,
                                            'dealer_db': dealer.db_name,
                                            'customer_ownership_name': cons_rec[0],
                                            'date_of_ownership': cons_rec[1],
                                            'status': 'missing_in_cons',
                                            'dealer_name': dealer.dealer_name,
                                            'vin_sn': dealer_vehicle_card.vin_sn
                                        })

                                both_vehicles_status = vehicle_synced.vehicle_status in ['new','customer','demo','own'] and dealer_vehicle_card.vehicle_status in ['new', 'customer','demo','own']
                                # if self.wholesales_hist and not both_vehicles_status:
                                #     print('need to enter')
                                #     raise ValidationError(f"Vehicle synchronization is not allowed for Vehicle status {vehicle_synced.vehicle_status} !. Only customer and new vehicles can be synchronized")
                                if self.wholesales_hist and both_vehicles_status:
                                    print('wholesale is going to be start')
                                    print('started')
                                    cons_wholesale_hist = self.env['wholesale.history'].sudo().search([('vehicle_id','=',self.vehicle_sync_id.id)])
                                    dealer_wholesale_hist = env['wholesale.history'].sudo().search([('vehicle_id','=',dealer_vehicle_card.id)])

                                    cons_wholesale = {rec.so_number for rec in cons_wholesale_hist}
                                    dealer_wholesale = {rec.so_number for rec in dealer_wholesale_hist}
                                    missing_in_dealer = cons_wholesale - dealer_wholesale
                                    print(missing_in_dealer)
                                    missing_in_cons = dealer_wholesale - cons_wholesale
                                    print(missing_in_cons)

                                    if missing_in_dealer or missing_in_cons:
                                        unmatched_found = True

                                    for record in missing_in_dealer:
                                        print(record)
                                        self.env['unmatched.record'].create({
                                            'conso_db': cons_db_name,
                                            'dealer_db': dealer.db_name,
                                            'so_number': record,
                                            'status': 'missing_in_dealer',
                                            'vin_sn': dealer_vehicle_card.vin_sn,
                                            'dealer_name': dealer.dealer_name,
                                        })

                                    for record in missing_in_cons:
                                        print(record)
                                        self.env['unmatched.record'].create({
                                            'conso_db': cons_db_name,
                                            'dealer_db': dealer.db_name,
                                            'so_number': record,
                                            'status': 'missing_in_cons',
                                            'vin_sn': dealer_vehicle_card.vin_sn,
                                            'dealer_name': dealer.dealer_name,
                                        })
                                if not unmatched_found:
                                    no_unmatched_dealers.append(dealer.dealer_name)
                    except psycopg2.OperationalError:
                        raise ValidationError(f"Database '{dealer.db_name}' does not exist.")
                if len(no_unmatched_dealers) == len(selected_records):
                    dealer_names = ', '.join(no_unmatched_dealers)
                    message = _("There are no unmatched records in the following dealers: %s") % dealer_names

                    record = self.env['unmatched.record'].create({
                        'no_unmatched_message': message,
                    })
                    no_unmatched_rec = self.env.ref('ac_vehicle_history.view_unmatched_record_form')

                    return {
                        'name': _('Message'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'unmatched.record',
                        'res_id': record.id,
                        'view_mode': 'form',
                        'target': 'new',
                        'view_id': no_unmatched_rec.id,
                        'context': {'create': False
                                    },
                    }

                else:
                    return {
                        'name': _('Unmatched Records'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'unmatched.record',
                        'view_mode': 'tree',
                        'target': 'new',
                        'context': {'create': False},
                    }
        else:
            print(cons_db_name, 'cons_db_name')
            connecting_consolidation_db = sql_db.db_connect(cons_db_name)
            with contextlib.closing(connecting_consolidation_db.cursor()) as cr:
                cr_env = api.Environment(cr, SUPERUSER_ID, {})
                print('Local ID:', self.vehicle_sync_id.id)
                print('Consolidate ID to search:', self.vehicle_sync_id.vin_sn)
                vehicle_synced = cr_env['fleet.vehicle'].sudo().search([
                    ('vin_sn', '=', self.vehicle_sync_id.vin_sn)
                ])
                if not vehicle_synced:
                    raise ValidationError(
                        _("Vehicle with ID %(vehicle_id)s not found in consolidation database %(db_name)s") % {
                            'vehicle_id': self.vehicle_sync_id.vin_sn,
                            'db_name': cons_db_name
                        }
                    )
                current_db_record = self.env['fleet.vehicle'].sudo().search([('id', '=', self.vehicle_sync_id.id)])
                update_vehicle_status_service = vehicle_synced.vehicle_status in ('customer', 'new', 'demo', 'own') and current_db_record.vehicle_status in ('customer', 'new', 'demo', 'own')
                both_vehicle_status = vehicle_synced.vehicle_status == 'customer' and current_db_record.vehicle_status == 'customer'
                both_vehicles_status = vehicle_synced.vehicle_status in ['customer','new','demo','own'] and current_db_record.vehicle_status in ['customer','new','demo','own']
                # if self.wholesales_hist and not both_vehicles_status:
                #     print('whole')
                #     raise ValidationError(
                #         f"Vehicle synchronization is not allowed for Vehicle status  {vehicle_synced.vehicle_status} only customer vehicles can be synchronized")
                # if self.service_hist and not update_vehicle_status_service:
                #     print('service')
                #     raise ValidationError(
                #         f"Vehicle synchronization is not allowed for Vehicle status  {vehicle_synced.vehicle_status} only customer vehicles can be synchronized")
                if self.ownership_hist and not both_vehicle_status:
                    print('owner')
                    raise ValidationError(
                        f"Vehicle synchronization is not allowed for Vehicle status {vehicle_synced.vehicle_status} only customer vehicles can be synchronized")

                if vehicle_synced.vin_sn == current_db_record.vin_sn:
                    # if vehicle_synced.vehicle_status == 'customer' and current_db_record.vehicle_status == 'customer':
                    if self.service_hist and update_vehicle_status_service:
                        cons_history = cr_env['service.history'].sudo().search([
                            ('vehicle_id', '=', vehicle_synced.id)
                        ])
                        # for con_serv_rec in cons_history:
                        #     print(con_serv_rec.ro_number, con_serv_rec.id, con_serv_rec.ro_id, 'ro number')

                        current_history = self.env['service.history'].sudo().search([
                            ('vehicle_id', '=', current_db_record.id)
                        ])

                        seen_ro_ids = set()
                        for rec in current_history:
                            if rec.ro_id in seen_ro_ids:
                                rec.unlink()
                            else:
                                seen_ro_ids.add(rec.ro_id)

                        # Refresh current history after removal
                        current_history = self.env['service.history'].sudo().search([
                            ('vehicle_id', '=', current_db_record.id)
                        ])

                        existing_signatures = set((rec.ro_id, rec.ro_number) for rec in current_history)
                        for cons_rec in cons_history:
                            if (cons_rec.ro_id, cons_rec.ro_number) in existing_signatures:
                                continue  # Skip existing
                            self.env['service.history'].sudo().create({
                                'vehicle_id': current_db_record.id,
                                'ro_number': cons_rec.ro_number,
                                'servicetype': cons_rec.servicetype,
                                'date': cons_rec.date,
                                'mileage': cons_rec.mileage,
                                'next_service_due': cons_rec.next_service_due,
                                # 'stock_id4': cons_rec.stock_id4.id,
                                # 'dealer_id': cons_rec.dealer_id.id,
                                'set_reminder': cons_rec.set_reminder,
                                'service_type_name': cons_rec.service_type_name,
                                'service_code': cons_rec.service_code,
                                'dealer_db_name': cons_rec.dealer_db_name,
                                'mileage_in': cons_rec.mileage_in,
                                'cons_service_history_id': cons_rec.cons_service_history_id,
                                'ro_id': cons_rec.ro_id,
                            })

                        print("Service history sync complete.")
                    if self.ownership_hist and both_vehicle_status:
                        print(vehicle_synced, 'vehicle_synced')
                        print(current_db_record, 'current_db_record')
                        cons_ownership_history = cr_env['ownership.history'].sudo().search([
                            ('vehicle_id', '=', vehicle_synced.id)
                        ])
                        self.compare_with_vehicle_card_data(vehicle_synced, cons_ownership_history)

                        current_db_ownership = self.env['ownership.history'].sudo().search([
                            ('vehicle_id', '=', current_db_record.id)
                        ])
                        current_db_record.update_customer_ownership()
                        current_db_ownership = self.env['ownership.history'].sudo().search([
                            ('vehicle_id', '=', current_db_record.id)
                        ])
                        existing_keys = set()
                        for current_rec in current_db_ownership:
                            key = (
                                current_rec.custmer_name.email if current_rec.custmer_name else '',
                                current_rec.custmer_name.mobile if current_rec.custmer_name else '',
                            )
                            if key in existing_keys:
                                current_rec.unlink()
                            else:
                                existing_keys.add(key)
                        cons_driver = vehicle_synced.driver_id
                        print(cons_driver,'CONNNS')
                        print(cons_driver.id,'DRIVER ID')
                        print(cons_driver.name,'CUSTOMER NAME')
                        for cons_owner in cons_ownership_history:
                            key = (
                                cons_owner.custmer_name.email if cons_owner.custmer_name else '',
                                cons_owner.custmer_name.mobile if cons_owner.custmer_name else '',
                            )
                            if key in existing_keys:
                                continue

                            customer = cons_owner.custmer_name

                            matched_customer = False
                            if customer:
                                # Check both email and mobile must be present
                                if not customer.email and not customer.mobile:
                                    raise ValidationError(
                                        f"Please update the {customer.name} email and mobile number in both {self.env.cr.dbname} DB and {cons_db_name} DB before fetching the data.")
                                # elif not customer.email:
                                #     raise ValidationError(
                                #         f"Please update the {customer.name} email ID in {cons_db_name} DB before fetching the data.")
                                # elif not customer.mobile:
                                #     raise ValidationError(
                                #         f"Please update the {customer.name} mobile number in {cons_db_name} DB before fetching the data.")
                                print(customer.email,'customer.email')
                                print(customer.mobile,'customer mobile')

                                domain = []
                                if customer.email and customer.mobile:
                                    domain = ['|', ('mobile', '=', customer.mobile),('email', '=', customer.email)]
                                elif customer.email:
                                    domain = [('email', '=', customer.email)]
                                elif customer.mobile:
                                    domain = [('mobile', '=', customer.mobile)]


                                # Search using both email and mobile (AND condition)
                                matched_customer = self.env['res.partner'].sudo().search(domain)
                                print(matched_customer, 'matched_customer')

                                if len(matched_customer) > 1:
                                    print(cons_driver.name, 'CUSTOMER NAME')
                                    # remember this one has definded for only temporary purpose
                                    # we need to define like who has own the vehicle for that name should come

                                    # Determine final name to use for matching (company or individual)
                                    driver_company_name = cons_driver.name
                                    if cons_driver.company_type == 'person':#and cons_driver.parent_id
                                        driver_company_name = cons_driver.name #cons_driver.parent_id.name here we have defind for parent
                                        print(driver_company_name,'driver_company_name')
                                    elif cons_driver.company_type == 'company':
                                        driver_company_name = cons_driver.name

                                    found = False
                                    print('hehe')
                                    print(driver_company_name,'driver_company_name')
                                    for rec in matched_customer:
                                        print(rec,'RECORD')
                                        if rec.mobile == cons_driver.mobile or rec.email == cons_driver.email:
                                            print(rec.mobile,'rec.mobile')
                                            print(rec.email,'rec.mobile')
                                            # Check name based on determined company name
                                            if rec.name == driver_company_name:
                                                print(f"Matched: {rec.name}")
                                                matched_customer = rec
                                                print(f"Matched Partner: {rec.name} (ID: {rec.id})")
                                                found = True
                                                break
                                    print(matched_customer,'Matched customer')
                                    if not found:
                                        raise ValidationError(
                                            f"Multiple contacts found for customer with email '{customer.email}' and mobile '{customer.mobile}' in '{self.env.cr.dbname}' DB."
                                        )
                                elif not matched_customer:
                                    raise ValidationError(
                                        f"Customer '{customer.name}' not found in '{self.env.cr.dbname}' DB. Please check and Update email and mobile."
                                    )
                            matched_sold_by = False
                            if cons_owner.sold_by.dealer_code:
                                matched_sold_by = self.env['res.partner'].sudo().search([
                                    ('dealer_code', '=', cons_owner.sold_by.dealer_code), ('is_dealer', '=', True)
                                ])

                                if not matched_sold_by:
                                    raise ValidationError(
                                        f"Dealer code is not present in {self.env.cr.dbname} DB for '{cons_owner.sold_by.name}'."
                                    )
                                elif len(matched_sold_by) > 1:
                                    person_partners = matched_sold_by.filtered(lambda p: p.company_type == 'person')
                                    if len(person_partners) == 1:
                                        print(person_partners.name)
                                        matched_sold_by = person_partners
                                    elif len(person_partners) > 1:
                                        raise ValidationError(
                                            f"Multiple individual contacts found with dealer code '{cons_owner.sold_by.dealer_code}' in {self.env.cr.dbname}. "
                                            f"Ensure dealer code is unique for individuals."
                                        )
                                    else:
                                        raise ValidationError(
                                            f"Multiple dealer contacts found with dealer code '{cons_owner.sold_by.dealer_code}'. Please verify uniqueness."
                                        )
                            # Create the missing ownership record

                            self.env['ownership.history'].sudo().create({
                                'vehicle_id': current_db_record.id,
                                'custmer_name': matched_customer.id if matched_customer else False,
                                'date_of_ownership': cons_owner.date_of_ownership,
                                'delivery_date': cons_owner.delivery_date,
                                'address': cons_owner.custmer_name.city if cons_owner.custmer_name else '',
                                'mobile': cons_owner.mobile,
                                'sold_by': matched_sold_by.id if matched_sold_by else False,
                                'stock_id1': cons_owner.stock_id1.id,
                            })
                            existing_keys.add(key)

                            all_ownership_records = self.env['ownership.history'].sudo().search([
                                ('vehicle_id', '=', current_db_record.id)
                            ])
                            seen_keys = set()
                            for record in all_ownership_records.sorted(key=lambda r: r.id):
                                key = (
                                    record.custmer_name.email if record.custmer_name else '',
                                    record.custmer_name.mobile if record.custmer_name else '',
                                )
                                if key in seen_keys:
                                    print(f"Removing duplicate ownership history: {record.id}, key: {key}")
                                    record.unlink()
                                else:
                                    seen_keys.add(key)
                            print("Created new ownership record :", cons_owner.custmer_name.name)
                        print("Ownership history sync from consolidation to dealer completed.")
                    if self.wholesales_hist and both_vehicles_status:
                        print('han han')
                        print('wholesale need to start')

                        # Fetch from both DBs
                        cons_wholesale = cr_env['wholesale.history'].sudo().search([
                            ('vehicle_id', '=', vehicle_synced.id)
                        ])
                        current_dealer_wholesale = self.env['wholesale.history'].sudo().search([
                            ('vehicle_id', '=', current_db_record.id)
                        ])
                        print(current_dealer_wholesale, 'CURRENT DEALER WHOLESALE')

                        # Step 1: Sync from consolidation → dealer
                        for rec in cons_wholesale:
                            existing = self.env['wholesale.history'].sudo().search([
                                ('vehicle_id', '=', current_db_record.id),
                                ('so_number', '=', rec.so_number),
                                ('so_id', '=', rec.so_id)
                            ], limit=1)

                            if existing:
                                print(f"⏭ {rec} Skipping existing SO Number: {rec.so_number}")
                                continue
                            vals = {
                                'vehicle_id': current_db_record.id,
                                'dealer_name': rec.dealer_name,
                                'so_number': rec.so_number,
                                'so_id': rec.so_id,
                                'delivery_date': rec.delivery_date,
                                'invoice_number': rec.invoice_number,
                                'invoice_id': rec.invoice_id,
                                'po_number': rec.po_number,
                                'transfer_type': rec.transfer_type,
                                'dealer_code': rec.dealer_code,
                            }

                            self.env['wholesale.history'].sudo().create(vals)
                            print(f"✅ Created new wholesale for SO: {rec.so_number}")

                        # Step 2: Re-fetch updated dealer records and remove duplicates
                        current_dealer_wholesale = self.env['wholesale.history'].sudo().search([
                            ('vehicle_id', '=', current_db_record.id)
                        ])
                        print(current_dealer_wholesale,'CURRENT DEALER WHOLESALE')
                        wholesale_list = list(current_dealer_wholesale)
                        deleted_ids = set()
                        for i in range(len(wholesale_list)):
                            rec = wholesale_list[i]
                            if rec.id in deleted_ids:
                                continue

                            for j in range(i + 1, len(wholesale_list)):
                                rec2 = wholesale_list[j]
                                if rec2.id in deleted_ids:
                                    continue
                                print(rec.so_number)
                                print(rec2.so_number)
                                if rec.so_number and rec2.so_number :
                                    if rec.so_number.strip() == rec2.so_number.strip():
                                        print(f"🗑 Deleting duplicate: {rec2.id} (SO: {rec2.so_number})")
                                        rec2.unlink()
                                        deleted_ids.add(rec2.id)
                        print("✅ Sync complete. Duplicates removed based on SO number.")

            return {'type': 'ir.actions.act_window_close'}


class SyncServiceUpdateLine(models.TransientModel):
    _name = 'sync.service.update.line'
    _description = 'Sync Service Update Line'

    sync_service_id = fields.Many2one('sync.service.update', string="Wizard")
    dealer_name = fields.Char(string="Dealer Name")
    dealer_code = fields.Char(string="Dealer Code")
    db_name = fields.Char(string="Database Name")
    select_dealers = fields.Boolean(string='Sync')


class UnmatchedVehicleDetails(models.TransientModel):
    _name = 'unmatched.record'
    _order = 'dealer_name, status, ro_reference'

    conso_db = fields.Char(string='Consolidation DB', readonly=True)
    dealer_db = fields.Char(string='Dealer DB', readonly=True)
    dealer_name = fields.Char(string='Dealer Name', readonly=True)
    ro_reference = fields.Char(string='RO Reference', readonly=True)
    customer_ownership_name = fields.Char(string='Ownership Name')
    date_of_ownership = fields.Date(string="Date of Ownership")
    status = fields.Selection([
        ('missing_in_dealer', 'Missing in Selected Dealer'),
        ('missing_in_cons', 'Missing in Consolidation'),
    ], string='Status', readonly=True)
    vin_sn = fields.Char('Vin no')
    so_number = fields.Char(string='SO Number')
    no_unmatched_message = fields.Text(string='Message')

    def done_action(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_update_merge(self):
        self.ensure_one()

        is_service = bool(self.ro_reference)
        is_ownership = bool(self.customer_ownership_name)
        is_wholesale = bool(self.so_number)
        print(is_wholesale,self.so_number,'=========>')
        print(self.vin_sn)
        # print(is_ownership, 'is_ownership')
        # print(self.customer_ownership_name, 'self.customer_ownership_name')

        if not any([is_service, is_ownership, is_wholesale]):
            raise UserError(_("No identifiable mismatch record."))

        if self.status == 'missing_in_dealer':
            db = sql_db.db_connect(self.dealer_db)
            print(self.dealer_db, 'db name')
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})

                if is_service:
                    service_history = self.env['service.history'].sudo().search([
                        ('ro_number', '=', self.ro_reference)
                    ], limit=1)
                    if not service_history:
                        raise UserError(
                            _(f"RO %s is not found in {self.env.cr.dbname} DB.") % self.ro_reference)

                    vin = service_history.vehicle_id.vin_sn
                    print(vin,'vinnnnnn')
                    dealer_vehicle = env['fleet.vehicle'].sudo().search([
                        ('vin_sn', '=', vin)
                    ], limit=1)
                    print(dealer_vehicle.vin_sn)
                    print(dealer_vehicle.vin_sn == vin)

                    if not dealer_vehicle:
                        raise UserError(_(f"Vehicle with VIN %s not found in {self.dealer_db} DB.") % vin)

                    vals = {
                        'vehicle_id': dealer_vehicle.id,
                        'ro_number': service_history.ro_number,
                        'servicetype': service_history.servicetype,
                        'date': service_history.date,
                        'mileage': service_history.mileage,
                        'next_service_due': service_history.next_service_due,
                        # 'stock_id4': service_history.stock_id4.id if service_history.stock_id4 else False,
                        'set_reminder': service_history.set_reminder,
                        'service_type_name': service_history.service_type_name,
                        'service_code': service_history.service_code,
                        'dealer_db_name': service_history.dealer_db_name,
                        'mileage_in': service_history.mileage_in,
                        'cons_service_history_id': service_history.cons_service_history_id,
                        'ro_id': service_history.ro_id,
                    }
                    env['service.history'].sudo().create(vals)

                elif is_ownership:
                    consolidation_vehicle = self.env['fleet.vehicle'].sudo().search([
                        ('vin_sn', '=', self.vin_sn)
                    ])
                    print(consolidation_vehicle.driver_id,'consolidation vehicle')
                    cons_driver = consolidation_vehicle.driver_id
                    print(cons_driver.name,'cons_driver')
                    print(cons_driver.mobile,'cons_driver')

                    if not consolidation_vehicle:
                        raise ValidationError(
                            f"Vehicle with VIN '{self.vin_sn}' not found in '{self.env.cr.dbname}' DB."
                        )
                    elif len(consolidation_vehicle) > 1:
                        raise ValidationError(
                            f"Multiple vehicle cards found for VIN '{self.vin_sn}' in '{self.env.cr.dbname}' DB. Please ensure VIN is unique."
                        )

                    ownership_history = self.env['ownership.history'].sudo().search([
                        ('vehicle_id', '=', consolidation_vehicle.id),
                    ])
                    if not ownership_history:
                        raise UserError(
                            _(f"Ownership history not found for VIN %s in {self.env.cr.dbname} DB.") % self.vin_sn)
                    vin = self.vin_sn
                    dealer_vehicle = env['fleet.vehicle'].sudo().search([
                        ('vin_sn', '=', vin)
                    ])
                    print(dealer_vehicle.driver_id,'dealer vehicle')

                    if len(dealer_vehicle) > 1:
                        raise ValidationError(
                            f"Multiple vehicle cards found for VIN '{self.vin_sn}' in {self.dealer_db} DB. "
                            f"Please ensure '{self.vin_sn}' is unique."
                        )
                    if not dealer_vehicle:
                        raise UserError(_(f"Vehicle with VIN %s not found in {self.dealer_db} DB.") % vin)
                    for owner_hist in ownership_history:
                        matched_customer = False
                        customer = owner_hist.custmer_name
                        if customer:

                            # Validate presence of both email and mobile
                            if not customer.email and not customer.mobile:
                                raise ValidationError(
                                    f"Please update the {customer.name} email and mobile number in both {self.env.cr.dbname} DB and {self.dealer_db} DB before fetching the data."
                                )
                            # elif not customer.email:
                            #     raise ValidationError(
                            #         f"Please update the {customer.email} in {self.env.cr.dbname} DB."
                            #     )
                            # elif not customer.mobile:
                            #     raise ValidationError(
                            #         f"Please update the {customer.mobile} in {self.env.cr.dbname} DB."
                            #     )

                            # Match using both email and mobile (AND condition)
                            domain = []
                            if customer.email and customer.mobile:
                                domain = ['|', ('mobile', '=', customer.mobile), ('email', '=', customer.email)]
                            elif customer.email:
                                domain = [('email', '=', customer.email)]
                            elif customer.mobile:
                                domain = [('mobile', '=', customer.mobile)]

                            matched_customer = env['res.partner'].sudo().search(domain)
                            print(matched_customer,'matched_customer')

                            if len(matched_customer) > 1:
                                print(cons_driver.name, 'CUSTOMER NAME')

                                # Determine final name to use for matching (company or individual)
                                driver_company_name = cons_driver.name
                                if cons_driver.company_type == 'person':#and cons_driver.parent_id
                                    driver_company_name = cons_driver.name #cons_driver.parent_id.name
                                elif cons_driver.company_type == 'company':
                                    driver_company_name = cons_driver.name

                                found = False
                                for rec in matched_customer:
                                    if rec.mobile == cons_driver.mobile or rec.email == cons_driver.email:
                                        # Check name based on determined company name
                                        if rec.name == driver_company_name:
                                            print(f"Matched: {rec.name}")
                                            matched_customer = rec
                                            print(f"Matched Partner: {rec.name} (ID: {rec.id})")
                                            found = True
                                            break
                                print(matched_customer, 'Matched customer')
                                if not found:
                                    raise ValidationError(
                                        f"Multiple contacts found with email '{customer.email}' and mobile '{customer.mobile}' in '{self.dealer_db}' DB. "
                                        f"Please ensure these values are unique."
                                    )
                            elif not matched_customer:
                                print(matched_customer, 'matched_customer')
                                raise ValidationError(
                                    f"Customer '{customer.name}' not found in '{self.dealer_db}' DB. Please check and update email and mobile."
                                )

                                # raise ValidationError(
                                #     f"Multiple contacts found with email '{customer.email}' and mobile '{customer.mobile}' in '{self.dealer_db}' DB. "
                                #     f"Please ensure these values are unique."
                                # )
                            # if not matched_customer:
                            #     print(matched_customer,'matched_customer')
                            #     raise ValidationError(
                            #         f"Customer '{customer.name}' not found in '{self.dealer_db}' DB. Please check and update email and mobile."
                            #     )
                        matched_sold_by = False
                        if owner_hist.sold_by.dealer_code:
                            matched_sold_by = env['res.partner'].sudo().search([
                                ('dealer_code', '=', owner_hist.sold_by.dealer_code)
                            ])
                            print(matched_sold_by, 'matched_sold_by')
                            if not matched_sold_by:
                                raise ValidationError(
                                    f"Dealer code is not present in dealer for '{owner_hist.sold_by.name}'."
                                )
                            elif len(matched_sold_by) > 1:
                                person_partners = matched_sold_by.filtered(lambda p: p.company_type == 'person')

                                if len(person_partners) > 1:
                                    raise ValidationError(
                                        f"Multiple individual contacts found with dealer code '{owner_hist.sold_by.dealer_code}' in {self.dealer_db}. "
                                        f"Please ensure dealer code is unique for individuals."
                                    )
                                elif len(person_partners) == 1:
                                    matched_sold_by = person_partners
                                    print('matched_sold_by', matched_sold_by.name)
                                else:
                                    raise ValidationError(
                                        f"Multiple contacts found with dealer code '{owner_hist.sold_by.dealer_code}'."
                                    )
                    vals = {
                        'vehicle_id': dealer_vehicle.id,
                        'custmer_name': matched_customer.id if matched_customer else False,
                        'date_of_ownership': owner_hist.date_of_ownership,
                        'delivery_date': owner_hist.delivery_date,
                        'address': owner_hist.custmer_name.city if owner_hist.custmer_name else '',
                        'mobile': owner_hist.mobile,
                        'sold_by': matched_sold_by.id if matched_sold_by else owner_hist.sold_by.id,
                    }
                    env['ownership.history'].sudo().create(vals)
                elif is_wholesale:
                    print('wholesale')
                    print(self.vin_sn,'VIN')

                    dealer_vehicle = env['fleet.vehicle'].sudo().search([('vin_sn', '=', self.vin_sn)], limit=1)
                    if not dealer_vehicle:
                        raise ValidationError(f"Vehicle {self.vin_sn} is not present in {self.dealer_db} DB")
                    print(dealer_vehicle, 'Dealer vehicle')

                    # Step 2: Get all consolidation-side wholesale records for this VIN
                    consol_wholesale_history = self.env['wholesale.history'].sudo().search([
                        ('vehicle_id.vin_sn', '=', self.vin_sn)
                    ])
                    print(consol_wholesale_history, 'Consolidation Wholesale Records')

                    # Step 3: Remove duplicates from consolidation side based on `so_number`
                    consol_list = list(consol_wholesale_history)
                    deleted_ids = set()

                    for i in range(len(consol_list)):
                        rec1 = consol_list[i]
                        if rec1.id in deleted_ids or not rec1.so_number:
                            continue

                        for j in range(i + 1, len(consol_list)):
                            rec2 = consol_list[j]
                            if rec2.id in deleted_ids or not rec2.so_number:
                                continue

                            if rec1.so_number.strip() == rec2.so_number.strip():
                                print(f"🗑 Deleting duplicate consolidation record ID {rec2.id} | SO: {rec2.so_number}")
                                rec2.unlink()
                                deleted_ids.add(rec2.id)

                    print("✅ Consolidation duplicates cleaned.")

                    # Step 4: Re-fetch cleaned consolidation records
                    consol_wholesale_history = self.env['wholesale.history'].sudo().search([
                        ('vehicle_id.vin_sn', '=', self.vin_sn)
                    ])

                    # Step 5: Sync to dealer (create only if not exists)
                    for rec in consol_wholesale_history:
                        print(f"🔄 Syncing: {rec.dealer_name}, {rec.so_number}, {rec.so_id}")

                        existing = env['wholesale.history'].sudo().search([
                            ('vehicle_id', '=', dealer_vehicle.id),
                            ('so_id', '=', rec.so_id)
                        ], limit=1)

                        if existing:
                            print(f"⏭ Skipping existing SO: {rec.so_number}")
                            continue  # No update (as per your rule)

                        vals = {
                            'vehicle_id': dealer_vehicle.id,
                            'dealer_name': rec.dealer_name,
                            'so_number': rec.so_number,
                            'so_id': rec.so_id,
                            'delivery_date': rec.delivery_date,
                            'invoice_number': rec.invoice_number,
                            'invoice_id': rec.invoice_id,
                            'po_number': rec.po_number,
                            'transfer_type': rec.transfer_type,
                            'dealer_code': rec.dealer_code,
                        }

                        env['wholesale.history'].sudo().create(vals)
                        print(f"✅ Created wholesale for SO: {rec.so_number}")

        elif self.status == 'missing_in_cons':
            db = sql_db.db_connect(self.dealer_db)
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                if is_service:
                    dealer_service = env['service.history'].sudo().search([
                        ('ro_number', '=', self.ro_reference)
                    ], limit=1)

                    if not dealer_service:
                        raise UserError(_(f"RO %s not found in {self.dealer_db} DB.") % self.ro_reference)

                    existing = self.env['service.history'].sudo().search([
                        ('ro_number', '=', dealer_service.ro_number)
                    ], limit=1)

                    if existing:
                        self.unlink()
                        return self._return_wizard_or_close()

                    vin = dealer_service.vehicle_id.vin_sn
                    conso_vehicle = self.env['fleet.vehicle'].sudo().search([
                        ('vin_sn', '=', vin)
                    ], limit=1)

                    if not conso_vehicle:
                        raise UserError(
                            _(f"Vehicle with VIN %s not found in {self.env.cr.dbname} DB.") % vin)

                    vals = {
                        'vehicle_id': conso_vehicle.id,
                        'ro_number': dealer_service.ro_number,
                        'servicetype': dealer_service.servicetype,
                        'date': dealer_service.date,
                        'mileage': dealer_service.mileage,
                        'next_service_due': dealer_service.next_service_due,
                        # 'stock_id4': dealer_service.stock_id4.id if dealer_service. else False,
                        'set_reminder': dealer_service.set_reminder,
                        'service_type_name': dealer_service.service_type_name,
                        'service_code': dealer_service.service_code,
                        'dealer_db_name': dealer_service.dealer_db_name,
                        'mileage_in': dealer_service.mileage_in,
                        'cons_service_history_id': dealer_service.cons_service_history_id,
                        'ro_id': dealer_service.ro_id,
                    }
                    self.env['service.history'].sudo().create(vals)

                elif is_ownership:
                    # print(self.vin_sn, 'vinssssn')
                    dealer_vehicle = env['fleet.vehicle'].sudo().search([('vin_sn', '=', self.vin_sn)])
                    dealer_ownerships = env['ownership.history'].sudo().search([
                        ('vehicle_id', '=', dealer_vehicle.id),
                    ])
                    if not dealer_ownerships:
                        raise UserError(
                            _(f"Ownership %s not found in {self.env.cr.dbname} DB.") % self.customer_ownership_name)
                    for dealer_ownership in dealer_ownerships:
                        existing = self.env['ownership.history'].sudo().search([
                            ('custmer_name', '=',
                             dealer_ownership.custmer_name.id if dealer_ownership.custmer_name else False),
                            ('mobile', '=', dealer_ownership.mobile),
                        ], limit=1)
                        if existing:
                            continue
                        vin = dealer_ownership.vehicle_id.vin_sn
                        conso_vehicle = self.env['fleet.vehicle'].sudo().search([
                            ('vin_sn', '=', vin)
                        ])
                        cons_driver = conso_vehicle.driver_id
                        print(cons_driver,'cons_driver ')
                        print(cons_driver.name,'cons_driver NAME')
                        if len(conso_vehicle) > 1:
                            raise UserError(
                                _(f" Multiple vehicle with VIN %s is found in DB {self.env.cr.dbname} DB.") % vin)
                        if not conso_vehicle:
                            raise UserError(
                                _(f"Vehicle with VIN %s not found in {self.env.cr.dbname} DB.") % vin)

                        matched_customer = False
                        customer = dealer_ownership.custmer_name
                        # print(customer.email, customer.mobile, 'customer from dealer side')
                        if customer:
                            if not customer.email and not customer.mobile:
                                raise ValidationError(
                                    f"Please Update the '{customer.name}' email and mobile number in both '{self.env.cr.dbname}' DB and '{self.dealer_db}' DB."
                                )
                            # elif not customer.email:
                            #     raise ValidationError(
                            #         f"Please Update the '{customer.email}'in '{self.dealer_db}' DB."
                            #     )
                            # elif not customer.mobile:
                            #     raise ValidationError(
                            #         f"Please Update the '{customer.mobile}' in '{self.dealer_db}' DB."
                            #     )

                            domain = []
                            if customer.email and customer.mobile:
                                domain = ['|', ('mobile', '=', customer.mobile), ('email', '=', customer.email),]
                            elif customer.email:
                                domain = [('email', '=', customer.email)]
                            elif customer.mobile:
                                domain = [('mobile', '=', customer.mobile)]

                            matched_customer = self.env['res.partner'].sudo().search(domain)
                            print(matched_customer,'matched_customer')

                            if len(matched_customer) > 1:
                                print(cons_driver.name, 'CUSTOMER NAME')

                                # Determine final name to use for matching (company or individual)
                                driver_company_name = cons_driver.name
                                if cons_driver.company_type == 'person':# and cons_driver.parent_id
                                    driver_company_name = cons_driver.name #cons_driver.parent_id.name
                                elif cons_driver.company_type == 'company':
                                    driver_company_name = cons_driver.name

                                found = False
                                for rec in matched_customer:
                                    if rec.mobile == cons_driver.mobile or rec.email == cons_driver.email:
                                        # Check name based on determined company name
                                        if rec.name == driver_company_name:
                                            print(f"Matched: {rec.name}")
                                            matched_customer = rec
                                            print(f"Matched Partner: {rec.name} (ID: {rec.id})")
                                            found = True
                                            break
                                print(matched_customer, 'Matched customer')
                                if not found:
                                    raise ValidationError(
                                        f"Multiple contacts found with email '{customer.email}' and mobile '{customer.mobile}' in '{self.env.cr.dbname}' DB. Please ensure uniqueness."
                                    )
                            elif not matched_customer:
                                print(matched_customer, 'matched_customer')
                                raise ValidationError(
                                    f"Customer '{customer.name}' is not found in '{self.env.cr.dbname}' DB. \n Please Update the Email and Mobile number."
                                )
                                # raise ValidationError(
                                #     f"Multiple contacts found with email '{customer.email}' and mobile '{customer.mobile}' in '{self.env.cr.dbname}' DB. Please ensure uniqueness."
                                # )
                            # if not matched_customer:
                            #     raise ValidationError(
                            #         f"Customer '{customer.name}' is not found in '{self.env.cr.dbname}' DB. \n Please Update the Email and Mobile number."
                            #     )
                        # print(matched_customer, '1111')
                        # print(matched_customer.name,'1111')

                        matched_sold_by = False
                        dealer_master_id = self.env['ars.consolidation.setup'].sudo().search(
                            [('dealer_code', '=', dealer_ownership.sold_by.dealer_code)], limit=1)
                        # print(dealer_ownership.sold_by.dealer_code, 'dealer_ownership.sold_by.dealer_code')
                        if not dealer_ownership.sold_by.dealer_code:
                            raise ValidationError(
                                f"Dealer code is not present in Dealer'{dealer_ownership.sold_by.name}'."
                            )
                        if dealer_ownership.sold_by.dealer_code:
                            matched_sold_by = self.env['res.partner'].sudo().search([
                                ('dealer_code', '=', dealer_ownership.sold_by.dealer_code)
                            ])
                            if not matched_sold_by:
                                raise ValidationError(
                                    f"Dealer code '{dealer_ownership.sold_by.dealer_code}' not present in consolidation for sold_by '{dealer_ownership.sold_by.name}'."
                                )
                            elif len(matched_sold_by) > 1:
                                person_partners = matched_sold_by.filtered(lambda p: p.company_type == 'person')
                                # print(person_partners.name, 'person_partners')
                                if len(person_partners) == 1:
                                    matched_sold_by = person_partners
                                    print('matched_sold_by', matched_sold_by.name)
                                elif len(person_partners) > 1:
                                    raise ValidationError(
                                        f"Multiple individual contacts found with dealer code '{dealer_ownership.sold_by.dealer_code}' in consolidation. "
                                        f"Please ensure dealer code is unique for individuals."
                                    )
                                else:
                                    raise ValidationError(
                                        f"Multiple contacts found with dealer code '{dealer_ownership.sold_by.dealer_code}'."
                                    )
                        vals = {
                            'vehicle_id': conso_vehicle.id,
                            'custmer_name': matched_customer.id if matched_customer else False,
                            'date_of_ownership': dealer_ownership.date_of_ownership,
                            'delivery_date': dealer_ownership.delivery_date,
                            'address': dealer_ownership.custmer_name.city if dealer_ownership.custmer_name else '',
                            'mobile': dealer_ownership.mobile,
                            'dealer_id': dealer_master_id.id,
                            'sold_by': matched_sold_by.id if matched_sold_by else False,
                        }
                        self.env['ownership.history'].sudo().create(vals)

                    self.env['unmatched.record'].sudo().search([
                        ('ro_reference', '=', self.ro_reference),
                        ('customer_ownership_name', '=', self.customer_ownership_name),
                        ('date_of_ownership', '=', dealer_ownership.date_of_ownership),
                        ('status', '=', 'missing_in_cons'),
                    ]).unlink()
                    # self.unlink()
                    return self._return_wizard_or_close()
                elif is_wholesale:
                    print('wholesale')
                    print(self.vin_sn, 'VIN')

                    cons_vehicle = self.env['fleet.vehicle'].sudo().search([('vin_sn', '=', self.vin_sn)], limit=1)

                    if not cons_vehicle:
                        raise ValidationError(f"Vehicle {self.vin_sn} is not present in {self.env.cr.dbname} DB")

                    # Fetch wholesale history from dealer
                    dealer_wholesale = env['wholesale.history'].sudo().search([('vehicle_id.vin_sn', '=', self.vin_sn)])
                    print(dealer_wholesale, 'DEALER id')

                    for rec in dealer_wholesale:
                        print(rec.dealer_name, rec.so_number, 'DEALER WHOLESALE DATA')
                        dealer_master_id = self.env['ars.consolidation.setup'].sudo().search([('dealer_code', '=', rec.dealer_code)])
                        # Check if already exists in consolidation
                        existing = self.env['wholesale.history'].sudo().search([
                            ('vehicle_id', '=', cons_vehicle.id),
                            ('so_number', '=', rec.so_number),
                            ('so_id', '=', rec.so_id)
                        ], limit=1)
                        print(existing, 'EXISTING')

                        vals = {
                            'vehicle_id': cons_vehicle.id,
                            'dealer_name': rec.dealer_name,
                            'so_number': rec.so_number,
                            'so_id': rec.so_id,
                            'delivery_date': rec.delivery_date,
                            'invoice_number': rec.invoice_number,
                            'invoice_id': rec.invoice_id,
                            'po_number': rec.po_number,
                            'transfer_type': rec.transfer_type,
                            'dealer_code': rec.dealer_code,
                            'dealer_master_id': dealer_master_id.id,
                        }

                        if existing:
                            print(f"⏭ Skipping existing SO Number: {rec.so_number}")
                            continue
                        else:
                            self.env['wholesale.history'].sudo().create(vals)
                            print(f"✅ Created wholesale for SO: {rec.so_number}")

                    # 🧹 Step: Remove duplicates in consolidation DB after syncing
                    cons_wholesale = self.env['wholesale.history'].sudo().search([
                        ('vehicle_id', '=', cons_vehicle.id)
                    ])
                    print(cons_wholesale,'****')
                    cons_wholesale_list = list(cons_wholesale)
                    deleted_ids = set()

                    for i in range(len(cons_wholesale_list)):
                        rec1 = cons_wholesale_list[i]
                        if rec1.id in deleted_ids:
                            continue

                        for j in range(i + 1, len(cons_wholesale_list)):
                            rec2 = cons_wholesale_list[j]
                            if rec2.id in deleted_ids:
                                continue
                            # Compare SO numbers safely
                            if rec1.so_number and rec2.so_number and rec1.so_number.strip() == rec2.so_number.strip():
                                print(f"🗑 Deleting duplicate in Consolidation: ID {rec2.id} | SO: {rec2.so_number}")
                                rec2.unlink()
                                deleted_ids.add(rec2.id)
                    print("✅ Duplicate cleanup in consolidation completed.")
        self.unlink()
        return self._return_wizard_or_close()

    def _return_wizard_or_close(self):
        remaining = self.env['unmatched.record'].sudo().search_count([])
        if remaining == 0:
            return {'type': 'ir.actions.act_window_close'}
        else:
            return {
                'name': _('Unmatched Records'),
                'type': 'ir.actions.act_window',
                'res_model': 'unmatched.record',
                'view_mode': 'tree',
                'target': 'new',
                'context': {'create': False},
            }


class WarningMessageWizard(models.TransientModel):
    _name = 'warning.message.wizard'
    _description = 'Warning Message Wizard'

    title = fields.Char(string="Title")
    message = fields.Text(string="Message")

    def action_confirm(self):
        return {'type': 'ir.actions.act_window_close'}
