from collections import defaultdict
from datetime import date, datetime, timedelta
import pytz
from odoo.http import request
from odoo.exceptions import UserError, AccessError, ValidationError
from lxml import etree
from openerp.osv.orm import setup_modifiers
from odoo import models, fields, api, _
from lxml import html


class ARS_MailActivity(models.Model):
    _name = 'mail.activity'
    _inherit = ['mail.activity', 'mail.thread']

    company_id = fields.Many2one('res.company', compute="get_company", store=True)
    active = fields.Boolean("Active", default=True)
    exact_psf_due_date = fields.Date(string='Due Date', store=True)
    satisfaction_status = fields.Selection(
        [('satisfied', 'Satisfied'), ('dissatisfied', 'Dissatisfied')],
        string="Survey Status", )

    response_create_date = fields.Datetime(
        string="Survey Complete Date",
        compute="_compute_response_create_date",
        store=True
    )

    @api.depends('response_id.create_date')
    def _compute_response_create_date(self):
        for rec in self:
            if rec.response_id:
                rec.response_create_date = rec.response_id.create_date
            else:
                rec.response_create_date = False

    @api.model
    def create(self, values):
        res = super(ARS_MailActivity, self).create(values)
        if self.note:
            text_con = html.fromstring(self.note)
            char_con = text_con.text_content()
            self.env['mail.activity.remark'].create({'activity_id': self.id,
                                                     'date': datetime.today(),
                                                     'remark': char_con})
        return res

    @api.multi
    def write(self, vals):
        for rec in self:
            if vals.get('note') and vals['note'] != rec.note:
                text_con = html.fromstring(vals['note'])
                char_con = text_con.text_content()
                self.env['mail.activity.remark'].create({'activity_id': rec.id,
                                                         'date': datetime.today(),
                                                         'remark': char_con})
        return super(ARS_MailActivity, self).write(vals)

    @api.depends('response_id', 'survey_percentage')
    def _compute_survey_percentage_stored(self):
        for rec in self:
            rec.survey_percentage_stored = rec.survey_percentage

    @api.multi
    @api.depends('response_id', 'survey_percentage')
    def get_survey_percentage(self):
        for rec in self:
            # print("==========")
            if rec.response_id.state == 'done':
                # try:
                questions = rec.response_id.user_input_line_ids.mapped('question_id')
                # question_marks = questions.mapped('labels_ids.quizz_mark')
                score = rec.response_id.quizz_score / (len(questions) * 100) * 100
                rec.survey_percentage = float("%.2f" % score)
                rec.write({'survey_marks': float("%.2f" % score)})
                # rec.write({'satisfaction_status': 'satisfied' if rec.survey_marks >= 60 else 'dissatisfied'})
                # except ZeroDivisionError:
                #     rec.survey_percentage = 0

    invoice_type = fields.Selection([('sales', 'Sales'), ('after_sales', 'After Sales')], string="Invoice Type")
    invoice_id = fields.Many2one('account.invoice', string="Customer Invoice")
    cre_id = fields.Many2one('cre_team_configuration', string="CRE Team")
    # stages = fields.Selection(
    #     [('pending', 'Pending'), ('survey_done', 'Survey Done'),
    #      ('ticket_created', 'Ticket Created'),
    #      ('survey_incomplete', 'Survey Incomplete'),
    #      ('completed', 'Completed')],
    #     string="Status", default="pending", store=True)
    stages = fields.Selection(
        [('pending', 'Pending'), ('survey_done', 'Survey Done'), ('ticket_created', 'Ticket Created'),
         ('completed', 'Completed')], string="Status", default="pending", store=True)
    # compute_stages = fields.Char(string="Compute Stages",compute="_get_compute_stages")
    survey_percentage = fields.Float(string="Survey %", compute="get_survey_percentage")
    survey_percentage_stored = fields.Float(compute="_compute_survey_percentage_stored")
    survey_marks = fields.Float(string="Survey Marks")
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response")
    ticket_count = fields.Integer(string="Ticket Count", compute="_get_ticket_count")
    psf_order_id = fields.Many2one('sale.order', 'Order ID', index=True)
    reason_id = fields.Many2one('mail.activity.cancel.reason')
    tag_ids = fields.Many2many('res.partner.category', string='Tags')
    cus_feedback = fields.Char('Feedback')
    survey_stage = fields.Selection([('survey_done', 'Complete Survey'),
                                     ('survey_incomplete', 'Incomplete Survey')],
                                    string="Survey Status", store=True)
    reg_no = fields.Char(string="Reg No")
    vin_no = fields.Char(string="Vin No")

    @api.multi
    def get_company(self):
        for rec in self:
            if rec.invoice_id and not rec.company_id:
                rec.company_id = rec.invoice_id.company_id
            else:
                company = rec.user_id.company_id.id
                rec.company_id = company

    @api.multi
    def _get_ticket_count(self):
        for rec in self:
            helpdesk_ticket_count = self.env['helpdesk.ticket'].search_count([('activity_source_id', '=', rec.id)])
            rec.ticket_count = helpdesk_ticket_count or 0

    # @api.depends('response_id')
    # @api.multi
    # def _get_compute_stages(self):
    #     for rec in self:
    #         if rec.response_id.state == 'done':
    #             rec.write({'compute_stages':'survey_done','stages' :'survey_done'})
    #         helpdesk_ticket_count = self.env['helpdesk.ticket'].search_count([('activity_source_id','=',rec.id)])

    #         if helpdesk_ticket_count > 1:
    #             rec.write({'compute_stages':'ticket_created','stages':'ticket_created'})
    #         helpdesk_ticket_ids = self.env['helpdesk.ticket'].search([('activity_source_id','=',rec.id)]).mapped('stage_id.sequence')
    #         if 2 in helpdesk_ticket_ids:
    #             rec.action_done()

    @api.multi
    def action_done(self):
        """ Wrapper without feedback because web button add context as
        parameter, therefore setting context to feedback """
        helpdesk_id = self.env['helpdesk.ticket'].search([('activity_source_id', '=', self.id)])
        if helpdesk_id and helpdesk_id.stage_id.sequence not in [2, 3]:
            raise ValidationError("Helpdesk Ticket has not been solved yet.")
        else:
            return self.action_feedback()

    @api.onchange('activity_type_id')
    def _onchange_activity_type_id(self):
        param = self.env['ir.config_parameter'].sudo()
        sale_followup_days = param.get_param('ars_mail_survey.sale_followup_days')
        postsale_followup_days = param.get_param('ars_mail_survey.postsale_followup_days')

        if self.activity_type_id:
            print(self.activity_type_id.name)
            self.summary = self.activity_type_id.summary
            tz = self.user_id.sudo().tz
            if tz:
                today_utc = pytz.UTC.localize(datetime.utcnow())
                today = today_utc.astimezone(pytz.timezone(tz))
            else:
                today = datetime.now()
            if self.invoice_type == 'sales':
                self.date_deadline = ((today + timedelta(days=int(sale_followup_days)))) if sale_followup_days else (
                        today + timedelta(days=self.env.ref('mail.mail_activity_data_call').days))
            elif self.invoice_type == 'after_sales':
                self.date_deadline = (
                    (today + timedelta(days=int(postsale_followup_days)))) if postsale_followup_days else (
                        today + timedelta(days=self.env.ref('mail.mail_activity_data_call').days))
            else:
                self.date_deadline = (today + timedelta(days=self.activity_type_id.days))

    @api.multi
    def get_invoice_form(self):
        return {
            'name': _('Invoice Details'),
            'res_model': 'account.invoice',
            'res_id': self.invoice_id.id,
            'views': [(False, 'form'), ],
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'self'
        }

    def update_res_partner(self):
        for activity in self:
            if activity.date_deadline <= fields.Date.today():
                self.env['bus.bus'].sendone(
                    (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
                    {'type': 'activity_updated', 'activity_deleted': False})

    def action_feedback(self, feedback=False):
        message = self.env['mail.message']
        if feedback:
            self.write(dict(feedback=feedback))
            log = self.env['activity_log_report'].sudo().search([('activity_id', '=', self.id)])
            if log:
                log.write(dict(feedback=self.feedback))
            self.write(dict(feedback=feedback))
        # Search for all attachments linked to the activities we are about to unlink. This way, we
        # can link them to the message posted and prevent their deletion.
        attachments = self.env['ir.attachment'].search_read([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ], ['id', 'res_id'])

        activity_attachments = defaultdict(list)
        for attachment in attachments:
            activity_id = attachment['res_id']
            activity_attachments[activity_id].append(attachment['id'])

        for activity in self:
            record = self.env[activity.res_model].browse(activity.res_id)
            if record and activity.activity_type_id:
                if 'testdrive' in activity.activity_type_id.name.lower() or 'test drive' in activity.activity_type_id.name.lower():
                    test_drive_obj = self.env['ars.test.drive']
                    if activity.feedback and activity.feedback[3:-4]:
                        test_drive_remark = activity.feedback[3:-4]
                    elif activity.summary:
                        test_drive_remark = activity.summary
                    elif activity.feedback and activity.feedback[3:-4]:
                        test_drive_remark = activity.feedback[3:-4]
                    test_drive_obj.create({'opportunity_id': record.id,
                                           'test_drive_date': datetime.today(),
                                           'user_id': activity.user_id.id,
                                           'test_drive_remark': test_drive_remark if test_drive_remark else ''})
                    record.is_test_drive = True
            record.message_post_with_view(
                'mail.message_activity_done',
                values={'activity': activity},
                subtype_id=self.env.ref('mail.mt_activities').id,
                mail_activity_type_id=activity.activity_type_id.id,
            )

            # Moving the attachments in the message
            # TODO: Fix void res_id on attachment when you create an activity with an image
            # directly, see route /web_editor/attachment/add
            activity_message = record.message_ids[0]
            message_attachments = self.env['ir.attachment'].browse(activity_attachments[activity.id])
            message_attachments.write({
                'res_id': activity_message.id,
                'res_model': activity_message._name,
            })
            activity_message.attachment_ids = message_attachments
            message |= activity_message
        if self.invoice_type in ['sales', 'after_sales']:
            pass
        else:
            self.unlink()
        return message.ids and message.ids[0] or False

    @api.multi
    def action_start_survey(self):
        request.session['type_id'] = self.id
        request.session['type'] = 'activity'
        param = self.env['ir.config_parameter'].sudo()
        sale_survey_id = param.get_param('ars_mail_survey.sale_survey_id')
        postsale_survey_id = param.get_param('ars_mail_survey.post_sale_survey_id')
        sale_survey = self.env['survey.survey'].browse(int(sale_survey_id))
        postsale_survey = self.env['survey.survey'].browse(int(postsale_survey_id))
        module = self.env.context.get('module')
        print(self.response_id, 'self.response_id')
        if self.invoice_type == 'sales':
            if module == 'crm_psf':
                request.session['action'] = self.env.ref('ars_mail_survey.action_inherited_mail_activity_view_1').id
            elif module == 'call_psf':
                request.session['action'] = self.env.ref('ac_con_psf_helpesk.action_inherited_mail_activity_view_2').id
            if not self.response_id:
                request.session['action'] = 'ars_mail_survey.sales_followup_mail_activity_action'
                response = self.env['survey.user_input'].create(
                    {'survey_id': sale_survey.id, 'partner_id': self.user_id.partner_id.id})
                self.response_id = response.id
            else:
                response = self.response_id
            return sale_survey.with_context(survey_token=response.token).action_start_survey()

        elif self.invoice_type == 'after_sales':
            if module == 'crm_psef':
                request.session['action'] = self.env.ref(
                    'ars_mail_survey.action_inherited_mail_crm_post_service_activity_view_1').id
            elif module == 'call_psef':
                request.session['action'] = self.env.ref(
                    'ac_con_psf_helpesk.action_inherited_mail_post_service_activity_view_1').id
            if not self.response_id:
                response = self.env['survey.user_input'].create(
                    {'survey_id': postsale_survey.id, 'partner_id': self.user_id.partner_id.id})
                self.response_id = response.id
            else:
                response = self.response_id
            # grab the token of the response and start surveying
            return postsale_survey.with_context(survey_token=response.token).action_start_survey()

    # @api.model
    # def create_helpdesk_ticket(self, activity_id):
    #     if activity_id.invoice_type == 'sales':
    #         seller = activity_id.env.user.company_id.partner_id.id
    #         vin_no = activity_id.env['account.invoice.line'].sudo().search(
    #             [('invoice_id', '=', activity_id.invoice_id.id),
    #              ('product_catalog_id.name', '=', 'Vehicle')],
    #             limit=1).vin_no
    #         sale_date = activity_id.invoice_id.date_invoice
    #         model = self.env['account.invoice.line'].sudo().search([('invoice_id', '=', activity_id.invoice_id.id)],
    #                                                                limit=1).product_id
    #         source_complaint_id = self.env['complaint.source'].sudo().search([('name', 'ilike', 'Post Sale Follow-up')])
    #         milage = 0
    #         vehicle_no = None
    #     else:
    #         seller = activity_id.invoice_id.reg_no.customer_ids.mapped('sold_by').ids[-1]
    #         vin_no = activity_id.vin
    #         sale_date = activity_id.invoice_id.reg_no.customer_ids.mapped('date_of_ownership')[-1]
    #         milage = activity_id.invoice_id.kilometer
    #         vehicle_no = activity_id.invoice_id.reg_no.licence_plate
    #         model = activity_id.invoice_id.model
    #         source_complaint_id = activity_id.env['complaint.source'].sudo().search(
    #             ['name', 'ilike', 'Post Service Follow-Up'])
    #     vals = {
    #         'name': 'Post Sales Follow up Complaint' if activity_id.invoice_type == 'sales' else 'Post Service Follow up Complaint' if activity_id.invoice_type == 'after_sales' else ' ',
    #         'user_id': activity_id.user_id.id,
    #         'partner_id': self.env['res.partner'].browse(activity_id.res_id).id,
    #         'partner_email': self.env['res.partner'].browse(activity_id.res_id).email,
    #         'activity_source_id': activity_id.id,
    #         'seller_dealer': seller,
    #         'vin_number': vin_no.name,
    #         'date_of_sale': sale_date,
    #         'milage': milage,
    #         'model': model.id,
    #         'vehicle_no': vehicle_no,
    #         'source_complaint_id': source_complaint_id.id
    #     }
    #     print(vals)
    #     helpdesk_model = self.env['helpdesk.ticket'].sudo()
    #     res = helpdesk_model.create(vals)
    #     activity_id.write({'stages': 'ticket_created'})

    @api.model
    def create_helpdesk_ticket(self, activity_id):
        if (type(activity_id).__name__) == 'list':
            activity_id = self.env['mail.activity'].search([('id', 'in', activity_id)])
        elif not activity_id:
            activity_id = self
        if activity_id.invoice_type == 'sales':
            seller = activity_id.env.user.company_id.partner_id.id
            vin_no = activity_id.env['account.invoice.line'].sudo().search(
                [('invoice_id', '=', activity_id.invoice_id.id)],
                limit=1).vin_no
            vin_no = vin_no.name if vin_no else False
            sale_date = activity_id.invoice_id.date_invoice
            model = self.env['account.invoice.line'].sudo().search([('invoice_id', '=', activity_id.invoice_id.id)],
                                                                   limit=1).product_id
            source_complaint_id = self.env['complaint.source'].sudo().search([('name', 'ilike', 'Post Sale Follow-up')])
            milage = 0
            vehicle_no = None
        else:
            seller = activity_id.invoice_id.reg_no.customer_ids.mapped('sold_by').ids
            seller = seller[-1] if seller else False
            vin_no = activity_id.invoice_id.vin
            sale_date = activity_id.invoice_id.reg_no.customer_ids.mapped('date_of_ownership')
            sale_date = sale_date[-1] if sale_date else False

            milage = activity_id.invoice_id.kilometer
            vehicle_no = activity_id.invoice_id.reg_no.license_plate
            model = activity_id.invoice_id.model
            source_complaint_id = activity_id.env['complaint.source'].sudo().search(
                [('name', 'ilike', 'Post Service Follow-Up')])
        vals = {
            'name': 'Post Sales Follow up Complaint' if activity_id.invoice_type == 'sales' else 'Post Service Follow up Complaint' if activity_id.invoice_type == 'after_sales' else ' ',
            'user_id': activity_id.user_id.id,
            'partner_id': self.env['res.partner'].browse(activity_id.res_id).id,
            'partner_email': self.env['res.partner'].browse(activity_id.res_id).email,
            'activity_source_id': activity_id.id,
            'seller_dealer': seller,
            'vin_number': vin_no,
            'date_of_sale': sale_date,
            'milage': milage,
            'model': model.id,
            'vehicle_no': vehicle_no,
            'source_complaint_id': source_complaint_id.id
        }
        # print(vals)
        helpdesk_model = self.env['helpdesk.ticket'].sudo()
        res = helpdesk_model.create(vals)
        activity_id.write({'stages': 'ticket_created'})

    def ticket_details(self):
        list_view = self.env.ref('helpdesk.helpdesk_tickets_view_tree')
        form_view = self.env.ref('helpdesk.helpdesk_ticket_view_form')
        return {
            'name': _('Tickets'),
            'res_model': 'helpdesk.ticket',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': list_view.id,
            'views': [(list_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('activity_source_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'target': 'self'
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_result = super(ARS_MailActivity, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                   toolbar=toolbar,
                                                                   submenu=submenu)
        """
        Used for invisible the fields in Pop-up form view.
        when we click on 'Schedule Activity' in sale, purchase, invoice,etc. 
        """
        if view_type == 'form':
            # Parse the XML from the 'arch' key in the result dictionary
            doc = etree.XML(res_result['arch'])
            print('Helooo', self.env.context.get('default_res_model'))
            print('Helooo', self.env.context)
            res_id = self.env.context.get('default_res_model')
            rec_id = self.env.context.get('default_res_id')
            user_ids = self.env['crm.lead'].search([('id', '=', rec_id)]).team_id.team_type
            fields = self.env['mail.activity'].fields_get()
            product_template_fields_attrs = {}
            for key, val in fields.items():
                product_template_fields_attrs[key] = 'invisible'
            if res_id:
                print('Performing')
                for field_name, attr in product_template_fields_attrs.items():
                    # List is used for invisible the fields inside it,
                    # some moore fields we want to invisible just add inside it.
                    if field_name in ['survey_marks', 'res_name', 'psf_order_id', 'exact_psf_due_date']:
                        # Perform any modifications to the XML doc here
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            node.set('attrs', "{'%s': 1}" % attr)
                            setup_modifiers(node, res_result['fields'][field_name])
                    if field_name in ['activity_type_id']:
                        print("INSIDE")
                        if user_ids == 'sales':
                            print("SALES")
                            activity_ids = self.env['mail.activity.type'].search([('type', '=', 'sales')])
                            for node in doc.xpath("//field[@name='activity_type_id']"):
                                user_filter = "[('id', 'in'," + str(activity_ids.ids) + " )]"
                                node.set('domain', user_filter)
                        if user_ids == 'after_sales':
                            print("after_sales")
                            activity_ids = self.env['mail.activity.type'].search([('type', '=', 'after_sales')])
                            for node in doc.xpath("//field[@name='activity_type_id']"):
                                user_filter = "[('id', 'in'," + str(activity_ids.ids) + " )]"
                                node.set('domain', user_filter)
                    res_result['arch'] = etree.tostring(doc)
        return res_result
