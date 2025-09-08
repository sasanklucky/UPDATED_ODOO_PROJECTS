from odoo import api, fields, models, _

class FleetVehicleCampaigns(models.Model):
    _inherit = 'fleet.vehicle'

    campaign_history_ids = fields.One2many(
        'campaign.history', 'campaign_vehicle_id', string="Campaign History"
    )
    sim_number = fields.Char('Sim Number')
    sim_installation_date = fields.Date('Campaign Done Date')


class CampaignHistory(models.Model):
    _name = 'campaign.history'
    _description = 'Campaign History'
    _rec_name = "campaign_name_ref"

    campaign_vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    vin_sn = fields.Char('Vin Number',related='campaign_vehicle_id.vin_sn')
    campaign_name = fields.Many2one('vehicle.campaigns', string='Campaign Name')
    campaign_name_ref = fields.Char(string='Campaign Name')
    campaign_ref = fields.Char(string='Campaign Ref')
    campaign_service_ref_id = fields.Integer(string="Campaign History Id")
    campaign_status = fields.Char(string="Campaign Status")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    # campaign_service_id  = fields.Integer(string="Campaign Order Id")
    campaign_service_name  = fields.Char(string="Campaign Order")
    camp_cancel_reasons = fields.Text(string='Remark')
    campaign_vehicle_status = fields.Selection(string="Vehicle Status",related='campaign_vehicle_id.vehicle_status')
    state = fields.Selection([('pending', 'Pending'), ('expired', 'Expired'), ('done', 'Done')],string='Campaign State')
    dealer_code = fields.Char(string='Dealer Code')
    dealer_db_name = fields.Char(string='Dealer DB Name')
    campaign_done_date = fields.Date(string='Campaign Done Date')




