from odoo import models, fields, tools, api, _


class stock_ageing_report(models.Model):
    _name = 'stock_ageing_report'
    _description = 'Stock Ageing Report'
    _auto = False

    def get_stock_count(self):
        for record in self:
            record.compute_days_90 = 0 if record.days_90 < 0 else record.days_90
            a = record.days_90 if record.days_90 < 0 else 0
            record.days_90_value = record.template_id.standard_price * record.compute_days_90

            record.compute_days_180 = 0 if record.days_180 + a < 0 else record.days_180 + a
            b = record.days_180 + a if record.days_180 + a < 0 else 0
            record.days_180_value = record.template_id.standard_price * record.compute_days_180

            record.compute_days_365 = 0 if record.days_365 + b < 0 else record.days_180 + b
            c = record.days_365 + b if record.days_365 + b < 0 else 0
            record.days_365_value = record.template_id.standard_price * record.compute_days_365

            record.compute_days_730 = 0 if record.days_730 + c < 0 else record.days_730 + c
            d = record.days_730 + c if record.days_730 + c < 0 else 0
            record.days_730_value = record.template_id.standard_price * record.compute_days_730

            record.compute_greater_730 = 0 if record.greater_730 + d < 0 else record.greater_730 + d
            record.greater_730_value = record.template_id.standard_price * record.compute_greater_730

    def get_parts_desc(self):
        for record in self:
            record.parts_category = 'Spares'

    def get_stock_value(self):
        for record in self:
            record.stock_value = record.template_id.standard_price * record.quantity

    template_id = fields.Many2one('product.template', 'Part Desc')
    default_code = fields.Char('Part Number')
    name = fields.Char('Part Desc')
    parts_category = fields.Char(compute="get_parts_desc", string='Part Category Desc')
    product_id = fields.Many2one('product.product', 'Product')
    location_id = fields.Many2one('stock.location', 'Bin Location')
    company_id = fields.Many2one('res.company', related='location_id.company_id')
    quantity = fields.Integer('Stock Quantity')
    stock_value = fields.Float(compute="get_stock_value", string='Stock Value')
    computed_quantity = fields.Integer('Computed Quantity')
    mrp_price = fields.Float(related="template_id.standard_price", string='MRP')
    list_price = fields.Float('Selling Price')
    days_90 = fields.Integer('< 90 days Stock Qty')
    days_180 = fields.Integer('91-180 days Stock Qty')
    days_365 = fields.Integer('181-365 days Stock Qty')
    days_730 = fields.Integer('366-730 days Stock Qty')
    greater_730 = fields.Integer('>730 days Stock')
    days_90_value = fields.Float(compute="get_stock_count", string='< 90 days Stock Value')
    days_180_value = fields.Float(compute="get_stock_count", string='91-180 days Stock Value')
    days_365_value = fields.Float(compute="get_stock_count", string='181-365 days Stock Value')
    days_730_value = fields.Float(compute="get_stock_count", string='366-730 days Stock Value')
    greater_730_value = fields.Float(compute="get_stock_count", string='>730 days Stock Value')

    compute_days_90 = fields.Integer(compute="get_stock_count", string='< 90 days Stock Qty')
    compute_days_180 = fields.Integer(compute="get_stock_count", string='91-180 days Stock Qty')
    compute_days_365 = fields.Integer(compute="get_stock_count", string='181-365 days Stock Qty')
    compute_days_730 = fields.Integer(compute="get_stock_count", string='366-730 days Stock Qty')
    compute_greater_730 = fields.Integer(compute="get_stock_count", string='>730 days Stock')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        print("table name", self._table);
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
            select row_number() over() as id,t.id as template_id,t.default_code,t.name,
    s.product_id,s.location_id,s.quantity,t.list_price,
    ((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null)
    - COALESCE( (select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null), 0 )) as computed_quantity,
    (COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE < 91 ),0)
    - COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE < 91 ),0)) as days_90,
    (COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 90 and (SELECT CURRENT_DATE) - date::DATE < 181),0)
    - COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 90 and (SELECT CURRENT_DATE) - date::DATE < 181),0)) as days_180,
    (COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 180 and (SELECT CURRENT_DATE) - date::DATE < 366),0)
    - COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 180 and (SELECT CURRENT_DATE) - date::DATE < 366),0)) as days_365,
    (COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 365 and (SELECT CURRENT_DATE) - date::DATE < 731),0)
    - COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 365 and (SELECT CURRENT_DATE) - date::DATE < 731),0)) as days_730,
    (COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 730),0)
    - COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 730),0)) as greater_730
    from stock_quant s join stock_location l
    on s.location_id = l.id join product_product p on p.id = s.product_id
    join product_template t on t.id = p.product_tmpl_id
    where l.usage = 'internal' and t.categ_id = (select id from product_category where name = 'Parts') 
    order by product_id asc     

        )""" % (self._table))
