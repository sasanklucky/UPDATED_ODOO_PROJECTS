from odoo import models, fields, api
from datetime import datetime
from datetime import timedelta

class ars_dashbord(models.Model):
    _inherit = 'crm.lead'
    @api.model
    def retrieve_ars_sales_dashboard(self):
        res = super(ars_dashbord, self).retrieve_sales_dashboard()
        symbol_currency = self.env['res.currency'].browse(res.get('currency_id')).symbol
        res.update({'symbol':symbol_currency})
        print(res)
        return res


    # @api.model
    # def count_event(self):
    #
    #     get_day = datetime.today()
    #     day_str = get_day.strftime('%Y-%m-%d')
    #     t=day_str+' 23:59:59'
    #
    #     day_str2 = get_day.strftime('%Y-%m-%d')
    #     t2 = day_str2+' 00:00:00'
    #
    #     cal_obj = self.env['calendar.event']
    #     meet_count = cal_obj.search_count([('start_datetime','<=',t),('start_datetime','>=',t2)])
    #     print(meet_count)
    #
    #     one_week = datetime.strptime(t2,"%Y-%m-%d %H:%M:%S") + timedelta(days=7)
    #     temp_week = one_week.strftime('%Y-%m-%d %H:%M:%S')
    #     meet_next_count = cal_obj.search_count([('start_datetime', '<=', temp_week), ('start_datetime', '>=', t2)])
    #     print(meet_next_count)
    #     return {'meet_count':meet_count,'meet_next_count':meet_next_count}






