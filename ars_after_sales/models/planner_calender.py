from odoo import models, fields, api,_


class planner_cander(models.Model):
    
    _name = 'planner.calender'
    
    
    
    name = fields.Char()
    resource_category = fields.Many2one('resource.category')
    member_ids = fields.One2many('res.users', 'planner_calender_id', string='Channel Members')
    
    
class user_cander(models.Model):
    
    _name = 'res.users'
    
    
    
    sale_team_id = fields.Many2one('planner.calender', 'Calender')