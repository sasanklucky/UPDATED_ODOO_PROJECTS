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
        return [self.env.user.company_id.id]
    
    @api.model
    def get_renvenue(self,**kwargs):
        pipeline_ids = self.env['crm.lead'].search([('type','=','opportunity'),('team_id.team_type','=','sales'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)])
        pipeline_count = self.env['crm.lead'].search_count([('type','=','opportunity'),('team_id.team_type','=','sales'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)])
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
    def get_year_user_models_list_data(self,**kwargs):
        current_year = datetime.now().date().year
        years = []
        for year in range(current_year,2017,-1):
            years.append({'year_index': year, 'year': year})
        users = self.env['res.users'].search_read(['|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)],['id','name'])
        models = self.env['product.template'].search_read([('categ_id.name','=','Vehicle')],['id','name'])
        return [years,users,models]
    
# 9941664760
    @api.model
    def get_lead_portlet_data(self,**args):
        argsYear = args.get('lead_year',False)
        argsSalesPerson = args.get('sales_person',False)
        argsModel = args.get('model',False)
        current_year = int(argsYear) if argsYear else datetime.now().date().year
        months,month_list, lead_data,filter_string = [],[],[],''
        salesPerson = self.env['res.users'].search([('id','=',int(argsSalesPerson))])
        model = self.env['product.template'].search([('id','=',int(argsModel))])
        for month in range(1,13):
            months.append({'month_index': date(current_year, month, 1).strftime('%m'),'month_name': date(current_year, month, 1).strftime('%B')})
            month_list.append(date(current_year, month, 1).strftime('%b'))
        if 'lead_year' in args or 'sales_person' in args:
            if argsSalesPerson == '0' and argsModel == '0':
                filter_string = argsYear
            elif argsSalesPerson == '0' and argsModel != '0':
                filter_string = argsYear + ' / ' + model.name
            elif argsSalesPerson != '0' and argsModel == '0':
                filter_string = argsYear + ' / ' + salesPerson.name
            else:
                filter_string = argsYear + ' / ' + salesPerson.name  + ' / ' + model.name 
        for m in months:
            domain = []
            start_date,end_date = self._get_month_range(current_year,m['month_index'])
            if 'lead_year' in args or 'sales_person' in args:
                if argsSalesPerson == '0' and argsModel == '0':
                    domain = [('team_id.team_type','=','sales'),('type','=','lead'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]  
                elif argsSalesPerson == '0' and argsModel != '0':
                    domain = [('team_id.team_type','=','sales'),('type','=','lead'),('vehicle_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]  
                elif argsSalesPerson != '0' and argsModel == '0':
                    domain = [('team_id.team_type','=','sales'),('type','=','lead'),('user_id','=',int(argsSalesPerson)),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                elif argsSalesPerson != '0' and argsModel != '0':
                    domain = [('team_id.team_type','=','sales'),('type','=','lead'),('user_id','=',int(argsSalesPerson)),('vehicle_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
            else:
                domain = [('team_id.team_type','=','sales'),('type','=','lead'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)] 
            lead_ids = self.env['crm.lead'].search(domain)
            filtered_lead_ids = lead_ids.filtered(lambda x: datetime.strptime(x.create_date,"%Y-%m-%d %H:%M:%S").date() >= start_date and datetime.strptime(x.create_date,"%Y-%m-%d %H:%M:%S").date() <= end_date)
            lead_data.append({
                'color': '#658864',
                'y': len(filtered_lead_ids)
            })
        return[current_year, month_list, lead_data,filter_string]


    @api.model
    def get_opportunities_portlet_data(self,**args):
        argsYear = args.get('opportunity_year',False)
        argsSalesPerson = args.get('sales_person',False)
        argsModel = args.get('model',False)

        current_year = int(argsYear) if argsYear else datetime.now().date().year
        opportunities_data,months,month_list,opportunities_stage_data,filter_string = [],[],[],[],''
        salesPerson = self.env['res.users'].search([('id','=',int(argsSalesPerson))])
        model = self.env['product.template'].search([('id','=',int(argsModel))])
        stage_list = self.env['crm.stage'].search(['|',('team_id.team_type','=','sales'),('team_id','=',False)])
        
        for month in range(1,13):
            months.append({'month_index': date(current_year, month, 1).strftime('%m'),'month_name': date(current_year, month, 1).strftime('%B')})
            month_list.append(date(current_year, month, 1).strftime('%b'))
        if 'opportunity_year' in args or 'sales_person' in args:
            if argsSalesPerson == '0' and argsModel == '0':
                filter_string = argsYear
            elif argsSalesPerson == '0' and argsModel != '0':
                filter_string = argsYear + ' / ' + model.name
            elif argsSalesPerson != '0' and argsModel == '0':
                filter_string = argsYear + ' / ' + salesPerson.name
            else:
                filter_string = argsYear + ' / ' + salesPerson.name  + ' / ' + model.name 

        for stage in stage_list:
            opportunity_domain = []
            if 'opportunity_year' in args or 'sales_person' in args:
                if argsSalesPerson == '0' and argsModel == '0':
                    opportunity_domain = [('team_id.team_type','=','sales'),('type','=','opportunity'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                elif argsSalesPerson == '0' and argsModel != '0':
                    opportunity_domain = [('team_id.team_type','=','sales'),('type','=','opportunity'),('vehicle_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                elif argsSalesPerson != '0' and argsModel == '0':
                    opportunity_domain = [('team_id.team_type','=','sales'),('type','=','opportunity'),('user_id','=',int(argsSalesPerson)),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                elif argsSalesPerson != '0' and argsModel != '0':
                    opportunity_domain = [('team_id.team_type','=','sales'),('type','=','opportunity'),('user_id','=',int(argsSalesPerson)),('vehicle_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
            else:
                opportunity_domain = [('team_id.team_type','=','sales'),('type','=','opportunity'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
            
            opportunity_ids = self.env['crm.lead'].search(opportunity_domain)
            filtered_opportunity_ids = opportunity_ids.filtered(lambda x: datetime.strptime(x.date_conversion,"%Y-%m-%d %H:%M:%S").date().year == current_year and x.stage_id.id == stage.id if x.date_conversion else None)
            opportunities_data.append({'name': stage.name,'y': len(filtered_opportunity_ids),'drilldown': stage.name})
            quotation_month_stage_data = []
            for m in months:
                start_date,end_date = self._get_month_range(current_year,m['month_index'])
                # lead_domain = [('team_id.team_type','=','sales'),('type','=','opportunity'),('stage_id','=',stage.id)] if argsSalesPerson == '0' else [('team_id.team_type','=','sales'),('type','=','opportunity'),('stage_id','=',stage.id),('user_id','=',int(argsSalesPerson))] 
                lead_ids = self.env['crm.lead'].search(opportunity_domain)
                filtered_opportunity = lead_ids.filtered(lambda x: datetime.strptime(x.date_conversion,"%Y-%m-%d %H:%M:%S").date() >= start_date and x.stage_id.id == stage.id and datetime.strptime(x.date_conversion,"%Y-%m-%d %H:%M:%S").date() <= end_date if x.date_conversion else None)
                quotation_month_stage_data.append([date(current_year, int(m['month_index']), 1).strftime('%b'), len(filtered_opportunity)])
                
            opportunities_stage_data.append({'name': stage.name,'id':stage.name,'data': quotation_month_stage_data})

        return [current_year,opportunities_data,opportunities_stage_data,filter_string]

    @api.model
    def get_quotations_portlet_data(self,**args):
        argsYear = args.get('quotation_year',False)
        argsSalesPerson = args.get('sales_person',False)
        argsModel = args.get('model',False)
        current_year = int(argsYear) if argsYear else datetime.now().date().year
        months,month_list, sent_quotation_data,cancel_quotation_data,order_generated_data,filter_string = [],[],[],[],[],''
        
        salesPerson = self.env['res.users'].search([('id','=',int(argsSalesPerson))])
        model = self.env['product.template'].search([('id','=',int(argsModel))])

        for month in range(1,13):
            months.append({'month_index': date(current_year, month, 1).strftime('%m'),'month_name': date(current_year, month, 1).strftime('%B')})
            month_list.append(date(current_year, month, 1).strftime('%b'))
        
        if 'quotation_year' in args or 'sales_person' in args:
            if argsSalesPerson == '0' and argsModel == '0':
                filter_string = argsYear
            elif argsSalesPerson == '0' and argsModel != '0':
                filter_string = argsYear + ' / ' + model.name
            elif argsSalesPerson != '0' and argsModel == '0':
                filter_string = argsYear + ' / ' + salesPerson.name
            else:
                filter_string = argsYear + ' / ' + salesPerson.name  + ' / ' + model.name 
        for m in months:
            sent_domain,cancel_domain,order_domain = [],[],[]
            start_date,end_date = self._get_month_range(current_year,m['month_index'])
            if 'quotation_year' in args or 'sales_person' in args:
                if argsSalesPerson == '0' and argsModel == '0':
                    sent_domain = [('sale_aftersales','=','sales'),('state','=','sent'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]  
                    cancel_domain = [('sale_aftersales','=','sales'),('state','=','cancel'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]  
                    order_domain = [('sale_aftersales','=','sales'),('state','=','sale'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]  

                elif argsSalesPerson == '0' and argsModel != '0':
                    sent_domain = [('sale_aftersales','=','sales'),('state','=','sent'),('order_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]  
                    cancel_domain = [('sale_aftersales','=','sales'),('state','=','cancel'),('order_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]  
                    order_domain = [('sale_aftersales','=','sales'),('state','=','sale'),('order_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]  
                elif argsSalesPerson != '0' and argsModel == '0':
                    sent_domain = [('sale_aftersales','=','sales'),('state','=','sent'),('user_id','=',int(argsSalesPerson)),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                    cancel_domain = [('sale_aftersales','=','sales'),('state','=','cancel'),('user_id','=',int(argsSalesPerson)),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                    order_domain = [('sale_aftersales','=','sales'),('state','=','sale'),('user_id','=',int(argsSalesPerson)),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                elif argsSalesPerson != '0' and argsModel != '0':
                    sent_domain = [('sale_aftersales','=','sales'),('state','=','sent'),('user_id','=',int(argsSalesPerson)),('order_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                    cancel_domain = [('sale_aftersales','=','sales'),('state','=','cancel'),('user_id','=',int(argsSalesPerson)),('order_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                    order_domain = [('sale_aftersales','=','sales'),('state','=','sale'),('user_id','=',int(argsSalesPerson)),('order_line.product_template_id','in',[int(argsModel)]),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
            else:
                sent_domain = [('sale_aftersales','=','sales'),('state','=','sent'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)] 
                cancel_domain = [('sale_aftersales','=','sales'),('state','=','cancel'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)] 
                order_domain = [('sale_aftersales','=','sales'),('state','=','sale'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)] 
            sent_quotation_ids = self.env['sale.order'].search(sent_domain)
            cancel_quotation_ids = self.env['sale.order'].search(cancel_domain)
            order_generated_ids = self.env['sale.order'].search(order_domain)
            filtered_sent_quotation_ids = sent_quotation_ids.filtered(lambda x: datetime.strptime(x.date_order,"%Y-%m-%d %H:%M:%S").date() >= start_date and datetime.strptime(x.date_order,"%Y-%m-%d %H:%M:%S").date() <= end_date if x.date_order else None)
            filtered_cancel_quotation_ids = cancel_quotation_ids.filtered(lambda x: datetime.strptime(x.date_order,"%Y-%m-%d %H:%M:%S").date() >= start_date and datetime.strptime(x.date_order,"%Y-%m-%d %H:%M:%S").date() <= end_date if x.date_order else None)
            filtered_order_generated_ids = order_generated_ids.filtered(lambda x: datetime.strptime(x.effective_date,"%Y-%m-%d").date() >= start_date and datetime.strptime(x.effective_date,"%Y-%m-%d").date() <= end_date if x.effective_date else None)

            sent_quotation_data.append({'y': len(filtered_sent_quotation_ids)})
            cancel_quotation_data.append({'y': len(filtered_cancel_quotation_ids)})
            order_generated_data.append({'y': len(filtered_order_generated_ids)})
        return[current_year, month_list, sent_quotation_data,filter_string,cancel_quotation_data,order_generated_data]

    @api.model
    def get_model_wise_sale_portlet_data(self,**args):
        argsYear = args.get('model_wise_sale_year',False)
        argsSalesPerson = args.get('sales_person',False)
        current_year = int(argsYear) if argsYear else datetime.now().date().year
        salesPerson = self.env['res.users'].search([('id','=',int(argsSalesPerson))])

        months,month_list,model_wise_sale_list,month_model_data,filter_string = [],[],[],[],''
        model_ids = self.env['product.template'].search_read([('catalog_type','=', 'Vehicle')],['id','name'])

        if 'model_wise_sale_year' in args or 'sales_person' in args:
            if argsSalesPerson == '0':
                filter_string = argsYear
            else:
                filter_string = argsYear + ' / ' + salesPerson.name

        for month in range(1,13):
            months.append({'month_index': date(current_year, month, 1).strftime('%m'),'month_name': date(current_year, month, 1).strftime('%B')})
            month_list.append(date(current_year, month, 1).strftime('%b'))

        for model in model_ids:
            domain,filtered_model_data = [],[]
            if 'model_wise_sale_year' in args or 'sales_person' in args:
                if argsSalesPerson == '0':
                    domain = [('sale_aftersales','=', 'sales'),('state','=','sale'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
                elif argsSalesPerson != '0':
                    domain = [('sale_aftersales','=', 'sales'),('state','=','sale'),('user_id','=',int(argsSalesPerson)),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
            else:
                domain = [('sale_aftersales','=', 'sales'),('state','=','sale'),'|',('company_id','=',self.env.user.company_id.id),('company_id.parent_id','=',self.env.user.company_id.id)]
            model_wise_sale_ids = self.env['sale.order'].search(domain)
            filtered_model_wise_sale_ids = model_wise_sale_ids.filtered(lambda x: int(model['id']) in x.order_line.mapped('product_template_id.id') and (datetime.strptime(x.effective_date,"%Y-%m-%d").date().year == current_year if x.effective_date else None))
            model_wise_sale_list.append({'name': model['name'],'y': len(filtered_model_wise_sale_ids) or 0,'drilldown': model['name']})
            for m in months:
                start_date,end_date = self._get_month_range(current_year,m['month_index'])
                filtered_model = model_wise_sale_ids.filtered(lambda x: datetime.strptime(x.effective_date,"%Y-%m-%d").date() >= start_date and int(model['id']) in x.order_line.mapped('product_template_id.id') and datetime.strptime(x.effective_date,"%Y-%m-%d").date() <= end_date if x.effective_date else None)
                filtered_model_data.append([date(current_year, int(m['month_index']), 1).strftime('%b'), len(filtered_model)])
            month_model_data.append({'name': model['name'],'id':model['name'],'data': filtered_model_data})
        return [current_year,model_wise_sale_list,month_model_data,filter_string]