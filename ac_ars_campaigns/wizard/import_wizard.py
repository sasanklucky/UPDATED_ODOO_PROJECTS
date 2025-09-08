import base64
import io
import csv
import openpyxl
from odoo import models, fields, api
from odoo.exceptions import UserError

class ImportButtonWizard(models.TransientModel):
    _name = 'import.button.wizard'

    campaigns_vin_id = fields.Many2one('vehicle.campaigns', string="Vehicle Campaign", required=True)
    file = fields.Binary(string='CSV or Excel File', required=True)
    filename = fields.Char(string='Filename')

    @api.multi
    def import_lines(self):
        self.ensure_one()

        if not self.filename:
            raise UserError("Please upload a file.")

        file_ext = self.filename.split('.')[-1].lower()
        decoded_file = base64.b64decode(self.file)

        if file_ext == 'csv':
            return self._import_from_csv(decoded_file)
        elif file_ext == 'xlsx':
            return self._import_from_excel(decoded_file)
        else:
            raise UserError("Unsupported file format. Please upload a .csv or .xlsx file.")

    def _import_from_csv(self, decoded_file):
        data_file = io.StringIO(decoded_file.decode('utf-8'))
        csv_reader = csv.DictReader(data_file)

        for row in csv_reader:
            vin_number = row.get('vin_number')
            # cam_active = row.get('active_id')
            if vin_number:
                self.env['vehicle.campaign.vin'].create({
                    'campaign_id': self.campaigns_vin_id.id,
                    'vin_number': vin_number,
                    # 'cam_active':cam_active
                })
        return {'type': 'ir.actions.act_window_close'}

    def _import_from_excel(self, decoded_file):
        file_stream = io.BytesIO(decoded_file)
        workbook = openpyxl.load_workbook(file_stream)
        sheet = workbook.active

        # Assumes header is in row 1 and 'vin_number' is in the first column
        for idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
            vin_number = row[0].value
            state = row[1].value
            if vin_number:
                self.env['vehicle.campaign.vin'].create({
                    'campaign_id': self.campaigns_vin_id.id,
                    'vin_number': vin_number,
                    'state': state
                })
        return {'type': 'ir.actions.act_window_close'}
