import locale
import datetime, calendar
from calendar import monthrange
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api

class CRMDashboard(models.Model):
    _inherit= 'crm.lead'

    @api.model
    def get_dealer_list(self,**kwargs):
        company_ids = self.env['res.company'].sudo().search_read([],['id','name'])
        return [company_ids]
    
    @api.model
    def get_renvenue(self,**kwargs):
        pipeline_ids = self.env['crm.lead'].search([('type','=','opportunity'),('team_id.team_type','=','sales')])
        pipeline_count = self.env['crm.lead'].search_count([('type','=','opportunity'),('team_id.team_type','=','sales')])
        revenue = sum(pipeline_ids.mapped('planned_revenue'))
        # locale.setlocale(locale.LC_ALL, 'en_US')
        revenue_amount = locale.format("%d", revenue, grouping=True)
        return [revenue_amount,pipeline_count]

    def _get_month_range(self, current_year=False, month_number=False):
        current_year = current_year
        month_number = month_number
        _, num_days = monthrange(int(current_year), int(month_number))
        start_date = date(int(current_year), int(month_number), 1)
        end_date = date(int(current_year), int(month_number), num_days)
        return start_date, end_date

    @api.model
    def get_year_user_list_data(self,**kwargs):
        current_year = datetime.now().date().year
        years,users = [],[]
        for year in range(current_year,2021,-1):
            years.append({'year_index': year, 'year': year})
        users = self.env['res.users'].search_read([],['id','name'])
        return [years,users]

    @api.model
    def get_lead_portlet_data(self,**args):
        argsYear = args.get('lead_year',False)
        argsSalesPerson = args.get('sales_person',False)
        
        current_year = int(argsYear) if argsYear else datetime.now().date().year
        months,month_list, lead_data = [],[],[]

        for month in range(1,13):
            months.append({'month_index': date(current_year, month, 1).strftime('%m'),'month_name': date(current_year, month, 1).strftime('%B')})
            month_list.append(date(current_year, month, 1).strftime('%b'))
        for m in months:
            start_date,end_date = self._get_month_range(current_year,m['month_index'])
            domain = [('team_id.team_type','=','sales'),('type','=','lead')] if argsSalesPerson == '0' else [('team_id.team_type','=','sales'),('type','=','lead'),('user_id','=',int(argsSalesPerson))] 
            lead_ids = self.env['crm.lead'].search(domain)
            filtered_lead_ids = lead_ids.filtered(lambda x: datetime.strptime(x.create_date,"%Y-%m-%d %H:%M:%S").date() >= start_date and datetime.strptime(x.create_date,"%Y-%m-%d %H:%M:%S").date() <= end_date)
            lead_data.append({
                'color': '#850000',
                'y': len(filtered_lead_ids)
            })
        return[current_year, month_list, lead_data]


    @api.model
    def get_opportunities_portlet_data(self,**args):
        argsYear = args.get('opportunity_year',False)
        argsSalesPerson = args.get('sales_person',False)

        current_year = int(argsYear) if argsYear else datetime.now().date().year
        opportunities_data,months,month_list,opportunities_stage_data = [],[],[],[]
        stage_list = self.env['crm.stage'].search(['|',('team_id.team_type','=','sales'),('team_id','=',False)])
        opportunities_domain = [('team_id.team_type','=','sales'),('type','=','opportunity'),('stage_id','in',stage_list.mapped('id'))] if argsSalesPerson == '0' else [('team_id.team_type','=','sales'),('type','=','opportunity'),('stage_id','in',stage_list.mapped('id')),('user_id','=',int(argsSalesPerson))]
        opportunities = self.env['crm.lead'].search(opportunities_domain) 
        total_opportunities = opportunities.filtered(lambda x: datetime.strptime(x.date_conversion,"%Y-%m-%d %H:%M:%S").date().year == current_year if x.date_conversion else None)
        
        for month in range(1,13):
            months.append({'month_index': date(current_year, month, 1).strftime('%m'),'month_name': date(current_year, month, 1).strftime('%B')})
            month_list.append(date(current_year, month, 1).strftime('%b'))

        for stage in stage_list:
            opportunity_domain = [('team_id.team_type','=','sales'),('type','=','opportunity')] if argsSalesPerson == '0' else [('team_id.team_type','=','sales'),('type','=','opportunity'),('user_id','=',int(argsSalesPerson))]
            opportunity_ids = self.env['crm.lead'].search(opportunity_domain)
            filtered_opportunity_ids = opportunity_ids.filtered(lambda x: datetime.strptime(x.date_conversion,"%Y-%m-%d %H:%M:%S").date().year == current_year and x.stage_id.id == stage.id if x.date_conversion else None)
            opportunities_data.append({'name': stage.name,'y': len(filtered_opportunity_ids),'drilldown': stage.name})
            quotation_month_stage_data = []
            for m in months:
                start_date,end_date = self._get_month_range(current_year,m['month_index'])
                lead_domain = [('team_id.team_type','=','sales'),('type','=','opportunity'),('stage_id','=',stage.id)] if argsSalesPerson == '0' else [('team_id.team_type','=','sales'),('type','=','opportunity'),('stage_id','=',stage.id),('user_id','=',int(argsSalesPerson))] 
                lead_ids = self.env['crm.lead'].search(lead_domain)
                filtered_opportunity = lead_ids.filtered(lambda x: datetime.strptime(x.date_conversion,"%Y-%m-%d %H:%M:%S").date() >= start_date and datetime.strptime(x.date_conversion,"%Y-%m-%d %H:%M:%S").date() <= end_date if x.date_conversion else None)
                quotation_month_stage_data.append([date(current_year, int(m['month_index']), 1).strftime('%b'), len(filtered_opportunity)])
                
            opportunities_stage_data.append({'name': stage.name,'id':stage.name,'data': quotation_month_stage_data})

        return [current_year,opportunities_data,opportunities_stage_data]

        
