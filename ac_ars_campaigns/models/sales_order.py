from email.policy import default
import threading
import contextlib
import logging
from odoo import models, fields, api,_, SUPERUSER_ID, sql_db
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import time
_logger = logging.getLogger(__name__)


def threaded_ro_closed_update(record_ids, db_name, user_id):
    start_time = time.time()
    _logger.info("RO Close Update Thread started at: %s", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)))

    try:
        connection = sql_db.db_connect(db_name)
        with contextlib.closing(connection.cursor()) as cr:
            with api.Environment.manage():
                env = api.Environment(cr, user_id, {'lang': 'en_US'})
                sale_orders = env['sale.order'].browse(record_ids).filtered(lambda so: so.state in ('done', 'sale') and not so.ro_closed_date)

                _logger.info("Processing %d sale orders", len(sale_orders))

                for rec in sale_orders:
                    _logger.info(f"Updating RO Close for: {rec.name}")
                    if rec.invoice_ids:
                        invoice = rec.invoice_ids.sorted(key=lambda inv: inv.id)[0]
                        rec.write({'ro_closed_date': invoice.create_date})
                        _logger.info(f"RO Close Date updated for {rec.name} to {invoice.create_date}")
                        env.user.notify_info(f"Ro Closed Date {rec.ro_closed_date} Updated Successfully")

                env.cr.commit()
                _logger.info("All RO Close Dates committed successfully.")


    except Exception as e:
        _logger.exception("Threaded RO Close Update failed: %s", str(e))

    end_time = time.time()
    duration = end_time - start_time
    _logger.info("Thread ended at: %s", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
    _logger.info("Total time taken for RO Close update (seconds): %.2f", duration)


class SalesOrders(models.Model):
    _inherit = "sale.order"

    stages = fields.Selection([
        ('estimation', 'Estimation'),
        ('repair_order', 'Repair Order'),
        ('waiting_for_parts', 'Waiting For Parts'),
        ('wip', 'Work In Progress'),
        ('ro_closed', 'Ro Closed'),
        ('cancel', 'Cancelled'),
    ], string='Stage', default='estimation',tracking=True, copy=False)
    campaign_his_id = fields.Many2one('campaign.history', string="Campaign History")
    ro_closed_date = fields.Datetime('Ro Closed Date')


    @api.multi
    def action_unlock(self):
        for order in self:
            if order.state == 'done':
                raise UserError("You cannot unlock an order that is already done.")
        return super(SalesOrders, self).action_unlock()

    @api.multi
    def action_reopen(self):
        for order in self:
            if order.state == 'done':
                order.write({'state': 'sale',
                             'stages': 'wip'
                             })

    def action_confirm(self):
        for record in self:
            categories = record.order_line.mapped('product_id.categ_id.name')
            if categories and set(categories) == {'Labor'}:
                record.write({'stages': 'wip'})
            else:
                record.write({'stages': 'waiting_for_parts'})
        return super(SalesOrders, self).action_confirm()

    def action_cancel(self):
        self.write({'stages':'cancel'})
        return super(SalesOrders, self).action_cancel()


    def action_draft(self):
        res = super(SalesOrders, self).action_draft()
        for rec in self:
            if rec.state == 'draft':
                rec.write({'stages':'estimation'})
        return res


    @api.multi
    def ro_closed_action(self):
        action = self.action_done()
        self.write({'ro_closed_date': datetime.now(),
                    'stages':'ro_closed'})
        self.env.user.notify_info(f"Ro Closed Date {self.ro_closed_date} Updated Successfully")

        model_with_fields = {}
        for record in self:
            for order_line_item in record.order_line:
                product = order_line_item.product_id
                if product and product.field_ids:
                    for field in product.field_ids:
                        model = field.model_id.model
                        field_name = field.name
                        clean_name = field_name[2:] if field_name.startswith('x_') else field_name
                        model_with_fields.setdefault(model, []).append(clean_name)
        missing_fields ={}
        for model, fields in model_with_fields.items():
            if model == 'fleet.vehicle': # here i have given for only sim number fields ,which is available in fleet.vehicle
                vehicle = self.env[model].search([('vin_sn', '=', self.vin_no)], limit=1)
                if not vehicle:
                    raise ValidationError("No vehicle found with VIN: %s" % self.vin_no)

                for field_name in fields:
                    if field_name in vehicle._fields:
                        mandatory_fields = []
                        if not vehicle[field_name]:
                            mandatory_fields.append(field_name)

                missing_fields[model] = mandatory_fields
        if missing_fields:
            vehicle = self.env[model].search([('vin_sn', '=', self.vin_no)], limit=1)
            return {
                'name': 'Mandatory Fields Updation',
                'type': 'ir.actions.act_window',
                'res_model': 'sim.installation',
                'view_id': self.env.ref('ac_ars_campaigns.view_mandatory_fields_update_form').id,
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_vehicle': vehicle.id,
                            'default_sale_id': self.id}
            }

    # Server Action Function
    @api.multi
    def ro_closed_update_action(self):
        db_name = self._cr.dbname
        user_id = self.env.user.id
        record_ids = [rec.id for rec in self]
        _logger.info("Launching RO Close Update Thread for %d records", len(record_ids))

        thread = threading.Thread(
            target=threaded_ro_closed_update,
            args=(record_ids, db_name, user_id),
            daemon=True
        )
        thread.start()


        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):

        res = super(StockPicking, self).button_validate()
        for picking in self:
            sale_orders = picking.sale_id
            if sale_orders:
                sale_orders.write({'stages': 'wip'})
        return res