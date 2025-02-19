from ast import literal_eval

from odoo import models, fields, api
from lxml import etree

class MenuAccessForParticularModels(models.Model):
    _name = 'master.menu.restriction'

    general_sale_bool = fields.Boolean("General Sale")
    general_sales_menus = fields.Many2many('ir.ui.menu', string='General sales menus', widget="many2many_tags")
    g_sale_model = fields.Many2many('ir.model', string='Models To Restrict')
    models_able_restrict = fields.Char("Models Can Restrict",
                                       default=f"product.template, res.users, res.company, fleet.vehicle, utm.source, utm.medium, service.options, service.type,"
                                               f"service.setup.manual, sale.order, product.product, product.pricelist, purchase.order, crm.lead, crm.lead.lost,"
                                               f"ars.sale.warranty, res.partner, res.partner.title, res.partner.category, res.partner.bank, res.bank, res.country,"
                                               f"res.country.state, res.country.group, stock.picking, product.uom, stock.change.product.qty, crm.lost.reason, product.category,"
                                               f"account.invoice")


class MenuAccessForAfterSales(models.Model):
    _name = 'menu.restrict.aftersales'

    after_sales_bool = fields.Boolean("After Sale")
    after_sales_menu = fields.Many2many('ir.ui.menu', string='After sales menus', widget="many2many_tags")
    a_sale_model = fields.Many2many('ir.model', string='Models To Restrict')
    models_able_restrict = fields.Char("Models Can Restrict",
                                       default=f"product.template, res.users, res.company, fleet.vehicle, utm.source, utm.medium, service.options, service.type,"
                                               f"service.setup.manual, sale.order, product.product, product.pricelist, purchase.order, crm.lead, crm.lead.lost,"
                                               f"ars.sale.warranty, res.partner, res.partner.title, res.partner.category, res.partner.bank, res.bank, res.country,"
                                               f"res.country.state, res.country.group, stock.picking, product.uom, stock.change.product.qty, crm.lost.reason, product.category,"
                                               f"account.invoice")


class MenuAccessForVehicleSales(models.Model):
    _name = 'menu.restrict.vehiclesales'

    vehicle_sale_bool = fields.Boolean("Vehicle Sale")
    vehicle_sales_menus = fields.Many2many('ir.ui.menu', string='Vehicle sales menus', widget="many2many_tags")
    v_sale_model = fields.Many2many('ir.model', string='Models To Restrict')
    models_able_restrict = fields.Char("Models Can Restrict",
                                       default=f"product.template, res.users, res.company, fleet.vehicle, utm.source, utm.medium, service.options, service.type,"
                                               f"service.setup.manual, sale.order, product.product, product.pricelist, purchase.order, crm.lead, crm.lead.lost,"
                                               f"ars.sale.warranty, res.partner, res.partner.title, res.partner.category, res.partner.bank, res.bank, res.country,"
                                               f"res.country.state, res.country.group, stock.picking, product.uom, stock.change.product.qty, crm.lost.reason, product.category,"
                                               f"account.invoice")


class MenuAccessForOtherSales(models.Model):
    _name = 'menu.restrict.othersales'

    others_sale_bool = fields.Boolean("Others Sale")
    others_sales_menus = fields.Many2many('ir.ui.menu', string='Others sales menus', widget="many2many_tags")
    o_sale_model = fields.Many2many('ir.model', string='Models To Restrict')
    models_able_restrict = fields.Char("Models Can Restrict",
                                       default=f"product.template, res.users, res.company, fleet.vehicle, utm.source, utm.medium, service.options, service.type,"
                                               f"service.setup.manual, sale.order, product.product, product.pricelist, purchase.order, crm.lead, crm.lead.lost,"
                                               f"ars.sale.warranty, res.partner, res.partner.title, res.partner.category, res.partner.bank, res.bank, res.country,"
                                               f"res.country.state, res.country.group, stock.picking, product.uom, stock.change.product.qty, crm.lost.reason, product.category,"
                                               f"account.invoice")


class arsCompanyMasterDataRestriction(models.Model):
    _inherit = 'res.company'

    gsale_restrict_master_data = fields.Boolean()
    vsale_restrict_master_data = fields.Boolean()
    asale_restrict_master_data = fields.Boolean()
    other_restrict_master_data = fields.Boolean()
    edit_access_partner_name = fields.Boolean()
    model_id = fields.Many2one('product.template')
    crm_restrict_till_date = fields.Date()
    # gsale_res_gr_ids = fields.Many2many('res.groups', string='G Sale Master Data', widget="many2many_tags")
    # asale_res_gr_ids = fields.Many2many('res.groups', string='A sale Master Data', widget="many2many_tags")
    # vsale_res_gr_ids = fields.Many2many('res.groups', string='V Sale Master Data', widget="many2many_tags")
    # others_res_gr_ids = fields.Many2many('res.groups', string='Others Master Data', widget="many2many_tags")


class arsConfigMaterDataRestriction(models.TransientModel):
    _inherit = 'res.config.settings'

    vehicle_operation = fields.Boolean("Vehicle Operations")
    parts_operations = fields.Boolean("Parts Operations")
    vehicle_invoicing = fields.Boolean("Vehicle Invoicing")
    catalog = fields.Boolean("Catalog")
    parts_invoicing = fields.Boolean("Parts Invoicing")
    reporting = fields.Boolean("Reporting")

    gsale_restrict_master_data = fields.Boolean(related="company_id.gsale_restrict_master_data")
    vsale_restrict_master_data = fields.Boolean(related="company_id.vsale_restrict_master_data")
    asale_restrict_master_data = fields.Boolean(related="company_id.asale_restrict_master_data")
    other_restrict_master_data = fields.Boolean(related="company_id.other_restrict_master_data")
    gsale_res_gr_ids = fields.Many2many('res.groups', 'res_config_gsale_res_gr_rel', 'res_id', 'config_id',
                                        string='G Sale Master Data')
    asale_res_gr_ids = fields.Many2many('res.groups', 'res_config_asale_res_gr_rel', 'res_id', 'config_id',
                                        string='A sale Master Data')
    vsale_res_gr_ids = fields.Many2many('res.groups', 'res_config_vsale_res_gr_rel', 'res_id', 'config_id',
                                        string='V Sale Master Data')
    others_res_gr_ids = fields.Many2many('res.groups', 'res_config_others_res_gr_rel', 'res_id', 'config_id',
                                         string='Others Master Data')

    restrict_crm_lead = fields.Boolean("Restrict lead by conditions")
    model_id = fields.Many2one('product.template', string="Model", related="company_id.model_id")
    till_date = fields.Date(related="company_id.crm_restrict_till_date")

    def set_values(self):
        res = super(arsConfigMaterDataRestriction, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        print('gsale_res_gr_ids', self.asale_res_gr_ids.ids, self.gsale_res_gr_ids.ids, self.vsale_res_gr_ids.ids,
              self.others_res_gr_ids.ids)

        param.set_param('ars_after_sales.gsale_restrict_master_data', self.gsale_restrict_master_data)
        param.set_param('ars_after_sales.gsale_res_gr_ids', self.gsale_res_gr_ids.ids)

        param.set_param('ars_after_sales.vsale_restrict_master_data', self.vsale_restrict_master_data)
        param.set_param('ars_after_sales.vsale_res_gr_ids', self.vsale_res_gr_ids.ids)

        param.set_param('ars_after_sales.asale_restrict_master_data', self.asale_restrict_master_data)
        param.set_param('ars_after_sales.asale_res_gr_ids', self.asale_res_gr_ids.ids)

        param.set_param('ars_after_sales.other_restrict_master_data', self.other_restrict_master_data)
        param.set_param('ars_after_sales.others_res_gr_ids', self.others_res_gr_ids.ids)
        param.set_param('ars_after_sales.restrict_crm_lead', self.restrict_crm_lead)
        # param.set_param('ars_after_sales.model_id', self.model_id.id if self.model_id else False)
        return res

    @api.model
    def get_values(self):
        res = super(arsConfigMaterDataRestriction, self).get_values()
        fetch_details = self.env['ir.config_parameter'].sudo()

        # Retrieve boolean values
        gs_bool = fetch_details.get_param('ars_after_sales.gsale_restrict_master_data')
        vs_bool = fetch_details.get_param('ars_after_sales.vsale_restrict_master_data')
        as_bool = fetch_details.get_param('ars_after_sales.asale_restrict_master_data')
        os_bool = fetch_details.get_param('ars_after_sales.other_restrict_master_data')
        crm_restrict = fetch_details.get_param('ars_after_sales.restrict_crm_lead')
        # model_id = fetch_details.get_param('ars_after_sales.model_id')

        # Retrieve Many2many fields as lists of IDs separately for each group field
        gs_mamy2many = fetch_details.get_param('ars_after_sales.gsale_res_gr_ids')
        vs_mamy2many = fetch_details.get_param('ars_after_sales.vsale_res_gr_ids')
        as_mamy2many = fetch_details.get_param('ars_after_sales.asale_res_gr_ids')
        os_mamy2many = fetch_details.get_param('ars_after_sales.others_res_gr_ids')

        res.update(
            gsale_res_gr_ids=[(6, 0, literal_eval(gs_mamy2many))] if gs_mamy2many else False,
            vsale_res_gr_ids=[(6, 0, literal_eval(vs_mamy2many))] if vs_mamy2many else False,
            asale_res_gr_ids=[(6, 0, literal_eval(as_mamy2many))] if as_mamy2many else False,
            others_res_gr_ids=[(6, 0, literal_eval(os_mamy2many))] if os_mamy2many else False,
            gsale_restrict_master_data=gs_bool,
            vsale_restrict_master_data=vs_bool,
            asale_restrict_master_data=as_bool,
            other_restrict_master_data=os_bool,
            restrict_crm_lead = crm_restrict,
        )
        return res


