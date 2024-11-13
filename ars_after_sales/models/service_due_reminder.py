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
        service_type_sequences = {record.name: record.sequence for record in
                                  self.env['service.type'].search([('sequence', '>=', 0)])}
        models = self.env['product.template'].search([('categ_id', '=', 'Vehicle')])
        vehicle_ids = {}
        services = {}
        next_service_reminders = {}

        for car in models:
            # Initialize a dictionary for each car model
            services[car.id] = {}
            next_service_reminders[car.id] = {}

            # Find all vehicles associated with this model and filter those that have service history records
            vehicles_with_history = self.env['fleet.vehicle'].search([
                ('vehicle_status', '=', 'customer'),
                ('categ_id', '=', 'Vehicle'),
                ('model_id', '=', car.id)
            ]).filtered(lambda v: self.env['service.history'].search_count([('vehicle_id', '=', v.id)]) > 0)

            # Assign filtered vehicles to vehicle_ids for this car model
            vehicle_ids[car.id] = vehicles_with_history

            for vehicle in vehicles_with_history:
                # Initialize a list to store relevant service types for each vehicle
                services[car.id][vehicle] = {}

                # Search for service history records related to this vehicle
                service_histories = self.env['service.history'].search([('vehicle_id', '=', vehicle.id)])

                # Find the maximum sequence value in the service types related to this vehicle's history
                max_sequence = -1
                for history in service_histories:
                    seq_records = self.env['service.type'].search(
                        [('name', '=', history.service_type_name), ('sequence', '>=', 0)])
                    for seq in seq_records:
                        if seq.sequence > max_sequence:
                            max_sequence = seq.sequence

                # Retrieve and append service types with matching sequences
                for history in service_histories:
                    seq_records = self.env['service.type'].search(
                        [('name', '=', history.service_type_name), ('sequence', '=', max_sequence)])
                    for seq in seq_records:
                        if seq.sequence == 0:
                            services[car.id][vehicle] = {'current_service': seq.name,
                                                     'current_service_id':seq.sequence,
                                                     'current_service_done_date': vehicle.customer_ids[-1].date_of_ownership if vehicle.customer_ids else datetime.now().date(),
                                                     'next_service_to_do': self.env['service.type'].search([('sequence', 'in', [max_sequence+1])]).id if self.env['service.type'].search([('sequence', 'in', [max_sequence+1])]) else 0}
                        else:
                            services[car.id][vehicle] = {'current_service': seq.name,
                                                         'current_service_id': seq.sequence,
                                                         'current_service_done_date': history.date,
                                                         'next_service_to_do': self.env['service.type'].search(
                                                             [('sequence', 'in', [max_sequence + 1])]).id if self.env[
                                                             'service.type'].search(
                                                             [('sequence', 'in', [max_sequence + 1])]) else 0}

        print("Services:", services)
        print("Vehicle IDs:", vehicle_ids)
        service_manuals = self.env['service.setup.manual']
        for product_model, vehicle_model_service in services.items():
            for vehicle, service in vehicle_model_service.items():
                next_service_type = service.get('next_service_to_do')
                for service_manual in service_manuals.search([('service_type', '=', next_service_type), ('model_id', '=', vehicle.model_id.id)]):
                    if (datetime.now().date() - datetime.strptime(
                        service.get('current_service_done_date'), '%Y-%m-%d').date()).days == (
                                            service_manual.days - remainder_days):
                        if product_model not in next_service_reminders:
                            next_service_reminders[product_model] = {}
                        if vehicle not in next_service_reminders[product_model]:
                            next_service_reminders[product_model][vehicle] = {}

                        next_service_reminders[product_model][vehicle] = {
                            'next_service': service_manual.service_type.name,
                        }
        print(next_service_reminders)
        for model, vehicle in next_service_reminders.items():
            for lead_data, lead_age in vehicle.items():
                for data in lead_data:
                    crm_stage = self.env['crm.stage'].search([('category_stage', '=', 'after_sales'),
                                                              ('name', '=', 'Service Due'),
                                                              ('team_id.company_id.id', '=', data.company_id.id)])
                    vals = {
                        'name': lead_age.get('next_service'),
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
        #     services = {}
        #     for service in service_manual:
        #         vehicles_for_service = self.env['fleet.vehicle'].search(
        #             [('vehicle_status', '=', 'customer'), ('categ_id', '=', 'Vehicle'),
        #              ('model_id', '=', service.model_id.id)]).filtered(
        #             lambda vehicle: vehicle.customer_ids and vehicle.customer_ids[-1].date_of_ownership).filtered(
        #             lambda vehicle: (datetime.now().date() - datetime.strptime(
        #                 vehicle.customer_ids[-1].date_of_ownership, '%Y-%m-%d').date()).days == (
        #                                     service.days - remainder_days))
        #         # print(service.days - remainder_days)
        #         services[service.service_type.name] = vehicles_for_service
        #     vehicle_model[car.id] = services
        # print(vehicle_model)
        # for model, service_age in vehicle_model.items():
        #     for lead_age, lead_data in service_age.items():
        #         for data in lead_data:
        #             crm_stage = self.env['crm.stage'].search([('category_stage', '=', 'after_sales'),
        #                                                       ('name', '=', 'Service Due'),
        #                                                       ('team_id.company_id.id', '=', data.company_id.id)])
        #             vals = {
        #                 'name': lead_age,
        #                 'partner_id': data.driver_id.id,
        #                 'regn_no': data.id,
        #                 'vin_no': data.vin_sn,
        #                 'vehicle_model': data.mvariant_id.id,
        #                 'stage_id': crm_stage.id,
        #                 'type': 'opportunity',
        #                 'company_id': data.company_id.id,
        #                 'team_id': crm_stage.team_id.id,
        #                 # 'kilometer_in': data.odometer,
        #                 'type_lead': 'appointment',
        #                 'model_id': data.model_id.id,
        #                 'sale_date_to_customer': data.customer_ids[-1].date_of_ownership,
        #             }
        #             # if 'model_id' not in vals:
        #             #     vals['model_id'] = data.model_id.id
        #             crm = self.env['crm.lead'].sudo().create(vals)