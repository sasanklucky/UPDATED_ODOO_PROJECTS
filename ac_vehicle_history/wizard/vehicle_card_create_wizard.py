from odoo import models, fields, api, registry, SUPERUSER_ID, sql_db, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date, datetime, time, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import contextlib
import logging
from odoo.sql_db import db_connect


class CreateVehicleCardWizard(models.TransientModel):
    _name = "vehiclecard.creation.wizard"
    _description = "If vehicle card doesn't present in the system this model business logics going to create vehicle card in the respective system to fetching the details from the consolidation database"

    vin_no = fields.Char(string="Vin Number", required=True)

    # is_customer = fields.Boolea

    def create_vehicle_card(self):
        print("called_wizard_function")
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        try:
            db = sql_db.db_connect(f"{cons_db_name}")
        except Exception as e:
            raise UserError(_("Could not connect to the consolidation database: %s") % str(e))
        # db = sql_db.db_connect(f"{cons_db_name}")
        try:
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', '=', self.vin_no)])
                categ_id = self.env['product.category'].sudo().search([('name', '=', 'Vehicle'), ('active', '=', True)])

                if not cons_fleet_obj:
                    raise ValidationError(_(f"Vehicle Card Not Found Please Check The VIN Number or Case{self.vin_no}"))
                if cons_fleet_obj.vehicle_status != 'customer':
                    raise ValidationError(_("Vehicle Card status Not in Customer "))

                existing_vehicle = self.env['fleet.vehicle'].sudo().search([('vin_sn','=',cons_fleet_obj.vin_sn or self.vin_no)], limit=1)
                if existing_vehicle:
                    raise ValidationError(_(f"Vehicle Card is Already Exist {existing_vehicle.vin_sn}"))

                if cons_fleet_obj.vehicle_status == 'customer' and cons_fleet_obj:
                    customer_id = cons_fleet_obj.driver_id
                    partner_obj = self.env['res.partner'].sudo().search(
                        ['|', '|', ('customer_code', '=', customer_id.customer_code), ('email', '=', customer_id.email),
                         ('mobile', '=', customer_id.mobile)], limit=1)

                    if not partner_obj:
                        customer_vals = {
                            'name': customer_id.name,
                            'customer_code': customer_id.customer_code or '',
                            'city': customer_id.city or '',
                            'street': customer_id.street or '',
                            'mobile': customer_id.mobile or '',
                            'email': customer_id.email or '',
                            'customer': True,
                        }
                        new_customer = self.env['res.partner'].create(customer_vals)
                    else:
                        new_customer = partner_obj

                    product_id = self.env['product.product'].sudo().search([('default_code', '=', cons_fleet_obj.mvariant_id.default_code),('active','=',True)])
                    if not product_id:
                        raise ValidationError(f"Product Doesn't Exist, Please Check the Product Code {cons_fleet_obj.mvariant_id.default_code}")
                    if not product_id.product_tmpl_id.id:
                        raise ValidationError(
                            _("The model associated with the product does not exist in the fleet vehicle model table."))

                    vehicle_vals = {
                        'vin_sn': cons_fleet_obj.vin_sn,
                        'categ_id': categ_id.id,
                        'driver_id':new_customer.id,
                        'contact_name':new_customer.id,
                        'engine_number': cons_fleet_obj.engine_number or '-',
                        'key_serial_number': cons_fleet_obj.key_serial_number or '-',
                        'license_plate': cons_fleet_obj.license_plate or '/',
                        'odometer': cons_fleet_obj.odometer,
                        'vehicle_status': 'new',
                        'model_id': product_id.product_tmpl_id.id,
                        'mvariant_id': product_id.id,
                        'consolidate_vehicle_card_id': cons_fleet_obj.id
                    }
                    new_vehicle_card = self.env['fleet.vehicle'].sudo().create(vehicle_vals)
                    new_vehicle_card.sudo().write({'odometer':cons_fleet_obj.odometer})
                    # update Ownership History from the consolidtion to this system
                    for ownership in cons_fleet_obj.customer_ids:
                        if ownership.sold_by:
                            dealer_obj = self.env['res.partner'].sudo().search([('is_dealer', '=', True), ('dealer_code', '=', ownership.sold_by.dealer_code)], limit=1)
                            if not dealer_obj:
                                new_dealer = self.env['res.partner'].sudo().create({
                                    'name': ownership.sold_by.name,
                                    'is_dealer': True,
                                    'dealer_code': ownership.sold_by.dealer_code or None,
                                    'mobile': ownership.sold_by.mobile or None,
                                    'email': ownership.sold_by.email or None,
                                    'street': ownership.sold_by.street or None,
                                    'city': ownership.sold_by.city or None,
                                })
                            else:
                                new_dealer = dealer_obj
                            ownership_vals = {
                                'vehicle_id': new_vehicle_card.id,
                                'custmer_name': new_customer.id,
                                'date_of_ownership': ownership.date_of_ownership,
                                'address': ownership.address or None,
                                'mobile': ownership.mobile or None,
                                'delivery_date': ownership.delivery_date or None,
                                'sold_by': new_dealer.id
                            }
                            new_vehicle_card.customer_ids = [(0, 0, ownership_vals)]
                            new_vehicle_card.write({'vehicle_status': 'customer'})
                    # update WholesaleHistory details
                    for wholesale in cons_fleet_obj.wholesale_ids:
                        wholesale_vals = {
                            'vehicle_id': new_vehicle_card.id,
                            'dealer_name': wholesale.dealer_name,
                            'so_number': wholesale.so_number,
                            'so_id': wholesale.so_id,
                            'delivery_date': wholesale.delivery_date,
                            'invoice_number': wholesale.invoice_number if wholesale.invoice_number else '',
                            'invoice_id': wholesale.invoice_id if wholesale.invoice_id else '',
                            'po_number': wholesale.po_number if wholesale.po_number else '',
                            'transfer_type': wholesale.transfer_type,
                            'dealer_code': wholesale.dealer_code,
                        }
                        new_vehicle_card.wholesale_ids = [(0, 0, wholesale_vals)]
                        # self.env['wholesale.history'].sudo().create(wholesale_vals)

                    if cons_fleet_obj.service_ids:
                        for service in cons_fleet_obj.service_ids:
                            service_vals = {
                                'vehicle_id': new_vehicle_card.id,
                                'ro_id': service.ro_id if service.ro_id else None,
                                'ro_number': service.ro_number if service.ro_number else None,
                                'servicetype': service.servicetype,
                                'service_type_name': service.service_type_name,
                                'date': service.date,
                                'mileage': service.mileage,
                                'mileage_in': service.mileage_in,
                                'next_service_due': service.next_service_due or None,
                                'set_reminder': service.set_reminder or None,
                                'dealer_db_name': service.dealer_db_name,
                                'cons_service_history_id': service.id
                            }
                            new_vehicle_card.service_ids = [(0, 0, service_vals)]

        except ValidationError as e:
            raise UserError(_("Validation Error: %s") % str(e))
        except Exception as e:
            logging.exception(str(e))
            raise UserError(_("An unexpected error occurred: %s") % str(e))

        return {
            'name': _('Vehicle Message'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'vehicle.message',
            'view_id': self.env.ref('ac_vehicle_history.view_vehicle_message').id,
            'target': 'new',
        }









