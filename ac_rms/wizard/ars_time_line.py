from odoo import models, fields,api



class ARS_check_regn(models.TransientModel):
    _name = "time.line"


    main_process_id = fields.Char('Process')
    start = fields.Datetime('Start Time')
    end = fields.Datetime('End Time')
    resource_id = fields.Many2one('resource.resource','Resource')
    user = fields.Many2one('res.users','Resource')

    @api.multi
    def get_mail_message_data(self):
        return True

