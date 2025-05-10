from odoo import api, fields, models


class ProductTemplates(models.Model):
    _inherit = "product.template"

    model_ids = fields.Many2many('ir.model', string='Models')

    field_ids = fields.Many2many(
        'ir.model.fields',
        string="Fields",
        domain="[('model_id', 'in', model_ids), ('ttype', 'not in', ['one2many', 'many2many', 'many2one'])]"
    )

    setup_line_ids = fields.One2many('labour.setup.line', 'setup_id', string="Fields")

    @api.onchange('field_ids')
    def _onchange_field_ids(self):
        lines = []
        for f in self.field_ids:
            lines.append((0, 0, {
                'name': f.name,
                'field_description': f.field_description,
                'model_name': f.model_id.model,
            }))
        self.setup_line_ids = [(5, 0, 0)] + lines

class LabourSetupLine(models.Model):
    _name = 'labour.setup.line'
    _description = 'Labour Setup Line'

    setup_id = fields.Many2one('product.template', string="Setup")
    name = fields.Char("Technical Name")
    field_description = fields.Char("Fields Label")
    model_name = fields.Char("Model")




# class ProductTemplates(models.Model):
#     _inherit = "product.template"
#
#     model_ids = fields.Many2many('ir.model', string='Models')
#
#     field_ids = fields.Many2many(
#         'ir.model.fields',
#         string="Fields",
#         domain="[('model_id', 'in', model_ids), ('ttype', 'not in', ['one2many', 'many2many', 'many2one'])]"
#     )
#
#     setup_line_ids = fields.One2many('labour.setup.line', 'setup_id', string="Fields")
#
#     @api.onchange('field_ids')
#     def _onchange_field_ids(self):
#         self._compute_setup_lines()
#
#     def _compute_setup_lines(self):
#         lines = []
#         for f in self.field_ids:
#             lines.append((0, 0, {
#                 'name': f.name,
#                 'field_description': f.field_description,
#                 'model_name': f.model_id.model,
#             }))
#         self.setup_line_ids = [(5, 0, 0)] + lines
#
#     def write(self, vals):
#         res = super().write(vals)
#         if 'field_ids' in vals:
#             for record in self:
#                 record._compute_setup_lines()
#         return res
#
#     @api.model
#     def create(self, vals):
#         record = super().create(vals)
#         if 'field_ids' in vals:
#             record._compute_setup_lines()
#         return record


# class LabourSetupLine(models.Model):
#     _name = 'labour.setup.line'
#     _description = 'Labour Setup Line'
#
#     setup_id = fields.Many2one('product.template', string="Setup")
#     name = fields.Char("Technical Name")
#     field_description = fields.Char("Fields Label")
#     model_name = fields.Char("Model")
