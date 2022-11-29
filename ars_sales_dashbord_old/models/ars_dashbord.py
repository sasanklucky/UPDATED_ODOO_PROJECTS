from odoo import models, fields, api, _
from datetime import datetime
from datetime import timedelta
from openerp.exceptions import UserError, ValidationError


class ars_dashbord(models.Model):
    _inherit = 'crm.lead'
    
    @api.model
    def retrieve_ars_sales_dashboard(self):
        res = super(ars_dashbord, self).retrieve_sales_dashboard()
        symbol_currency = self.env['res.currency'].browse(res.get('currency_id')).symbol
        res.update({'symbol':symbol_currency})
        print(res)
        return res

    # @api.constrains('mobile')
    # def check_dublicate_mob_no(self):
    #     if self.mobile:
    #         self.check_mob(self.mobile)

    def check_mob(self,mob_no):
        """ Function:
            1) Fetched dublicate records from Lead and Opportunities in crm_dublicate_records and validate
            2) Fetched dublicate records Customer in partner_duplicate_records and validate
        """
        crm_dublicate_records = (self.env['crm.lead'].sudo().search([('mobile', '=', mob_no)],limit=1, order='id desc'))
        if crm_dublicate_records:
            raise ValidationError(f"""Mobile Number ({mob_no}) already against the reference Lead/Opportuity :- {crm_dublicate_records.name}""")

    @api.model
    def create(self, vals):
        if 'mobile' in vals:
            self.check_mob(vals['mobile'])
        res = super(ars_dashbord, self).create(vals)
        return res
    
    @api.multi
    def write(self, vals):
        # if 'mobile' in vals:
        #     self.check_mob(vals['mobile'])
        res = super(ars_dashbord, self).write(vals)
        return res

class ars_res_partner(models.Model):
    _inherit = 'res.partner'
        
    
    # @api.constrains('mobile')
    # def check_dublicate_mob_no(self):
    #     if self.mobile:
    #         self.check_mob(self.mobile)

    def check_mob(self,mob_no):
        """ Function:
            1) Fetched dublicate records from Lead and Opportunities in crm_dublicate_records and validate
        """
        crm_dublicate_records = (self.env['res.partner'].sudo().search([('mobile', '=', mob_no)],limit=1, order='id desc'))
        if crm_dublicate_records:
            raise ValidationError(f"""Mobile Number ({mob_no}) already against the Partner :- {crm_dublicate_records.name}""")

    @api.model
    def create(self, vals):
        if 'mobile' in vals:
            self.check_mob(vals['mobile'])
        res = super(ars_res_partner, self).create(vals)
        return res
    
    @api.multi
    def write(self, vals):
        # if 'mobile' in vals:
        #     self.check_mob(vals['mobile'])
        res = super(ars_res_partner, self).write(vals)
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






