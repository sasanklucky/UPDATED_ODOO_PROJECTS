from odoo import models, fields, api

class HelpdeskCategoryI(models.Model):
    _name = 'helpdesk_category_i'
    _description = 'Helpdesk Category I'

    name = fields.Char(string="Category I")


class HelpdeskCategoryII(models.Model):
    _name = 'helpdesk_category_ii'
    _description = 'Helpdesk Category II'

    name = fields.Char(string="Name")
    parent_id = fields.Many2one('helpdesk_category_i',string="Parent")
    