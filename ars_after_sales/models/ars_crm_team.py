from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class ARS_crm_team(models.Model):
    _inherit = "crm.team"

    team_type = fields.Selection([('sales', 'Sales'), ('website', 'Website'),('after_sales', 'After Sales')], string='Channel Type', default='sales',
                                  required=True,
                                  help="The type of this channel, it will define the resources this channel uses.")


    #for Aftersales & Sales user on click CRM menu action.
    # TODO JEM : refactor this stuff with xml action, proper customization,
    @api.model
    def action_your_pipeline(self):
        userid = self.env.user
        if userid.sale_team_id.team_type == 'after_sales':
            action = self.env.ref('ars_after_sales.action_crm_lead_opportunities_appointment').read()[0]
            tree_view_id = self.env.ref('ars_after_sales.crm_case_tree_view_oppor_inherit').id
            form_view_id = self.env.ref('ars_after_sales.crm_case_form_view_oppor_inherit').id
            kanb_view_id = self.env.ref('ars_after_sales.crm_case_kanban_view_leads_inherit').id
        else:
            action = self.env.ref('crm.crm_lead_opportunities_tree_view').read()[0]
            tree_view_id = self.env.ref('crm.crm_case_tree_view_oppor').id
            form_view_id = self.env.ref('crm.crm_case_form_view_oppor').id
            kanb_view_id = self.env.ref('crm.crm_case_kanban_view_leads').id
        user_team_id = self.env.user.sale_team_id.id
        if not user_team_id:
            user_team_id = self.search([], limit=1).id
            action['help'] = """<p class='oe_view_nocontent_create'>Click here to add new opportunities</p><p>
        Looks like you are not a member of a sales channel. You should add yourself
        as a member of one of the sales channel.
    </p>"""
            if user_team_id:
                action[
                    'help'] += "<p>As you don't belong to any sales channel, Odoo opens the first one by default.</p>"

        action_context = safe_eval(action['context'], {'uid': self.env.uid})
        if user_team_id:
            action_context['default_team_id'] = user_team_id

        action['views'] = [
            [kanb_view_id, 'kanban'],
            [tree_view_id, 'tree'],
            [form_view_id, 'form'],
            [False, 'graph'],
            [False, 'calendar'],
            [False, 'pivot']
        ]
        action['context'] = action_context
        return action



    @api.onchange('team_type')
    def _onchange_team_type(self):
        # res = super(ARS_crm_team, self)._onchange_team_type()
        if self.team_type in ('sales','after_sales'):
            self.use_opportunities = True
            self.use_quotations = True
            self.use_invoices = True
            self.use_leads = lambda self: self.user_has_groups('crm.group_use_lead')
            # do not override dashboard_graph_model 'crm.opportunity.report' if crm is installed
            self.dashboard_graph_model = 'crm.opportunity.report'
            # if not self.dashboard_graph_model:
            #     self.dashboard_graph_model = 'sale.report'
        else:
            self.use_quotations = False
            self.use_invoices = False
            self.dashboard_graph_model = 'sale.report'
        # return super(ARS_crm_team, self)._onchange_team_type()



