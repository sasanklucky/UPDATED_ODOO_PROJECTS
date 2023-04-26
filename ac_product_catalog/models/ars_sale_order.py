from odoo import models, fields, api, _
from odoo.tools import format_date


class ARSSaleOrder(models.Model):

    @api.multi
    def _prepare_invoice(self):
        res = super(ARSSaleOrder, self)._prepare_invoice()
        return res
