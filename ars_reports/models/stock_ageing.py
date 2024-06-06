from odoo import models, fields, tools, api, _


class stock_ageing_report(models.Model):
    _name = 'stock.ageing.report'
    _description = 'Stock Ageing Report'
    _auto = False

    # def get_stock_count(self):
    #     for record in self:
    #         record.compute_days_90 = 0 if record.days_90 < 0 else record.days_90
    #         a = record.days_90 if record.days_90 < 0 else 0
    #         record.days_90_value = record.template_id.standard_price * record.compute_days_90
    #
    #         record.compute_days_180 = 0 if record.days_180 + a < 0 else record.days_180 + a
    #         b = record.days_180 + a if record.days_180 + a < 0 else 0
    #         record.days_180_value = record.template_id.standard_price * record.compute_days_180
    #
    #         record.compute_days_365 = 0 if record.days_365 + b < 0 else record.days_180 + b
    #         c = record.days_365 + b if record.days_365 + b < 0 else 0
    #         record.days_365_value = record.template_id.standard_price * record.compute_days_365
    #
    #         record.compute_days_730 = 0 if record.days_730 + c < 0 else record.days_730 + c
    #         d = record.days_730 + c if record.days_730 + c < 0 else 0
    #         record.days_730_value = record.template_id.standard_price * record.compute_days_730
    #
    #         record.compute_greater_730 = 0 if record.greater_730 + d < 0 else record.greater_730 + d
    #         record.greater_730_value = record.template_id.standard_price * record.compute_greater_730

    # def get_parts_desc(self):
    #     for record in self:
    #         record.parts_category = 'Spares'

    def get_stock_value(self):
        for record in self:
            record.stock_value = record.template_id.standard_price * record.quantity
            record.days_90_stock_val = record.template_id.standard_price * record.days_90_stock_bal
            record.days_180_stock_val = record.template_id.standard_price * record.days_180_stock_bal
            record.days_365_stock_val = record.template_id.standard_price * record.days_365_stock_bal
            record.days_730_stock_val = record.template_id.standard_price * record.days_730_stock_bal
            record.greater_730_stock_val = record.template_id.standard_price * record.greater_730_stock_bal

    template_id = fields.Many2one('product.template', 'Part Desc')
    default_code = fields.Char('Part Number')
    name = fields.Char('Part Desc')
    parts_category = fields.Char(string='Part Category Desc')
    product_id = fields.Many2one('product.product', 'Product')
    location_id = fields.Many2one('stock.location', 'Bin Location')
    company_id = fields.Many2one('res.company', related='location_id.company_id')
    quantity = fields.Integer('Stock Quantity')
    stock_value = fields.Float(compute="get_stock_value", string='Stock Value')
    computed_quantity = fields.Integer('Computed Quantity')
    mrp_price = fields.Float(related="template_id.standard_price", string='MRP')
    list_price = fields.Float('Selling Price')

    greater_730_stock_bal = fields.Integer(string='>730 days Stock')
    greater_730_stock_val = fields.Float(compute="get_stock_value", string='>730 days Stock Value')
    days_730_stock_bal = fields.Integer(string='366-730 days Stock Qty')
    days_730_stock_val = fields.Float(compute="get_stock_value", string='366-730 days Stock Qty Value')
    days_365_stock_bal = fields.Integer(string='181-365 days Stock Qty')
    days_365_stock_val = fields.Float(compute="get_stock_value", string='181-365 days Stock Qty Value')
    days_180_stock_bal = fields.Integer(string='91-180 days Stock Qty')
    days_180_stock_val = fields.Float(compute="get_stock_value", string='91-180 days Stock Qty Value')
    days_90_stock_bal = fields.Integer(string='< 90 days Stock Qty')
    days_90_stock_val = fields.Float(compute="get_stock_value", string='< 90 days Stock Qty Value')



    # days_90 = fields.Integer('< 90 days Stock Qty')
    # days_180 = fields.Integer('91-180 days Stock Qty')
    # days_365 = fields.Integer('181-365 days Stock Qty')
    # days_730 = fields.Integer('366-730 days Stock Qty')
    # greater_730 = fields.Integer('>730 days Stock')
    # days_90_value = fields.Float(compute="get_stock_count", string='< 90 days Stock Value')
    # days_180_value = fields.Float(compute="get_stock_count", string='91-180 days Stock Value')
    # days_365_value = fields.Float(compute="get_stock_count", string='181-365 days Stock Value')
    # days_730_value = fields.Float(compute="get_stock_count", string='366-730 days Stock Value')
    # greater_730_value = fields.Float(compute="get_stock_count", string='>730 days Stock Value')
    #
    # compute_days_90 = fields.Integer(compute="get_stock_count", string='< 90 days Stock Qty')
    # compute_days_180 = fields.Integer(compute="get_stock_count", string='91-180 days Stock Qty')
    # compute_days_365 = fields.Integer(compute="get_stock_count", string='181-365 days Stock Qty')
    # compute_days_730 = fields.Integer(compute="get_stock_count", string='366-730 days Stock Qty')
    # compute_greater_730 = fields.Integer(compute="get_stock_count", string='>730 days Stock')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        print('hello')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        print("table name", self._table);
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as (
                WITH initial_values AS (
                SELECT 
                row_number() over() as id,t.id as template_id,t.default_code as default_code,t.name as name,
                s.product_id as product_id,s.location_id as location_id,s.quantity as quantity,t.list_price as list_price,
                'Spares' as parts_category,
                --prop.value_float as cost,
                --s.quantity * prop.value_float  as stock_value,
                COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 730),0) as greater_730_incoming,
                COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 730),0) as greater_730_outgoing,
                COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 365 and (SELECT CURRENT_DATE) - date::DATE < 731),0) as days_730_incoming,
                COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 365 and (SELECT CURRENT_DATE) - date::DATE < 731),0) as days_730_outgoing,
                COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 180 and (SELECT CURRENT_DATE) - date::DATE < 366),0) as days_365_incoming,
                COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 180 and (SELECT CURRENT_DATE) - date::DATE < 366),0) as days_365_outgoing,
                COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 90 and (SELECT CURRENT_DATE) - date::DATE < 181),0) as days_180_incoming,
                COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE > 90 and (SELECT CURRENT_DATE) - date::DATE < 181),0) as days_180_outgoing,
                COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE < 91 ),0) as days_90_incoming,
                COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null and (SELECT CURRENT_DATE) - date::DATE < 91 ),0) as days_90_outgoing,
                COALESCE((select sum(qty_done) from stock_move_line where location_dest_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null), 0) as total_incoming,
                COALESCE((select sum(qty_done) from stock_move_line where location_id = s.location_id and product_id = s.product_id and state='done' and move_id is not null), 0) as total_outgoing
                    
                from stock_quant s join stock_location l
                on s.location_id = l.id 
                join product_product p on p.id = s.product_id
                --JOIN ir_property prop on prop.res_id = 'product.product,' || p.id
                join product_template t on t.id = p.product_tmpl_id
                join product_catalog pc on t.catalog_type = pc.id
                where l.usage = 'internal' and pc.name = 'Parts' and t.active = True
                order by product_id asc),
            
            stage1_calculations AS (
                SELECT
                *,
                case
                    when total_outgoing > greater_730_incoming then 0
                    else greater_730_incoming - total_outgoing
                end as greater_730_stock_bal,
                case when total_outgoing - greater_730_incoming > 0 then total_outgoing - greater_730_incoming else 0 end as total_outgoing2,
                case when total_outgoing - greater_730_incoming - days_730_incoming > 0 then total_outgoing - greater_730_incoming - days_730_incoming else 0 end as total_outgoing3,
                case when total_outgoing - greater_730_incoming - days_730_incoming - days_365_incoming > 0 then total_outgoing - greater_730_incoming - days_730_incoming - days_365_incoming else 0 end as total_outgoing4,
                case when total_outgoing - greater_730_incoming - days_730_incoming - days_365_incoming - days_180_incoming > 0 then total_outgoing - greater_730_incoming - days_730_incoming - days_365_incoming - days_180_incoming else 0 end as total_outgoing5,
                case when total_outgoing - greater_730_incoming - days_730_incoming - days_365_incoming - days_180_incoming - days_90_incoming > 0 then total_outgoing - greater_730_incoming - days_730_incoming - days_365_incoming - days_180_incoming - days_90_incoming else 0 end as total_outgoing6			
                FROM initial_values
            ),
            stage2_calculations AS (
                SELECT
                *,
                case
                    when days_730_incoming - total_outgoing2 < 0 then 0
                    else days_730_incoming - total_outgoing2
                end as days_730_stock_bal,
                case
                    when days_365_incoming - total_outgoing3 < 0 then 0
                    else days_365_incoming - total_outgoing3
                end as days_365_stock_bal,
                case
                    when days_180_incoming - total_outgoing4 < 0 then 0
                    else days_180_incoming - total_outgoing4
                end as days_180_stock_bal,
                case
                    when days_90_incoming - total_outgoing5 < 0 then 0
                    else days_90_incoming - total_outgoing5
                end as days_90_stock_bal
                FROM stage1_calculations
            )   
            
            select row_number() over() as id,template_id,default_code,product_id,location_id,quantity,
            name,list_price,parts_category,greater_730_incoming,greater_730_outgoing,days_730_incoming,
            days_730_outgoing,days_365_incoming,days_365_outgoing,days_180_incoming,
            days_180_outgoing,days_90_incoming,days_90_outgoing,total_incoming,total_outgoing,greater_730_stock_bal,
            days_730_stock_bal,days_365_stock_bal,days_180_stock_bal,days_90_stock_bal
            --greater_730_incoming,greater_730_outgoing,days_730_incoming,days_730_outgoing,days_365_incoming,days_365_outgoing,days_180_incoming,days_180_outgoing,days_90_incoming,days_90_outgoing,total_incoming,total_outgoing,         
            --greater_730_stock_bal,
            --days_730_stock_bal,
            --days_365_stock_bal,
            --days_180_stock_bal,
            --days_90_stock_bal,
            from stage2_calculations
    -- 			join stage1_calculations on initial_values.id = stage1_calculations.id
    -- 			join stage2_calculations on stage2_calculations.id = stage1_calculations.id
        )""" % (self._table))
