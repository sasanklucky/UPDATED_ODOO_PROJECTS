from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from odoo.exceptions import UserError, AccessError

class AccountInvoice_inherit(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def _determine_user_to_assign(self,type):
        cre_team_id = self.env['cre_team_configuration'].search([('type','=',type)],limit=1)
        member_ids = sorted(cre_team_id.team_member_ids.ids) if cre_team_id.team_member_ids else sorted(cre_team_id.team_member_ids.ids)
        assigned_user_id = False
        if member_ids:
            if cre_team_id.assign_method == 'randomly':
                last_assigned_user = self.env['mail.activity'].search([('cre_id', '=', cre_team_id.id)], order='create_date desc, id desc', limit=1).user_id
                index = 0
                if last_assigned_user and last_assigned_user.id in member_ids:
                    previous_index = member_ids.index(last_assigned_user.id)
                    index = (previous_index + 1) % len(member_ids)
                    assigned_user_id = self.env['res.users'].browse(member_ids[index])
                else:
                    previous_index = member_ids.index(cre_team_id.team_member_ids[0].id)
                    index = (previous_index + 1) % len(member_ids)
                    assigned_user_id = self.env['res.users'].browse(member_ids[index])
            elif cre_team_id.assign_method == 'balanced':
                ticket_count_data = self.env['mail.activity'].read_group([('user_id', 'in', member_ids), ('cre_id', '=', cre_team_id.id)], ['user_id'], ['user_id'])
                open_ticket_per_user_map = dict.fromkeys(member_ids, 0)
                open_ticket_per_user_map.update((item['user_id'][0], item['user_id_count']) for item in ticket_count_data)
                assigned_user_id = self.env['res.users'].browse(min(open_ticket_per_user_map, key=open_ticket_per_user_map.get))
        return assigned_user_id

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        warranty_ids = self.env['ars.sale.warranty'].search(
            [('order_id.name', '=', self.origin), ('partner_id', '=', self.partner_id.id)])
        for wr in warranty_ids:
            # if wr.state in ('draft', 'inprocess'):
            #     raise UserError(_('Some of warranty claims are in Draft/In-Process state. Please check and proceed.'))
            # else:
            self._cr.execute("update ars_sale_warranty set state='done' where id =" + str(wr.id))
        res = super(AccountInvoice_inherit, self).action_invoice_open()
        self.ensure_one()
        vin_no = self.env['account.invoice.line'].search([('invoice_id','=',self.id)],limit=1).vin_no
        param = self.env['ir.config_parameter'].sudo()
        sale_followup_days = param.get_param('ars_mail_survey.sale_followup_days')
        postsale_followup_days = param.get_param('ars_mail_survey.postsale_followup_days')
        today = date.today()
        sale_order_search = self.env['mail.activity'].search([('psf_order_id','=',self.order_id.id)])
        if not sale_order_search and not self.partner_id.opt_out:
                if self and self.team_id.team_type == 'sales' and self.type not in  ['in_refund','in_invoice']:
                    user_id = self._determine_user_to_assign(type='post_sales')
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_call').id,
                        'summary': _('PSF Sales/' + (vin_no.name if vin_no else '')),
                        'res_id': self.order_id.partner_id.id,
                        'res_model_id': self.env.ref('mail.model_res_partner').id,
                        'invoice_type': 'sales',
                        'invoice_id': self.id,
                        'mobile': self.order_id.partner_id.mobile,
                        'cre_id': self.env['cre_team_configuration'].search([('type','=','post_sales')],limit=1).id,
                        'user_id': user_id.id if user_id else self.env.user.id,
                        'date_deadline': (today + timedelta(days=int(sale_followup_days))) if sale_followup_days else (today + timedelta(days=self.env.ref('mail.mail_activity_data_call').days))
                    })
                if (self and self.team_id.team_type == 'after_sales' and self.type not in ['in_refund','in_invoice']
                        and not self.service_options.psf_restrict):
                    user_id = self._determine_user_to_assign(type='post_service')
                    self.env['mail.activity'].sudo().create({
                        'psf_order_id':self.order_id.id,
                        'activity_type_id': self.env.ref('mail.mail_activity_data_call').id,
                        'summary': _('PSF Service/' + (self.vin if self.vin else '')),
                        'res_id': self.order_id.partner_id.id,
                        'res_model_id': self.env.ref('mail.model_res_partner').id,
                        'invoice_type': 'after_sales',
                        'invoice_id': self.id,
                        'mobile': self.order_id.partner_id.mobile,
                        'cre_id': self.env['cre_team_configuration'].search([('type','=','post_service')],limit=1).id,
                        'user_id':user_id.id if user_id else self.env.user.id,
                        'date_deadline' : (today + timedelta(days=int(postsale_followup_days))) if postsale_followup_days else (today + timedelta(days=self.env.ref('mail.mail_activity_data_call').days))
                    })
            # activity._onchange_activity_type_id()
        return res
