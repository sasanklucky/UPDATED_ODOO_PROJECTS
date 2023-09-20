from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import datetime, timedelta
from datetime import date

class ARSPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _compute_vehicle_count(self):
        for partner in self:
            # operator = 'child_of' if partner.is_company else '='  # the opportunity count should counts the opportunities of this company and all its contacts
            partner.vehicle_count = self.env['fleet.vehicle'].search_count([('driver_id', '=', partner.id)])

    vehicle_count = fields.Integer("Vehicle", compute='_compute_vehicle_count')
    pan_no = fields.Char("PAN No")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('transgender', 'Transgender')])
    dob = fields.Date('DOB')
    age = fields.Integer(compute='_compute_age_from_dob')
    add_as_seller = fields.Boolean('Add Seller')

    @api.multi
    @api.depends('dob')
    def _compute_age_from_dob(self):
        today = date.today()
        for record in self:
            if record.dob:
                dob = datetime.strptime(record.dob, '%Y-%m-%d')
                record.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


    @api.multi
    def crm_customer_vehicle(self):
        for partner in self:
            # operator = 'child_of' if partner.is_company else '='  # the opportunity count should counts the opportunities of this company and all its contacts
            vehicle_count = self.env['fleet.vehicle'].search([('driver_id', '=', partner.id)])
            form_view = self.env.ref('ars_vehicle_sales.ars_vehicle_view_form_inherit')
            list_view = self.env.ref('fleet.fleet_vehicle_view_tree')
            if len(vehicle_count) > 1:
                return {
                    'name': _('Vehicle'),
                    'res_model': 'fleet.vehicle',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'view_id': list_view.id,
                    'views': [(list_view.id, 'tree'), (form_view.id, 'form')],
                    'domain': [('id', 'in', vehicle_count.ids)],
                    'type': 'ir.actions.act_window',
                    'target': 'self'
                }
            else:
                return {
                    'name': _('Vehicle'),
                    'res_model': 'fleet.vehicle',
                    'res_id': vehicle_count.id,
                    'views': [(form_view.id, 'form'), ],
                    'context': {'default_driver_id': partner.id, 'create': False, 'edit': False},
                    'type': 'ir.actions.act_window',
                    'target': 'current'
                }
#     @api.one
#     @api.constrains('mobile')
#     def _check_duplicate_mobile(self):
#         res_details = self.env['res.partner'].search([('mobile', '=', self.mobile)])
#         if res_details:
#             raise ValidationError(_('Allready Mobile Number Exists.'))
#
