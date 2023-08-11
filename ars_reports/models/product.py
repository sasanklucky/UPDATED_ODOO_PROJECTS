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


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _description = 'Vehicle Report'

    # warr_start_date = fields.Datetime(string='Warranty Validation')
    @api.multi
    def _get_insurance_details(self):
        insurance_id = self.insurance_ids.ids
        res = False
        if self.insurance_ids:
            insurance_id.sort() if len(insurance_id) > 1 else insurance_id
            res = self.insurance_ids.search([('id', '=', insurance_id[-1])])
        return res

    def _get_ownership_details(self):
        owner_id = self.customer_ids.ids
        res = False
        if self.customer_ids:
            owner_id.sort() if len(owner_id) > 1 else owner_id
            res = self.customer_ids.search([('id', '=', owner_id[-1])])
        return res
