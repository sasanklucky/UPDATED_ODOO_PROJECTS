from odoo import models, fields, tools, api, _
from collections import defaultdict
from datetime import datetime
from datetime import date


class activity_log_report(models.Model):
    _name = 'activity_log_report'

    def get_tag(self):
        for record in self:
            tag_lst = []
            for tag in record.lead_id.tag_ids:
                tag_lst.append(tag.id)
            record.tags = [(6, 0, tag_lst)]

    def compute_date(self):
        print()
        for record in self:
            # print('hello the test is',type(datetime.strptime(record.date_deadline,'%Y-%m-%d')),type(date.today()))
            if datetime.strptime(record.date_deadline, '%Y-%m-%d').date() >= date.today():
                record.date_boolean = True

    lead_id = fields.Many2one('crm.lead', string='Lead')
    activity_type_id = fields.Many2one('mail.activity.type', 'Activity')
    summary = fields.Char('Summary')
    date_deadline = fields.Date('Due Date')
    user_id = fields.Many2one('res.users', 'Assigned to')
    note = fields.Html('Note')
    activity_id = fields.Many2one('mail.activity', 'Activity Id')
    feedback = fields.Html('Feedback')
    company_name = fields.Char(related="lead_id.partner_id.name", string="Dealership Name")
    city = fields.Char(related="lead_id.partner_id.city", string="City")
    tags = fields.Many2many('crm.lead.tag', compute="get_tag")
    state = fields.Char(related="lead_id.partner_id.state_id.name", string="State")
    pin = fields.Char(related="lead_id.partner_id.zip", string="Pin")
    date_boolean = fields.Boolean(compute="compute_date")


class customer_dump_mis_report(models.Model):
    _name = 'customer_dump_mis_report'
    _description = 'Customer Enquiry Dump Mis Report'
    _auto = False

    def get_address(self):
        address = ''
        for record in self:
            record.address2 = f'{record.address} {record.address1}'

    def get_color(self):
        for record in self:
            color = record.product_id.attribute_value_ids.filtered(lambda x: x.attribute_id.name == 'color').ids
            if color:
                attribute = self.env['product.attribute.value'].sudo().search([('id', 'in', color)])
                record.color = attribute.name

    def get_invoice(self):
        for record in self:
            sales_order = self.env['sale.order'].sudo().search(
                [('opportunity_id', '=', record.record_id), ('state', '=', 'draft')])
            if sales_order:
                record.invoice = 'YES'
            else:
                record.invoice = 'NO'

            # if sales_order:
            #     invoice = self.env['account.invoice'].sudo().search([('order_id','in',sales_order)])
            #     if invoice:
            #         record.invoice = 'YES'
            #     else:
            #         record.invoice = 'NO'
            # else:
            #     record.invoice = 'NO'

    def get_existing_customer(self):
        for record in self:
            invoice = self.env['account.invoice'].sudo().search(
                [('partner_id', '=', record.partner_id.id), ('state', '=', 'paid')])
            if invoice:
                record.existing_customer = 'YES'
            else:
                record.existing_customer = 'NO'

    record_id = fields.Integer()
    company_id = fields.Many2one('res.company', 'Dealer Name')
    dealer_zone = fields.Selection(related="company_id.dealer_zone")
    dealer_code = fields.Char(related="company_id.dealer_code")
    enquiry_date = fields.Char('Enquiry Creation Date')
    purchase_date = fields.Char('Expected Purchase Date')
    no_of_days = fields.Char('Intension To Purchase Days')
    enquiry_category = fields.Char('Enquiry Category')
    user_id = fields.Many2one('res.users', 'Sales Consultant')
    partner_id = fields.Many2one('res.partner', 'Partner')
    city = fields.Char(related="partner_id.city")
    address = fields.Char(related="partner_id.street")
    address1 = fields.Char(related="partner_id.street2")
    address2 = fields.Char(compute="get_address")
    title = fields.Many2one('res.partner.title', 'Salutation')
    contact_name = fields.Char('Contact Name')
    phone = fields.Char('Phone')
    mobile = fields.Char("Mobile")
    email = fields.Char('Email ID')
    product_id = fields.Many2one('product.product', 'Variant')
    make = fields.Char(related="product_id.product_tmpl_id.brand_id.name")
    model = fields.Char(related="product_id.product_tmpl_id.name")
    color = fields.Char(compute="get_color")
    source_id = fields.Many2one('utm.source', 'Source')
    medium_id = fields.Many2one('utm.medium', 'First Enquiry Mode')
    invoice = fields.Char(compute="get_invoice")
    stage_id = fields.Many2one('crm.stage')
    test_drive = fields.Char()
    lost_reason = fields.Many2one('crm.lost.reason')
    existing_customer = fields.Char(compute="get_existing_customer")
    referred = fields.Char()
    note_1 = fields.Html('Note(1)')
    feedback_1 = fields.Html('Feedback(1)')
    note_2 = fields.Html('Note(2)')
    feedback_2 = fields.Html('Feedback(2)')
    note_3 = fields.Html('Note(3)')
    feedback_3 = fields.Html('Feedback(3)')


    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        print("table name", self._table);
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
        select row_number() over() as id,a.id as record_id,a.company_id,a.create_date::Date as enquiry_date,a.date_deadline 
            as purchase_date,a.date_deadline - a.create_date::Date as no_of_days,
            case
            when a.date_deadline - a.create_date::Date <= 30 then 'HOT'
            when a.date_deadline - a.create_date::Date > 30 and a.date_deadline - a.create_date::Date <= 60 then 'WARM'
            when a.date_deadline - a.create_date::Date > 60 then 'COLD'
            else ''
            end as enquiry_category,a.user_id,a.partner_id,a.title,a.contact_name,
            a.phone,a.mobile,a.email_from as email,a.source_id,a.medium_id,a.stage_id,a.lost_reason,b.product_id,
            a.referred as referred,
            case when a.is_test_drive = True then 'YES' else 'NO' end as test_drive,
			(select summary from activity_log_report where lead_id = a.id order by id desc limit 1 OFFSET 0) as note_1,
			(select feedback from activity_log_report where lead_id = a.id order by id desc limit 1 OFFSET 0) as feedback_1,
			(select summary from activity_log_report where lead_id = a.id order by id desc limit 1 OFFSET 1) as note_2,
			(select feedback from activity_log_report where lead_id = a.id order by id desc limit 1 OFFSET 1) as feedback_2,
			(select summary from activity_log_report where lead_id = a.id order by id desc limit 1 OFFSET 2) as note_3,
			(select feedback from activity_log_report where lead_id = a.id order by id desc limit 1 OFFSET 2) as feedback_3
            from crm_lead a join crm_lead_line b on a.id = b.lead_order_id
            where a.type = 'opportunity'
            
           
        )""" % (self._table))


        # select row_number() over() as id,a.id as record_id,a.company_id,a.create_date::Date as enquiry_date,a.date_deadline 
        #     as purchase_date,a.date_deadline - a.create_date::Date as no_of_days,
        #     case
        #     when a.date_deadline - a.create_date::Date <= 30 then 'HOT'
        #     when a.date_deadline - a.create_date::Date > 30 and a.date_deadline - a.create_date::Date <= 60 then 'WARM'
        #     when a.date_deadline - a.create_date::Date > 60 then 'COLD'
        #     else ''
        #     end as enquiry_category,a.user_id,a.partner_id,a.title,a.contact_name,
        #     a.phone,a.mobile,a.email_from as email,a.source_id,a.medium_id,a.stage_id,a.lost_reason,b.product_id,
        #     a.referred as referred
        #     from crm_lead a join crm_lead_line b on a.id = b.lead_order_id
        #     where a.type = 'opportunity'



class activity_inherit(models.Model):
    _inherit = 'mail.activity'



    @api.model
    def create(self, values):
        print('custom create called')
        res = super(activity_inherit, self).create(values)
        if res.res_model == 'crm.lead':
            self.env['activity_log_report'].create({
               'lead_id': res.res_id,
               'activity_type_id': res.activity_type_id.id,
               'summary': res.summary,
               'date_deadline': res.date_deadline,
               'user_id': res.user_id.id,
               'note': res.note,
               'activity_id':res.id

            })
        return res


    # def action_feedback(self, feedback=False):
    #     message = self.env['mail.message']
    #     if feedback:
    #         self.write(dict(feedback=feedback))
    #         log = self.env['activity_log_report'].sudo().search([('activity_id','=',self.id)])
    #         if log:
    #             log.write(dict(feedback=self.feedback))
    #
    #     # Search for all attachments linked to the activities we are about to unlink. This way, we
    #     # can link them to the message posted and prevent their deletion.
    #     attachments = self.env['ir.attachment'].search_read([
    #         ('res_model', '=', self._name),
    #         ('res_id', 'in', self.ids),
    #     ], ['id', 'res_id'])
    #
    #     activity_attachments = defaultdict(list)
    #     for attachment in attachments:
    #         activity_id = attachment['res_id']
    #         activity_attachments[activity_id].append(attachment['id'])
    #
    #     for activity in self:
    #         record = self.env[activity.res_model].browse(activity.res_id)
    #         record.message_post_with_view(
    #             'mail.message_activity_done',
    #             values={'activity': activity},
    #             subtype_id=self.env.ref('mail.mt_activities').id,
    #             mail_activity_type_id=activity.activity_type_id.id,
    #         )
    #
    #         # Moving the attachments in the message
    #         # TODO: Fix void res_id on attachment when you create an activity with an image
    #         # directly, see route /web_editor/attachment/add
    #         activity_message = record.message_ids[0]
    #         message_attachments = self.env['ir.attachment'].browse(activity_attachments[activity.id])
    #         message_attachments.write({
    #             'res_id': activity_message.id,
    #             'res_model': activity_message._name,
    #         })
    #         activity_message.attachment_ids = message_attachments
    #         message |= activity_message
    #
    #     self.unlink()
    #     return message.ids and message.ids[0] or False
