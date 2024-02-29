from odoo import fields, models, api, _, tools
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.partner_shipping_id:
            for do_pick in self.picking_ids:
                print('dopick-------------------->', do_pick)
                do_pick.write({'to_street': self.partner_shipping_id.street or '',
                               'to_street2': self.partner_shipping_id.street2 or '',
                               'to_city': self.partner_shipping_id.city or '',
                               'to_state_id': self.partner_shipping_id.state_id.id or '',
                               'to_zip': self.partner_shipping_id.zip or '',
                               'street': self.warehouse_id.partner_id.street or '',
                               'street2': self.warehouse_id.partner_id.street2 or '',
                               'city': self.warehouse_id.partner_id.city or '',
                               'state_id': self.warehouse_id.partner_id.state_id.id or '',
                               'zip': self.warehouse_id.partner_id.zip or '',
                               'to_name' : self.partner_shipping_id.name or '',
                               'to_vat' : self.partner_id.vat or '',
                               'from_name' : self.warehouse_id.name or '',
                               'vat' : self.warehouse_id.partner_id.vat or '',
                               })
        else:
            for do_pick in self.picking_ids:
                print('dopick-------------------->', do_pick)
                do_pick.write({'to_street': self.partner_id.street or '',
                               'to_street2': self.partner_id.street2 or '',
                               'to_city': self.partner_id.city or '',
                               'to_state_id': self.partner_id.state_id or '',
                               'to_zip': self.partner_id.zip or '',
                               'street': self.warehouse_id.partner_id.street or '',
                               'street2': self.warehouse_id.partner_id.street2 or '',
                               'city': self.warehouse_id.partner_id.city or '',
                               'state_id': self.warehouse_id.partner_id.state_id or '',
                               'zip': self.warehouse_id.partner_id.zip or '',
                               'to_name' : self.partner_id.name or '',
                               'to_vat' : self.partner_id.vat or '',
                               'from_name' : self.warehouse_id.name or '',
                               'vat' : self.warehouse_id.partner_id.vat or '',
                               })

        return res
