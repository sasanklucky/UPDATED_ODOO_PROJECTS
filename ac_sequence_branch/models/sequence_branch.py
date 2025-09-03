from odoo import models, fields, api, _



class BranchSeq(models.Model):

    _inherit = 'ir.sequence'


    branch = fields.Many2one('branch.master.company')



