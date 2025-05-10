from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import date


class CampaignsCards(models.Model):
    _name = 'vehicle.campaigns'
    _description = 'Vehicle Campaigns'


    name = fields.Char(string="Name")
    start_date = fields.Date(string="Starting Date")
    end_date = fields.Date(string="Ending Date")
    stage = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('waiting_to_start', 'Waiting To Start'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], string='Stages', default='draft', tracking=True)


    @api.onchange('start_date', 'end_date')
    def _onchange_ongoing_stage(self):
        today = date.today()
        for record in self:
            start_date = fields.Date.from_string(record.start_date) if isinstance(record.start_date, str) else record.start_date
            end_date = fields.Date.from_string(record.end_date) if isinstance(record.end_date, str) else record.end_date

            if start_date and not end_date:
                record.stage = 'scheduled'
                return

            if start_date and end_date:
                if start_date > end_date:
                    raise UserError(_("End date cannot be before start date"))

                if start_date > today:
                    record.stage = 'scheduled'
                elif start_date <= today and today <= end_date:
                    record.stage = 'ongoing'
                elif today > end_date:
                    record.stage = 'completed'
                print(today, end_date)

    cons_vehicles_camp_id = fields.Integer('Vehicle Campaign ID')
    service_type = fields.Many2one('service.type', 'Service Type')
    service_options = fields.Many2one('service.options', 'Service Options')
    failed = fields.Char(string='Failed')
    campaigns = fields.Selection([
        ('vin', 'VIN'),
        ('model', 'Model'),
    ], string='Campaigns')

    # One2many relationship to VIN entries
    vin_ids = fields.One2many(
        'vehicle.campaign.vin',
        'campaign_id',
        string='VIN Numbers'
    )
    unmatched_vin_ids = fields.One2many('vehicle.campaign.vin', 'campaign_id', string="Unmatched VINs", compute='_compute_unmatched_vins', store=False)

    instruction = fields.Many2one('instructions',string='Instruction')




    def action_open_import_wizard(self):
        self.ensure_one()
        return {
            'name': 'Import Vins',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('ac_ars_campaigns.view_import_vin_wizard').id,
            'res_model': 'import.button.wizard',
            'target': 'new',
            'context': {
                'default_campaigns_vin_id': self.id,
            },

        }

    def execute_campaign(self):
        self.ensure_one()
        if not self.vin_ids:
            raise UserError(_( f"Cannot execute: No VINs added to {self.name}"))
        # self.stage = 'waiting_to_start'
        vin_numbers = self.vin_ids.mapped('vin_number')
        vehicles = self.env["fleet.vehicle"].sudo().search([('vin_sn', 'in', vin_numbers)])

        # Get all VINs from fleet.vehicle that are in our campaign
        matched_vins = vehicles.mapped('vin_sn')

        # Update cam_active for each VIN in our campaign
        for vin_record in self.vin_ids:
            if vin_record.vin_number in matched_vins:
                vin_record.cam_active = True
                vin_record.status = "Success"
            else:
                vin_record.cam_active = False
                vin_record.status = "VIN not found in Vehicles Cards"



        for rec in  vehicles:
            related_vins = self.vin_ids.filtered(lambda vin: vin.vin_number == rec.vin_sn)
            state = [vin.state for vin in related_vins]
            print(state)
            vals = {
                'campaign_vehicle_id': rec.id,
                'campaign_name': self.id,
                'campaign_name_ref': self.name,
                'campaign_ref': self.id,
                'campaign_status': self.stage,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'state': state[0]
            }
            print(vals)
            existing_history = self.env['campaign.history'].search([('campaign_name', '=', self.id), ('campaign_vehicle_id', '=', rec.id)])
            if not existing_history:
                x = self.env['campaign.history'].sudo().create(vals)
                x.write({'campaign_service_ref_id': x.id})
            elif existing_history:
                vals['campaign_service_ref_id'] = existing_history.id
                existing_history.write(vals)


    @api.depends('vin_ids.cam_active')
    def _compute_unmatched_vins(self):
        for record in self:
            record.unmatched_vin_ids = record.vin_ids.filtered(lambda vin: not vin.cam_active)

    def paused_action(self):
        print('paused')


class VehicleCampaignVIN(models.Model):
    _name = 'vehicle.campaign.vin'
    _description = 'Campaign VIN Numbers'

    campaign_id = fields.Many2one('vehicle.campaigns', string='Campaign')
    vin_number = fields.Char(string='VIN', required=True)
    cam_active = fields.Boolean(string='active')
    status = fields.Text(string="Campaign Status", help="unmatched VIN notifications")
    state = fields.Selection([('pending', 'Pending'), ('expired', 'Expired'), ('done', 'Done')])

