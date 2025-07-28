from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    context_show_master = fields.Boolean(
        string='Context Show Master',
        compute='_compute_context_show_master',
        store=False
    )

    @api.depends_context('context_show_master')
    def _compute_context_show_master(self):
        for rec in self:
            rec.context_show_master = self.env.context.get('context_show_master', True)
