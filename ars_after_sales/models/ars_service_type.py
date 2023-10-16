from odoo import models, fields, api, _
from datetime import datetime
import logging
import json

_logger = logging.getLogger(__name__)


class ARSServiceType(models.Model):
    _name = 'service.type'

    name = fields.Char('Sale Type')


class ARSServiceOptions(models.Model):
    _name = 'service.options'

    name = fields.Char('Service Options')
    service_type = fields.Many2one('service.type', 'Service Type')
    warranty_ir_seq = fields.Many2one('ir.sequence',
                                      string='Sequence',company_dependent=True,
                                      domain=lambda self: [('company_id', '=', self.env.user.company_id.id)])
