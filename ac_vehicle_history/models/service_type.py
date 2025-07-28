from odoo import models, fields, api, _, registry, SUPERUSER_ID, sql_db
from datetime import datetime
import logging
import json
from datetime import timedelta
import contextlib

_logger = logging.getLogger(__name__)


class ServiceType(models.Model):
    _inherit = "service.type"

    sequence = fields.Integer(string="Sequence", default=0)
    code = fields.Char("code", required=1)

class ServiceHistory(models.Model):
    _inherit = "service.history"


    cons_service_history_id = fields.Integer('Consolidate Service History Id')
    service_type_name = fields.Char(string="Service Type Name")
    mileage_in = fields.Integer(string="Mileage")
    service_code = fields.Char(string="Service Code")
    dealer_db_name = fields.Char("Dealer DB Name", required=True)




class FleetVehicleConsolepdf(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model
    def _get_service_history_from_pdf(self):
        """
            This function to passed data to service history report this is customized one.
            if the service history model contain order field value which is sale order the if part will execute and found the RO order
            if it's not else part will execute and connect the deealer database found the RO order and retutn the data
            The another function is commented that is available in below of this function
        """
        # res = {}
        # cust_voice = []
        # line_item = []
        # data = False
        all_service_details = []
        service_details =[]
        try:
            service_orders = self.service_ids.mapped('dealer_db_name')
            processed_ids = set()
            for service_db in service_orders:
                services = self.service_ids.filtered(lambda r: r.dealer_db_name == service_db)
                print('Filtered services:', services)
                database = service_db
                db = sql_db.db_connect(f"{database}")
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    for service in services:
                        if service.id in processed_ids:
                            continue
                        processed_ids.add(service.id)
                        domain = [('id', '=', service.ro_id)]
                        print('Domain for search:', domain)
                    # for service in services:
                    #     domain = [('id', '=', service.ro_id)]
                    #     print('0989809', domain)
                        res_model = env['sale.order'].sudo()
                        data = res_model.search(domain)
                        print('data2687678', data)
                        if data:
                            sr_close_date = data.invoice_ids.mapped('create_date')[-1] if data.invoice_ids else None
                            res = {
                                'name': data.name,
                                'date_order': data.date_order,
                                'sr_close_date': sr_close_date,
                                'servicetype':service.servicetype,
                                'mileage':service.mileage,
                                'dealer_name': data.company_id.name,
                                'dealer_short_name': data.company_id.display_name_short,
                                'dealer_code': data.company_id.dealer_code,
                                'dealer_city': data.company_id.city,
                                'warranty': data.warranty_ids.name,
                            }
                            ser_res = {
                                'name': data.name,
                                'date_order': data.date_order,
                                'sr_close_date': sr_close_date,
                                'servicetype':service.servicetype,
                                'mileage':service.mileage,
                                'dealer_name':data.company_id.name,
                                'dealer_short_name':data.company_id.display_name_short,
                                'dealer_code':data.company_id.dealer_code,
                                'dealer_city':data.company_id.city,
                                'warranty':data.warranty_ids.name,
                            }
                            cust_voice = []
                            line_item=[]
                            for voice in data.customer_voice_sale:
                                cust_voice.append({'name': voice.name, 'instructions': voice.instructions})
                            for sol in data.order_line:
                                line_item.append({'name': sol.product_catalog_id.name,
                                                  'default_code': sol.product_id.default_code,
                                                  'description': sol.name,
                                                  'category_type': sol.category.name,
                                                  'product_uom_qty': sol.product_uom_qty,
                                                  'warranty_claim': data.warranty_ids.name,
                                                  'qty_delivered': sol.qty_delivered,
                                                  })
                            res.update({'customer_voice': cust_voice, 'order_line': line_item})
                            print('line_item',line_item)
                            all_service_details.append(res)
                            print('ressssssssssss------', res)
                            service_details.append(ser_res)
                            print('ser_res', ser_res)
            all_service_details = sorted(all_service_details, key=lambda x:x['sr_close_date'])
            print('all_service_details', all_service_details)
            service_details = sorted(service_details, key=lambda x:x['sr_close_date'])
            print('service_details', service_details)

        except Exception as e:
            print(e)
            all_service_details = False
        print(all_service_details, 'all_service_detailsall_service_detailsall_service_details pdf------------------')
        return {'all_service_details':all_service_details,'service_details':service_details}