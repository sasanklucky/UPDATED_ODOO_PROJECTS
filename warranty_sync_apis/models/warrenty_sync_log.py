from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from datetime import datetime

class WarrentySyncLog(models.Model):
    _name = "warrenty_sync_log"
    _description = "Warrenty Sync Log"
    _rec_name = 'warrenty_sequence'
    _order = 'id desc'

    warrenty_record = fields.Many2one('ars.sale.warranty')
    warrenty_sequence = fields.Char()
    payload = fields.Char()
    status = fields.Char()
    sync_message = fields.Char()