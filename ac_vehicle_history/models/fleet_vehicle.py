from odoo import models, fields, api, _
from werkzeug.routing import ValidationError
from lxml import etree



class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    consolidate_vehicle_card_id = fields.Integer(string='consolidate_vehicle_card_id')
    wholesale_ids = fields.One2many('wholesale.history', 'vehicle_id', string="Wholesale History")
    service_type_sequence = fields.Integer(string="Service Type Sequence", compute='compute_service_type_sequence')

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
            if len(rec.service_ids) >= 1 and len(rec.customer_ids)>=1 and len(rec.insurance_ids) >=1 and len(rec.emission_ids) >=1 and len(rec.wholesale_ids) >=1:
                raise ValidationError("You Cannot Archive Entries Contains Vehicle Card")

    @api.multi
    def unlink(self):
        for rec in self:
            if len(rec.service_ids) >= 1 and len(rec.customer_ids)>=1 and len(rec.insurance_ids) >=1 and len(rec.emission_ids) >=1 and len(rec.wholesale_ids) >=1:
                raise ValidationError("You Cannot Delete Entries Contains Vehicle Card")
        return super(FleetVehicle, self).unlink()


    # @api.depends('service_ids')
    # @api.multi
    def compute_service_type_sequence(self):
        for rec in self:
            service_types = self.env['service.type'].sudo().search([('code', 'in', rec.service_ids.mapped('service_code'))])
            if service_types:
                max_sequence = max(service_types.mapped('sequence'))
                rec.service_type_sequence = max_sequence

            # last_service_history = rec.service_ids.sorted(id, reverse=True)[:1]
            # print(last_service_history,'last_service_historylast_service_history')
            # service_type = self.env['service.type'].sudo().search([('name', '=', last_service_history.service_type_name or last_service_history.servicetype)])
            # rec.service_type_sequence = service_type.sequence

    def update_vehicle_service_history(self):
        ServiceHistory = self.env['service.history']
        for vehicle in self.filtered(lambda v: v.vehicle_status == 'customer' and v.service_ids):
            service_records = ServiceHistory.search([('vehicle_id', '=', vehicle.id)])
            to_update = service_records.filtered(lambda s: s.order.id)
            for record in to_update:
                if record.order.id:  # Ensure order has a valid ID
                    for sale_q in record.order:
                        record.write({'ro_id': sale_q.id,
                                      'servicetype': sale_q.service_type.name,
                                      'service_type_name': sale_q.service_type.name,
                                      'service_code': sale_q.service_type.code,
                                      'dealer_db_name': record.dealer_db_name if record.dealer_db_name else self._cr.dbname,
                                      'mileage_in': record.mileage_in if record.mileage_in else sale_q.mileage_in,
                                      'ro_number': record.ro_number if record.ro_number else sale_q.name})

            duplicate_orders = ServiceHistory.read_group(
                [('vehicle_id', '=', vehicle.id),('order', '!=', False)],  # Filter only records with order.id
                ['ro_id'],  # Group by order.id
                ['ro_id']  # Fields to group on
            )
            # print(duplicate_orders, 'duplicate_orders')
            duplicate_order_ids = [
                group['ro_id']
                for group in duplicate_orders
                if group['ro_id_count'] > 1
            ]
            # print(duplicate_order_ids)
            # Remove duplicates
            for order_id in duplicate_order_ids:
                duplicates = self.env['service.history'].search([('order', '=', order_id),('vehicle_id', '=', vehicle.id)])
                duplicates_to_delete = duplicates.sorted(key=lambda s: s.create_date)[1:]
                # Log the IDs to be deleted
                # print(f"Duplicates to delete: {duplicates_to_delete.ids}")
                # Unlink duplicates one by one
                for duplicate in duplicates_to_delete:
                    # Double-check if the record exists before unlinking
                    if not duplicate.exists():
                        # print(f"Record with ID: {duplicate.id} does not exist or was already deleted.")
                        continue  # Skip to the next record

                    try:
                        # print(f"Unlinking record with ID: {duplicate.id}")
                        duplicate.sudo().unlink()
                    except Exception as e:
                        print(f"Error unlinking record with ID: {duplicate.id}: {e}")


class WholesaleHistory(models.Model):
    _name = 'wholesale.history'
    _description = "This model store to sale vehicle details"

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", required=True, ondelete='cascade', index=True, copy=False)
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


