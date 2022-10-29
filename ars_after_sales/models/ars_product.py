# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class WmsProduct(models.Model):
    _inherit = "product.template"

    standard_time = fields.Float(help='Standard time for service product in minuets')
    prod_cat = fields.Many2one('product.category')
    category_code_desc = fields.Char(related='prod_cat.category_code', readonly=True)



class WmsProductCategory(models.Model):
    _inherit = "product.category"

    product_id = fields.Many2one('product.template')
    category_code = fields.Char()

class ARS_stock_quant(models.Model):
    _inherit = "stock.quant"

    category_id = fields.Many2one('product.category',string="Product Category")

    @api.model
    def create(self, vals):
        cr = self._cr
        if 'product_id' in vals:
            print(">>>>>",vals['product_id'])
            cr.execute("""select categ_id from product_template pt
            inner join product_product pp on pt.id =  pp.product_tmpl_id
            where pp.id = """+str(vals.get('product_id')))

            categ_id = [x[0] for x in cr.fetchall()]
            vals.update({"category_id" : categ_id and categ_id[0] or False})
        return super(ARS_stock_quant, self).create(vals)

    def action_update(self):
        quant_obj = self.env['stock.quant']
        quant_ids = quant_obj.search([])
        for case in quant_ids:
            if not case.category_id:
                case.category_id = case.product_id.categ_id