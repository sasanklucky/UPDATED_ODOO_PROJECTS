from odoo import api, fields, models
from datetime import datetime

class InvoiceSyncLog(models.Model):
    _name = "invoice_sync_log"
    _description = "Invoice Sync Log"
    _rec_name = 'invoice_sequence'
    _order = 'id desc'

    invoice_record = fields.Many2one('account.invoice')
    invoice_sequence = fields.Char()
    payload = fields.Char()
    status = fields.Char()
    sync_message = fields.Char()