from odoo import models, fields, api

class product_attribute_custom(models.Model):
    _inherit = "product.attribute.value"

    @api.multi
    def _variant_color_name(self, variable_attributes):
        variant_name = ''
        # for variant in variable_attributes:
        #     variant_name += ", ".join(
        #         [f"{v.attribute_id.name}:{v.name}" for v in variant if v.attribute_id in variable_attributes])
        return ", ".join([f"{v.name}" for v in self if v.attribute_id in variable_attributes])