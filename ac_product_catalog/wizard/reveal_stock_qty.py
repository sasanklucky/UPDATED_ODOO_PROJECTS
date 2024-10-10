from odoo import models, fields, api, _,registry, SUPERUSER_ID, sql_db
from odoo.exceptions import ValidationError, UserError, RedirectWarning, except_orm
import contextlib

class PurchaseRevealStockQty(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def stock_reveal_wizard(self):
        if not self.order_line:
            raise ValidationError(_("Please Select at least one Line Item"))

        purchase_lines = self._prepare_purchase_lines()
        ims_reveal_stock_qty = self._get_ims_reveal_stock_qty(purchase_lines)
        update_in_wiz = self._prepare_update_in_wizard(ims_reveal_stock_qty)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Reveal From IMS',
            'res_model': 'ims.stock.reveal.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('ac_product_catalog.view_qty_reveal_from_ims_wizard').id,
            'target': 'new',
            'context': {
                'default_confirmation_message': 'Are you sure you want to confirm this purchase order?',
                'default_purchase_order_line_ids': update_in_wiz,
                'purchase_order_id': self.id,
            },
        }

    def _prepare_purchase_lines(self):
        """Prepare the purchase lines for processing."""
        return [{
            'product_id': line.product_id.id,
            'quantity': line.qty_available_line,
            'default_code': line.product_id.default_code,
        } for line in self.order_line]

    def _get_ims_reveal_stock_qty(self, purchase_lines):
        """Retrieve stock quantities from the IMS."""
        param = self.env['ir.config_parameter'].sudo()
        child_company_type = param.get_param('purchase_order_sync_apis.po_company_type')
        enable_po_sync = param.get_param('purchase_order_sync_apis.enable_po_sync')

        if child_company_type == 'is_child_company' and enable_po_sync == 'yes':
            database = param.get_param('purchase_order_sync_apis.parent_db_name')
            return self._fetch_stock_quantities_from_database(database, purchase_lines)

        # Return purchase_lines without modification if conditions are not met
        return purchase_lines

    def _fetch_stock_quantities_from_database(self, database, purchase_lines):
        """Fetch stock quantities from the specified database."""
        try:
            db = sql_db.db_connect(database)
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                ims_product_env = env['product.product'].sudo()

                # Create a mapping of default codes to their respective stock quantities
                stock_quantities = {line['default_code']: line for line in purchase_lines}
                print(stock_quantities, "stock_quantities")
                products = ims_product_env.search([
                    ('default_code', 'in', list(stock_quantities.keys()))
                ])
                # Create a set to keep track of matched default codes
                matched_codes = set()

                for product in products:
                    line = stock_quantities.get(product.default_code)
                    if line:
                        line['ims_reveal_qty'] = [product.stock_reveal_quantity, product.a_reveal_stock]
                        matched_codes.add(product.default_code)

                missing_codes = [code for code in stock_quantities.keys() if code not in matched_codes]
                if missing_codes:
                    missing_codes_str = ', '.join(missing_codes)
                    raise ValidationError(
                        _("The following product default codes are missing in the IMS database: %s") % missing_codes_str)

                # Set ims_reveal_qty to 0 for any default codes that did not match
                for line in purchase_lines:
                    if 'ims_reveal_qty' not in line:
                        line['ims_reveal_qty'] = 0

                return purchase_lines
        except Exception as e:
            raise ValidationError(_("Error while fetching stock quantities: %s") % str(e))

    def _prepare_update_in_wizard(self, ims_reveal_stock_qty):
        """Prepare the data for the wizard update."""
        return [(0, 0, {
            'product_id': line_item['product_id'],
            'quantity': line_item['quantity'],
            'ims_reveal_qty': line_item['ims_reveal_qty'][0] if line_item['ims_reveal_qty'][1] else 0,
            'default_code': line_item['default_code']
        }) for line_item in ims_reveal_stock_qty]


class ImsStockRevealWizard(models.TransientModel):
    _name = 'ims.stock.reveal.wizard'
    _description = 'Displays the stock of IMS'

    confirmation_message = fields.Char(string="Message",
                                       default="Available Quantities in IMS")
    purchase_order_line_ids = fields.One2many(
        'ims.stock.reveal.wizard.line',
        'wizard_id',
        string="Purchase Order Lines"
    )
    product_category = fields.Many2one('product.catalog', string='Product Category')
    product_template_id = fields.Many2one('product.template', string='Model')
    product_id = fields.Many2many('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True)

    show_product_template = fields.Boolean(string="Show Product Template", default=False)

    @api.onchange('product_category')
    def onchange_product_based_on_catalog(self):
        """Show product template only for categories with variants (like Vehicle)"""
        if self.product_category:
            if self.product_category.name == 'Vehicle':  # Change 'Vehicle' to the actual catalog name
                self.show_product_template = True
                # Filter product templates based on selected product category
                product_templates = self.env['product.template'].sudo().search([
                    ('catalog_type', '=', self.product_category.id)
                ])
                return {'domain': {'product_template_id': [('id', 'in', product_templates.ids)]}}
            else:
                self.show_product_template = False
                # Directly filter products for non-variant categories
                products = self.env['product.product'].sudo().search([
                    ('catalog_type', '=', self.product_category.id)
                ])
                return {'domain': {'product_id': [('id', 'in', products.ids)]}}
        else:
            self.show_product_template = False
            return {'domain': {'product_template_id': [], 'product_id': []}}

    @api.onchange('product_template_id')
    def onchange_product_template_id(self):
        """Handle product variant filtering based on the selected product template"""
        self.product_id = [(5, 0, 0)]  # Clear the many2many field

        if self.product_template_id:
            # Get variants for the selected product template
            variant_ids = self.env['product.product'].sudo().search([
                ('product_tmpl_id', '=', self.product_template_id.id)
            ])

            if variant_ids:
                return {'domain': {'product_id': [('id', 'in', variant_ids.ids)]}}
            else:
                # If there are no variants, allow selecting all products from this template
                return {'domain': {'product_id': [('id', 'in', self.product_template_id.product_variant_ids.ids)]}}
        else:
            return {'domain': {'product_id': []}}


    @api.multi
    def fetch_data_from_other_db(self):
        if self.purchase_order_line_ids:
            self.purchase_order_line_ids.unlink()
        if self.product_id:
            # Fetch data from other database
            product_ids = self.product_id.ids
            purchase_lines = [{'product_id': prod.id, 'default_code': prod.default_code, 'qty_available_line': prod.qty_available} for prod in self.product_id]
            print(purchase_lines)

            # Use existing method to fetch stock quantities
            database = self.env['ir.config_parameter'].sudo().get_param('purchase_order_sync_apis.parent_db_name')
            ims_reveal_stock_qty = self._fetch_stock_quantities_from_database(database, purchase_lines)

            # Update the one2many field with the fetched data
            update_lines = []
            for line_item in ims_reveal_stock_qty:
                update_lines.append((0, 0, {
                    'product_id': line_item['product_id'],
                    'default_code': line_item['default_code'],
                    'quantity': line_item['qty_available_line'],
                    'ims_reveal_qty': line_item['ims_reveal_qty'][0] if line_item['ims_reveal_qty'][1] else 0,
                }))

            self.purchase_order_line_ids = update_lines
            return {
                "type": "ir.actions.do_nothing",
            }

    @api.multi
    def confirm_action(self):
        purchase_order_id = self.env.context.get('purchase_order_id')
        purchase_lines = self._get_purchase_lines(purchase_order_id)

        ims_reveal_stock_qty = self._updated_with_ims_reveal_stock_qty(purchase_lines)

        self._update_purchase_order_lines(purchase_order_id, ims_reveal_stock_qty)

        return {'type': 'ir.actions.act_window_close'}

    def _get_purchase_lines(self, purchase_order_id):
        """Retrieve purchase lines from the given purchase order ID."""
        return [{
            'product_id': line.product_id.id,
            'quantity': line.qty_available_line,
            'default_code': line.product_id.default_code,
        } for line in self.env['purchase.order'].browse(purchase_order_id).order_line]

    def _updated_with_ims_reveal_stock_qty(self, purchase_lines):
        """Retrieve stock quantities from the IMS."""
        try:
            param = self.env['ir.config_parameter'].sudo()
            child_company_type = param.get_param('purchase_order_sync_apis.po_company_type')
            enable_po_sync = param.get_param('purchase_order_sync_apis.enable_po_sync')

            if child_company_type == 'is_child_company' and enable_po_sync == 'yes':
                database = param.get_param('purchase_order_sync_apis.parent_db_name')
                return self._fetch_stock_quantities_from_database(database, purchase_lines)

            return purchase_lines  # Return purchase_lines without modification if conditions are not met
        except Exception as e:
            raise ValidationError(_("Error while updating IMS reveal stock quantities: %s") % str(e))

    def _fetch_stock_quantities_from_database(self, database, purchase_lines):
        """Fetch stock quantities from the specified database."""
        try:
            db = sql_db.db_connect(database)
            with contextlib.closing(db.cursor()) as cr:
                cr.autocommit(True)
                env = api.Environment(cr, SUPERUSER_ID, {})
                ims_product_env = env['product.product'].sudo()

                # Create a mapping of default codes to their respective stock quantities
                default_codes = [line['default_code'] for line in purchase_lines if line.get('default_code')]
                products = ims_product_env.search([('default_code', 'in', default_codes)])

                stock_mapping = {product.default_code: [product.stock_reveal_quantity, product.a_reveal_stock] for product in products}

                missing_codes = [line['default_code'] for line in purchase_lines if
                                 line['default_code'] not in stock_mapping]

                if missing_codes:
                    raise ValidationError(
                        _("The following product default codes are missing in the IMS database: %s") % ', '.join(
                            missing_codes)
                    )

                for line in purchase_lines:
                    line['ims_reveal_qty'] = stock_mapping.get(line['default_code'], 0)

                return purchase_lines
        except Exception as e:
            raise ValidationError(_("Error while fetching stock quantities: %s") % str(e))

    def _update_purchase_order_lines(self, purchase_order_id, ims_reveal_stock_qty):
        """Update purchase order lines with IMS revealed quantities."""
        for line_item in ims_reveal_stock_qty:
            product_id = line_item.get('product_id')
            if product_id:
                purchase_order_line = self.env['purchase.order.line'].search([
                    ('order_id', '=', purchase_order_id),
                    ('product_id', '=', product_id)
                ])
                if purchase_order_line:
                    purchase_order_line.write({
                        'ims_reveal_qty': line_item['ims_reveal_qty'][0] if line_item['ims_reveal_qty'][1] else 0
                    })
                else:
                    raise ValidationError(
                        _("Product with ID %s not found in the Purchase Order Lines.") % product_id
                    )
            else:
                print("No product ID found in this line.")


class ImsStockRevealWiZLines(models.TransientModel):
    _name = 'ims.stock.reveal.wizard.line'
    _description = 'IMS Stock Reveal Wizard Lines'

    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="DMS Stock")
    default_code = fields.Char(string="Internal Reference")
    ims_reveal_qty = fields.Float(string="IMS Stock")
    wizard_id = fields.Many2one('ims.stock.reveal.wizard', string="Wizard", required=True)

class Product(models.Model):
    _inherit = "product.product"

    stock_reveal_quantity = fields.Float('Reveal Stock to Dealer',  readonly=True, store=True)
    a_reveal_stock = fields.Boolean("Allow To Reveal Stock", related="product_tmpl_id.allow_to_reveal_stock",
                                    store=True)

class PurchaseOrderLineRevealQty(models.Model):
    _inherit = "purchase.order.line"

    ims_reveal_qty = fields.Float(string='IMS Reveal Qty')

class ProductTemplateRevealQty(models.Model):
    _inherit = "product.template"

    stock_reveal_quantity = fields.Float('Reveal Stock to Dealer',  readonly=True, store=True)
    allow_to_reveal_stock = fields.Boolean("Allow To Reveal Stock")
