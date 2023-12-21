from odoo import api, fields, models


class ShellLocation(models.Model):
    _name = "shell.location"
    _description = "Shelf Location"
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _rec_name = 'name'
    _order = 'parent_left'

    name = fields.Char('Name', index=True, translate=True, track_visibility='always')
    code = fields.Char('Code')
    parent_id = fields.Many2one('shell.location', 'Parent Shelf Location', index=True, ondelete='cascade')
    child_id = fields.One2many('shell.location', 'parent_id', 'Child Shelf Location')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)


class ProductTemplateShellLocation(models.Model):
    _inherit = 'product.template'

    shell_location = fields.Many2many('shell.location', string="Shelf Location", track_visibility='always')

    def create(self, values):
        record = super(ProductTemplateShellLocation, self).create(values)
        record._log_changes_in_chatter()
        return record

    def write(self, values):
        result = super(ProductTemplateShellLocation, self).write(values)
        self._log_changes_in_chatter()
        return result

    def _log_changes_in_chatter(self):
        user = self.env.user.sudo()
        print('user', user)
        for record in self:
            record.message_post(body="Shell Locations updated: {}".format(record.shell_location.mapped('name')),
                                author_id=user.partner_id.id)
