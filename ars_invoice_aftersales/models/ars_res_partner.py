from odoo import models, fields, api
from odoo.tools.translate import _

class ARSResPartner(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [
        ('mobile_uniq', 'unique (mobile)', 'The name of the Degree of Recruitment must be unique!')
    ]



    @api.multi
    def _compute_estimate_count(self):
        for partner in self:
            partner.estimate_count = self.env['sale.order'].search_count(
                [('state', '=', 'draft'), ('partner_id', '=', partner.id), ('sale_aftersales', '=', 'after_sales')])

    estimate_count = fields.Integer(compute='_compute_estimate_count')

    @api.multi
    def customer_estimate(self):
        for partner in self:
            estimate_count = self.env['sale.order'].search([('state', '=', 'draft'), ('partner_id', '=', partner.id),('sale_aftersales', '=', 'after_sales')])
            form_view = self.env.ref('ars_after_sales.view_order_form_inherit')
            list_view = self.env.ref('ars_after_sales.view_quotation_tree_inherit')
            if len(estimate_count) > 1:
                return {
                    'name': _('Estimation'),
                    'res_model': 'sale.order',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'view_id': list_view.id,
                    'views': [(list_view.id, 'tree'), (form_view.id, 'form')],
                    'domain': [('id', 'in', estimate_count.ids)],
                    'type': 'ir.actions.act_window',
                    'target': 'self'
                }
            else:
                return {
                    'name': _('Estimation'),
                    'res_model': 'sale.order',
                    'res_id': estimate_count.id,
                    'views': [(form_view.id, 'form'), ],
                    'type': 'ir.actions.act_window',
                    'target': 'self'
                }


    @api.multi
    def _compute_so_count(self):
        for partner in self:
            partner.so_count = self.env['sale.order'].search_count(
                [('state', '=', 'so'), ('partner_id', '=', partner.id)])

    so_count = fields.Integer(compute='_compute_so_count')

    @api.multi
    def customer_so_preparation(self):
        for partner in self:
            so_count = self.env['sale.order'].search([('state', '=', 'so'), ('partner_id', '=', partner.id)])
            form_view = self.env.ref('ars_after_sales.view_order_form_inherit')
            list_view = self.env.ref('ars_after_sales.view_quotation_tree_inherit')
            if len(so_count) > 1:
                return {
                    'name': _('So Preparation'),
                    'res_model': 'sale.order',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'view_id': list_view.id,
                    'views': [(list_view.id, 'tree'), (form_view.id, 'form')],
                    'domain': [('id', 'in', so_count.ids)],
                    'type': 'ir.actions.act_window',
                    'target': 'self'
                }
            else:
                return {
                    'name': _('So Preparation'),
                    'res_model': 'sale.order',
                    'res_id': so_count.id,
                    'views': [(form_view.id, 'form'), ],
                    'type': 'ir.actions.act_window',
                    'target': 'self'
                }

    @api.multi
    def _compute_order_count(self):
        for partner in self:
            partner.order_count = self.env['sale.order'].search_count(
                [('state', '=', 'sale'), ('partner_id', '=', partner.id), ('sale_aftersales', '=', 'after_sales')])

    order_count = fields.Integer(compute='_compute_order_count')

    @api.multi
    def customer_service_order(self):
        for partner in self:
            order_count = self.env['sale.order'].search([('state', '=', 'sale'), ('partner_id', '=', partner.id), ('sale_aftersales', '=', 'after_sales')])
            form_view = self.env.ref('ars_after_sales.view_order_form_inherit')
            list_view = self.env.ref('ars_after_sales.view_order_tree_inherit')
            if len(order_count) > 1:
                return {
                    'name': _('Service Order'),
                    'res_model': 'sale.order',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'view_id': list_view.id,
                    'views': [(list_view.id, 'tree'), (form_view.id, 'form')],
                    'domain': [('id', 'in', order_count.ids)],
                    'type': 'ir.actions.act_window',
                    'target': 'self'
                }
            else:
                return {
                    'name': _('Service Order'),
                    'res_model': 'sale.order',
                    'res_id': order_count.id,
                    'views': [(form_view.id, 'form'), ],
                    'type': 'ir.actions.act_window',
                    'target': 'self'
                }
