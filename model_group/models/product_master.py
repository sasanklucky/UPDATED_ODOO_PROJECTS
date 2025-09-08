# models/product_master.py
from odoo import models, fields, api


class ProductMaster(models.Model):
    _name = 'model.groups'
    _description = 'model groups'

    name = fields.Char(string='Model group Name', required=True)
    code = fields.Char(string='Model group Code')
    description = fields.Text(string='Description')
    image = fields.Binary(
        string="Group Image",
        help="Upload product image here"
    )
    template_ids = fields.One2many(
        'product.template',
        'master_id',
        string='Product Templates'
    )
    template_count = fields.Integer(
        compute='_compute_template_count',
        string='Number of Templates'
    )
    related_count = fields.Integer(string="related_count",
                                   compute='compute_vehicle_count',
                                   default=0)




    def compute_vehicle_count(self):
        for master in self:
            master.related_count = len(master.template_ids)

    def action_view_related_templates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'model group of {self.name}',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('master_id', '=', self.id)],
            'context': {
                'default_master_id': self.id,
                'search_default_master_id': self.id
            }
        }




    def _compute_template_count(self):
        for master in self:
            master.template_count = len(master.template_ids)

    def action_view_templates(self):
        action = self.env.ref('product.product_template_action').read()[0]
        action['domain'] = [('master_id', '=', self.id)]
        action['context'] = {'default_master_id': self.id}
        return action