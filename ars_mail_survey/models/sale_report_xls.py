from odoo import models, api, fields
import io
import base64
from datetime import datetime, timedelta

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ARSMailActivity(models.Model):
    _inherit = "mail.activity"

    @api.multi
    def export_sale_xls(self, data):
        question_list = []
        # for record in data:
        #     questions = record.response_id.user_input_line_ids
        #     for rec in questions:
        #         question_list.append(rec)
        param = self.env['ir.config_parameter'].sudo()
        sale_survey_id = param.get_param('ars_mail_survey.sale_survey_id')
        sale_survey = self.env['survey.survey'].browse(int(sale_survey_id))
        for page in sale_survey.page_ids:
            question_list = page.question_ids

        questions_list = question_list
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheets = workbook.add_worksheet('PSF Sale Report')
        sheets.set_column('C:C', 35)
        sheets.set_column('D:X', 25)
        sheets.set_column('J:J', 35)
        sheets.set_column('V:W', 35)
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True, 'bg_color': '#8f8f8f'})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        # sheets.merge_range(0, 0, 2, 23, 'After-Sales PSF Report', format0)
        sheets.write(1, 1, 'Month', format21)
        sheets.write(1, 0, 'Sl No', format21)
        sheets.write(1, 2, 'Sales Person', format21)
        sheets.write(1, 3, 'Date of Delivery', format21)
        sheets.write(1, 4, 'Model', format21)
        sheets.write(1, 5, 'VIN No', format21)
        sheets.write(1, 6, 'Customer Name', format21)
        sheets.write(1, 7, 'Contact Person', format21)
        sheets.write(1, 8, 'Contact No', format21)
        sheets.write(1, 9, 'Delivery Type', format21)
        sheets.write(1, 10, 'After Sales Introduction', format21)
        sheets.write(1, 11, 'Due Date', format21)
        sheets.write(1, 12, 'Contact Status', format21)
        sheets.write(1, 13, 'PSF Status.', format21)
        sheets.write(1, 14, 'VOC', format21)
        if questions_list:
            q_rw = 15
            for quest in questions_list:
                sheets.write(1, q_rw, quest.question, format21)
                q_rw += 1

        sheets.write(1, 25, 'CRM Remarks', format21)
        sheets.write(1, 26, 'Actions Taken', format21)
        sheets.write(1, 27, 'Current Status', format21)
        sheets.write(1, 28, 'Complaint Close Date', format21)
        sheets.write(1, 29, 'Ageing', format21)
        row, column, sl = 2, 0, 0
        for rec in data:
            helpdesk_ticket = self.env['helpdesk.ticket'].search([('activity_source_id', '=', rec.id)])
            date_object = fields.Date.from_string(rec.date_deadline)
            month_number = date_object.month
            month_words = {
                1: 'January',
                2: 'February',
                3: 'March',
                4: 'April',
                5: 'May',
                6: 'June',
                7: 'July',
                8: 'August',
                9: 'September',
                10: 'October',
                11: 'November',
                12: 'December',
            }
            month_word = month_words.get(month_number, '')
            invoice = rec.invoice_id
            sheets.write(row, column + 1, month_word, format11)
            sheets.write(row, column, sl + 1, format11)
            sheets.write(row, column + 2, rec.user_id.name, format11)
            if invoice.gate_pass_date:
                gate_date = datetime.strptime(invoice.gate_pass_date, '%Y-%m-%d')
                gate_pass_date = gate_date.strftime('%d-%m-%Y')
                sheets.write(row, column + 3, gate_pass_date, format11)
            vin_no = self.env['account.invoice.line'].search([('invoice_id', '=', invoice.id)], limit=1).vin_no
            sheets.write(row, column + 4, vin_no.product_id.name, format11)
            sheets.write(row, column + 5, vin_no.name, format11)
            sheets.write(row, column + 6, rec.res_name, format11)
            # sheets.write(row, column + 7, vin_no.contact_name.name, format11)   #to be corrcted
            if rec.mobile:
                # sheets.write(row, column + 8, rec.mobile, format11)
                sheets.write(row, column + 8, '******' + rec.mobile[-4:] , format11)
            if invoice.delivery_type:
                select_del_type = dict(invoice.fields_get(allfields=['delivery_type'])['delivery_type']
                                       ['selection'])[invoice.delivery_type]
                sheets.write(row, column + 9, select_del_type, format11)
            if invoice.after_sale_intro:
                select_after_intro = dict(invoice.fields_get(allfields=['after_sale_intro'])['after_sale_intro']
                                          ['selection'])[invoice.after_sale_intro]
                sheets.write(row, column + 10, select_after_intro, format11)
            if invoice.gate_pass_date:
                create_date = fields.Datetime.from_string(invoice.gate_pass_date)
                psf_date_calc = create_date + timedelta(days=3)
                psf_date = psf_date_calc.strftime("%d-%m-%Y")

                sheets.write(row, column + 11, psf_date, format11)
            sheets.write(row, column + 12, rec.stages, format11)
            sheets.write(row, column + 13, rec.survey_percentage, format11)
            an_cl = 15
            for question in questions_list:
                quest_vals = False
                for qst_vals in rec.response_id.user_input_line_ids:
                    if question.id == qst_vals.question_id.id:
                        if qst_vals.question_id.type != 'multiple_choice':
                            rating_star = qst_vals.question_id.labels_ids.filtered(
                                lambda x: x.quizz_mark == qst_vals.quizz_mark)
                            sheets.write(row, column + an_cl, rating_star.value if rating_star else '0 Star', format11)
                            an_cl += 1
                        else:

                            if quest_vals != qst_vals.question_id.id:
                                voc_cus = ''
                                score_rate = len(
                                    rec.response_id.user_input_line_ids.filtered(lambda x: x.question_id.id == question.id))
                                voc_cus += str(score_rate)+ 'Star'
                                sheets.write(row, column + an_cl, voc_cus , format11)
                                quest_vals = question.id
                                an_cl += 1
            for tickets in helpdesk_ticket:
                if tickets.description:
                    sheets.write(row, column + 25, tickets.description, format11)
                voc_cus = ''
                for voc in tickets.sol_ids:
                    if voc.name:
                        value_text = voc.name
                        voc_cus += value_text + ',' + ' '
                sheets.write(row, column + 26, voc_cus, format11)  #from log note
                if tickets.stage_id.name:
                    sheets.write(row, column + 27, tickets.stage_id.name, format11)
                if tickets.close_date:
                    sheets.write(row, column + 28, tickets.close_date, format11)
                if tickets.create_date and tickets.close_date:
                    start_date = fields.Datetime.from_string(tickets.create_date)
                    end_date = fields.Datetime.from_string(tickets.close_date)
                    delta = end_date - start_date
                    ageing = delta.days
                    sheets.write(row, column + 29, ageing, format11)
            row += 1
            sl += 1
        workbook.close()
        output.seek(0)
        data = output.read()
        output.close()
        data = base64.encodebytes(data)
        doc_id = self.env['ir.attachment'].create(
            {'datas': data, 'name': 'Aftersale_psf_report_' + str(datetime.now().date()) + '.xls',
             'datas_fname': 'Aftersale_psf_report_' + str(datetime.now().date()) + '.xls',
             })

        return doc_id
