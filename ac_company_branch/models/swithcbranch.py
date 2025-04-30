from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(Http, self).session_info()
        user = request.env.user

        # Add branch data
        res.update({
            "user_branches": {
                "current_branch": (user.branch_id.id, user.branch_id.name) if user.branch_id else (None, ''),
                "allowed_branches": [(b.id, b.name) for b in user.allowed_branch_ids if b.company_id.id == user.company_id.id]
            }
        })
        return res
