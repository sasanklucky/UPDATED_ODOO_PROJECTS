from odoo import models, fields, api


class AutomationEmailConf(models.Model):
    _name = 'automation.email.conf'
    _description = 'Automation Email Configuration'
    _rec_name = 'report_template_id'

    mail_list_ids = fields.Many2many('res.partner', string='After-Sales PSF RSA Mail List')
    psf_rsa_report = fields.Boolean(string="Vehicle-Sales PSF RSA Report")
    csi_ssi_report = fields.Boolean(string="SSI CSI Report")
    ecb_report = fields.Boolean(string="ECB Report")
    report_template_id = fields.Many2one('mail.template')
    mail_template = fields.Html()
    mail_subject = fields.Text()

    @api.onchange('report_template_id')
    def get_template_content(self):
        content = self.report_template_id.body_html
        subject = self.report_template_id.subject
        self.mail_template = content
        self.mail_subject = subject


class AutomatedReport(models.Model):
    _name = 'automated.report'
    _description = "Automated Report for After-sale and Vehicle-sale"

    def send_csi_ssi_mail(self):
        print('send_csi_ssi_mail')
        rsa_attachment_vehicle_sale, rsa_attachment_after_sale, template = False, False, False
        records = self.env['automation.email.conf'].search([])
        for record in records:
            if record.csi_ssi_report:
                users = record.mail_list_ids
                model1 = self.env['after.sale.report'].search([])
                model2 = self.env['vehicle.sale.psf.report'].search([])
                rsa_attachment_after_sale_id = model1.export_xls(param=True)

                rsa_attachment_vehicle_sale_id = model2.export_xls_weekly(param=True)
                attachment_ids = []
                if rsa_attachment_after_sale_id:
                    attachment_ids.append(rsa_attachment_after_sale_id)
                if rsa_attachment_vehicle_sale_id:
                    attachment_ids.append(rsa_attachment_vehicle_sale_id)
                if record.report_template_id:
                    template = record.report_template_id
                    template.attachment_ids = [(5,)]

                    template.attachment_ids = [(4, attachment_id.id) for attachment_id in
                                               attachment_ids] if attachment_ids else False
                    template.send_mail(self.id, email_values={'recipient_ids': [(4, user.id) for user in users],
                                                          }, force_send=True)
                else:
                    mail_values = {
                        'subject': record.mail_subject,
                        'body_html': record.mail_template,
                        'recipient_ids': [(4, user.id) for user in record.mail_list_ids]
                    }
                    mail_obj = self.env['mail.mail'].create(mail_values)
                    mail_obj.write({'attachment_ids': [(4, attachment_id.id) for attachment_id in
                                               attachment_ids] if attachment_ids else False})
                    mail_obj.send()
