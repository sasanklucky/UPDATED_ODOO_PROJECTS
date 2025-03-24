from odoo import models, fields, api
from ast import literal_eval
from passlib.context import CryptContext

class arsConfigMaterDataRestriction(models.TransientModel):
    _inherit = 'res.config.settings'


    xlsx_model_restrict = fields.Many2many('ir.model', 'res_config_xlsx_model_restrict_rel', 'model_id', 'config_id',
                                        string="Model", help="Select the model")
    password_protection = fields.Char(related="company_id.stored_password", string="Password")

    def set_values(self):
        res = super(arsConfigMaterDataRestriction, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        print('xlsx_model_restrict', self.xlsx_model_restrict.ids)

        param.set_param('ars_after_sales.xlsx_model_restrict', self.xlsx_model_restrict.ids)
        param.set_param('web_export_view.password_protection', self.password_protection)
        return res

    @api.model
    def get_values(self):
        res = super(arsConfigMaterDataRestriction, self).get_values()
        fetch_details = self.env['ir.config_parameter'].sudo()


        # Retrieve Many2many fields as lists of IDs separately for each group field
        xlsx_model_restrict = fetch_details.get_param('ars_after_sales.xlsx_model_restrict')
        password_protection = self.env['ir.config_parameter'].sudo().get_param('web_export_view.password_protection')
        res.update(
            xlsx_model_restrict=[(6, 0, literal_eval(xlsx_model_restrict))] if xlsx_model_restrict else False,
            password_protection= password_protection,
        )
        return res

class ArsCompany(models.Model):
    _inherit = "res.company"

    stored_password = fields.Char(string="Password Store")


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def verify_password(self, user_id, password):
        user = self.browse(user_id)
        if not user:
            return False

        encrypted_password = user.password_crypt  # Hashed password
        crypt_ctx = CryptContext(schemes=["pbkdf2_sha512", "plaintext"], deprecated="auto")

        return crypt_ctx.verify(password, encrypted_password)