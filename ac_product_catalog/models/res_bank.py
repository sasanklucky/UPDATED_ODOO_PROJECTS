from odoo import fields,models, api


class ResBank(models.Model):
    _inherit = 'res.bank'

    beneficiary_name = fields.Char('Beneficiary Name')
    account_number = fields.Char('Account Number')
    ifsc_code = fields.Char('IFSC Code')
    branch_code = fields.Char('Branch Code')
    bank_code = fields.Char('Bank Code')


class ResCompany(models.Model):
    _inherit = 'res.company'

    bank_account_id = fields.Many2one('res.bank')




#  transaction happens partner address on readonly
class ARSResPartner(models.Model):
    _inherit = 'res.partner'

    can_edit_address = fields.Boolean(compute="_compute_can_edit_address")
    can_edit_address_child = fields.Boolean(string="Address Child", compute="_compute_can_edit_address_child")

    @api.depends(
         "meeting_ids", "sale_order_ids", "invoice_ids",
        # "vehicle_count", "estimate_count", "so_count", "purchase_order_count", "sale_order_count"
    )
    def _compute_can_edit_address(self):
        for partner in self:
            partner.can_edit_address = any([
                # partner.opportunity_ids,
                partner.meeting_ids,
                partner.sale_order_ids,
                partner.invoice_ids,
                # partner.vehicle_count > 0,
                # partner.estimate_count > 0,
                # partner.so_count > 0,
                # partner.purchase_order_count > 0,
                # partner.sale_order_count > 0
            ])


    @api.depends("parent_id", "parent_id.can_edit_address")
    def _compute_can_edit_address_child(self):
        for partner in self:
            partner.can_edit_address_child = partner.parent_id and partner.parent_id.can_edit_address

    def write(self, vals):
        result = super(ARSResPartner, self).write(vals)
        tracked_fields = {
            "meeting_ids", "sale_order_ids",  "invoice_ids"
        }
        if any(field in vals for field in tracked_fields):
            self._compute_can_edit_address()
        return result



#
# class ARSResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     can_edit_address = fields.Boolean(compute="_compute_can_edit_address", store=True)
#     can_edit_address_child = fields.Boolean('Address Child')
#
    # @api.depends(
    #     "opportunity_ids", "meeting_ids", "sale_order_ids", "task_ids", "invoice_ids",
    #     # "vehicle_count", "estimate_count", "so_count", "purchase_order_count", "sale_order_count"
    # )
    # def _compute_can_edit_address(self):
    #     for partner in self:
    #         partner.can_edit_address = any([
    #             partner.opportunity_ids,
    #             partner.meeting_ids,
    #             partner.sale_order_ids,
    #             partner.task_ids,
    #             partner.invoice_ids,
    #             # partner.vehicle_count > 0,
    #             # partner.estimate_count > 0,
    #             # partner.so_count > 0,
    #             # partner.purchase_order_count > 0,
    #             # partner.sale_order_count > 0
    #         ])

#     def write(self, vals):
#         result = super(ARSResPartner, self).write(vals)
#         tracked_fields = {
#             "opportunity_ids", "meeting_ids", "sale_order_ids", "task_ids", "invoice_ids",
#             # "vehicle_count", "estimate_count", "so_count", "purchase_order_count", "sale_order_count"
#         }
#         if any(field in vals for field in tracked_fields):
#             self._compute_can_edit_address()
#         return result
#
