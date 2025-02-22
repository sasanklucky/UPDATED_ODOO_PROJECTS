from lxml import etree
from ast import literal_eval
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm


class CRMMenuRestrict(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def write(self, vals):
        # for rec in self:
        userid = self.env.user
        booking_stage_id = userid.company_id.booking_stage_id
        param = self.env['ir.config_parameter'].sudo()
        restrict_crm = param.get_param('ars_after_sales.restrict_crm_lead')
        model_ids = userid.company_id.model_ids
        models = ','.join(str(v.name if v.name else 'None') for v in model_ids)
        if restrict_crm and userid.company_id.crm_restrict_till_date and self.booking_date:
            till_date = fields.Datetime.from_string(userid.company_id.crm_restrict_till_date).date()
            booking_date = fields.Datetime.from_string(self.booking_date).date()
            if restrict_crm and self.model_id.id in model_ids.ids and self.stage_id == booking_stage_id and till_date >= booking_date:
                if 'stage_id' in vals:
                    res = super(CRMMenuRestrict, self).write(vals)
                    return res
                else:
                    test_msg = {'message': 'You cannot edit the record in "Booked" state', 'title': 'Warning',
                                'sticky': True}
                    userid.notify_warning(**test_msg)
                    raise UserError(f"CRM pipeline modifications are only allowed before {till_date}. "
                                    f"Editing outside this period is restricted for the Model {models}. "
                                    f"Please contact the support team for assistance")
            elif 'model_id' in vals and vals['model_id'] in model_ids.ids:
                raise UserError(f"You cannot change the models {models} until the date {till_date}. "
                                f"Please contact the support team for assistance")
            else:
                res = super(CRMMenuRestrict, self).write(vals)
                return res
        elif restrict_crm and booking_stage_id and self.stage_id == booking_stage_id:
            raise UserError("Booked date is not selected or updated. Please contact the support team for assistance")
        else:
            res = super(CRMMenuRestrict, self).write(vals)
            return res
