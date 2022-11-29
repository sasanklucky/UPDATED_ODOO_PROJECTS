from odoo import models, fields, api,_
from datetime import datetime,timedelta

class ResourceCategory(models.Model):
    _name = "resource.category"
    _description = "Resource Detail"

    name = fields.Char()
    code = fields.Char()
    
class Resource_skill(models.Model):
    _name = "resource.skill"
    
    name = fields.Char()


class ARS_ResourceResource(models.Model):
    _inherit = "resource.resource"
    _description = "Resource Detail"

    resource_category = fields.Many2one('resource.category')
    resource_partner = fields.Many2one('res.partner')
    resource_skill = fields.Many2one('resource.skill')


    @api.model
    def create(self, values):
        partner = self.env['res.partner']
        res = super(ARS_ResourceResource, self).create(values)
        if res.resource_type == 'material':
            vals = {'name': values.get('name')}
            partner_id_resource = partner.create(vals)
            res.resource_partner = partner_id_resource
        return res


    @api.multi
    def unlink(self):
        self.resource_partner.unlink()
        return super(ARS_ResourceResource, self).unlink()

