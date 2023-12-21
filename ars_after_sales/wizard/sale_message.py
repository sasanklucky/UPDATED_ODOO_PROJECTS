from odoo import models, fields,api


class SaleMessage(models.TransientModel):
    _name = 'sale.message'

    @api.model
    def default_get(self, fields):
        res = super(SaleMessage, self).default_get(fields)
        # Fetch the custom message from the configuration parameter
        custom_message = self.env['ir.config_parameter'].sudo().get_param('ars_after_sales.sale_text')
        res['sale_text'] = custom_message
        return res

    sale_text = fields.Text(string='Message',readonly=True)

    def sale_message_define(self):
        return {'type': 'ir.actions.act_window_close'}