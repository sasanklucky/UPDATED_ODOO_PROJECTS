from dateutil.relativedelta import relativedelta
import json
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger("_____")


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _description = 'Information on a vehicle'

    @api.constrains('vin_sn')
    def check_vin(self):
        if self.vin_sn:
            if not str(self.vin_sn).isalnum():
                raise ValidationError(_('VIN is not Alphanumeric'))
            if len(self.vin_sn) != 17:
                raise ValidationError(_('VIN Have %s Characters. It Should be 17') % len(self.vin_sn))
    #Added New Constraints restrict to create duplicate vehicle card.
    @api.constrains('vin_sn')
    def _check_unique_vin_sn(self):
        for record in self:
            if record.vin_sn:
                # Search for other vehicles with the same VIN
                duplicate = self.search([
                    ('vin_sn', '=', record.vin_sn),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError("VIN Number must be unique!")

    @api.multi
    def get_years(self):
        year_list = []
        for i in range(2014, 2036):
            year_list.append((i, str(i)))
        return year_list

    mvariant_id = fields.Many2one('product.product', 'Model Variants')
    model_id = fields.Many2one('product.template', 'Model', required=True, help='Model of the vehicle')
    name = fields.Char(compute="_compute_vehicle_name", store=True)

    contact_name = fields.Many2one('res.partner', string='Contact Person')
    vehicle_status = fields.Selection(
        [('demo', 'Demo'), ('customer', 'Customer'), ('own', 'Own'), ('new', 'New Vehicle')], 'Vehicle Status',
        select=True, default='customer')
    # kilometer_till = fields.Integer(string='Kilometer Till')
    #     reg_no = fields.Char(string='Regn No.')
    age = fields.Integer(string='Age', compute="_age")
    # prodcution_year = fields.Date(string='Prodcution Year')
    prodcution_month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                                         (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                                         (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
                                        string='Month', )
    prodcution_year = fields.Selection('get_years', string='Production Year')
    # model_year = fields.Date(string='Model Year')
    model_month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                                    (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                                    (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
                                   string='Month', )
    model_year = fields.Selection('get_years', string='Model Year')
    initial_reg_no = fields.Char(string='Initial Reg.No')
    service_due = fields.Char(string='Service Due')
    engine_code = fields.Char(string='Engine Code')
    engine_number = fields.Char(string='Engine Number')
    key_serial_number = fields.Char(string='Battery Serial Number')
    categ_id = fields.Many2one('product.category', 'Vehicle Category', related="mvariant_id.product_tmpl_id.categ_id")
    emission_test_category = fields.Char(string='Emission Test Category')
    warranty_validation = fields.Datetime(string='Warranty Validation')
    extented_warranty_no = fields.Char(string='Extented Warranty No')
    extented_warranty_validation = fields.Datetime(string='Warranty Validation')
    customer_ids = fields.One2many('ownership.history', 'vehicle_id')
    emission_ids = fields.One2many('emission.history', 'vehicle_id')
    insurance_ids = fields.One2many('insurance.history', 'vehicle_id')
    service_ids = fields.One2many('service.history', 'vehicle_id')
    lot_id = fields.Many2one('stock.production.lot', 'Stock Production Lot', copy=False)
    license_plate = fields.Char(required=False, help='License plate number of the vehicle (i = plate number for a car)')
    driver_id = fields.Many2one('res.partner', 'Customer', track_visibility="onchange", help='Customer of the vehicle',
                                copy=False)
    consolidate_vehicle_card_id = fields.Integer(string='consolidate_vehicle_card_id')
    is_demo_vehicle = fields.Boolean(string="Demo Vehicle")
    demo_vehicle_label = fields.Char(string="Demo Label", compute="_compute_demo_vehicle_label")

    @api.depends('is_demo_vehicle')
    def _compute_demo_vehicle_label(self):
        for rec in self:
            rec.demo_vehicle_label = "Demo Vehicle" if rec.is_demo_vehicle else "Not Demo Vehicle"

    @api.multi
    def toggle_demo_vehicle(self):
        for rec in self:
            rec.is_demo_vehicle = not rec.is_demo_vehicle

    # engine_type_code = fields.Char(string='Engine Type Code', related="product_id.product_tmpl_id.engine_type_code")
    # no_of_cylinder = fields.Char(string='No of Cylinder', related="product_id.product_tmpl_id.no_of_cylinder")
    # cylinder_capacity = fields.Char(string='Cylinder Capacity', related="product_id.product_tmpl_id.cylinder_capacity")
    # power_kw = fields.Char(string='Power(KW)', related="product_id.product_tmpl_id.power_kw")
    # power_hp = fields.Char(string='Power(HP)', related="product_id.product_tmpl_id.power_hp")
    # top_speed = fields.Char(string='Top Speed', related="product_id.product_tmpl_id.top_speed")
    # accellaration = fields.Char(string='Acceleration', related="product_id.product_tmpl_id.accellaration")
    # transmission_type_code = fields.Char(string='Transmission Code',
    #                                      related="product_id.product_tmpl_id.transmission_type_code")
    # tyre_details = fields.Char(string='Tyre Details ', related="product_id.product_tmpl_id.tyre_details")
    # no_of_doors = fields.Char(string='No of Doors', related="product_id.product_tmpl_id.no_of_doors")
    # empty_weight = fields.Float(string='Empty Weight', related="product_id.product_tmpl_id.empty_weight")
    # total_weight = fields.Float(string='Total Weight', related="product_id.product_tmpl_id.total_weight")
    # roof_load = fields.Char(string='Roof Load', related="product_id.product_tmpl_id.roof_load")
    # trailer_load = fields.Char(string='Trailer Load', related="product_id.product_tmpl_id.trailer_load")
    # awd = fields.Char(string='AWD', related="product_id.product_tmpl_id.awd")
    # no_of_axeles = fields.Char(string='No of Axeles', related="product_id.product_tmpl_id.no_of_axeles")
    # wheel_base = fields.Char(string='Wheel Base', related="product_id.product_tmpl_id.wheel_base")
    # front_axle_load = fields.Char(string='Front Axle Load', related="product_id.product_tmpl_id.front_axle_load")
    # rear_axle_load = fields.Char(string='Rear Axle Load', related="product_id.product_tmpl_id.rear_axle_load")
    # fuel_type = fields.Selection([('petrol', 'Petrol'), ('diesel', 'Diesel')], 'Fuel Type')
    # # color = fields.Char()
    # car_type = fields.Char(string='Car Type')
    # seating_capacity = fields.Char(string='Seating Capacity')
    # engine_capacity = fields.Char(string="Engine Capacity")
    # city_mileage = fields.Char(string="City Mileage")
    # highway_mileage = fields.Char(string="Highway Mileage")
    # power_steering = fields.Boolean(string="Power Streeing")
    # ac = fields.Boolean(string="A/C")
    # steering_adjustment = fields.Boolean(string="Steering Adjustment")
    # power_window = fields.Many2one('power.window', 'Power Window', index=True)
    # centre_locking = fields.Boolean(string="Centre Locking")
    # description = fields.Text()
    #Commented the below constrain to write new constraints
    # sql_constraints = [
    #     ('driver_id_unique', 'CHECK(1=1)', 'Only one car can be assigned to the same employee!'),
    #     ('vin_sn_unique', 'CHECK(1=1)', 'Only one car can be assigned to the same VIN Number!')
    # ]
    _sql_constraints = [

        ('vin_sn_unique', 'unique(vin_sn)', 'VIN/Chassis Number must be unique for each vehicle!')
    ]

    @api.onchange('vin_sn')
    def _check_lot_number(self):
        if self.vin_sn:
            if not self.lot_id:
                lot_id = self.env['stock.production.lot'].search([('name', '=', self.vin_sn)])
                if lot_id:
                    self.lot_id = lot_id.id
                else:
                    print("Lot Number not Present in the lot")

    @api.depends('model_id.brand_id.name', 'model_id.name', 'license_plate')
    def _compute_vehicle_name(self):
        for record in self:
            brand_name = (record.model_id.brand_id and record.model_id.brand_id.name + '/') or ''
            record.name = brand_name + record.model_id.name + '/' + (
                    record.license_plate == '/' and record.vin_sn or record.license_plate or _('No Plate'))

    @api.multi
    def get_vehcile_features(self):
        self.ensure_one()

        view = self.env.ref('ars_vehicle_sales.ars_models_vehicle_features')
        return {
            'name': _('Vehicle Features'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.template',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.model_id.id,
            'context': self.env.context,
        }

    @api.multi
    def name_get(self):
        context = dict(self.env.context)
        # print(context)
        result = []
        ress = super(FleetVehicle, self).name_get()

        if ress:
            for res in ress:
                r = list(res)
                st_pr_lt = self.browse(int(r[0]))
                if st_pr_lt.license_plate and st_pr_lt.vin_sn and st_pr_lt.license_plate == '/':
                    r[1] = f'{st_pr_lt.license_plate} - [{st_pr_lt.vin_sn}]'
                    res_t = tuple(r)
                    result.append(res_t)
                else:
                    r[1] = st_pr_lt.license_plate
                    res_t = tuple(r)
                    result.append(res_t)
        if result:
            ress = result
        return ress

    @api.onchange('vehicle_status')
    def company_get(self):
        if self.vehicle_status == 'new':
            self.driver_id = self.env.user.company_id.partner_id.id

    @api.model
    def create(self, data):
        vehicle = super(FleetVehicle, self.with_context(mail_create_nolog=True)).create(data)
        if self.vehicle_status == 'customer':
            if not self.customer_ids:
                raise ValidationError(_("Please Update Ownership History"))
            else:
                for line in self.customer_ids:
                    if line.sold_by.id == False:
                        raise ValidationError(_("Please Update Selling Dealer Details in Ownership History"))
        return vehicle

    # @api.model
    # def create(self,data):
    #     data.update({'customer_ids' : [(0, 0, {'custmer_name': self.partner_id.id,
    #                                        'date_of_ownership': datetime.now(),
    #                                        'address': self.partner_id.city,
    #                                        'mobile': self.partner_id.mobile})]})
    #     vehicle=super(FleetVehicle, self.with_context(mail_create_nolog=True)).create(data)
    #     return vehicle

    @api.multi
    def write(self, vals):
        if 'driver_id' in vals and 'customer_ids' not in vals and 'date_of_ownership' not in vals:
            res = self.env['res.partner'].browse(vals.get('driver_id'))
            # vals.update({'customer_ids': [(0, 0, {'custmer_name': res.id,
            #                                       'date_of_ownership': datetime.now(),
            #                                       'address': res.street,
            #                                       'sold_by': self.env.user.company_id.partner_id.id,
            #                                       'mobile': res.mobile})]})
        res = super(FleetVehicle, self).write(vals)
        if self.vehicle_status == 'customer' and 'customer_ids' not in vals:
            if not self.customer_ids:
                raise ValidationError(_("Please Update Ownership History"))
            else:
                for line in self.customer_ids:
                    if line.sold_by.id == False:
                        raise ValidationError(_("Please Update Selling Dealer Details in Ownership History"))
        return res

    @api.model
    def _auto_init(self):
        self.env.cr.execute("""
                                ALTER TABLE fleet_vehicle  DROP CONSTRAINT IF EXISTS fleet_vehicle_driver_id_unique;
                            """)

    @api.onchange('driver_id')
    def child_user(self):
        driver = self.driver_id.id
        multiple_name = {}
        if self.driver_id.child_ids:
            # customer_details = self.env['res.partner'].search([('', '=', driver)])

            multiple_name['domain'] = {'contact_name': [('id', '=', self.driver_id.child_ids.ids)]}

        else:
            multiple_name['domain'] = {'contact_name': [('id', '=', self.driver_id.ids)]}
            self.contact_name = self.driver_id.id
        return multiple_name

    # @api.onchange('vin_sn','mvariant_id')
    # def create_vin(self):
    #     vehicle_details = self.env['stock.production.lot']
    #     if self.vin_sn and self.model_id:
    #         vehicle_details.create({'name':self.vin_sn,'product_id':self.mvariant_id.id})
    #         # for res in customer_details:
    #             # res.create({'name':sself.vin_sn})

    # @api.onchange('vin_sn','mvariant_id')
    # def create_vin(self):
    #     vehicle_details = self.env['stock.production.lot'].search([('name', '=', self.vin_sn)])
    #     if vehicle_details:
    #         for res in customer_details:
    #             res.create({'vin_no':vehicle_details.id})

    @api.multi
    def update_customer_ownership(self):
        lot_obj = self.env['stock.production.lot']
        sale_order_line_obj = self.env['sale.order.line']

        for rec in self:
            if rec.vehicle_status != 'customer' or not rec.vin_sn:
                continue

            # Get or find the lot
            lot_id = rec.lot_id
            if not lot_id:
                lot_id = lot_obj.sudo().search([('name', '=', rec.vin_sn)], order='id desc', limit=1)
                if not lot_id:
                    continue

            # Get sale lines for that VIN
            sale_lines = sale_order_line_obj.search([('vin_no', '=', lot_id.id)])
            sale_lines_by_partner = {}
            invoice_dates_by_partner = {}

            for line in sale_lines:
                partner = line.order_id.partner_id
                if partner not in sale_lines_by_partner:
                    sale_lines_by_partner[partner] = []
                    invoice_dates_by_partner[partner] = set()
                sale_lines_by_partner[partner].append(line)
                if not partner.supplier:
                    invoice_dates_by_partner[partner].update(
                        line.order_id.invoice_ids.filtered(lambda inv: inv.state not in ['draft', 'cancel']).mapped('date_invoice')
                    )

            # If customer_ids is empty, create ownership record
            if not rec.customer_ids:
                ownership_history = []
                for sale in sale_lines:
                    partner = sale.order_id.partner_id
                    if partner == rec.driver_id and not partner.supplier:
                        for invoice in sale.order_id.invoice_ids:
                            if invoice.state not in ['draft', 'cancel']:
                                ownership_history.append((0, 0, {
                                    'custmer_name': partner.id,
                                    'order': sale.order_id.id,
                                    'date_of_ownership': invoice.date_invoice,
                                    'address': partner.city,
                                    'mobile': partner.mobile,
                                    'sold_by': sale.order_id.company_id.partner_id.id,
                                }))
                if ownership_history:
                    rec.customer_ids = ownership_history
                continue  # Skip the rest if we just added ownership

            # Clean up incorrect customer_ids
            to_unlink_ids = []
            for record in rec.customer_ids:
                partner = record.custmer_name
                invoice_dates = invoice_dates_by_partner.get(partner, set())
                if record.date_of_ownership not in invoice_dates:
                    to_unlink_ids.append(record.id)

            if to_unlink_ids:
                rec.customer_ids.browse(to_unlink_ids).unlink()

            # Retain only the latest valid owner record
            owner_data = rec.customer_ids.filtered(
                lambda r: r.custmer_name in sale_lines_by_partner and not r.custmer_name.supplier and r.date_of_ownership in invoice_dates_by_partner.get(r.custmer_name, set())
            )
            if len(owner_data) > 1:
                owner_data.sorted(key=lambda r: r.id, reverse=True)[1:].unlink()


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    @api.multi
    def action_lost_reason_apply(self):
        # for rec in self:
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        if not self.env.user.has_group('ars_vehicle_sales.group_access_crm_stage'):
            for rec in leads:
                if rec.stage_id.probability == 100:
                    raise UserError(f' You do not have access to change the state of the pipeline (id: {rec.id}) from Won')
        for rec in leads:
            rec.write({'lost_reason': self.lost_reason_id.id, 'child_lost_reason': self.child_lost_reason.id})
            rec.action_set_lost()


    @api.onchange('lost_reason_id')
    def set_lost_reason_ids(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids')).team_id.team_type
        print(leads,"leadsleadsleadsleadsleadsleadsleads")
        parent_lost_reasons = self.env['crm.lost.reason'].search([('sale_type', '=', leads), ('active', '=', True)])
        print(len(parent_lost_reasons))
        if parent_lost_reasons:
            return {'domain': {'lost_reason_id': [('id', 'in', parent_lost_reasons.ids)]}}
        else:
            return {'domain': {'lost_reason_id': [('id', 'in', False)]}}


    # @api.depends('lead_id')
    # def get_lost_reason_domain(self):
    #     for this in self:
    #         domain = ([('type', '=', this.lead_id.type)] if this.lead_id else [])
    #         this.lost_reason_domain = json.dumps(domain)
    #
    # lead_id = fields.Many2one('crm.lead')
    # lost_reason_domain = fields.Char(compute='get_lost_reason_domain')

    # @api.depends('lost_reason_id')
