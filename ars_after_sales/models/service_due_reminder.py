from odoo import models, fields, api, _
from datetime import date, timedelta, datetime


class ServiceLeadCreation(models.Model):
    _inherit = "crm.lead"

    service_type = fields.Many2one('service.type', 'Service Type')
    service_options = fields.Many2one('service.options', 'Service Options')
    sale_date_to_customer = fields.Date('Sale Date')
    pick_up_drop_crm = fields.Selection([('yes', 'YES'), ('no', 'NO')], string='Pick Up and Drop')

    @api.onchange('service_options')
    def set_domain_service_type(self):
        self.service_type = False
        if self.service_options:
            service_options = self.env['service.type'].sudo().search(
                [('service_option_id', '=', self.service_options.id)])
            return {'domain': {'service_type': [('id', 'in', service_options.ids)]}}
        else:
            return {'domain': {'service_type': [('id', 'in', False)]}}

    @api.onchange('pick_up_drop_crm')
    def change_type_lead(self):
        for rec in self:
            if rec.pick_up_drop_crm == 'yes':
                rec.type_lead = 'p&d'
            elif rec.pick_up_drop_crm == 'no':
                rec.type_lead = 'appointment'

    def creation_of_lead_for_service(self):
        """
        1. remainder_days : used to create lead based on prior days.
        2. models : fetch all vehicle's from 'product.template' model.
        3. service_manual : used to segregate the service setup days based on the car's or model.
        4. vehicles_for_service : used to flitter the records from 'fleet.vehicle' model based on the date_of_ownership
            and services days with difference of prior day's.
        data_types used dictionary's :- vehicle_model = {}, services = {}  "dictionary will not allow duplicate keys but
                                                                                                        allows values"
        o/p:- {'product.template' : {'service.type': 'fleet.vehicle'}}
        :return:
        """
        vehicle_model = {}
        remainder_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'ars_after_sales.next_service_remainder'))
        models = self.env['product.template'].search([('categ_id', '=', 'Vehicle')])
        for car in models:
            service_manual = self.env['service.setup.manual'].search([('model_id', '=', car.id)])
            services = {}
            for service in service_manual:
                vehicles_for_service = self.env['fleet.vehicle'].search(
                    [('vehicle_status', '=', 'customer'), ('categ_id', '=', 'Vehicle'),
                     ('model_id', '=', service.model_id.id)]).filtered(
                    lambda vehicle: vehicle.customer_ids and vehicle.customer_ids[-1].date_of_ownership).filtered(
                    lambda vehicle: (datetime.now().date() - datetime.strptime(
                        vehicle.customer_ids[-1].date_of_ownership, '%Y-%m-%d').date()).days == (
                                            service.days - remainder_days))
                # print(service.days - remainder_days)
                services[service.service_type.name] = vehicles_for_service
            vehicle_model[car.id] = services
        print(vehicle_model)
        for model, service_age in vehicle_model.items():
            for lead_age, lead_data in service_age.items():
                for data in lead_data:
                    crm_stage = self.env['crm.stage'].search([('category_stage', '=', 'after_sales'),
                                                              ('name', '=', 'Service Due'),
                                                              ('team_id.company_id.id', '=', data.company_id.id)])
                    vals = {
                        'name': lead_age,
                        'partner_id': data.driver_id.id,
                        'regn_no': data.id,
                        'vin_no': data.vin_sn,
                        'vehicle_model': data.mvariant_id.id,
                        'stage_id': crm_stage.id,
                        'type': 'opportunity',
                        'company_id': data.company_id.id,
                        'team_id': crm_stage.team_id.id,
                        # 'kilometer_in': data.odometer,
                        'type_lead': 'appointment',
                        'model_id': data.model_id.id,
                        'sale_date_to_customer': data.customer_ids[-1].date_of_ownership,
                    }
                    # if 'model_id' not in vals:
                    #     vals['model_id'] = data.model_id.id
                    crm = self.env['crm.lead'].sudo().create(vals)