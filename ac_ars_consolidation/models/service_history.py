from odoo import api, fields, models, registry, SUPERUSER_ID, sql_db
from datetime import datetime
from datetime import timedelta
import contextlib


class FleetVehicleConsole(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model
    def _get_service_history_from_dealers(self):
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
        service_details = []
        try:
            service_orders = self.service_ids.mapped('dealer_db_name')
            service_orders = list(set(service_orders))
            for service_db in service_orders:
                services = self.service_ids.filtered(lambda r: r.dealer_db_name == service_db)
                database = service_db
                db = sql_db.db_connect(f"{database}")
                with contextlib.closing(db.cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    domain = [('id', '=', services.mapped('ro_id'))]
                    res_model = env['sale.order'].sudo()
                    datas = res_model.search(domain)
                    if datas:
                        for data in datas:
                            sr_close_date = data.invoice_ids.mapped('create_date')[-1] if data.invoice_ids else None
                            res = {
                                'name': data.name,
                                'date_order': data.date_order,
                                'sr_close_date': sr_close_date,
                                'servicetype': data.service_options.name,
                                'mileage': data.mileage_in
                            }
                            ser_res = {
                                'name': data.name,
                                'date_order': data.date_order,
                                'sr_close_date': sr_close_date,
                                'servicetype': data.service_options.name,
                                'mileage': data.mileage_in,
                                'dealer_name': data.company_id.name
                            }
                            cust_voice = []
                            line_item = []
                            for voice in data.customer_voice_sale:
                                cust_voice.append({'name': voice.name, 'instructions': voice.instructions})
                            for sol in data.order_line:
                                line_item.append({'name': sol.product_catalog_id.name,
                                                  'default_code': sol.product_id.default_code,
                                                  'description': sol.name,
                                                  'category_type': sol.category.type,
                                                  'product_uom_qty': sol.product_uom_qty
                                                  })
                            res.update({'customer_voice': cust_voice, 'order_line': line_item})
                            all_service_details.append(res)
                            service_details.append(ser_res)
            all_service_details = sorted(all_service_details, key=lambda x: x['sr_close_date'])
            service_details = sorted(service_details, key=lambda x: x['sr_close_date'])

        except Exception as e:
            print(e)
            all_service_details = False
        print(all_service_details, 'all_service_detailsall_service_detailsall_service_details------------------')
        return {'all_service_details': all_service_details, 'service_details': service_details}


class ARS_ServiceHistory(models.Model):
    _inherit = 'service.history'

    dealer_id = fields.Many2one('ars.consolidation.setup')
    ro_id = fields.Integer()
    ro_number = fields.Char('RO Reference')

    # @api.model
    # def _get_service_history_from_dealers(self):
    #     """
    #         This function to passed data to service history report this is customized one.
    #         if the service history model contain order field value which is sale order the if part will execute and found the RO order
    #         if it's not else part will execute and connect the deealer database found the RO order and retutn the data
    #         The another function is commented that is available in below of this function
    #     """
    #     print(self,'selffffffffffffff')
    #     print('_get_service_history_from_dealers_get_service_history_from_dealers')
    #     res = {}
    #     cust_voice = []
    #     line_item = []
    #     data = False
    #     try:
    #          with api.Environment.manage():
    #              # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
    #             new_cr = self.pool.cursor()
    #             new_cr.autocommit(True)
    #             self = self.with_env(self.env(cr=new_cr))
    #             if self.order and self.order.id == self.ro_id:
    #                 domain = [('id', '=', self.order.id)]
    #                 data = self.env['sale.order'].sudo().search(domain)
    #                 print(data,'if______dataaaaaaa')
    #                 new_cr.close()
    #             if not self.order:
    #                 database = self.dealer_id.db_name or self.dealer_db_name
    #                 db = sql_db.db_connect(f"{database}")
    #                 domain = [('id', '=', self.ro_id)]
    #                 with contextlib.closing(db.cursor()) as cr:
    #                     cr.autocommit(True)
    #                     env = api.Environment(cr, SUPERUSER_ID, {})
    #                     res_model = env['sale.order'].sudo()
    #                     data = res_model.search(domain)
    #                     print(data,'else____datadatadata')
    #                     if data:
    #                         res = {
    #                             'name': data.name,
    #                             'date_order': data.date_order,
    #                             'sr_close_date': data.invoice_ids.mapped('create_date')[-1] if data.invoice_ids else None
    #                         }
    #                         for voice in data.customer_voice_sale:
    #                             cust_voice.append({'name': voice.name, 'instructions': voice.instructions})
    #                         for sol in data.order_line:
    #                             line_item.append({'name': sol.product_catalog_id.name,
    #                                               'default_code': sol.product_id.default_code,
    #                                               'description': sol.name,
    #                                               'category_type': sol.category.type,
    #                                               'product_uom_qty': sol.product_uom_qty
    #                                               })
    #                         res.update({'customer_voice': cust_voice, 'order_line': line_item})
    #     except Exception as e:
    #         print(e)
    #         res = False
    #         print(res, 'ressssssssssss------------------')
    #         return res

    # def _get_service_history_from_dealers(self):
    #     res = {}
    #     cust_voice = []
    #     line_item = []
    #     try:
    #         database = self.dealer_id.db_name
    #         db = sql_db.db_connect(f"{database}")
    #         domain = [('id', '=', self.ro_id)]
    #         with contextlib.closing(db.cursor()) as cr:
    #             cr.autocommit(True)
    #             env = api.Environment(cr, SUPERUSER_ID, {})
    #             res_model = env['sale.order'].sudo()
    #             data = res_model.search(domain)
    #             res = {'name': data.name, 'date_order': data.date_order,
    #                    'sr_close_date': data.invoice_ids.mapped('create_date')[-1]
    #                    }
    #             for voice in data.customer_voice_sale:
    #                 cust_voice.append({'name': voice.name, 'instructions': voice.instructions})
    #             for sol in data.order_line:
    #                 line_item.append({'name': sol.product_catalog_id.name,
    #                                   'default_code': sol.product_id.default_code,
    #                                   'description': sol.name, 'category_type': sol.category.type,
    #                                   'product_uom_qty': sol.product_uom_qtyx
    #                                   })
    #             res.update({'customer_voice': cust_voice, 'order_line': line_item})
    #             return res
    #     except Exception as e:
    #         print(e)
    #         return False


class ARS_OwnershipHistory(models.Model):
    _inherit = 'ownership.history'

    dealer_id = fields.Many2one('ars.consolidation.setup')
