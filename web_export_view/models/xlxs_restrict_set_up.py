from odoo import models, fields, api
from ast import literal_eval

class arsConfigMaterDataRestriction(models.TransientModel):
    _inherit = 'res.config.settings'


    xlsx_model_restrict = fields.Many2many('ir.model', 'res_config_xlsx_model_restrict_rel', 'model_id', 'config_id',
                                        string="Model", help="Select the model")


    def set_values(self):
        res = super(arsConfigMaterDataRestriction, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        print('xlsx_model_restrict', self.xlsx_model_restrict.ids)

        param.set_param('ars_after_sales.xlsx_model_restrict', self.xlsx_model_restrict.ids)

        return res

    @api.model
    def get_values(self):
        res = super(arsConfigMaterDataRestriction, self).get_values()
        fetch_details = self.env['ir.config_parameter'].sudo()


        # Retrieve Many2many fields as lists of IDs separately for each group field
        xlsx_model_restrict = fetch_details.get_param('ars_after_sales.xlsx_model_restrict')

        res.update(
            xlsx_model_restrict=[(6, 0, literal_eval(xlsx_model_restrict))] if xlsx_model_restrict else False,
        )
        return res
