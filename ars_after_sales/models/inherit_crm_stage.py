from odoo import models, fields, api
from odoo.exceptions import ValidationError


# class ARS_crm_lead(models.Model):
#     _inherit = "crm.lead"
#
#     sales_channel = fields.Selection([('after_sales', 'After Sales'), ('sales', 'Sales')], string="Sales Channel")

class ARS_Stage(models.Model):
    _inherit = "crm.stage"
    _description = "Stage of case"
    # _rec_name = 'name'
    # _order = "sequence, name, id"

    category_stage = fields.Selection([('after_sales', 'After Sales'), ('sales', 'Sales')], string="Category Stage")

    @api.model
    def create(self,vals):
        if self.env.user.has_group("base.group_system"):
            pass
        else:
            raise ValidationError('You cannot Create Stages')
        return super(ARS_Stage,self).create(vals)
