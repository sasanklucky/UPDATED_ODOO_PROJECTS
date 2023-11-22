from odoo import models, fields, api


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        con = self.env.context
        sale_report1 = self.env.ref('sale.action_report_saleorder')
        sale_report2 = self.env.ref('sale.action_report_pro_forma_invoice')
        sale_report3 = self.env.ref('ars_reports.repair_order_report_download')
        sale_report4 = self.env.ref('ars_after_sales.estimate_order')
        if 'default_sale_aftersales' in con and con.get('default_sale_aftersales') == 'after_sales':
            sale_report1.unlink_action()
            # sale_report2.unlink_action()
            sale_report3.create_action()
            sale_report4.create_action()
        elif 'default_sale_aftersales' in con and con.get('default_sale_aftersales') == 'sales':
            sale_report1.create_action()
            sale_report2.create_action()
            sale_report3.unlink_action()
            sale_report4.unlink_action()
        else:
            sale_report1.create_action()
            sale_report2.create_action()
            sale_report3.unlink_action()
            sale_report4.unlink_action()
        res = super(SaleOrderInherit, self).fields_view_get(view_id, view_type, toolbar, submenu)
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        con = self.env.context
        invoice_report1 = self.env.ref('account.account_invoices')
        invoice_report2 = self.env.ref('account.account_invoices_without_payment')
        invoice_report3 = self.env.ref('ars_vehicle_sales.before_sales_invoice')
        if 'default_ars_invoice_type' in con and con.get('default_ars_invoice_type') == 'vehicle':
            invoice_report1.unlink_action()
            invoice_report2.unlink_action()
            invoice_report3.create_action()
        elif 'default_ars_invoice_type' in con and con.get('default_ars_invoice_type') == 'after_sales':
            invoice_report3.unlink_action()
            invoice_report1.create_action()
            invoice_report2.create_action()
        else:
            invoice_report3.create_action()
        res = super(AccountInvoice, self).fields_view_get(view_id, view_type, toolbar, submenu)
        return res
