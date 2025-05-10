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

    campaign_service_name_ref = fields.Char('Campaign')

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
        print(cons_db_name, 'vvvvvvvvvv')
        is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
        db = sql_db.db_connect(f"{cons_db_name}")
        if is_cons_enable and cons_db_name:
            if vehicle and (self.sale_aftersales == 'after_sales' or self.sale_type == 'after_sales'):
                # last_service_history = vehicle.service_ids.sorted(id, reverse=True)[:-1]
                last_service_history = vehicle.service_ids.sorted(lambda s: s.id, reverse=True)[:1]
                last_campaign = vehicle.campaign_history_ids.sorted(lambda s: s.campaign_name_ref == self.campaign_service_name_ref, reverse=True)[:1]
                if last_service_history:
                    last_service_history = last_service_history[0]
                    print(last_service_history, 'last_service_history')
                    try:
                        with contextlib.closing(db.cursor()) as cr:
                            cr.autocommit(True)
                            env = api.Environment(cr, SUPERUSER_ID, {})
                            cons_vehicle_card = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vehicle.vin_sn)],
                                                                                   limit=1)
                            if not cons_vehicle_card and vehicle.consolidate_vehicle_card_id != 0:
                                cons_vehicle_card = env['fleet.vehicle'].sudo().browse(
                                    vehicle.consolidate_vehicle_card_id)
                            dealer_code = self.env.user.company_id.dealer_code
                            dealer_id = env['ars.consolidation.setup'].sudo().search(
                                [('dealer_code', '=', dealer_code)], limit=1)
                            if cons_vehicle_card:
                                service_vals = {
                                    'vehicle_id': cons_vehicle_card.id,
                                    'ro_id': self.id,
                                    'ro_number': self.name,
                                    'servicetype': self.service_type.name,
                                    'date': date.today(),
                                    'service_type_name': self.service_type.name,
                                    'mileage_in': self.mileage_in,
                                    'service_code': self.service_type.code,
                                    'mileage': self.mileage_in,
                                    'dealer_db_name': self.env.cr.dbname,
                                    'next_service_due': last_service_history.next_service_due,
                                    'set_reminder': last_service_history.set_reminder,
                                    'dealer_id': dealer_id.id if dealer_id else None,
                                }
                                check_console_ro_name = env['service.history'].sudo().search(
                                    [('ro_number', '=', self.name)], limit=1)
                                if check_console_ro_name:
                                    check_console_ro_name.update(service_vals)
                                    cons_service_id = check_console_ro_name
                                else:
                                    cons_service_id = env['service.history'].sudo().create(service_vals)
                                # query = "UPDATE service_history SET servicetype = %s, mileage = %s WHERE id = %s"
                                # env.cr.execute(query, (last_service_history.servicetype, last_service_history.mileage, cons_service_id.id))
                                # logging.info("Service History Updated in Consolidation vehicle Card")
                                last_service_history.write({'cons_service_history_id': cons_service_id.id})
                            else:
                                raise ValidationError(
                                    _(f"Vehicle Card Couldn't Find in Consolidation System Please Check Vin Number {vehicle.vin_sn}"))
                    except Exception as e:
                        _logger.error(e)
                        raise UserError(_(e))
                if last_campaign:
                    last_campaign = last_campaign[0]
                    try:
                        with contextlib.closing(db.cursor()) as cr:
                            cr.autocommit(True)
                            env = api.Environment(cr, SUPERUSER_ID, {})
                            cons_vehicle_card = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vehicle.vin_sn)],
                                                                                   limit=1)
                            if not cons_vehicle_card and vehicle.consolidate_vehicle_card_id != 0:
                                cons_vehicle_card = env['fleet.vehicle'].sudo().browse(
                                    vehicle.consolidate_vehicle_card_id)
                            if cons_vehicle_card:
                                sim_details_vals = {'sim_number': vehicle.sim_number,
                                                    'sim_installation_date': vehicle.sim_installation_date}
                                cons_vehicle_card.update(sim_details_vals)
                                dealer_code = self.env.user.company_id.dealer_code
                                dealer_id = env['ars.consolidation.setup'].sudo().search(
                                    [('dealer_code', '=', dealer_code)], limit=1)
                                dealer_campaign_vals = {
                                    # "campaign_name":last_campaign.campaign_name.id,
                                    "campaign_name_ref":last_campaign.campaign_name_ref,
                                    "campaign_ref":last_campaign.campaign_ref,
                                    "campaign_status":last_campaign.campaign_status,
                                    "start_date":last_campaign.start_date,
                                    "end_date":last_campaign.end_date,
                                    # "campaign_service_id":self.id,
                                    # 'sim_number':
                                    "campaign_service_name": self.name,
                                    "camp_cancel_reasons":last_campaign.camp_cancel_reasons,
                                    "campaign_vehicle_status":last_campaign.campaign_vehicle_status,
                                    "state":last_campaign.state,
                                    # "campaign_done_date":last_campaign.campaign_done_date,
                                    "dealer_db_name":self.env.cr.dbname,
                                    "dealer_code":dealer_id.dealer_code if dealer_id else None,
                                }
                                check_console_campaign_name = env['campaign.history'].sudo().search(
                                    [('campaign_ref', '=', last_campaign.campaign_ref), ('id', '=', last_campaign.campaign_service_ref_id)], limit=1)
                                if check_console_campaign_name:
                                    check_console_campaign_name.update(dealer_campaign_vals)
                                    cons_service_id = check_console_campaign_name
                                else:
                                    cons_service_id = env['campaign.history'].sudo().create(dealer_campaign_vals)
                                    print(cons_service_id,'aaaaaaaaa')
                                last_campaign.write({'campaign_ref':cons_service_id.id,
                                                     "dealer_db_name":self.env.cr.dbname,
                                                     "dealer_code":dealer_id.dealer_code if dealer_id else None,
                                                     # "campaign_service_id":self.id,
                                                     "campaign_service_name": self.name,
                                                     })

                    except Exception as e:
                        _logger.error(e)
                        raise UserError(_(e))
            return res
        else:
            # res = super(SaleOrder, self)._prepare_invoice()
            return res

    @api.multi
    def action_convert(self, vals):
        print("function_called........")
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
        db = sql_db.db_connect(f"{cons_db_name}")
        if is_cons_enable and cons_db_name and 'continue' not in vals:
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
                            cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', '=', fleet_obj.vin_sn)],
                                                                                limit=1)
                        if cons_fleet_obj:
                            fleet_obj.sudo().write({'odometer': cons_fleet_obj.odometer})
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
                                        'dealer_db_name': con_service.dealer_db_name,
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
                            # if cons_fleet_obj.campaign_history_ids and len(cons_fleet_obj.campaign_history_ids) >= 1:

                             # 1. Build a dictionary of existing campaigns from current DB, excluding `self.id`
                            existing_campaign_dict = {
                                (rec.campaign_name_ref, rec.campaign_ref): {
                                    'id': rec.id,
                                    'state': rec.state,
                                    'status': rec.campaign_status
                                }
                                for rec in fleet_obj.campaign_history_ids
                            }

                            # 2. Loop through campaigns from another DB (consolidated object)
                            for camp_service in cons_fleet_obj.campaign_history_ids:
                                key = (camp_service.campaign_name_ref, camp_service.campaign_ref)

                                # Skip if already synced
                                if key in existing_campaign_dict:
                                    continue
                                # 3. Get or create related campaign definition
                                varr = self.env['vehicle.campaigns'].sudo().search([
                                    ('name', '=', camp_service.campaign_name_ref)
                                ], limit=1)
                                if not varr:
                                    service_types = self.env['service.type'].search([
                                        ('code', '=', camp_service.campaign_name.service_type.code),
                                        ('name', '=', camp_service.campaign_name.service_type.name)
                                    ], limit=1)
                                    # Assuming `consol_vehicle_camp` is defined earlier or needs to be defined here
                                    consol_vehicle_camp = {
                                        'name': camp_service.campaign_name.name,
                                        'start_date': camp_service.start_date,
                                        'end_date': camp_service.end_date,
                                        'stage': camp_service.campaign_name.stage,
                                        'cons_vehicles_camp_id': camp_service.campaign_name.id,
                                        'service_type': service_types.id,
                                        'campaign_service_ref_id': camp_service.campaign_service_ref_id,
                                        'service_options': service_types.service_option_id.id if service_types.service_option_id else False,
                                    }
                                    varr = self.env['vehicle.campaigns'].sudo().create(consol_vehicle_camp)

                                # 4. Prepare data to sync vehicle-level campaign (if needed)
                                service_types = self.env['service.type'].search([
                                    ('code', '=', varr.service_type.code),
                                    ('name', '=', varr.service_type.name)
                                ], limit=1)

                                consol_vehicle_camp_vals = {
                                    'name': varr.name,
                                    'start_date': varr.start_date,
                                    'end_date': varr.end_date,
                                    'stage': varr.stage,
                                    'instruction': varr.instruction.id,
                                    'cons_vehicles_camp_id': varr.cons_vehicles_camp_id,
                                    'service_type': varr.service_type.id,
                                    'service_options': varr.service_type.service_option_id.id if varr.service_type.service_option_id else False,
                                }

                                existed_camp = self.env['vehicle.campaigns'].sudo().search([
                                    ('cons_vehicles_camp_id', '=', varr.cons_vehicles_camp_id)
                                ], limit=1)

                                if not existed_camp:
                                    existed_camp = self.env['vehicle.campaigns'].sudo().create(consol_vehicle_camp_vals)

                                # 5. Create new campaign history since it's not in the current DB
                                dealer_campaign_vals = {
                                    'campaign_vehicle_id': fleet_obj.id,
                                    'campaign_name_ref': camp_service.campaign_name_ref,
                                    'campaign_ref': camp_service.campaign_ref,
                                    'campaign_status': camp_service.campaign_status,
                                    'campaign_service_ref_id': camp_service.campaign_service_ref_id,
                                    'start_date': camp_service.start_date,
                                    'end_date': camp_service.end_date,
                                    'state': camp_service.state,
                                    'campaign_name': existed_camp.id,
                                }

                                existed_campagin_his = self.env['campaign.history'].sudo().search([('campaign_service_ref_id', '=', camp_service.campaign_service_ref_id)], limit=1)
                                if existed_campagin_his:
                                    existed_campagin_his.update(dealer_campaign_vals)
                                    campaign_id = existed_campagin_his.id
                                else:
                                    new_history = self.env['campaign.history'].sudo().create(dealer_campaign_vals)
                                    campaign_id = new_history.id
                                    print(f"Created new campaign history: {new_history.id}")

                                # 6. Add to dict to prevent duplicates
                                existing_campaign_dict[key] = {
                                    'id': campaign_id,
                                    'state': camp_service.state,
                                    'status': camp_service.campaign_status
                                }

                            # 6. Conflict check for "pending" state with "ongoing" status
                            conflicting = [
                                (name_ref, ref, val['id'])
                                for (name_ref, ref), val in existing_campaign_dict.items()
                                if val['state'] == 'pending' and val['status'] == 'ongoing'
                            ]

                            # 7. Show confirmation wizard if conflict found
                            if conflicting:
                                campaign_name, campaign_id, history_id = conflicting[0]
                                self.write({'campaign_his_id': history_id})
                                return {
                                    'name': 'Campaign Message',
                                    'type': 'ir.actions.act_window',
                                    'view_mode': 'form',
                                    'view_id': self.env.ref('ac_ars_campaigns.view_convert_so_message_form').id,
                                    'res_model': 'convert.so.wizard',
                                    'target': 'new',
                                    'context': {
                                        'default_text': f"""There is an ongoing <strong>{campaign_name}</strong> Campaign for this vehicle card!<br/>
                                                            Are you sure you want to proceed with it?""",
                                        'default_campaign_history_id': history_id,
                                        'default_sale_estimation_id': self.id
                                    },
                                }

                        else:
                            raise ValidationError(_("Consolidated vehicle card doesn't exist for this vehicle."))
                else:
                    raise ValidationError(
                        _("Vehicle card doesn't exist for the given VIN and driver ID. VIN: " + vin_number + ", Driver: " + self.partner_id.name))

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
        fleet_obj = self.env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin_number)], limit=1)
        action = self.env.ref("ars_reports.sale_action_service_history_invoice")
        return self.env.ref('ars_reports.sale_action_service_history_invoice').report_action(fleet_obj)
