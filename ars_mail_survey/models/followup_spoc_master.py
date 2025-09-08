from odoo import models, fields, api

class CRETeamConfiguration(models.Model):
    _name = 'cre_team_configuration'
    _description = 'CRE Team Configuration'

    name = fields.Char('Name')
    type = fields.Selection([('post_sales','Post Sales'),('post_service','Post Service')],string="Team Type")
    assign_method = fields.Selection([('randomly', 'Random'),('balanced', 'Balanced')], string='Assignment Method', default='balanced')
    team_member_ids = fields.Many2many('res.users',string="Team Members")