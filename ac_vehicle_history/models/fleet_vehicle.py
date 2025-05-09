from logging import exception

from odoo import models, fields, api, _, SUPERUSER_ID, sql_db
from werkzeug.routing import ValidationError
from lxml import etree
import contextlib
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    wholesale_ids = fields.One2many('wholesale.history', 'vehicle_id', string="Wholesale History")
    service_type_sequence = fields.Integer(string="Service Type Sequence", compute='compute_service_type_sequence')
    po_ref = fields.Char(string="PO Ref")

    #Added For to enable/disable the create button through setup.
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        template_result = super(FleetVehicle, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                 submenu=submenu)
        doc = etree.XML(template_result['arch'])
        param = self.env['ir.config_parameter'].sudo()
        is_vehicle_creation_enable = param.get_param('ac_vehicle_history.is_vehicle_create')
        if not is_vehicle_creation_enable:
            doc.set('create', 'false')
        template_result['arch'] = etree.tostring(doc)
        return template_result

    # @api.model
    # def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    #     template_result = super(FleetVehicle, self).fields_view_get(view_id=view_id,view_type=view_type, toolbar=toolbar,submenu=submenu)
    #     doc = etree.XML(template_result['arch'])
    #     doc.set('create', 'false')
    #     template_result['arch'] = etree.tostring(doc)
    #     return template_result

    @api.constrains('active')
    def check_vehicle_card(self):
        for rec in self:
            if len(rec.service_ids) >= 1 and len(rec.customer_ids) >= 1 and len(rec.insurance_ids) >= 1 and len(
                    rec.emission_ids) >= 1 and len(rec.wholesale_ids) >= 1:
                raise ValidationError("You Cannot Archive Entries Contains Vehicle Card")

    @api.multi
    def unlink(self):
        for rec in self:
            if len(rec.service_ids) >= 1 and len(rec.customer_ids) >= 1 and len(rec.insurance_ids) >= 1 and len(
                    rec.emission_ids) >= 1 and len(rec.wholesale_ids) >= 1:
                raise ValidationError("You Cannot Delete Entries Contains Vehicle Card")
        return super(FleetVehicle, self).unlink()

    # @api.depends('service_ids')
    # @api.multi
    def compute_service_type_sequence(self):
        for rec in self:
            service_types = self.env['service.type'].sudo().search(
                [('code', 'in', rec.service_ids.mapped('service_code'))])
            if service_types:
                max_sequence = max(service_types.mapped('sequence'))
                rec.service_type_sequence = max_sequence

            # last_service_history = rec.service_ids.sorted(id, reverse=True)[:1]
            # print(last_service_history,'last_service_historylast_service_history')
            # service_type = self.env['service.type'].sudo().search([('name', '=', last_service_history.service_type_name or last_service_history.servicetype)])
            # rec.service_type_sequence = service_type.sequence

    def update_vehicle_service_history(self):
        ServiceHistory = self.env['service.history']
        param = self.env['ir.config_parameter'].sudo()

        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')

        for vehicle in self.filtered(lambda v: v.vehicle_status == 'customer' and v.service_ids):
            # --- Step 1: Update local service.history with order details ---
            service_records = ServiceHistory.search([('vehicle_id', '=', vehicle.id)])
            to_update = service_records.filtered(lambda s: s.order.id)

            for record in to_update:
                if record.order.id:
                    for sale_q in record.order:
                        record.write({
                            'ro_id': sale_q.id,
                            'servicetype': sale_q.service_type.name,
                            'service_type_name': sale_q.service_type.name,
                            'service_code': sale_q.service_type.code,
                            'dealer_db_name': record.dealer_db_name or self._cr.dbname,
                            'mileage_in': record.mileage_in or sale_q.mileage_in,
                            'ro_number': record.ro_number or sale_q.name,
                        })

            # --- Step 2: Remove duplicate service records ---
            duplicate_orders = ServiceHistory.read_group(
                [('vehicle_id', '=', vehicle.id), ('order', '!=', False)],
                ['ro_id'],
                ['ro_id']
            )
            duplicate_order_ids = [group['ro_id'] for group in duplicate_orders if group['ro_id_count'] > 1]

            for order_id in duplicate_order_ids:
                duplicates = ServiceHistory.search([
                    ('order', '=', order_id),
                    ('vehicle_id', '=', vehicle.id)
                ])
                duplicates_to_delete = duplicates.sorted(key=lambda s: s.create_date)[1:]
                for duplicate in duplicates_to_delete:
                    if duplicate.exists():
                        try:
                            duplicate.sudo().unlink()
                        except Exception as e:
                            _logger.error(f"Error unlinking duplicate service history ID {duplicate.id}: {e}")

            # --- Step 3: Consolidation Sync ---
            if is_cons_enable and cons_db_name:
                try:
                    db = sql_db.db_connect(cons_db_name)
                    with contextlib.closing(db.cursor()) as cr:
                        cr.autocommit(True)
                        env = api.Environment(cr, SUPERUSER_ID, {})

                        cons_vehicle_card = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vehicle.vin_sn)],
                                                                               limit=1)
                        if not cons_vehicle_card and vehicle.consolidate_vehicle_card_id:
                            cons_vehicle_card = env['fleet.vehicle'].sudo().browse(vehicle.consolidate_vehicle_card_id)

                        if cons_vehicle_card:
                            dealer_code = self.env.user.company_id.dealer_code
                            if not dealer_code:
                                raise ValidationError(_("Dealer code not present in user's company"))

                            dealer_id = env['ars.consolidation.setup'].sudo().search(
                                [('dealer_code', '=', dealer_code)], limit=1)
                            if not dealer_id:
                                raise ValidationError(_("Dealer code does not match with consolidation setup"))

                            con_service_recs = cons_vehicle_card.service_ids
                            local_service_recs = vehicle.service_ids

                            # --- Insert missing records from consolidated to local ---
                            remaining_con_service_recs = con_service_recs.filtered(
                                lambda x: x.id not in local_service_recs.mapped('cons_service_history_id'))
                            for rec in remaining_con_service_recs:
                                self.env['service.history'].sudo().create({
                                    'vehicle_id': vehicle.id,
                                    'ro_id': rec.ro_id,
                                    'ro_number': rec.ro_number,
                                    'servicetype': rec.servicetype,
                                    'date': rec.date,
                                    'service_type_name': rec.service_type_name,
                                    'mileage_in': rec.mileage_in,
                                    'service_code': rec.service_code,
                                    'mileage': rec.mileage,
                                    'next_service_due': rec.next_service_due,
                                    'set_reminder': rec.set_reminder,
                                    'dealer_db_name': rec.dealer_db_name,
                                    'cons_service_history_id': rec.id,
                                })

                            # --- Insert missing records from local to consolidated ---
                            remaining_local_service = local_service_recs.filtered(
                                lambda x: not x.cons_service_history_id)
                            for rec in remaining_local_service:
                                cons_rec = env['service.history'].sudo().create({
                                    'vehicle_id': cons_vehicle_card.id,
                                    'ro_id': rec.ro_id,
                                    'ro_number': rec.ro_number,
                                    'servicetype': rec.servicetype,
                                    'date': rec.date,
                                    'service_type_name': rec.service_type_name,
                                    'mileage_in': rec.mileage_in,
                                    'service_code': rec.service_code,
                                    'mileage': rec.mileage_in,
                                    'dealer_db_name': self.env.cr.dbname,
                                    'next_service_due': rec.next_service_due,
                                    'set_reminder': rec.set_reminder,
                                    'dealer_id': dealer_id.id if dealer_id else None,
                                })
                                rec.sudo().write({'cons_service_history_id': cons_rec.id})

                except Exception as e:
                    _logger.error(f"Consolidation sync error: {e}")
                    raise UserError(_("Error during consolidation sync: %s") % e)

    #
    # def update_vehicle_service_history(self):
    #     ServiceHistory = self.env['service.history']
    #     param = self.env['ir.config_parameter'].sudo()
    #     cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
    #     is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
    #     db = sql_db.db_connect(f"{cons_db_name}")
    #     if is_cons_enable and cons_db_name:
    #         try:
    #             with contextlib.closing(db.cursor()) as cr:
    #                 cr.autocommit(True)
    #                 env = api.Environment(cr, SUPERUSER_ID, {})
    #
    #                 for vehicle in self.filtered(lambda v: v.vehicle_status == 'customer' and v.service_ids):
    #                     service_records = ServiceHistory.search([('vehicle_id', '=', vehicle.id)])
    #                     to_update = service_records.filtered(lambda s: s.order.id)
    #                     for record in to_update:
    #                         if record.order.id:  # Ensure order has a valid ID
    #                             for sale_q in record.order:
    #                                 record.write({'ro_id': sale_q.id,
    #                                               'servicetype': sale_q.service_type.name,
    #                                               'service_type_name': sale_q.service_type.name,
    #                                               'service_code': sale_q.service_type.code,
    #                                               'dealer_db_name': record.dealer_db_name if record.dealer_db_name else self._cr.dbname,
    #                                               'mileage_in': record.mileage_in if record.mileage_in else sale_q.mileage_in,
    #                                               'ro_number': record.ro_number if record.ro_number else sale_q.name})
    #
    #                     duplicate_orders = ServiceHistory.read_group(
    #                         [('vehicle_id', '=', vehicle.id), ('order', '!=', False)],
    #                         # Filter only records with order.id
    #                         ['ro_id'],  # Group by order.id
    #                         ['ro_id']  # Fields to group on
    #                     )
    #                     # print(duplicate_orders, 'duplicate_orders')
    #                     duplicate_order_ids = [
    #                         group['ro_id']
    #                         for group in duplicate_orders
    #                         if group['ro_id_count'] > 1
    #                     ]
    #                     # print(duplicate_order_ids)
    #                     # Remove duplicates
    #                     for order_id in duplicate_order_ids:
    #                         duplicates = self.env['service.history'].search(
    #                             [('order', '=', order_id), ('vehicle_id', '=', vehicle.id)])
    #                         duplicates_to_delete = duplicates.sorted(key=lambda s: s.create_date)[1:]
    #                         # Log the IDs to be deleted
    #                         # print(f"Duplicates to delete: {duplicates_to_delete.ids}")
    #                         # Unlink duplicates one by one
    #                         for duplicate in duplicates_to_delete:
    #                             # Double-check if the record exists before unlinking
    #                             if not duplicate.exists():
    #                                 # print(f"Record with ID: {duplicate.id} does not exist or was already deleted.")
    #                                 continue  # Skip to the next record
    #
    #                             try:
    #                                 # print(f"Unlinking record with ID: {duplicate.id}")
    #                                 duplicate.sudo().unlink()
    #                             except Exception as e:
    #                                 print(f"Error unlinking record with ID: {duplicate.id}: {e}")
    #
    #                     cons_vehicle_card = env['fleet.vehicle'].sudo().search([('vin_sn', '=', vehicle.vin_sn)],
    #                                                                            limit=1)
    #                     if not cons_vehicle_card and vehicle.consolidate_vehicle_card_id != 0:
    #                         cons_vehicle_card = env['fleet.vehicle'].sudo().browse(vehicle.consolidate_vehicle_card_id)
    #                     if cons_vehicle_card:
    #                         dealer_code = self.env.user.company_id.dealer_code
    #                         if dealer_code:
    #                             dealer_id = env['ars.consolidation.setup'].sudo().search(
    #                                 [('dealer_code', '=', dealer_code)], limit=1)
    #                             if not dealer_id:
    #                                 raise ValidationError(_("Dealer code does not match with consolidation setup"))
    #                         else:
    #                             raise ValidationError(_("Dealer code not present user company"))
    #
    #                         con_service_recs = cons_vehicle_card.service_ids
    #                         vehicle_service_ids = vehicle.service_ids
    #
    #                         if len(con_service_recs) > len(vehicle_service_ids):
    #                             # Need to insert into dealer service histories
    #                             remaining_con_service_recs = con_service_recs.filtered(
    #                                 lambda x: x.id not in vehicle_service_ids.mapped('cons_service_history_id'))
    #                             for rec in remaining_con_service_recs:
    #                                 service_vals = {
    #                                     'vehicle_id': vehicle.id,
    #                                     'ro_id': rec.ro_id,
    #                                     'ro_number': rec.ro_number,
    #                                     'servicetype': rec.servicetype,
    #                                     'date': rec.date,
    #                                     'service_type_name': rec.service_type_name,
    #                                     'mileage_in': rec.mileage_in,
    #                                     'service_code': rec.service_code,
    #                                     'mileage': rec.mileage,
    #                                     'next_service_due': rec.next_service_due,
    #                                     'set_reminder': rec.set_reminder,
    #                                     'dealer_db_name': rec.dealer_db_name,
    #                                     'cons_service_history_id': rec.id,  # Add this to link the record
    #                                 }
    #                                 self.env['service.history'].sudo().create(service_vals)
    #                             self.update_vehicle_service_history()
    #
    #                         if len(con_service_recs) < len(vehicle_service_ids):
    #                             # Need to insert into cons service histories
    #                             remaining_vehicle_service_ids = vehicle_service_ids.filtered(
    #                                 lambda x: not x.cons_service_history_id)
    #
    #                             for rec in remaining_vehicle_service_ids:
    #                                 service_vals = {
    #                                     'vehicle_id': cons_vehicle_card.id,
    #                                     'ro_id': rec.ro_id,
    #                                     'ro_number': rec.ro_number,
    #                                     'servicetype': rec.servicetype,
    #                                     'date': rec.date,
    #                                     'service_type_name': rec.service_type_name,
    #                                     'mileage_in': rec.mileage_in,
    #                                     'service_code': rec.service_code,
    #                                     'mileage': rec.mileage_in,
    #                                     'dealer_db_name': self.env.cr.dbname,
    #                                     'next_service_due': rec.next_service_due,
    #                                     'set_reminder': rec.set_reminder,
    #                                     'dealer_id': dealer_id.id if dealer_id else None,
    #                                 }
    #                                 cons_rec = env['service.history'].sudo().create(service_vals)
    #                                 rec.sudo().write({'cons_service_history_id': cons_rec.id})
    #                             self.update_vehicle_service_history()
    #
    #                         if len(con_service_recs) == len(vehicle_service_ids):
    #                             remaining_con_service_recs = con_service_recs.filtered(
    #                                 lambda x: x.id not in vehicle_service_ids.mapped('cons_service_history_id'))
    #                             for rec in remaining_con_service_recs:
    #                                 service_vals = {
    #                                     'vehicle_id': vehicle.id,
    #                                     'ro_id': rec.ro_id,
    #                                     'ro_number': rec.ro_number,
    #                                     'servicetype': rec.servicetype,
    #                                     'date': rec.date,
    #                                     'service_type_name': rec.service_type_name,
    #                                     'mileage_in': rec.mileage_in,
    #                                     'service_code': rec.service_code,
    #                                     'mileage': rec.mileage,
    #                                     'next_service_due': rec.next_service_due,
    #                                     'set_reminder': rec.set_reminder,
    #                                     'dealer_db_name': rec.dealer_db_name,
    #                                     'cons_service_history_id': rec.id,  # Add this to link the record
    #                                 }
    #                                 self.env['service.history'].sudo().create(service_vals)
    #                                 self.update_vehicle_service_history()
    #                             remaining_vehicle_service_ids = vehicle_service_ids.filtered(
    #                                 lambda x: not x.cons_service_history_id)
    #                             for rec in remaining_vehicle_service_ids:
    #                                 service_vals = {
    #                                     'vehicle_id': cons_vehicle_card.id,
    #                                     'ro_id': rec.id,
    #                                     'ro_number': rec.ro_number,
    #                                     'servicetype': rec.servicetype.name,
    #                                     'date': rec.date,
    #                                     'service_type_name': rec.service_type_name,
    #                                     'mileage_in': rec.mileage_in,
    #                                     'service_code': rec.service_type.code,
    #                                     'mileage': rec.mileage_in,
    #                                     'dealer_db_name': self.env.cr.dbname,
    #                                     'next_service_due': rec.next_service_due,
    #                                     'set_reminder': rec.set_reminder,
    #                                     'dealer_id': dealer_id.id if dealer_id else None,
    #                                 }
    #                                 cons_rec = env['service.history'].sudo().create(service_vals)
    #                                 rec.sudo().write({'cons_service_history_id': cons_rec.id})
    #                                 self.update_vehicle_service_history()
    #
    #         except Exception as e:
    #             _logger.error(e)
    #             raise UserError(_(e))


class WholesaleHistory(models.Model):
    _name = 'wholesale.history'
    _description = "This model store to sale vehicle details"

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", required=True, ondelete='cascade', index=True,
                                 copy=False)
    dealer_name = fields.Char(string="Dealer Name")
    so_number = fields.Char(string="SO Number")
    so_id = fields.Integer(string="So Id")
    delivery_date = fields.Date(string="Delivery Date")
    invoice_number = fields.Char(string="Invoice Number")
    invoice_id = fields.Integer(string="Invoice Id")
    po_number = fields.Char(string="PO Reference")
    transfer_type = fields.Selection(
        [('internal_transfer', 'Internal Transfer'), ('external_transfer', 'External Transfer')],
        string="Transfer Type")
    dealer_code = fields.Char(string="Dealer Code")
    dealer_master_id = fields.Many2one('ars.consolidation.setup', string="Dealer Master")
    vehicle_received = fields.Boolean(string="Vehicle Received", default=False)
