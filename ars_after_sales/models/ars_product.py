# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class WmsProduct(models.Model):
    _inherit = "product.template"

    standard_time = fields.Float(help='Standard time for service product in minuets')
    prod_cat = fields.Many2one('product.category')
    category_code_desc = fields.Char(related='prod_cat.category_code', readonly=True)
    mrp = fields.Float(string='MRP')
    access_price_unit = fields.Boolean('Modify Unit Price')

    @api.multi
    def create_supplier_info(self):
        suppliers = self.env['res.partner'].search([('supplier', '=', True), ('add_as_seller', '=', True)])
        for record in self:
            seller = record.seller_ids.mapped('name')
            for supplier in suppliers:
                if supplier not in seller:
                    record.seller_ids.create({'name': supplier.id, 'product_tmpl_id': record.id,
                                              'price': record.standard_price
                                              })
            for seller_id in record.seller_ids:
                if seller_id.name not in suppliers:
                    seller_id.unlink()
                else:
                    seller_id.write({'price': record.standard_price})


class WmsProductCategory(models.Model):
    _inherit = "product.category"

    product_id = fields.Many2one('product.template')
    category_code = fields.Char()


class ARS_stock_quant(models.Model):
    _inherit = "stock.quant"

    category_id = fields.Many2one('product.category', string="Product Category")

    @api.model
    def create(self, vals):
        cr = self._cr
        if 'product_id' in vals:
            # print(">>>>>", vals['product_id'])
            cr.execute("""select categ_id from product_template pt
            inner join product_product pp on pt.id =  pp.product_tmpl_id
            where pp.id = """ + str(vals.get('product_id')))

            categ_id = [x[0] for x in cr.fetchall()]
            vals.update({"category_id": categ_id and categ_id[0] or False})
        return super(ARS_stock_quant, self).create(vals)


    def action_update(self):
        quant_obj = self.env['stock.quant']
        quant_ids = quant_obj.search([])
        for case in quant_ids:
            if not case.category_id:
                case.category_id = case.product_id.categ_id


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def action_invoice_sal_tree1(self):
        return {
            'name': 'After-Sales Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'domain': [
                ('type', '=', 'out_invoice'),
                ('team_id.team_type', '=', 'after_sales'),
                ('company_id', 'in', self.env.user.company_ids.ids),
            ],
            'context': {
                'type': 'out_invoice',
                'journal_type': 'sale',
                'default_ars_invoice_type': 'after_sales',
            },
            'views': [
                (self.env.ref('account.invoice_tree').id, 'tree'),
                (self.env.ref('ars_after_sales.invoice_form_inherit').id, 'form'),  # fixed
            ],
        }