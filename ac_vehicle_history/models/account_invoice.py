from odoo import models, fields, api, registry, SUPERUSER_ID, sql_db, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date, datetime, time, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import contextlib
import logging
_logger = logging.getLogger(__name__)



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        fleet_obj = self.env['fleet.vehicle']
        param = self.env['ir.config_parameter'].sudo()
        cons_db_name = param.get_param('ac_vehicle_history.consolidate_db_name')
        is_cons_enable = param.get_param('ac_vehicle_history.is_consolidation')
        db = sql_db.db_connect(f"{cons_db_name}")
        if is_cons_enable and cons_db_name:
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                print(self._context.get('default_type'),self._context.get('type'),'eeee')
                if (self._context.get('default_type') or self._context.get('type') == 'out_invoice') and (self.ars_invoice_type == 'vehicle' or self.order_id.sale_type == 'vehicle'):
                    for inv_line in self.invoice_line_ids:
                        if inv_line.vin_no:
                            vin_sn = inv_line.vin_no.name
                            vehicle_card = self.env['fleet.vehicle'].sudo().search([('vin_sn', '=', vin_sn)], limit=1)
                            if not vehicle_card:
                                _logger.warning("Vehicle card with VIN %s not found", vin_sn)
                                continue
                            for wholesale_id in vehicle_card.wholesale_ids:
                                if self.origin or (self.sale_order_number == wholesale_id.so_number):
                                    wholesale_id.write({'invoice_number': self.number, 'invoice_id': self.id,
                                                        'delivery_date': self.date_invoice})
                            cons_vehicle_card = env['fleet.vehicle'].sudo().browse(
                                vehicle_card.consolidate_vehicle_card_id)
                            for wholesale_id in cons_vehicle_card.wholesale_ids:
                                if self.origin or (self.sale_order_number == wholesale_id.so_number):
                                    wholesale_id.write({'invoice_number': self.number, 'invoice_id': self.id,
                                                        'delivery_date': self.date_invoice})
                if self.ars_invoice_type == 'after_sales' or self.order_id.sale_type == 'after_sales':
                        # vin_no  = self.order_id.vin_no or self.env['sale.order'].sudo().search([('name','=', (self.origin or self.sale_order_number))]).vin_no or self.vin
                        vin_no = self.order_id.vin_no or self.env['sale.order'].sudo().search([('name', '=', (self.origin or self.sale_order_number))], limit=1).vin_no or self.vin
                        vehicle_card = self.env['fleet.vehicle'].sudo().search([('vin_sn','=',vin_no)], limit=1)
                        if vehicle_card:
                                cons_vehicle_card = env['fleet.vehicle'].sudo().browse( vehicle_card.consolidate_vehicle_card_id)
                                cons_vehicle_card.sudo().write({'odometer': self.kilometer_out})
                                vehicle_card.sudo().write({'odometer': self.kilometer_out})
                                dealer_db_set = set(service_history.dealer_db_name for service_history in cons_vehicle_card.service_ids)
                                # Loop over each database and perform the update
                                for db_name in dealer_db_set:
                                    if self.env.cr.dbname != db_name:
                                        db = sql_db.db_connect(f"{db_name}")
                                        with contextlib.closing(db.cursor()) as new_cr:
                                            new_cr.autocommit(True)
                                            dealer_env = api.Environment(new_cr, SUPERUSER_ID, {})
                                            dealer_vehicle_card = dealer_env['fleet.vehicle'].sudo().search([('vin_sn', '=', cons_vehicle_card.vin_sn)], limit=1)
                                            if dealer_vehicle_card:
                                                dealer_vehicle_card.sudo().write({'odometer': self.kilometer_out})
            return res
        else:
            # res = super(AccountInvoice, self).action_invoice_open()
            return res
