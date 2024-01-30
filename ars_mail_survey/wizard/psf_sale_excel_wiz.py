from odoo import models, fields, api, _


class PSFSaleReportExcel(models.TransientModel):
    _name = 'sale.excel.wiz'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.multi
    def action_psf_sale(self):
        mail_act_obj = self.env['mail.activity']
        mail_activity = mail_act_obj.search([('date_deadline', '>=', self.start_date), ('date_deadline', '<=', self.end_date),('invoice_type','=','sales')])
        doc_id = mail_act_obj.export_sale_xls(mail_activity)
        print('doc_id',doc_id)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?id=%s&download=true' % doc_id.id,
            'target': 'current',
        }