from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from datetime import datetime

class PoSyncLog(models.Model):
    _name = "po_sync_log"
    _description = "Purchase Sync Log"
    _rec_name = 'purchase_sequence'
    _order = 'id desc'

    purchase_record = fields.Many2one('purchase.order')
    purchase_sequence = fields.Char()
    payload = fields.Char()
    status = fields.Char()
    sync_message = fields.Char()