from odoo import models, fields, api, registry, SUPERUSER_ID, sql_db, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date, datetime, time, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import contextlib
import logging
from odoo.sql_db import db_connect
from odoo.tools.float_utils import float_compare
from odoo.osv.expression import OR
from odoo.tools.safe_eval import safe_eval
from odoo import tools

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def check_consolidation_vehicle_card(self, vin_sn=None, line=None):
        fleet_obj = self.env['fleet.vehicle'].sudo()
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        db = sql_db.db_connect(f"{cons_db_name}")
        print(db)
        with contextlib.closing(db.cursor()) as cr:
            cr.autocommit(True)
            env = api.Environment(cr, SUPERUSER_ID, {})
            cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin_sn)], limit=1)
            vals = {}
            if line.product_id.default_code != cons_fleet_obj.mvariant_id.default_code:
                raise ValidationError(
                    _(f"You Cannot Purchase this Vehicle, Because Product Doesn't Match Consolidation {line.product_id.default_code}"))
            wholesale_data = {}
            if cons_fleet_obj:
                if cons_fleet_obj.vehicle_status == 'new':
                    last_rec = cons_fleet_obj.wholesale_ids.ids[-1] if cons_fleet_obj.wholesale_ids else False
                    if last_rec:
                        wholesale_id = env['wholesale.history'].sudo().browse(last_rec)
                        if self.env.user.company_id.dealer_code != wholesale_id.dealer_code:
                            raise ValidationError(
                                _(f" You Cannot Buy Vehicle, Because vehicle card Dealer Code Doesn't Match {str(wholesale_id.dealer_name)}"))
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
                    raise ValidationError(
                        _(f"You Cannot Purchase this vehicle, Because Vehicle Status not in New status {cons_fleet_obj.vehicle_status}"))
            else:
                raise ValidationError(_(f"VIN Couldn't Find in the Consolidation System: {vin_sn}"))

    def button_validate(self):
        fleet_obj = self.env['fleet.vehicle']
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
        db = sql_db.db_connect(f"{cons_db_name}")
        if is_cons_enable and cons_db_name:
            is_po = self.move_lines[0].purchase_line_id if self.move_lines else False
            is_so = self.move_lines[0].sale_line_id if self.move_lines else False
            po_order = is_po.order_id if self.move_lines else False
            if self.origin and 'Return of' in self.origin and self.picking_type_id.code == "outgoing" and is_po and po_order and po_order.purchase_type == 'vehicle' and po_order.product_catalog_id.name.strip().lower() == 'vehicle':
                vins = []
                for line in self.move_line_ids:
                    # if int(line.qty_done) == 0:
                    #     raise ValidationError(_(f"Quantity done 0 for product {line.product_id.name}"))
                    if not line:
                        raise ValidationError(_('No move lines present'))
                    vin = line.lot_name if line.lot_name else line.lot_id.name
                    if vin:
                        vins.append(vin)

                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', 'in', vins)])
                    for line in self.move_line_ids:
                        vin = line.lot_name if line.lot_name else line.lot_id.name
                        if vin:
                            con_vehicle = cons_fleet_obj.filtered(lambda x: x.vin_sn == vin)
                            if con_vehicle.mvariant_id.default_code != line.product_id.default_code:
                                raise ValidationError(_("Product does not match with consolidate db"))

                    fleet_obj_ = fleet_obj.sudo().search([('vin_sn', 'in', vins)])
                    for rec in cons_fleet_obj:
                        # vehicle = self.env['fleet.vehicle'].search([('vin_sn', '=', rec.vin_sn)], limit=1)
                        # if vehicle:
                        #     if rec.mvariant_id.default_code != vehicle.mvariant_id.default_code:
                        #         raise ValidationError(_("Product does not match with consolidate db"))
                        if rec.vehicle_status != 'new':
                            raise ValidationError(_(f"Vehicle status not new for VIN: {rec.vin_sn}"))
                        if rec.driver_id.dealer_code != self.company_id.dealer_code:
                            raise ValidationError(_(f"Customer not same in consolidation for VIN: {rec.vin_sn}"))
                        if rec.customer_ids:
                            raise ValidationError(
                                _(f"Ownership history already exists in consolidation for VIN: {rec.vin_sn}"))
                        record = rec.wholesale_ids.filtered(
                            lambda x: x.dealer_code == self.env.user.company_id.dealer_code)
                        if not record:
                            raise ValidationError(
                                _(f"Wholesale history not present for dealer {self.env.user.company_id} in consolidation for VIN: {rec.vin_sn}"))

                        if rec.service_ids:
                            service_type_code = env['service.type'].search([('name', '=', 'PDI Service')]).code

                            pdi_record = rec.service_ids.filtered(lambda x: x.service_code.strip() == service_type_code.strip())
                            if pdi_record:
                                raise ValidationError(_(f"PDI already created in consolidation for VIN: {rec.vin_sn}"))
                            else:
                                raise ValidationError(
                                    _(f"Service history already exists in consolidation for VIN: {rec.vin_sn}"))
                    for rec in fleet_obj_:
                        if rec.service_ids:
                            service_type_code = env['service.type'].search([('name', '=', 'PDI Service')]).code

                            pdi_record = rec.service_ids.filtered(lambda x: x.service_code.strip() == service_type_code.strip())
                            if pdi_record:
                                raise ValidationError(_(f"PDI already created for VIN: {rec.vin_sn}"))
                            else:
                                raise ValidationError(
                                    _(f"Service history already exists for VIN: {rec.vin_sn}"))

                    res = super(StockPicking, self).button_validate()
                    for rec in cons_fleet_obj:
                        record = rec.wholesale_ids.filtered(
                            lambda x: x.dealer_code == self.env.user.company_id.dealer_code)
                        if record:
                            for recc in record:
                                recc.write({'vehicle_received': False})

                    if self.partner_id.is_dealer:
                        for rec in fleet_obj_:
                            record = rec.wholesale_ids.filtered(
                                lambda x: x.dealer_code == self.env.user.company_id.dealer_code)
                            if record:
                                for recc in record:
                                    recc.write({'vehicle_received': False})
                    else:
                        for rec in fleet_obj_:
                            try:
                                # Delete the record
                                rec.sudo().unlink()
                                _logger.info(f"Deleted record with ID {rec.id}.")
                            except Exception as e:
                                _logger.error(f"Failed to delete record with ID {rec.id}: {e}")
                                raise ValidationError(_("Failed to delete record with ID %s: %s" % (rec.id, e)))
                    return res
            if self.origin and 'Return of' in self.origin and self.picking_type_id.code == "incoming" and is_so and self.sale_id.sale_type == 'vehicle':
                vins = []
                for line in self.move_line_ids:
                    # if int(line.qty_done) == 0:
                    #     raise ValidationError(_(f"Quantity done 0 for product {line.product_id.name}"))
                    if not line:
                        raise ValidationError(_('No move lines present'))
                    vin = line.lot_name if line.lot_name else line.lot_id.name
                    if vin:
                        vins.append(vin)

                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', 'in', vins)])
                    fleet_obj_ = fleet_obj.sudo().search([('vin_sn', 'in', vins)])

                    for line in self.move_line_ids:
                        vin = line.lot_name if line.lot_name else line.lot_id.name
                        if vin:
                            con_vehicle = cons_fleet_obj.filtered(lambda x: x.vin_sn == vin)
                            if con_vehicle.mvariant_id.default_code != line.product_id.default_code:
                                raise ValidationError(_("Product does not match with consolidate db"))

                    # for rec in cons_fleet_obj:
                    #     vehicle = self.env['fleet.vehicle'].search([('vin_sn', '=', rec.vin_sn)], limit=1)
                    #     if vehicle:
                    #         if rec.mvariant_id.default_code != vehicle.mvariant_id.default_code:
                    #             raise ValidationError(_("Product does not match with consolidate db"))
                    if self.partner_id.is_dealer:
                        for rec in cons_fleet_obj:
                            if rec.wholesale_ids:
                                wholesale_rec = rec.wholesale_ids.filtered(
                                    lambda x: x.dealer_code == self.partner_id.dealer_code)
                                for wh_rec in wholesale_rec:
                                    if wh_rec.vehicle_received:
                                        raise ValidationError(
                                            _(f"Vehicle already received, Please return the purchase order first"))
                                if not wholesale_rec:
                                    raise ValidationError(
                                        _(f"Wholesale history not exists for the dealer {self.partner_id.name} in consolidation for VIN: {rec.vin_sn}"))
                            else:
                                raise ValidationError(
                                    _(f"Wholesale history not exists in consolidation for VIN: {rec.vin_sn}"))
                            if rec.vehicle_status != 'new':
                                raise ValidationError(_(f"Vehicle status not new for VIN: {rec.vin_sn}"))
                            if rec.driver_id.dealer_code != self.partner_id.dealer_code:
                                raise ValidationError(
                                    _(f"Dealer not same in picking and consolidation for VIN: {rec.vin_sn}"))
                            if rec.customer_ids:
                                raise ValidationError(
                                    _(f"Ownership history already exists in consolidation for VIN: {rec.vin_sn}"))

                            if rec.service_ids:
                                raise ValidationError(
                                    _(f"Service history already exists in consolidation for VIN: {rec.vin_sn}"))

                        for rec in fleet_obj_:
                            if rec.vehicle_status != 'new':
                                raise ValidationError(_(f"Vehicle status not new for VIN: {rec.vin_sn}"))
                            if rec.driver_id.dealer_code != self.partner_id.dealer_code:
                                raise ValidationError(
                                    _(f"Dealer not same in picking and vehicle card for VIN: {rec.vin_sn}"))
                            if rec.customer_ids:
                                raise ValidationError(
                                    _(f"Ownership history already exists in vehicle card for VIN: {rec.vin_sn}"))
                            if rec.wholesale_ids:
                                wholesale_rec = rec.wholesale_ids.filtered(
                                    lambda x: x.dealer_code == self.partner_id.dealer_code)
                                if not wholesale_rec:
                                    raise ValidationError(
                                        _(f"Wholesale history not exists for the dealer {self.partner_id.name} in vehicle card for VIN: {rec.vin_sn}"))
                            else:
                                raise ValidationError(
                                    _(f"Wholesale history not exists in vehicle card for VIN: {rec.vin_sn}"))

                            if rec.service_ids:
                                # pdi_record = rec.service_ids.filtered(lambda x: x.service_code.strip()) == 'ST0007'
                                # if pdi_record:
                                #     pass
                                # else:
                                #     raise ValidationError(
                                #         _(f"Service history already exists in consolidation for VIN: {rec.vin_sn}"))
                                raise ValidationError(
                                    _(f"Service history already exists in vehicle card for VIN: {rec.vin_sn}"))
                        res = super(StockPicking, self).button_validate()
                        for rec in cons_fleet_obj:
                            if rec.wholesale_ids:
                                wholesale_rec = rec.wholesale_ids.filtered(
                                    lambda x: x.dealer_code == self.partner_id.dealer_code)
                                for who_rec in wholesale_rec:
                                    who_rec.unlink()
                            dealer = env['res.partner'].search([('dealer_code','=',self.env.user.company_id.partner_id.dealer_code)], limit=1)
                            rec.write({'vehicle_status': 'new', 'driver_id': dealer.id,
                                       'contact_name': dealer.id})
                        for rec in fleet_obj_:
                            if rec.wholesale_ids:
                                wholesale_rec = rec.wholesale_ids.filtered(
                                    lambda x: x.dealer_code == self.partner_id.dealer_code)
                                for who_rec in wholesale_rec:
                                    who_rec.unlink()

                            rec.write({'vehicle_status': 'new', 'driver_id': self.env.user.company_id.partner_id.id,
                                       'contact_name': self.env.user.company_id.partner_id.id})
                        return res
                    else:
                        for rec in cons_fleet_obj:
                            if rec.vehicle_status != 'customer':
                                raise ValidationError(_(f"Vehicle status not customer for VIN: {rec.vin_sn}"))
                            if rec.driver_id.name.strip() != self.partner_id.name.strip():
                                raise ValidationError(
                                    _(f"Customer not same in picking and consolidation for VIN: {rec.vin_sn}"))
                            if rec.customer_ids:
                                owner_details = rec.customer_ids.filtered(
                                    lambda x: x.custmer_name.name.strip() == self.partner_id.name.strip())
                                if not owner_details:
                                    raise ValidationError(
                                        _(f"Ownership history not exists in consolidation for VIN: {rec.vin_sn} for customer {self.partner_id.name}"))
                            if not rec.customer_ids:
                                raise ValidationError(
                                    _(f"Ownership history not exists in consolidation for VIN: {rec.vin_sn}"))

                            if rec.wholesale_ids:
                                wholesale_rec = rec.wholesale_ids.filtered(
                                    lambda x: x.dealer_code == self.env.user.company_id.dealer_code)
                                if not wholesale_rec:
                                    raise ValidationError(
                                        _(f"Wholesale history not exists for the dealer {self.env.user.company_id.name} in consolidation for VIN: {rec.vin_sn}"))
                            else:
                                raise ValidationError(
                                    _(f"Wholesale history not exists in consolidation for VIN: {rec.vin_sn}"))

                            if rec.service_ids:
                                service_type_code = env['service.type'].search([('name', '=', 'PDI Service')]).code
                                pdi_record = rec.service_ids.filtered(lambda x: x.service_code.strip() == service_type_code.strip())

                                if pdi_record:
                                    pass
                                else:
                                    raise ValidationError(
                                        _(f"Service history already exists in consolidation or PDI not created for VIN: {rec.vin_sn}"))

                        for rec in fleet_obj_:
                            if rec.vehicle_status != 'customer':
                                raise ValidationError(_(f"Vehicle status not customer for VIN: {rec.vin_sn}"))
                            if rec.driver_id.name.strip() != self.partner_id.name.strip():
                                raise ValidationError(
                                    _(f"Customer not same in picking and consolidation for VIN: {rec.vin_sn}"))
                            if rec.customer_ids:
                                owner_details = rec.customer_ids.filtered(
                                    lambda x: x.custmer_name.name.strip() == self.partner_id.name.strip())
                                if not owner_details:
                                    raise ValidationError(
                                        _(f"Ownership history not exists for VIN: {rec.vin_sn} for customer {self.partner_id.name}"))
                            else:
                                raise ValidationError(
                                    _(f"Ownership history does not exists for VIN: {rec.vin_sn}"))
                            if rec.wholesale_ids:
                                wholesale_rec = rec.wholesale_ids.filtered(
                                    lambda x: x.dealer_code == self.env.user.company_id.dealer_code)
                                if not wholesale_rec:
                                    raise ValidationError(
                                        _(f"Wholesale history not exists for the dealer {self.env.user.company_id.name} in consolidation for VIN: {rec.vin_sn}"))
                            else:
                                raise ValidationError(
                                    _(f"Wholesale history not exists in consolidation for VIN: {rec.vin_sn}"))

                            if rec.service_ids:
                                service_type_code = env['service.type'].search([('name', '=', 'PDI Service')]).code

                                pdi_record = rec.service_ids.filtered(lambda x: x.service_code.strip() == service_type_code.strip())
                                if pdi_record:
                                    pass
                                else:
                                    raise ValidationError(
                                        _(f"Service history already exists in consolidation for VIN: {rec.vin_sn}"))

                        res = super(StockPicking, self).button_validate()
                        for rec in cons_fleet_obj:
                            if rec.customer_ids:
                                owner_details = rec.customer_ids.filtered(
                                    lambda x: x.custmer_name.name.strip() == self.partner_id.name.strip())
                                if owner_details:
                                    for recc in owner_details:
                                        recc.unlink()
                            dealer = env['res.partner'].search([('dealer_code','=',self.env.user.company_id.partner_id.dealer_code)], limit=1)
                            rec.write({'vehicle_status': 'new', 'driver_id': dealer.id,
                                       'contact_name': dealer.id})
                        for rec in fleet_obj_:
                            if rec.customer_ids:
                                owner_details = rec.customer_ids.filtered(
                                    lambda x: x.custmer_name.name.strip() == self.partner_id.name.strip())
                                if owner_details:
                                    for recc in owner_details:
                                        recc.unlink()
                            rec.write({'vehicle_status': 'new', 'driver_id': self.env.user.company_id.partner_id.id,
                                       'contact_name': self.env.user.company_id.partner_id.id})
                        return res

            if self.picking_type_id.code == "incoming" and is_po:
                po_id = self.move_lines[0].purchase_line_id.order_id if self.move_lines else False
                if po_id and po_id.purchase_type == 'vehicle' and po_id.product_catalog_id.name.strip().lower() == 'vehicle':
                    vins = [line.lot_name if line.lot_name else line.lot_id.name
                            for line in self.move_line_ids if line]
                    if not vins:
                        raise ValidationError(_('Please add some line'))
                    existing_vehicle = self.env['fleet.vehicle'].sudo().search([('vin_sn', 'in', vins)])
                    with contextlib.closing(db.cursor()) as cr:
                        cr.autocommit(True)
                        env = api.Environment(cr, SUPERUSER_ID, {})
                        cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', 'in', vins)])

                        for line in self.move_line_ids:
                            vin = line.lot_name if line.lot_name else line.lot_id.name
                            if vin:
                                con_vehicle = cons_fleet_obj.filtered(lambda x: x.vin_sn == vin)
                                if con_vehicle.mvariant_id.default_code != line.product_id.default_code:
                                    raise ValidationError(_("Product does not match with consolidate db"))

                        # for rec in cons_fleet_obj:
                        #     vehicle = self.env['fleet.vehicle'].search([('vin_sn', '=', rec.vin_sn)], limit=1)
                        #     if vehicle:
                        #         if rec.mvariant_id.default_code != vehicle.mvariant_id.default_code:
                        #             raise ValidationError(_("Product does not match with consolidate db"))
                        if existing_vehicle and self.partner_id.is_dealer == True:
                            dealer_sorted_wholesale_ids = existing_vehicle.wholesale_ids.sorted(
                                key=lambda r: r.create_date,
                                reverse=True)
                            cons_sorted_wholesale_ids = cons_fleet_obj.wholesale_ids.sorted(key=lambda r: r.create_date,
                                                                                            reverse=True)
                            if dealer_sorted_wholesale_ids and cons_sorted_wholesale_ids:
                                if dealer_sorted_wholesale_ids[
                                   :1].dealer_code == self.env.user.company_id.dealer_code and \
                                        cons_sorted_wholesale_ids[
                                        :1].dealer_code == self.env.user.company_id.dealer_code:
                                    pass
                                else:
                                    raise ValidationError(
                                        _(f"Vehicle Card already exists for VIN: {existing_vehicle.vin_sn}"))
                        if existing_vehicle and self.partner_id.is_dealer == False:
                            raise ValidationError(
                                _(f"Vehicle Card already exists for VIN: {existing_vehicle.vin_sn}"))
                        else:
                            pass
                        res = super(StockPicking, self).button_validate()

                        for rec in cons_fleet_obj:
                            for record in rec.wholesale_ids:
                                if record.dealer_code == self.env.user.company_id.dealer_code:
                                    record.sudo().write({'vehicle_received': True})
                        for line in self.move_line_ids:
                            vin = line.lot_name if line.lot_name else line.lot_id.name
                            if vin and (
                                    line.move_id.product_catalog_id.code.strip() == "VEH" or line.move_id.product_catalog_id.name.strip() == "Vehicle"):
                                if not str(vin).isalnum():
                                    raise ValidationError(_('VIN is not Alphanumeric'))
                                if len(vin) != 17:
                                    raise ValidationError(
                                        _('VIN Have %s Characters. It Should be 17') % len(vin))
                                vals = {'model_id': line.move_id.product_id.product_tmpl_id.id,
                                        'mvariant_id': line.move_id.product_id.id,
                                        'vehicle_status': 'new',
                                        'vin_sn': line.lot_name if line.lot_name else line.lot_id.name,
                                        'categ_id': line.move_id.product_id.product_tmpl_id.categ_id.id,
                                        'license_plate': '/',
                                        'driver_id': self.env.user.company_id.partner_id.id,
                                        'contact_name': self.env.user.company_id.partner_id.id,
                                        'engine_number': line.motor_number,
                                        'key_serial_number': line.battery_number,
                                        'po_ref': po_id.name}

                            vehicle_card = fleet_obj.sudo().search([('vin_sn', '=', vin)], limit=1)
                            if not vehicle_card:
                                vehicle_card = fleet_obj.sudo().create(vals)
                                vin_sn = vin
                                consolidation_data = self.check_consolidation_vehicle_card(vin_sn, line)
                                if consolidation_data:
                                    wholesale_data = consolidation_data.get('wholesale_data', {})
                                    if wholesale_data:
                                        vals.update(
                                            {'consolidate_vehicle_card_id': consolidation_data.get('vehicle_card_id')})
                                        wholesale_obj = self.env['wholesale.history'].create({
                                            'vehicle_id': vehicle_card.id,
                                            'dealer_name': wholesale_data.get('dealer_name'),
                                            'so_number': wholesale_data.get('so_number'),
                                            'so_id': wholesale_data.get('so_id'),
                                            'delivery_date': wholesale_data.get('delivery_date'),
                                            'invoice_number': wholesale_data.get('invoice_number'),
                                            'invoice_id': wholesale_data.get('invoice_id'),
                                            'po_number': wholesale_data.get('po_number'),
                                            'transfer_type': wholesale_data.get('transfer_type'),
                                            'dealer_code': wholesale_data.get('dealer_code')
                                        })
                        fleet_obj_vins = fleet_obj.sudo().search([('vin_sn', 'in', vins)])
                        for rec in fleet_obj_vins:
                            for record in rec.wholesale_ids:
                                if record.dealer_code == self.env.user.company_id.dealer_code:
                                    record.sudo().write({'vehicle_received': True})
                    return res
                # else:
                #     res = super(StockPicking, self).button_validate()
                #     return res
            if self.picking_type_id.code == "outgoing" and self.sale_id.sale_type == "vehicle" and is_so:
                vins = [line.lot_name if line.lot_name else line.lot_id.name
                        for line in self.move_line_ids if line]
                if not vins:
                    raise ValidationError(_('Please add some line'))
                existing_vins = fleet_obj.sudo().search([('vin_sn', 'in', vins)])
                if not existing_vins or len(existing_vins) != len(vins):
                    raise ValidationError(
                        _("Some VINs are missing in the Current system. Please check the provided VINs."))

                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    for vin in vins:
                        vehicle_card = fleet_obj.sudo().search([('vin_sn', '=', vin)], limit=1)
                        cons_fleet_obj = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin)], limit=1)
                        if vehicle_card and cons_fleet_obj:
                            if vehicle_card.mvariant_id.default_code != cons_fleet_obj.mvariant_id.default_code:
                                raise ValidationError(_("Product does not match with consolidate db"))

                        if cons_fleet_obj.vehicle_status != 'new' or vehicle_card.vehicle_status != 'new':
                            raise ValidationError(
                                _("Vehicle Status Not in New Status for VIN: %s. Operation not allowed." % vin))

                        service_count = len(cons_fleet_obj.service_ids)
                        if service_count <= 0 and self.partner_id.is_dealer == False:
                            raise ValidationError(_("Please Do PDI Service Before selling this Vehicle"))
                        if service_count >= 1:
                            service_type_code = env['service.type'].search([('name', '=', 'PDI Service')]).code
                            cons_service_ids = [service.cons_service_history_id for service in
                                                vehicle_card.service_ids]
                            service_codes = cons_fleet_obj.service_ids.mapped('service_code')
                            if service_type_code not in service_codes:
                                raise ValidationError(
                                    _("Should be Complete PDI Service Before Selling this Vehicle"))
                            for con_service in cons_fleet_obj.service_ids:
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
                                        'dealer_db_name': con_service.dealer_db_name,
                                        'cons_service_history_id': con_service.id,  # Add this to link the record
                                    }
                                    self.env['service.history'].sudo().create(service_vals)
                    res = super(StockPicking, self).button_validate()
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
                                vehicle_card.write({'driver_id': self.sale_id.partner_id.id,
                                                    'contact_name': self.sale_id.partner_id.id})
                                consolidate_vehicle_card = env['fleet.vehicle'].sudo().browse(
                                    vehicle_card.consolidate_vehicle_card_id)
                                if not consolidate_vehicle_card:
                                    consolidate_vehicle_card = cons_fleet_obj
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
                                    company_obj = env['res.company'].sudo().search(
                                        [('dealer_code', '=', self.sale_id.partner_id.dealer_code)], limit=1)
                                    consolidate_vehicle_card.write({'driver_id': company_obj.partner_id.id,
                                                                    'contact_name': company_obj.partner_id.id})
                                    return res

                    else:
                        for line in self.move_line_ids:
                            vin_sn = line.lot_id.name if line.lot_id else line.lot_name
                            vehicle_card = fleet_obj.sudo().search([('vin_sn', '=', vin_sn)], limit=1)

                            if not vehicle_card:
                                continue

                            db_name = self._cr.dbname
                            partner = self.sale_id.partner_id
                            dealer_master_id = env['ars.consolidation.setup'].sudo().search(
                                [('dealer_code', '=', self.env.user.company_id.dealer_code)], limit=1)
                            current_dealer_code = self.env.user.company_id.dealer_code
                            customer_code = partner.customer_code or f"{db_name}_{partner.id}"

                            ownership_data = {
                                'custmer_name': partner.id,
                                'date_of_ownership': datetime.now(),
                                'address': partner.city,
                                'mobile': partner.mobile,
                                'sold_by': self.env.user.company_id.partner_id.id,
                            }
                            vehicle_card.write({
                                'customer_ids': [(0, 0, ownership_data)],
                                'driver_id': partner.id,
                                'contact_name': partner.id,
                                'vehicle_status': 'customer'
                            })

                            if vehicle_card.driver_id:
                                current_card = vehicle_card.driver_id
                                current_customer_card = self.env['res.partner'].sudo().browse(current_card.id)
                                current_parent = current_customer_card.parent_id
                            consolidate_vehicle_card = env['fleet.vehicle'].sudo().browse(
                                vehicle_card.consolidate_vehicle_card_id) if vehicle_card.consolidate_vehicle_card_id else None
                            if not consolidate_vehicle_card:
                                consolidate_vehicle_card = env['fleet.vehicle'].sudo().search(
                                    [('vin_sn', '=', vin_sn)], limit=1)
                            if not consolidate_vehicle_card:
                                raise ValidationError(_("Vehicle card Missing in Consolidated Database"))
                            # --- Sync Parent Contact in Consolidation DB ---
                            cons_parent = False
                            if current_parent:
                                cons_parent_domain = []
                                if current_parent.customer_code:
                                    cons_parent_domain.append(('customer_code', '=', current_parent.customer_code))
                                if current_parent.email:
                                    cons_parent_domain.append(('email', '=', current_parent.email))
                                if current_parent.mobile:
                                    cons_parent_domain.append(('mobile', '=', current_parent.mobile))

                                final_domain = []
                                for condition in cons_parent_domain:
                                    final_domain = OR([final_domain, [condition]])
                                cons_parent = env['res.partner'].sudo().search(final_domain, limit=1)
                                if not cons_parent:
                                    duplicate_mobile = self.env['res.partner'].sudo().search([('mobile','=',current_parent.mobile)]).filtered(lambda x: not x.parent_id)
                                    for partner in duplicate_mobile:
                                        if partner.company_type == 'company':
                                            cons_parent = env['res.partner'].sudo().create({
                                                'name': partner.name,
                                                'company_type': 'company',
                                                'customer': False,
                                                'supplier': False,
                                                'active': True,
                                                'customer_code': customer_code,
                                                'city': partner.city,
                                                'street': partner.street
                                            })
                                            _logger.info("Created parent in consolidation DB: %s", cons_parent.name)
                                            if partner.child_ids:
                                                for rec in partner.child_ids:
                                                   child_vals = {
                                                        'name': rec.name,
                                                        'company_type': 'person',
                                                        'customer': False,
                                                        'supplier': False,
                                                        'active': True,
                                                        'parent_id': cons_parent.id,
                                                        'customer_code':customer_code,
                                                        'city': rec.city,
                                                        'mobile': rec.mobile,
                                                        'email': rec.email,
                                                        'street': rec.street
                                                    }
                                                   cons_childs = env['res.partner'].sudo().create(child_vals)
                            elif partner.company_type == 'person':
                                existing_partner = env['res.partner'].sudo().search([
                                    '|', '|',
                                    ('mobile', '=', partner.mobile),
                                    ('customer_code', '=', customer_code),
                                    ('email', '=', partner.email),
                                ],limit=1)
                                if not existing_partner:
                                    cons_customer = env['res.partner'].sudo().create({
                                        'name': partner.name,  # use current_parent for child's name
                                        'email': partner.email,
                                        'mobile': partner.mobile,
                                        'city': partner.city,
                                        'street': partner.street,
                                        'phone': partner.phone,
                                        'company_type': 'person',
                                        'is_dealer': False,
                                        'customer_code': customer_code,
                                        'customer': True,
                                    })
                            company_id = env['res.company'].sudo().search([('dealer_code', '=', current_dealer_code)])
                            search_domain = ['|',
                                             ('mobile', '=', partner.mobile),
                                             ('email', '=', partner.email)
                                             ]

                            if cons_parent:
                                # search_domain.append(('parent_id', '=', cons_parent.id))
                                search_domain = ['|'] + search_domain + [('parent_id', '=', cons_parent.id)]
                            cons_customer = env['res.partner'].sudo().search(search_domain, limit=1)
                            cons_ownership_data = {
                                'custmer_name': cons_customer.id,
                                'date_of_ownership': datetime.now(),
                                'address': cons_customer.city,
                                'mobile': cons_customer.mobile,
                                'dealer_id': dealer_master_id.id,
                                'sold_by': company_id.partner_id.id,
                            }
                            consolidate_vehicle_card.write({
                                'customer_ids': [(0, 0, cons_ownership_data)],
                                'driver_id': cons_customer.id,
                                'contact_name': cons_customer.id,
                                'vehicle_status': 'customer'
                            })
                        return super(StockPicking, self).button_validate()
            return super(StockPicking, self).button_validate()
        else:
            res = super(StockPicking, self).button_validate()
            return res


class StockQuant(models.Model):
    _inherit = 'stock.quant'
    _description = 'Quants'

    @api.constrains('quantity')
    def check_quantity(self):
        for quant in self:
            if (
                    float_compare(quant.quantity, 1, precision_rounding=quant.product_uom_id.rounding) > 0
                    and quant.lot_id
                    and quant.product_id.tracking == 'serial'
                    and quant.company_id.id == quant.lot_id.company_id.id  # Ensure same company
            ):
                message_base = _('A serial number should only be linked to a single product.')
                message_quant = _('Please check the following serial number (name, id): ')
                message_sn = '(%s, %s)' % (quant.lot_id.name, quant.lot_id.id)
                raise ValidationError("\n".join([message_base, message_quant, message_sn]))
