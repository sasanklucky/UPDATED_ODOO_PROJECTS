from odoo import api, fields, models, _
from odoo.exceptions import AccessError
from lxml import etree
from openerp.osv.orm import setup_modifiers


class InvoiceLines(models.Model):
    _inherit = "account.invoice.line"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        template_result = super(InvoiceLines, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        doc = etree.XML(template_result['arch'])
        print('Account.ovoice')
        print(self.env.context)
        fields = self.env['account.invoice.line'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        if view_type == 'form':
            # Restrict specific fields
            restricted_fields = []
            for field_name in fields.keys():
                if field_name not in restricted_fields:
                    for node in doc.xpath(f"//field[@name='{field_name}']"):
                        # Apply options
                        node.set('options', "{'no_open': True, 'no_create':True}")
                        # Apply attributes
                        # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                        # Setup modifiers
                        setup_modifiers(node, template_result['fields'][field_name])
        template_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return template_result

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        template_result = super(StockMove, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        doc = etree.XML(template_result['arch'])
        print('stocj.ovoice')
        print(self.env.context)
        fields = self.env['stock.move'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        if view_type == 'form':
            # Restrict specific fields
            restricted_fields = []
            for field_name in fields.keys():
                if field_name not in restricted_fields:
                    for node in doc.xpath(f"//field[@name='{field_name}']"):
                        # Apply options
                        node.set('options', "{'no_open': True, 'no_create':True}")
                        # Apply attributes
                        # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                        # Setup modifiers
                        setup_modifiers(node, template_result['fields'][field_name])
        template_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return template_result

class StockInventoryLines(models.Model):
    _inherit = "stock.inventory.line"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        template_result = super(StockInventoryLines, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        doc = etree.XML(template_result['arch'])
        print('stocj.ovoice')
        print(self.env.context)
        fields = self.env['stock.inventory.line'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        if view_type == 'form':
            # Restrict specific fields
            restricted_fields = []
            for field_name in fields.keys():
                if field_name not in restricted_fields:
                    for node in doc.xpath(f"//field[@name='{field_name}']"):
                        # Apply options
                        node.set('options', "{'%s': True}" % default_options[field_name])
                        # Apply attributes
                        # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                        # Setup modifiers
                        setup_modifiers(node, template_result['fields'][field_name])
        template_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return template_result

class StockMoveLines(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        template_result = super(StockMoveLines, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        doc = etree.XML(template_result['arch'])
        print('stocj.ovoice11')
        print(self.env.context)
        fields = self.env['stock.move.line'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        if view_type == 'form':
            # Restrict specific fields
            restricted_fields = []
            for field_name in fields.keys():
                if field_name not in restricted_fields:
                    for node in doc.xpath(f"//field[@name='{field_name}']"):
                        # Apply options
                        node.set('options', "{'%s': True}" % default_options[field_name])
                        # Apply attributes
                        # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                        # Setup modifiers
                        setup_modifiers(node, template_result['fields'][field_name])
        template_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return template_result