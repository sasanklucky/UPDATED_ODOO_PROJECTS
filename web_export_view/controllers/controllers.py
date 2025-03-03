# Copyright 2016 Henry Zhou (http://www.maxodoo.com)
# Copyright 2016 Rodney (http://clearcorp.cr/)
# Copyright 2012 Agile Business Group
# Copyright 2012 Therp BV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import odoo.http as http
from openerp.exceptions import UserError, ValidationError
from odoo import  _
from odoo.http import request, Response
from odoo.addons.web.controllers.main import ExcelExport


class ExcelExportView(ExcelExport):
    def __getattribute__(self, name):
        if name == 'fmt':
            raise AttributeError()
        return super(ExcelExportView, self).__getattribute__(name)

    @http.route('/web/export/xls_view', type='http', auth='user')
    def export_xls_view(self, data, token):
        data = json.loads(data)
        model = data.get('model', [])
        columns_headers = data.get('headers', [])
        rows = data.get('rows', [])

        return request.make_response(
            self.from_data(columns_headers, rows),
            headers=[
                ('Content-Disposition', 'attachment; filename="%s"'
                 % self.filename(model)),
                ('Content-Type', self.content_type)
            ],
            cookies={'fileToken': token}
        )


    @http.route('/web/export/get_allowed_models', type='json', auth='user')
    def get_allowed_models(self):
        # Fetch the latest configuration settings
        config_group_records = request.env['res.config.settings'].sudo().search([], order='create_date desc',
                                                                                limit=1)

        # Get restricted models
        mode_restrict = [group.model.strip() for groups in config_group_records for group in
                         groups.xlsx_model_restrict
                         if group.model]

        return mode_restrict