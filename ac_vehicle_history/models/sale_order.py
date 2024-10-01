from odoo import models, fields, api, registry, SUPERUSER_ID, sql_db, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date, datetime, time, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import contextlib
import logging
from odoo.sql_db import db_connect

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = " This class model to used to extend the service validation and service history validation"

    # is_vcard_available = fields.Boolean(string="Is Vehicle Card", default=False)

    @api.onchange('vin_no')
    def onchange_vin_no(self):
        # vin_number = self.fleet_vin_no.vin_sn if self.fleet_vin_no else self.vin_no
        vin_number = self.vin_no
        if vin_number:
            fleet_obj = self.env['fleet.vehicle'].search([('vin_sn', '=', vin_number)])
            if not fleet_obj:
                raise ValidationError(_("Vehicle Card Not Present in the System, Create New Vehicle Card"))
        # else:
        #     raise ValidationError(_("Please provide a valid VIN number."))


    # def action_confirm(self):
        # self.ensure_one()
        # param = self.env['ir.config_parameter'].sudo()
        # cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        # is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
        # db = sql_db.db_connect(f"{cons_db_name}")
        # if is_cons_enable and cons_db_name:
        # if self.sale_type == 'vehicle' and self.sale_aftersales == 'sale':
        #     vin_number = self.fleet_vin_no.vin_sn if self.fleet_vin_no and self.fleet_vin_no.vin_sn else self.vin_no
        #     service_type_name = self.env['service.type'].search([('name','=','PDI Service')]).name
        #     service_type_code = self.env['service.type'].search([('name', '=', 'PDI Service')]).code
        #     if vin_number:
        #         vehicle_card = self.env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin_number)])
        #         service_count = len(vehicle_card.service_ids)
        #         if service_count <= 0:
        #              raise ValidationError(_("Please Do Service Before selling this Vehicle"))
        #         if service_count >= 1:
        #             print("53453453")
        #             for service in vehicle_card.service_ids:
        #                 if not service.service_code == service_type_code:
        #                     raise ValidationError(_("Should be Complete PDI Service Before Selling this Vehicle"))
        #     res = super(SaleOrder, self).action_confirm()
        #     return res
        # else:
        #     res = super(SaleOrder, self).action_confirm()
        #     return res

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        vehicle = self.env['fleet.vehicle'].search(
            [('driver_id', '=', self.partner_id.id), ('license_plate', '=', self.regn_no.license_plate),
             ('vin_sn', '=', self.vin_no)])
        # nxt_due = self.env.user.company_id.next_service_due
        # remainder = self.env.user.company_id.next_service_remainder
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
        db = sql_db.db_connect(f"{cons_db_name}")
        if is_cons_enable and cons_db_name:
            if vehicle and (self.sale_aftersales == 'after_sales' or self.sale_type == 'after_sales'):
                # last_service_history = vehicle.service_ids.sorted(id, reverse=True)[:-1]
                last_service_history = vehicle.service_ids.sorted(lambda s: s.id, reverse=True)[:1]

                if last_service_history:
                    last_service_history = last_service_history[0]
                    print(last_service_history, 'last_service_history')
                    try:
                        with contextlib.closing(db.cursor()) as cr:
                            cr.autocommit(True)
                            env = api.Environment(cr, SUPERUSER_ID, {})
                            cons_vehicle_card = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vehicle.vin_sn), ('license_plate', '=', vehicle.license_plate)],limit=1)
                            if vehicle.consolidate_vehicle_card_id:
                                cons_vehicle_card = env['fleet.vehicle'].sudo().browse(vehicle.consolidate_vehicle_card_id)
                            dealer_code = self.env.user.company_id.dealer_code
                            dealer_id = env['ars.consolidation.setup'].sudo().search([('dealer_code','=',dealer_code)], limit=1)
                            if cons_vehicle_card:
                                service_vals = {
                                    'vehicle_id': cons_vehicle_card.id,
                                    'ro_id': self.id,
                                    'ro_number':  self.name,
                                    'servicetype': self.service_type.name,
                                    'date': date.today(),
                                    'service_type_name': self.service_type.name,
                                    'mileage_in': self.mileage_in,
                                    'service_code': self.service_type.code,
                                    'mileage':  self.mileage_in,
                                    'dealer_db_name': self.env.cr.dbname,
                                    'next_service_due': last_service_history.next_service_due,
                                    'set_reminder': last_service_history.set_reminder,
                                    'dealer_id':dealer_id.id if dealer_id else None,
                                }
                                cons_service_id = env['service.history'].sudo().create(service_vals)
                                # query = "UPDATE service_history SET servicetype = %s, mileage = %s WHERE id = %s"
                                # env.cr.execute(query, (last_service_history.servicetype, last_service_history.mileage, cons_service_id.id))
                                # logging.info("Service History Updated in Consolidation vehicle Card")
                                last_service_history.write({'cons_service_history_id': cons_service_id.id})
                            else:
                                raise ValidationError(_(f"Vehicle Card Couldn't Find in Consolidation System Please Check Vin Number {vehicle.vin_sn}"))
                    except Exception as e:
                        _logger.error(e)
                        raise UserError(_(e))

            return res
        else:
            # res = super(SaleOrder, self)._prepare_invoice()
            return res

    @api.multi
    def action_convert(self):
        print("function_called........")
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
        db = sql_db.db_connect(f"{cons_db_name}")
        if is_cons_enable and cons_db_name:
            if self.sale_type == 'after_sales' or self.sale_aftersales == 'after_sales':
                # vin_number = self.fleet_vin_no.vin_sn if self.fleet_vin_no and self.fleet_vin_no.vin_sn else self.vin_no
                vin_number = self.vin_no
                fleet_obj = self.env['fleet.vehicle'].sudo().search(
                    [('vin_sn', '=', vin_number), ('driver_id', '=', self.partner_id.id)], limit=1)
                if fleet_obj:
                    with contextlib.closing(db.cursor()) as cr:
                        cr.autocommit(True)
                        env = api.Environment(cr, SUPERUSER_ID, {})
                        if fleet_obj.consolidate_vehicle_card_id:
                            cons_fleet_obj = env['fleet.vehicle'].sudo().browse(fleet_obj.consolidate_vehicle_card_id)
                        else:
                            cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', '=', fleet_obj.vin_sn)], limit=1)
                        if cons_fleet_obj:
                            fleet_obj.sudo().write({'odometer':cons_fleet_obj.odometer})
                            cons_service_ids = [service.cons_service_history_id for service in fleet_obj.service_ids]
                            for con_service in cons_fleet_obj.service_ids:
                                if con_service.id not in cons_service_ids:
                                    cons_service_vals = {
                                        'vehicle_id': fleet_obj.id,
                                        'ro_id': con_service.ro_id,
                                        'ro_number': con_service.ro_number,
                                        'servicetype': con_service.servicetype,
                                        'date': con_service.date,
                                        'service_type_name': con_service.service_type_name,
                                        'mileage_in': con_service.mileage_in,
                                        'service_code': con_service.service_code,
                                        'mileage': con_service.mileage,
                                        'next_service_due': con_service.next_service_due,
                                        'set_reminder': con_service.set_reminder,
                                        'dealer_db_name':con_service.dealer_db_name,
                                        'cons_service_history_id': con_service.id,  # Add this to link the record
                                    }
                                    self.env['service.history'].sudo().create(cons_service_vals)

                            # Check if the service type sequence is valid
                            if len(fleet_obj.service_ids) >= 1:
                                if not int(self.service_type.sequence) > int(fleet_obj.service_type_sequence) and self.service_type.sequence !=-1:
                                    raise ValidationError(
                                        _("You cannot create RO. You're trying to create an unordered service. "
                                          "Please check the vehicle card's service history.")
                                    )
                        else:
                            raise ValidationError(_("Consolidated vehicle card doesn't exist for this vehicle."))
                else:
                    raise ValidationError(_("Vehicle card doesn't exist for the given VIN and driver ID. VIN: " + vin_number + ", Driver: " + self.partner_id.name))


                    # raise ValidationError(_(f"Vehicle card doesn't exist for the given VIN and driver ID. {vin_number, self.partner_id.name}"))

            # Call the parent method to continue with the original logic
            res = super(SaleOrder, self).action_convert()
            return res
        else:
            res = super(SaleOrder, self).action_convert()
            return res


    def print_service_history_report(self):
        # vin_number = self.fleet_vin_no.vin_sn if self.fleet_vin_no and self.fleet_vin_no.vin_sn else self.vin_no
        vin_number = self.vin_no
        fleet_obj =  self.env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin_number)], limit=1)
        action = self.env.ref("ars_reports.sale_action_service_history_invoice")
        return self.env.ref('ars_reports.sale_action_service_history_invoice').report_action(fleet_obj)
