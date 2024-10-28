from odoo import models, fields, api, registry, SUPERUSER_ID, sql_db, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date, datetime, time, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import contextlib
import logging
from odoo.sql_db import db_connect

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def check_consolidation_vehicle_card(self, vin_sn=None, line=None):
            fleet_obj = self.env['fleet.vehicle'].sudo()
            param = self.env['ir.config_parameter'].sudo()
            cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
            db = sql_db.db_connect(f"{cons_db_name}")
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin_sn)], limit=1)
                vals = {}
                if line.product_id.default_code != cons_fleet_obj.mvariant_id.default_code:
                    raise ValidationError(_(f"You Cannot Purchase this Vehicle, Because Product Doesn't Match Consolidation {line.product_id.default_code}"))
                wholesale_data = {}
                if cons_fleet_obj:
                    if cons_fleet_obj.vehicle_status == 'new':
                        last_rec = cons_fleet_obj.wholesale_ids.ids[-1] if cons_fleet_obj.wholesale_ids else False
                        if last_rec:
                            wholesale_id = env['wholesale.history'].sudo().browse(last_rec)
                            if self.env.user.company_id.dealer_code != wholesale_id.dealer_code:
                                raise ValidationError(_(f" You Cannot Buy Vehicle, Because vehicle card Dealer Code Doesn't Match {str(wholesale_id.dealer_name)}"))
                            if self.env.user.company_id.dealer_code == wholesale_id.dealer_code:
                                wholesale_data.update({
                                    'dealer_name': wholesale_id.dealer_name,
                                    'so_number': wholesale_id.so_number,
                                    'so_id': wholesale_id.so_id,
                                    'delivery_date': wholesale_id.delivery_date,
                                    'invoice_number': wholesale_id.invoice_number if wholesale_id.invoice_number else '',
                                    'invoice_id': wholesale_id.invoice_id if wholesale_id.invoice_id else '',
                                    'po_number': wholesale_id.po_number if wholesale_id.po_number else '',
                                    'transfer_type': wholesale_id.transfer_type,
                                    'dealer_code': wholesale_id.dealer_code
                                })

                                vals.update({'wholesale_data': wholesale_data, 'vehicle_card_id': cons_fleet_obj.id})
                                return vals
                        else:
                            raise ValidationError(_("You Cannot Buy vehicle without Wholesale History "))
                    else:
                        raise ValidationError(_(f"You Cannot Purchase this vehicle, Because Vehicle Status not in New status {cons_fleet_obj.vehicle_status}"))
                else:
                    raise ValidationError(_(f"VIN Couldn't Find in the Consolidation System: {vin_sn}"))

    def button_validate(self):
        fleet_obj = self.env['fleet.vehicle']
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
        db = sql_db.db_connect(f"{cons_db_name}")
        if is_cons_enable and cons_db_name:
            if self.picking_type_id.code == "incoming":
                vins = [line.lot_name if line.lot_name else line.lot_id.name
                        for line in self.move_line_ids if line]
                if not vins:
                    raise ValidationError(_('Please add some line'))
                existing_vehicle = self.env['fleet.vehicle'].sudo().search([('vin_sn', 'in', vins)])
                if existing_vehicle:
                    raise ValidationError(_(f"Vehicle Card already exists for VIN: {existing_vehicle.vin_sn}"))
                res = super(StockPicking, self).button_validate()
                return res
            if self.picking_type_id.code == "outgoing" and self.sale_id.sale_type =="vehicle":
                vins = [line.lot_name if line.lot_name else line.lot_id.name
                        for line in self.move_line_ids if line]
                if not vins:
                    raise ValidationError(_('Please add some line'))
                existing_vins = fleet_obj.sudo().search([('vin_sn', 'in', vins)])
                if not existing_vins or len(existing_vins) != len(vins):
                    raise ValidationError(_("Some VINs are missing in the Current system. Please check the provided VINs."))

                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    for vin in vins:
                        vehicle_card = fleet_obj.sudo().search([('vin_sn', '=', vin)], limit=1)
                        cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin)], limit=1)

                        if cons_fleet_obj.vehicle_status != 'new' or vehicle_card.vehicle_status != 'new':
                            raise ValidationError(
                                _("Vehicle Status Not in New Status for VIN: %s. Operation not allowed." % vin))

                        service_count = len(cons_fleet_obj.service_ids)
                        if service_count <= 0:
                            raise ValidationError(_("Please Do PDI Service Before selling this Vehicle"))
                        if service_count >= 1:
                            service_type_code = env['service.type'].search([('name', '=', 'PDI Service')]).code
                            cons_service_ids = [service.cons_service_history_id for service in
                                                vehicle_card.service_ids]
                            for con_service in cons_fleet_obj.service_ids:
                                if not con_service.service_code == service_type_code:
                                    raise ValidationError(
                                        _("Should be Complete PDI Service Before Selling this Vehicle"))
                                if con_service.id not in cons_service_ids:
                                    service_vals = {
                                        'vehicle_id': vehicle_card.id,
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
                                    self.env['service.history'].sudo().create(service_vals)
                    if self.sale_id.partner_id.is_dealer:
                        for vin in vins:
                            vehicle_card = fleet_obj.sudo().search([('vin_sn', '=', vin)], limit=1)
                            cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin)], limit=1)
                            vals = {
                                'vehicle_id': vehicle_card.id,
                                'dealer_name': self.sale_id.partner_id.name,
                                'so_number': self.origin,
                                'so_id': self.sale_id.id,
                                'delivery_date': datetime.today(),
                                'invoice_number': '',
                                'invoice_id': '',
                                'transfer_type': 'internal_transfer',
                                'dealer_code': self.sale_id.partner_id.dealer_code
                            }
                            wholesale_obj = self.env['wholesale.history'].sudo().create(vals)
                            if wholesale_obj:
                                vehicle_card.write({'driver_id':self.sale_id.partner_id.id, 'contact_name':self.sale_id.partner_id.id})
                                consolidate_vehicle_card = env['fleet.vehicle'].sudo().browse(
                                    vehicle_card.consolidate_vehicle_card_id)
                                dealer_master_id = env['ars.consolidation.setup'].sudo().search(
                                    [('dealer_code', '=', self.sale_id.partner_id.dealer_code)], limit=1)

                                cons_wholesale_vals = {
                                    'vehicle_id': consolidate_vehicle_card.id,
                                    'dealer_name': self.sale_id.partner_id.name,
                                    'so_number': self.origin,
                                    'so_id': self.sale_id.id,
                                    'delivery_date': datetime.today(),
                                    'invoice_number': '',
                                    'invoice_id': '',
                                    'transfer_type': 'internal_transfer',
                                    'dealer_code': self.sale_id.partner_id.dealer_code,
                                    'dealer_master_id': dealer_master_id.id
                                }

                                cons_wholesale_obj = env['wholesale.history'].sudo().create(cons_wholesale_vals)
                                _logger.info("consolidation wholesale history created")
                                if cons_wholesale_obj:
                                    company_obj = env['res.company'].sudo().search([('dealer_code','=',self.sale_id.partner_id.dealer_code)], limit=1)
                                    consolidate_vehicle_card.write({'driver_id':company_obj.partner_id.id,'contact_name':company_obj.partner_id.id})
                                    return super(StockPicking, self).button_validate()

                    else:
                        for line in self.move_line_ids:
                            vin_sn = line.lot_id.name if line.lot_id else line.lot_name
                            vehicle_card = fleet_obj.sudo().search([('vin_sn', '=', vin_sn)], limit=1)

                            if vehicle_card:
                                db_name = self._cr.dbname
                                customer_code = self.sale_id.partner_id.customer_code or f"{db_name}_{self.sale_id.partner_id.id}"
                                dealer_master_id = env['ars.consolidation.setup'].sudo().search(
                                    [('dealer_code', '=', self.env.user.company_id.dealer_code)], limit=1)
                                ownership_data = {
                                    'custmer_name': self.sale_id.partner_id.id,
                                    'date_of_ownership': datetime.now(),
                                    'address': self.sale_id.partner_id.city,
                                    'mobile': self.sale_id.partner_id.mobile,
                                    # 'dealer_id':dealer_master_id.id,
                                    'sold_by': self.env.user.company_id.partner_id.id,
                                }
                                vehicle_card.customer_ids = [(0, 0, ownership_data)]
                                vehicle_card.write({'driver_id': self.sale_id.partner_id.id, 'contact_name':self.sale_id.partner_id.id,'vehicle_status': 'customer'})
                                consolidate_vehicle_card = env['fleet.vehicle'].sudo().browse(
                                    vehicle_card.consolidate_vehicle_card_id)
                                if not consolidate_vehicle_card:
                                    raise ValidationError(_("Vehicle card Missing in Consolidated Database"))

                                consolidate_customer_obj = env['res.partner'].sudo()
                                email, mobile = self.sale_id.partner_id.email, self.sale_id.partner_id.mobile
                                cons_customer_obj = consolidate_customer_obj.search([
                                    '|', '|',
                                    ('email', '=', email),
                                    ('mobile', '=', mobile),
                                    ('customer_code', '=', customer_code)
                                ], limit=1)

                                if not cons_customer_obj:
                                    new_customer_data = {
                                        'name': self.sale_id.partner_id.name,
                                        'email': email,
                                        'mobile': mobile,
                                        'city': self.sale_id.partner_id.city,
                                        'phone': self.sale_id.partner_id.phone,
                                        'is_dealer': False,
                                        'customer_code': customer_code
                                    }
                                    new_customer = consolidate_customer_obj.sudo().create(new_customer_data)
                                    _logger.info("New Customer Created in consolidation database %s", new_customer)

                                    company_id = env['res.company'].sudo().search(
                                        [('dealer_code', '=', self.env.user.company_id.dealer_code)])
                                    dealer_master_id = env['ars.consolidation.setup'].sudo().search(
                                        [('dealer_code', '=', self.env.user.company_id.dealer_code)], limit=1)
                                    cons_ownership_data = {
                                        'custmer_name': new_customer.id,
                                        'date_of_ownership': datetime.now(),
                                        'address': new_customer.city,
                                        'mobile': new_customer.mobile,
                                        'dealer_id': dealer_master_id.id,
                                        'sold_by': company_id.partner_id.id,
                                    }
                                    consolidate_vehicle_card.customer_ids = [(0, 0, cons_ownership_data)]
                                    consolidate_vehicle_card.write(
                                        {'driver_id': new_customer.id, 'contact_name':new_customer.id,'vehicle_status': 'customer'})
                                else:
                                    existing_customer = cons_customer_obj[0]
                                    company_id = env['res.company'].sudo().search([('dealer_code', '=', self.env.user.company_id.dealer_code)])
                                    dealer_master_id = env['ars.consolidation.setup'].sudo().search(
                                        [('dealer_code', '=', self.env.user.company_id.dealer_code)], limit=1)
                                    cons_ownership_data = {
                                        'custmer_name': existing_customer.id,
                                        'date_of_ownership': datetime.now(),
                                        'address': existing_customer.city,
                                        'mobile': existing_customer.mobile,
                                        'dealer_id': dealer_master_id.id,
                                        'sold_by': company_id.partner_id.id,
                                    }
                                    consolidate_vehicle_card.customer_ids = [(0, 0, cons_ownership_data)]
                                    consolidate_vehicle_card.write(
                                        {'driver_id': existing_customer.id, 'contact_name':existing_customer.id, 'vehicle_status': 'customer'})
                                    _logger.info("Ownership history updated consolidation database %s", consolidate_vehicle_card.id)
                        return super(StockPicking, self).button_validate()
        else:
            res = super(StockPicking, self).button_validate()
            return res
