from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class ConvertSOWizard(models.TransientModel):
    _name = 'convert.so.wizard'

    text = fields.Html(string='Message')
    sale_estimation_id = fields.Many2one('sale.order')
    cancel_reason = fields.Text(string='Cancel Reason')
    show_cancel_reason = fields.Boolean(default=False)
    campaign_history_id = fields.Many2one('campaign.history', string="Campaign History")
    # sim_installation_date = fields.Date(string='SIM Assignment Date', default=fields.Date.context_today)
    is_campagin = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),

    ],default='no', string='Campagin Needed')

    def action_done(self):
        sale_order = self.env['sale.order'].browse(self.env.context.get('default_sale_estimation_id'))
        for record in self:
            cam_history = self.env['campaign.history'].search([('id', '=', record.campaign_history_id.id)], limit=1)
            if record.is_campagin == 'yes':
                print(sale_order.name,'namee')
                service_type = cam_history.campaign_name.service_type
                service_option = cam_history.campaign_name.service_options
                instruction = cam_history.campaign_name.instruction
                print(cam_history.campaign_name_ref, cam_history.campaign_vehicle_id.vin_sn,'SSSSSSSSSSSSSSSSS')
                fleet_vehicle = self.env['fleet.vehicle'].search([('vin_sn', '=', sale_order.vin_no)], limit=1)
                if fleet_vehicle:
                    sale_order.write({'campaign_service_name_ref': record.campaign_history_id.campaign_name_ref})
                    return {
                        'name': 'CAMPAIGN UPDATION',
                        'type': 'ir.actions.act_window',
                        'res_model': 'click.done.action',
                        'view_id': self.env.ref('ac_ars_campaigns.view_confirm_update_form').id,
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_sale_order_id': sale_order.id,
                            'default_original_wizard_id': self.id,
                            'default_campaign_service_type': service_type.id if service_type else False,
                            'default_campaign_service_option': service_option.id if service_option else False,
                            'default_instruction_id': instruction.id if instruction else False,
                        }
                    }
                else:
                    raise UserError("No fleet vehicle found with VIN: %s" % sale_order.vin_no)
            else:
                cam_history_service = self.env['campaign.history'].search([('id', '=', record.campaign_history_id.id)], limit=1)
                if cam_history_service:
                    cam_history_service.write({'camp_cancel_reasons':record.cancel_reason})
                    sale_order.write({'campaign_service_name_ref': record.campaign_history_id.campaign_name_ref})
        vals = {
            'continue': True
        }
        return sale_order.action_convert(vals)


class ClickableAction(models.TransientModel):
    _name = 'click.done.action'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    campaign_service_type = fields.Many2one('service.type', string='Campaign Service Type')
    campaign_service_option = fields.Many2one('service.options', string='Campaign Service Option')
    instruction_id = fields.Many2one('instructions', string='Instruction')

    def _prepare_so_line(self, line, sale_line, count, partner):
        """ Prepares sale order line values from instruction line """
        rse_data = {}
        data = {
            'product_id': line.product_id.id,
            'product_template_id': line.product_template_id.id if line.product_template_id else False,
            'product_catalog_id': line.product_catalog_id.id if line.product_catalog_id else False,
            'name': line.name,
            'product_uom_qty': line.product_uom_qty,
            'qty_delivered': line.qty_delivered,
            'qty_invoiced': line.qty_invoiced,
            'product_uom': line.product_uom.id,
            'category': line.category.id if line.category else False,
            'price_unit': line.product_id.list_price,
            'tax_id': [(6, 0, line.tax_id.ids)],
            'price_subtotal': line.price_subtotal,
            'customer_split': partner.id if partner else False,
        }

        if count == 0 and not sale_line:
            rse_data = data
        else:
            if not sale_line.filtered(lambda y: y.product_id == line.product_id) and line.product_id:
                rse_data = data

        return rse_data

    def action_updation(self):
        self.ensure_one()
        # Update campaign service fields
        self.sale_order_id.write({
            'service_type': self.campaign_service_type.id,
            'service_options': self.campaign_service_option.id,
            'customer_voice_sale': [(0, 0, {
                'name': '',
                'instructions': self.instruction_id.id,

            })]
        })
        #  Add order lines from instruction
        sale_lines = self.sale_order_id.order_line
        count = 0
        new_lines = []

        for instruction_line in self.instruction_id.order_line:
            line_vals = self._prepare_so_line(instruction_line, sale_lines, count, self.sale_order_id.partner_id)
            if line_vals:
                new_lines.append((0, 0, line_vals))
                count += 1

        if new_lines:
            self.sale_order_id.write({'order_line': new_lines})
        vals = {
            'continue': True
        }
        return self.sale_order_id.action_convert(vals)


    # def action_updation(self):
    #     self.ensure_one()
    #     self.sale_order_id.write({
    #         'service_type': self.campaign_service_type.id,
    #         'service_options': self.campaign_service_option.id,
    #     })
