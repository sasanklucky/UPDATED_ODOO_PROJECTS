# models/product_template.py
from odoo import models, fields,api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    master_id = fields.Many2one(
        'model.groups',
        string='Model Group',
        index=True
    )

    @api.constrains('master_id', 'catalog_type_name')
    def _check_master_id_required(self):
        for rec in self:
            if rec.catalog_type_name == 'Vehicle' and not rec.master_id:
                raise ValidationError("Model Group is required when Catalog Type is Vehicle.")



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
        readonly=True  # Optional: only make it editable if needed
    )
