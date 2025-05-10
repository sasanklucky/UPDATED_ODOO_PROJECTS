import json
import re
from odoo import models, fields, api, _
from datetime import datetime, time, date
from datetime import timedelta
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from openerp.exceptions import UserError, ValidationError



class ARSGST(models.Model):
    _inherit = 'res.partner'

    vat = fields.Char(string='GSTIN', help="GSTIN Number")


    @api.constrains('vat', 'state_id')
    def _check_gstin_format(self):
        for record in self:
            if record.vat:
                gstin = record.vat
                # print('GSTIN:', gstin)

                if len(gstin) != 15:
                    raise ValidationError("GSTIN must be exactly 15 characters long.")

                if not gstin[:2].isdigit():
                    raise ValidationError("GSTIN must start with a valid numeric state code.")

                state_code = gstin[:2]
                # print('State Code from GSTIN:', state_code)

                if record.state_id:
                    if record.state_id.code != state_code:
                        raise ValidationError(
                            f"GSTIN's state code ({state_code}) does not match the selected state code ({record.state_id.code})."
                        )
                    # print('Valid GSTIN for selected state:', record.state_id.code)
                else:
                    state = self.env['res.country.state'].search([('code', '=', state_code)], limit=1)
                    if not state:
                        raise ValidationError(
                            f"Invalid GSTIN: The first two digits ({state_code}) do not match any state code."
                        )
                    # print('Valid GSTIN without state_id:', state.code)

                gstin_pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z0-9]{2}Z[A-Z0-9]$'
                if not re.match(gstin_pattern, gstin):
                    raise ValidationError("Invalid GSTIN format.\r\n.GSTIN must be in the format nnAAAAAnnnnA_Z_ where n=number, A=alphabet, _=either.")
                print('Valid GSTIN format!')

