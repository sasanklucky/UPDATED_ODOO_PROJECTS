from odoo import models, fields, api

class ars_configure_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    # def stage_filters(self):
    #     print("ok im running")
    #     act=self.env['crm.stage']
    #     for r in act.search([('team_id','=','After sales')]):
    #          print("executed")

    sale_followup_days = fields.Integer('Sale Followup Activity Days')
    postsale_followup_days = fields.Integer('Post Sale Followup Activity Days')
    survey_percentage = fields.Float('Survey Percentage')
    sale_survey_id = fields.Many2one('survey.survey', string="Sale Survey")
    post_sale_survey_id = fields.Many2one('survey.survey', string="Post Sale Survey")


    @api.multi
    def set_values(self):
        super().set_values()
        param = self.env['ir.config_parameter'].sudo()
        sale_followup_days = self.sale_followup_days or False
        postsale_followup_days = self.postsale_followup_days or False
        sale_survey_id = self.sale_survey_id.id or False
        post_sale_survey_id = self.post_sale_survey_id.id or False
        survey_percentage = self.survey_percentage or False
        sale_text = self.sale_text or False
        max_fleet_size = self.max_fleet_size or False
        param.set_param('ars_mail_survey.sale_followup_days', sale_followup_days)
        param.set_param('ars_mail_survey.postsale_followup_days', postsale_followup_days)
        param.set_param('ars_mail_survey.sale_survey_id', sale_survey_id)
        param.set_param('ars_mail_survey.post_sale_survey_id', post_sale_survey_id)
        param.set_param('ars_mail_survey.survey_percentage',survey_percentage)
        param.set_param('ars_after_sales.sale_text',sale_text)
        param.set_param('ars_after_sales.max_fleet_size',max_fleet_size)


    @api.model
    def get_values(self):
        res = super().get_values()
        sale_followup_days = self.env['ir.config_parameter'].sudo().get_param('ars_mail_survey.sale_followup_days')
        postsale_followup_days = self.env['ir.config_parameter'].sudo().get_param('ars_mail_survey.postsale_followup_days')
        sale_survey_id = self.env['ir.config_parameter'].sudo().get_param('ars_mail_survey.sale_survey_id')
        post_sale_survey_id = self.env['ir.config_parameter'].sudo().get_param('ars_mail_survey.post_sale_survey_id')
        survey_percentage = self.env['ir.config_parameter'].sudo().get_param('ars_mail_survey.survey_percentage')
        sale_text = self.env['ir.config_parameter'].sudo().get_param('ars_after_sales.sale_text')
        max_fleet_size = self.env['ir.config_parameter'].sudo().get_param('ars_after_sales.max_fleet_size')
        res.update(
            sale_followup_days = int(sale_followup_days) if sale_followup_days else False,
            postsale_followup_days = int(postsale_followup_days) if postsale_followup_days else False,
            survey_percentage = float(survey_percentage) if survey_percentage else False,
            sale_survey_id = int(sale_survey_id) if sale_survey_id else False,
            post_sale_survey_id = int(post_sale_survey_id) if post_sale_survey_id else False,
            sale_text = sale_text if sale_text else False,
            max_fleet_size = int(max_fleet_size) if max_fleet_size else False)

        return res
