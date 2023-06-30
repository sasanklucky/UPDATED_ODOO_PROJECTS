from odoo import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class POSyncCheckWizard(models.Model):
    _name = 'po_sync_check_wizard'

    def _get_default_po_status(self):
        ids = self.env['purchase.order'].search([
            ('state', '=', 'purchase'),('sync_po', '=', False)])
        return ids

    sync_status_ids = fields.Many2many('purchase.order', string="Records Status",default=lambda self: self._get_default_po_status())


    @api.multi
    def posync_now(self):
        print("wiz called now---")
        if self.sync_status_ids:
            self.env['purchase.order']._cron_sync_po_to_so_in_parent()
        else:
            raise ValidationError(_('No Data (Purchase Orders) found in Draft state.'))

class SOSyncCheckWizard(models.Model):
    _name = 'so_sync_check_wizard'

    def _get_default_po_status(self):
        ids = self.env['sale.order'].search([('ready_for_sync','=',True),('child_po_id_ref','!=',False)])
        return ids

    sync_status_ids = fields.Many2many('sale.order', string="Records Status",default=lambda self: self._get_default_po_status())


    @api.multi
    def sosync_now(self):
        print("wiz called now---")
        if self.sync_status_ids:
            self.env['sale.order']._cron_sync_so_to_po_in_child()
        else:
            raise ValidationError(_('No Data (Sale Orders) found in Draft state.'))

class UpdateSaleOrderLine(models.Model):
    _name = 'update_sale_order_line'

    def _get_default_tax_id(self):
        ids = self.env['account.tax'].browse(self._context.get("tax_ids")).ids
        return ids
    
    tax_ids = fields.Many2many('account.tax', string="Records Status",default=lambda self: self._get_default_tax_id())
    order_line_id = fields.Many2one('sale.order.line', string="order line id")
    price_unit = fields.Float()

    def update_value(self):
        #update value to tax and unit price
        price_subtotal = self.price_unit * self.order_line_id.product_uom_qty
        query = f""" update sale_order_line set price_unit={self.price_unit}, price_subtotal={price_subtotal} where id={self.order_line_id.id} """
        self._cr.execute(query)
        query = f""" delete from account_tax_sale_order_line_rel where sale_order_line_id = {self.order_line_id.id} """
        self._cr.execute(query)
        for rec in self.tax_ids:
            query = f""" INSERT INTO account_tax_sale_order_line_rel (sale_order_line_id, account_tax_id) VALUES ({str(self.order_line_id.id)},{str(rec.id)}); """
            self._cr.execute(query)
        self.order_line_id.order_id._amount_all()
