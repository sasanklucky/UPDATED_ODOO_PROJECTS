from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = "mail.activity"

    @api.model
    def create(self, vals):
        record = super(MailActivity, self).create(vals)
        if record.res_model == 'crm.lead' and record.res_id:
            record.update_lead_stage()
        return record

    def write(self, vals):
        res = super(MailActivity, self).write(vals)
        if 'date_deadline' in vals:
            for record in self:
                if record.res_model == 'crm.lead' and record.res_id:
                    record.update_lead_stage()
        return res

    def update_lead_stage(self):
        """Update lead stage dynamically based on activity due date, considering multi-company and sales team"""
        for activity in self:
            lead = self.env['crm.lead'].search([('id', '=', activity.res_id)], order="create_date desc", limit=1)  # Fetch latest data
            if lead and lead.team_id.team_type == 'sales':
                today = fields.Date.from_string(fields.Date.today())
                deadline = fields.Date.from_string(activity.date_deadline)
                print(f"today :{today}, activity.date_deadline :{activity.date_deadline} ")
                days_diff = (deadline - today).days
                # Define the base domain to filter stages by company and sales team
                stage_domain = [('team_id', 'in', [lead.team_id.id, False])]

                # Add team_id to filter stages for the correct sales team
                if lead.team_id:
                    stage_domain += ['|', ('team_id', '=', False), ('team_id', '=', lead.team_id.id)]
                if lead.stage_id.name in ['HOT', 'hot', 'Hot', 'COLD', 'Cold', 'cold', 'WARM', 'Warm', 'warm', 'NEW', 'New', 'new', 'test drive', 'TEST DRIVE', 'Test Drive']:

                    hot_stage = self.env['ir.config_parameter'].sudo().get_param('crm_stage_hot')
                    warm_stage = self.env['ir.config_parameter'].sudo().get_param('crm_stage_warm')
                    cold_stage = self.env['ir.config_parameter'].sudo().get_param('crm_stage_cold')

                    hot_stage = int(hot_stage) if hot_stage else None
                    warm_stage = int(warm_stage) if warm_stage else None
                    cold_stage = int(cold_stage) if cold_stage else None

                    # Determine the appropriate stage based on the due date difference
                    if days_diff <= hot_stage:  # Hot stage
                        stage = 'Hot'
                        stage_domain.extend(['|', '|', ('name', '=', 'Hot'), ('name', '=', 'HOT'), ('name', '=', 'hot')])
                    elif hot_stage < days_diff <= warm_stage:  # Warm stage
                        stage = 'Warm'
                        stage_domain.extend(['|', '|', ('name', '=', 'Warm'), ('name', '=', 'WARM'), ('name', '=', 'warm')])
                    elif days_diff >= cold_stage:
                        stage_domain.extend(['|', '|', ('name', '=', 'Cold'), ('name', '=', 'COLD'), ('name', '=', 'cold')])
                        stage = 'Cold'
                    print(stage_domain)
                    # Use `_stage_find()` to get the correct stage
                    if stage_domain:
                        new_stage = lead._stage_find(team_id=lead.team_id.id, domain=stage_domain)
                        print(new_stage, 'stage')
                        if new_stage:
                            lead.stage_id = new_stage.id
                        else:
                            raise ValidationError(
                                _(f"Please create a {stage} stage under the {lead.team_id.name} before proceeding."))

                # Only For Test Drive it should come to here. because we implemented Test drive from both
                # elif activity.activity_type_id.name.lower().strip().replace(" ", "") == 'testdrive' and lead.stage_id.name in ['HOT', 'hot', 'Hot', 'COLD', 'Cold', 'cold', 'WARM', 'Warm', 'warm', 'NEW', 'New', 'new']:
                #     stage_domain.extend(['|', '|', ('name', '=', 'Test Drive'), ('name', '=', 'TEST DRIVE'), ('name', '=', 'test drive')])
                #     new_stage_test_drive = lead._stage_find(team_id=lead.team_id.id, domain=stage_domain)
                #     print(new_stage_test_drive, 'stage')
                #     if new_stage_test_drive:
                #         lead.stage_id = new_stage_test_drive.id
                #     else:
                #         raise ValidationError(_(f"Please create a {activity.activity_type_id.name} stage under the {lead.team_id.name} before proceeding."))

    @api.model
    def cron_update_lead_stages(self):
        """Scheduled action to update lead stages based on the latest mail.activity"""
        today = fields.Date.from_string(fields.Date.today())
        leads = self.env['crm.lead'].search([]).filtered(lambda l: l.team_id.team_type == 'sales' and l.active == True and l.stage_id.name in ['hot','HOT', 'Hot', 'COLD', 'cold', 'Cold', 'warm', 'Warm', 'WARM', 'NEW', 'New', 'new'] and len(l.vehicle_line) > 0)  # Get all CRM Leads of sales
        # print(len(leads))
        for lead in leads:
            # print(len(lead.vehicle_line))
            if lead.team_id.team_type == 'sales':
                last_activity = self.env['mail.activity'].search([
                    ('res_model', '=', 'crm.lead'),
                    ('res_id', '=', lead.id)
                ], order="create_date desc", limit=1)

                if last_activity:
                    # activity_name = last_activity.activity_type_id.name.lower().strip().replace(" ", "")
                    # if activity_name == 'testdrive':
                    #     continue  # Skip the rest of the loop for "Test Drive" activities
                    deadline = fields.Date.from_string(last_activity.date_deadline)
                    days_diff = (deadline - today).days

                    stage_name = False  # Default: No change
                    hot_stage = self.env['ir.config_parameter'].sudo().get_param('crm_stage_hot')
                    warm_stage = self.env['ir.config_parameter'].sudo().get_param('crm_stage_warm')
                    cold_stage = self.env['ir.config_parameter'].sudo().get_param('crm_stage_cold')

                    hot_stage = int(hot_stage) if hot_stage else None
                    warm_stage = int(warm_stage) if warm_stage else None
                    cold_stage = int(cold_stage) if cold_stage else None

                    if days_diff <= hot_stage:
                        stage_name = 'Hot'
                    elif hot_stage < days_diff <= warm_stage:
                        stage_name = 'Warm'
                    elif days_diff >= cold_stage:
                        stage_name = 'Cold'


                    if stage_name:
                        stage = self.env['crm.stage'].search([
                            '|', ('team_id', '=', False), ('team_id', '=', lead.team_id.id),
                            ('name', 'ilike', stage_name)
                        ], limit=1)

                        if stage:
                            print(lead.id)
                            lead.stage_id = stage.id
                            _logger.info(f"Updated Lead {lead.id} ({lead.name}) to Stage: {stage.name}")
                        else:
                            _logger.warning(f"Stage '{stage_name}' not found for Lead {lead.id} ({lead.name})")

        _logger.info("CRM Lead Stages Update Cron Job Completed.")

    def unlink(self):
        """Override unlink to check if there are remaining scheduled activities for the CRM lead"""
        for activity in self:
            if activity.res_model == 'crm.lead' and activity.res_id:
                lead = self.env['crm.lead'].browse(activity.res_id)
                if lead.stage_id.name not in ['RETAIL', 'Retail', 'retail', 'BOOKED', 'Booked', 'booked'] and lead.stage_id:
                    # Check if any other scheduled activities exist for the lead
                    other_activities = self.env['mail.activity'].search_count([
                        ('res_model', '=', 'crm.lead'),
                        ('res_id', '=', lead.id),
                        ('id', '!=', activity.id)  # Exclude the one being deleted
                    ])
                    team_id = lead.team_id.id if lead.team_id else False
                    # Find "Booked" stage
                    stage_new = lead._stage_find(team_id=team_id, domain=[('name', 'in', ['New', 'NEW', 'new'])])
                    if not stage_new:
                        raise ValidationError(
                            _(f"Please create a 'New' stage under the {lead.team_id.name} before proceeding."))
                    if other_activities == 0:
                        _logger.info(f"No scheduled activities left for CRM Lead {lead.id} ({lead.name})")
                        lead.stage_id = stage_new.id

        return super(MailActivity, self).unlink()

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def write(self, vals):
        """Detect cancellation of sale order and update the CRM stage."""
        for order in self:
            previous_state = order.state  # Store the current state before update

        # Call the original write method
        result = super(SaleOrderInherit, self).write(vals)
        # After the write, check if the sale order is now canceled
        for order in self:
            crm_lead = order.opportunity_id
            if crm_lead and order.sale_type == 'vehicle':
                if 'state' in vals and vals['state'] == 'cancel' and previous_state != 'cancel':
                    if order.opportunity_id and order.lost_reason_id and order.child_lost_reason_id.id:  # Check if it's linked to a CRM lead
                        crm_lead.write({'lost_reason': order.lost_reason_id.id,
                                        'child_lost_reason': order.child_lost_reason_id.id})  # Assign reason

                        # Post log note in CRM lead chatter
                        # crm_lead.message_post(
                        #     body=f"Opportunity marked as lost due to sale order cancellation. <br/>"
                        #          f"<b>Reason:</b> {order.sale_cancel_reason_id.name}",
                        #     subtype="mail.mt_note"
                        # )
                        # Mark the lead as lost
                        crm_lead.action_set_lost()



                elif 'state' in vals and vals['state'] == 'sale':
                    if order.opportunity_id:  # Check if it's linked to a CRM lead
                        # Search for the "Lost" stage in CRM pipeline
                        stage_domain = ['|', ('team_id', '=', False), ('team_id', '=', crm_lead.team_id.id)]
                        # Add stage names for Test Drive
                        stage_domain.extend(['|', '|',
                                             ('name', '=', 'BOOKED'),
                                             ('name', '=', 'Booked'),
                                             ('name', '=', 'booked')
                                             ])
                        # Use `_stage_find()` to get the correct stage
                        if stage_domain:
                            booked_stage = crm_lead._stage_find(team_id=crm_lead.team_id.id, domain=stage_domain)
                            if not booked_stage:
                                raise ValidationError(_(f"Please create a 'Booked' stage under the {crm_lead.team_id.name} before proceeding."))

                            # Update the CRM lead stage
                            crm_lead.stage_id = booked_stage.id

        return result

class ArsSaleAdvancePaymentStageCheck(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for sl in sale_orders:
            if sl.sale_aftersales == 'sales' and sl.sale_type == 'vehicle':
                # Perform stage validation once
                crm_lead = self.env['crm.lead']
                team_id = sl.team_id.id if sl.team_id else False
                # Find "Booked" stage
                # stage_booked = crm_lead._stage_find(team_id=team_id, domain=[('name', 'in', ['Booked', 'booked', 'BOOKED'])])
                # if not stage_booked:
                #     raise ValidationError(_(f"Please create a 'Booked' stage under the {sl.team_id.name} before proceeding."))

                # Find "Retail" stage
                stage_retail = crm_lead._stage_find(team_id=team_id, domain=[('name', 'in', ['Retail', 'retail', 'RETAIL'])])
                if not stage_retail:
                    raise ValidationError(_(f"Please create a 'Retail' stage under the {sl.team_id.name} before proceeding."))

        return super(ArsSaleAdvancePaymentStageCheck, self).create_invoices()


# ''' Commented the code because not to lost the crm lead when user need to create credit note'''
# class CreditNoteReason(models.TransientModel):
#     _inherit = "account.invoice.refund"
#
#     # Added field for credit note reason purpose.
#     lost_reason_id = fields.Many2one('crm.lost.reason', 'Lost Reason')
    # ''' Commented the code because not to lost the crm lead when user need to create credit note'''

    # @api.multi
    # def compute_refund(self, mode='refund'):
    #     """Override refund process to update Lost Reason in the related CRM lead."""
    #     result = super(CreditNoteReason, self).compute_refund(mode)
    #
    #     invoices = self.env['account.invoice'].browse(self._context.get('active_ids', []))
    #     sale_orders = invoices.mapped('order_id')
    #
    #     # If the invoice is a refund (Credit Note)
    #     if not sale_orders and invoices.mapped('refund_invoice_id'):
    #         sale_orders = invoices.mapped('refund_invoice_id.order_id')
    #
    #     for sale_order in sale_orders:
    #         leads = sale_order.mapped('opportunity_id')
    #         if leads and self.lost_reason_id:
    #             leads.write({'lost_reason': self.lost_reason_id.id})
    #
    #             leads.message_post(body=_("Lost Reason updated: %s") % self.lost_reason_id.name)
    #
    #             leads.action_set_lost()
    #
    #     return result


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def write(self, vals):
        # Perform stage validation once
        # crm_lead = self.env['crm.lead']
        # team_id = self.team_id.id if self.team_id else False
        # # Find "Booked" stage
        # stage_booked = crm_lead._stage_find(team_id=team_id, domain=[('name', 'ilike', 'Booked')])
        # if not stage_booked:
        #     raise ValidationError(_(f"Please create a 'Booked' stage under the {self.team_id.name} before proceeding."))
        #
        # # Find "Retail" stage
        # stage_retail = crm_lead._stage_find(team_id=team_id, domain=[('name', 'ilike', 'Retail')])
        # if not stage_retail:
        #     raise ValidationError(_(f"Please create a 'Retail' stage under the {self.team_id.name} before proceeding."))
        res = super(AccountInvoice, self).write(vals)

        if 'state' in vals:  # Check if invoice state changed
            for invoice in self:
                if invoice.ars_invoice_type == 'vehicle' and invoice.type == 'out_invoice':
                    sale_orders = invoice.mapped('order_id')

                    # Check if it's a Credit Invoice (Refund)
                    if not sale_orders and invoice.refund_invoice_id:
                        sale_orders = invoice.refund_invoice_id.mapped('order_id')

                    for sale_order in sale_orders:
                        leads = sale_order.mapped('opportunity_id')
                        for lead in leads:
                            all_invoices = sale_order.invoice_ids | self.env['account.invoice'].search([
                                ('refund_invoice_id', 'in', sale_order.invoice_ids.ids)
                            ])  # Include related refunds

                            has_done_invoice = any(inv.state in ['open', 'paid'] for inv in all_invoices)

                            if has_done_invoice:
                                retail_stage = lead._stage_find(team_id=lead.team_id.id,
                                                                domain=[('name', 'ilike', 'Retail')])
                                if retail_stage:
                                    lead.stage_id = retail_stage.id

        return res

class CrmLeadLostStage(models.Model):
    _inherit = 'crm.lead'

    stage_name = fields.Char(related='stage_id.name', store=True)

    @api.multi
    def action_set_lost(self):
        # Call original method to archive the lead
        res = super(CrmLeadLostStage, self).action_set_lost()

        for rec in self:
            lost_stage = self._stage_find(team_id=rec.team_id.id, domain=[('name', 'ilike', 'Lost'), ('fold', '=', True)])
            if lost_stage:
                self.write({'stage_id': lost_stage.id})

        return res
# class ConfigParameterCrm(models.Model):
#     _inherit = 'ir.config_parameter'
#
#     crm_hot_stage = fields.Char

    # def create(self, vals):
    #     # Perform stage validation once
    #     crm_lead = self.env['crm.lead']
    #     team_id = self.team_id.id if self.team_id else False
    #     # Find "Booked" stage
    #     stage_booked = crm_lead._stage_find(team_id=team_id, domain=[('name', 'ilike', 'Booked')])
    #     if not stage_booked:
    #         raise ValidationError(_(f"Please create a 'Booked' stage under the {self.team_id.name} before proceeding."))
    #
    #     # Find "Retail" stage
    #     stage_retail = crm_lead._stage_find(team_id=team_id, domain=[('name', 'ilike', 'Retail')])
    #     if not stage_retail:
    #         raise ValidationError(_(f"Please create a 'Retail' stage under the {self.team_id.name} before proceeding."))
    #
    #     res = super(AccountInvoice, self).create(vals)
    #     if 'state' in vals:  # Check if invoice state changed
    #         for invoice in self:
    #             sale_orders = invoice.mapped('order_id')
    #
    #             # Check if it's a Credit Invoice (Refund)
    #             if not sale_orders and invoice.refund_invoice_id:
    #                 sale_orders = invoice.refund_invoice_id.mapped('order_id')
    #
    #             for sale_order in sale_orders:
    #                 leads = sale_order.mapped('opportunity_id')
    #                 for lead in leads:
    #                     all_invoices = sale_order.invoice_ids | self.env['account.invoice'].search([
    #                         ('refund_invoice_id', 'in', sale_order.invoice_ids.ids)
    #                     ])  # Include related refunds
    #
    #                     has_draft_invoice = any(inv.ars_invoice_type == 'vehicle' and inv.type == 'out_invoice' for inv in all_invoices)
    #
    #                     if has_draft_invoice:
    #                         booked_stage = lead._stage_find(domain=[('name', 'ilike', 'Booked')])
    #                         if booked_stage:
    #                             lead.stage_id = booked_stage.id
    #                     else:
    #                         retail_stage = lead._stage_find(domain=[('name', 'ilike', 'Retail')])
    #                         if retail_stage:
    #                             lead.stage_id = retail_stage.id
    #
    #     return res