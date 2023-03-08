from odoo import models, fields, api, _
from datetime import datetime, timedelta
from lxml import etree
from openerp.osv.orm import setup_modifiers


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"

    stages = fields.Many2one('crm.stage')


class ARS_MailActivity(models.Model):
    _inherit = "mail.activity"

    mobile = fields.Char(string="Mobile", compute='_get_mobile_number', store=True)

    @api.multi
    def _get_mobile_number(self):
        for res in self:
            if res.res_model == 'crm.lead':
                crm_rec = self.env[res.res_model].browse(res.res_id)
                res.mobile = crm_rec.mobile
            else:
                print("Mail activity mobile update", res.res_model)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        con = self.env.context
        res = super(ARS_MailActivity, self).fields_view_get(view_id, view_type, toolbar, submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            userid = self.env.user
            if userid.sale_team_id.team_type == 'sales':
                user_ids = self.env['res.users'].search([('sale_team_id', '=', userid.sale_team_id.id)])
                for node in doc.xpath("//field[@name='user_id']"):
                    user_filter = "[('id', 'in'," + str(user_ids.ids) + " )]"
                    node.set('domain', user_filter)
            elif userid.sale_team_id.team_type == 'after_sales':
                user_ids = self.env['res.users'].search([('sale_team_id', '=', userid.sale_team_id.id)])
                for node in doc.xpath("//field[@name='user_id']"):
                    user_filter = "[('id', 'in'," + str(user_ids.ids) + " )]"
                    node.set('domain', user_filter)

        res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def default_get(self, fields):
        con = self.env.context
        res = super(ARS_MailActivity, self).default_get(fields)
        if self.env.context.get('active_ids'):
            model_obj = self.env.context.get('active_model')
            model_id = self.env['ir.model'].search([('model', '=', model_obj)]).id
            res.update({
                'res_id': self.env.context.get('active_ids')[0],
                'res_model': self.env.context.get('active_model'),
                'res_model_id': model_id
            })

        if not fields or 'res_model_id' in fields and res.get('res_model'):
            res['res_model_id'] = self.env['ir.model']._get(res['res_model']).id
        return res

    @api.multi
    def action_close_dialog(self):
        con = self.env.context
        if self.env.context.get('active_ids'):
            for act_id in self.env.context.get('active_ids'):
                if act_id != self.env.context.get('active_ids')[0]:
                    model_obj = self.env.context.get('active_model')
                    model_id = self.env['ir.model'].search([('model', '=', model_obj)]).id
                    values = {
                        'res_id': act_id,
                        'res_model': self.env.context.get('active_model'),
                        'res_model_id': model_id,
                        'user_id': self.user_id.id,
                        'activity_type_id': self.activity_type_id.id,
                        'date_deadline': self.date_deadline
                    }
                    activity = super(ARS_MailActivity, self).create(values)
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def customer_details(self):
        e = self.res_model
        f = self.res_id
        return {
            'name': _('Customer Details'),
            'res_model': self.res_model,
            'res_id': self.res_id,
            'views': [(False, 'form'), ],
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'self'
        }
