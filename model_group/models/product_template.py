# models/product_template.py
from odoo import models, fields,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    master_id = fields.Many2one(
        'model.groups',
        string='Model Group',
        index=True
    )



class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    master_id = fields.Many2one(
        'model.groups',
        string='Model Group',
        related='model_id.master_id',
        store=True,
        readonly=False  # Optional: only make it editable if needed
    )


class Accountinvoice(models.Model):
    _inherit = 'account.invoice'

    master_id = fields.Many2one(
        'model.groups',
        string='Model Group',
        related='model.master_id',
        store=True,
        readonly=False  # Optional: only make it editable if needed
    )
