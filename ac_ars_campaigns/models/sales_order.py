from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

class SalesOrders(models.Model):
    _inherit = "sale.order"

    stages = fields.Selection([
        ('estimation', 'Estimation'),
        ('repair_order', 'Repair Order'),
        ('waiting_for_parts', 'Waiting For Parts'),
        ('wip', 'Work In Progress'),
        ('ro_closed', 'Ro Closed'),
    ], string='Stage', default='estimation', tracking=True,copy=False)
    campaign_his_id = fields.Many2one('campaign.history', string="Campaign History")

    @api.multi
    def action_unlock(self):
        for order in self:
            if order.state == 'done' and order.sale_type in ('parts','accessories'):
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
                print(categories,'cccc')
                record.write({'stages': 'wip'})
            else:
                record.write({'stages': 'waiting_for_parts'})
                print(categories,'rrrr')
        return super(SalesOrders, self).action_confirm()

    def action_cancel(self):
        self.write({'stages':'estimation'})
        return super(SalesOrders, self).action_cancel()

    # def action_convert(self):
    #     res = super(SalesOrders,self).action_convert()
    #     self.write({'stages':'repair_order'})
    #     return res

    def ro_closed_action(self):
        action = self.action_done()
        self.write({'stages':'ro_closed'})
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
                    print(field_name,'aaa')
                    if field_name in vehicle._fields:
                        print(f"{field_name} -> {vehicle[field_name]}")
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
        else:
            print('No Mandaitory fileds')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):

        res = super(StockPicking, self).button_validate()
        for picking in self:
            sale_orders = picking.sale_id
            if sale_orders:
                sale_orders.write({'stages': 'wip'})
        return res