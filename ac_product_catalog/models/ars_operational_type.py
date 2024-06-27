from odoo import models, fields, api, _
from odoo.tools import format_date


class ARSPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type(self):
        print(self.purchase_type)
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    purchase_type = fields.Selection([('general', 'General Purchase'), ('vehicle', 'Vehicle Purchase'),
                                      ('after_sales', 'After Sales')], string='Type')

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES, required=True,
                                      default=_default_picking_type,
                                      help="This will determine operation type of incoming shipment")

    @api.onchange('purchase_type')
    def _update_picking_type_based_on_purchase_type(self):
        global types
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        if self.purchase_type:
            if self.purchase_type == 'vehicle':
                types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id),
                                         ('warehouse_id.ars_type', '=', 'vehicle')])
            elif self.purchase_type == 'after_sales':
                types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id),
                                         ('warehouse_id.ars_type', '=', 'after_sales')])
            else:
                types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        self.picking_type_id = types[:1].id

    admin_access = fields.Boolean(compute="_check_if_admin")

    @api.multi
    @api.depends('order_line')
    def _check_if_admin(self):
        context = self.env.context
        user = context['uid'] if 'uid' in context else False
        user = self.env['res.users'].browse(user)
        for record in self:
            record.admin_access = False
            if user.has_group("base.group_system"):
                record.admin_access = True
            else:
                record.admin_access = False


class ARSPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(ARSPurchaseOrderLine, self)._prepare_stock_moves(picking)
        for re in res:
            re['product_template_id'] = self.product_template_id.id
            re['product_catalog_id'] = self.product_catalog_id.id
        return res


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    purchase_type = fields.Selection([('general', 'General Sales'), ('vehicle', 'Vehicle Sales'),
                                      ('after_sales', 'After Sales')], string='Type')


class ARSStockPicking(models.Model):
    _inherit = 'stock.picking'

    ars_type = fields.Selection([('general', 'General Sales'), ('vehicle', 'Vehicle Sales'),
                                 ('after_sales', 'After Sales')], string='Type')
