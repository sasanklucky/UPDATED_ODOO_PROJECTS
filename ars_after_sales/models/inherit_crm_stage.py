from odoo import models, fields, api

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

