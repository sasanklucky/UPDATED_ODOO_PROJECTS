from odoo import models, fields, api, tools, _


class WholesaleReport(models.Model):
    _name = 'wholesale.report'
    _description = 'Wholesale Report'
    _auto = False

    def get_color(self):
        for record in self:
            color = record.product_id.attribute_value_ids.filtered(
                lambda x: x.attribute_id.name == 'colour' or x.attribute_id.name == 'Ext. colour').ids
            if color:
                color_list = []
                for i in color:
                    attribute = self.env['product.attribute.value'].sudo().search([('id', '=', i)])
                    color_list.append(attribute.name)
                record.color = ', '.join(str(attribute) for attribute in color_list)

    sl_no = fields.Integer()
    dealer_code = fields.Char(string="Dealer Code")
    dealer_city = fields.Char(string="City", related="outlet.city")
    dealer_state = fields.Many2one('res.country.state', string="State", related="outlet.state_id")
    date_of_invoice = fields.Date(string="Date of Invoice")
    invoice_number = fields.Char(string="Invoice Number")
    vin_no = fields.Char(string="Vin No")
    model_group = fields.Char(string="Model Group")
    product_template_id = fields.Many2one('product.template', string="Model")
    product_id = fields.Many2one('product.product', string="Product")
    color = fields.Char(string="Color", compute="get_color")
    outlet = fields.Many2one('res.company', string="Outlet")
    basic_price = fields.Float(string="Basic Price")
    gst = fields.Float(string="GST")
    total = fields.Float(string="Total")
    motor_number = fields.Char(string="Motor Number")
    vendor = fields.Char(string="Vendor")
    vendor_reference_no = fields.Char(string="Vendor Reference No")
    description = fields.Char(string="Description")

    @api.multi
    def sql_query(self, companys, start_date, end_date):
        tools.drop_view_if_exists(self.env.cr, self._table)
        if len(companys) == 1:
            company_ids = f"({companys[0]})"
        else:
            company_ids = str(tuple(companys))

        date_filter = ""
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = fields.Datetime.from_string(start_date)
            if isinstance(end_date, str):
                end_date = fields.Datetime.from_string(end_date)
            start_date_str = "'{}'".format(start_date.strftime('%Y-%m-%d %H:%M:%S'))
            end_date_str = "'{}'".format(end_date.strftime('%Y-%m-%d %H:%M:%S'))
            date_filter = f"AND ai.date_invoice::date BETWEEN {start_date_str} AND {end_date_str}"

        self.env.cr.execute(f"""
                CREATE OR REPLACE VIEW {self._table} AS (
                    select row_number() over(order by mvl.id ASC) as id,
                    mvl.id AS sl_no,
                    ai.number as invoice_number,
                    ai.date_invoice as date_of_invoice,
                    mvl.lot_name as vin_no,
                    mvl.motor_number as motor_number,
                    pp.product_tmpl_id as product_template_id,
                    ail.product_id as product_id,
                    ail.price_subtotal_signed as basic_price,
                    (ail.price_total - ail.price_subtotal) as gst,
                    ail.price_total as total,
                    ai.company_id as outlet,
                    rc.dealer_code as dealer_code,
                    ai.reference as vendor_reference_no,
                    rp.name as vendor,
                    ail.name as description,
                    mg.name AS model_group
                    from account_invoice_line ail 
                    left join account_invoice ai on ai.id = ail.invoice_id
                    left join purchase_order_line pol on ail.purchase_line_id = pol.id
                    left join stock_move mv on mv.purchase_line_id = pol.id
                    left join stock_move_line mvl on mvl.move_id = mv.id
                    left join res_company rc on rc.id = ai.company_id
                    left join sale_order so on so.id = ai.order_id
                    left join product_product pp on ail.product_id = pp.id
                    left join res_partner rp on ai.partner_id = rp.id
                    LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    LEFT JOIN model_groups mg ON mg.id = pt.master_id
                    where ai.type = 'in_invoice' and ai.ars_type = 'vehicle'
                AND ai.company_id IN {company_ids}
                        {date_filter}
            )
        """)




class WholesaleReportPSFWizard(models.TransientModel):
    _name = 'wholesale.report.wizard'

    company_id = fields.Many2many('res.company', default=lambda self: self.env.user.company_ids)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    def wholesale_report_qty(self):
        self.ensure_one()
        comp_ids = []
        for rec in self.company_id:
            comp_ids.append(rec.id)
        query = self.env['wholesale.report']
        query.sudo().sql_query(companys=comp_ids,start_date=self.start_date, end_date=self.end_date)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Wholesale Report',
            'res_model': 'wholesale.report',
            'view_mode': 'tree',
            'view_type': 'form',
            'context': self.env.context,
            'target': 'current',
        }


