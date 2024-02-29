# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ARSTestDrive(models.Model):
    _name = 'ars.test.drive'

    user_id = fields.Many2one('res.users', 'Test Drive Given By')
    test_drive_date = fields.Date("Test Drive Date")
    test_drive_remark = fields.Text('Test Drive Remark')
    opportunity_id = fields.Many2one('crm.lead')

    @api.model
    def create(self, values):
        context = self.env.context
        res_id = super(ARSTestDrive, self).create(values)
        if 'default_opportunity_id' in context:
            opportunity = self.env['crm.lead'].search([('id', '=', context['default_opportunity_id'])])
            if opportunity:
                opportunity.write({'is_test_drive': True})
        return res_id



