from odoo import models, fields
import io
import base64
from datetime import datetime, timedelta

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ARSMailActivity(models.Model):
    _inherit = "mail.activity"

    def export_service_xls(self, data):
        question_list = []
        # for record in data:
        #     questions = record.response_id.user_input_line_ids
        #     for rec in questions:
        #         question_list.append(rec)
        param = self.env['ir.config_parameter'].sudo()
        postsale_survey_id = param.get_param('ars_mail_survey.post_sale_survey_id')
        postsale_survey = self.env['survey.survey'].browse(int(postsale_survey_id))
        for page in postsale_survey.page_ids:
            question_list = page.question_ids

        questions_list = question_list
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheets = workbook.add_worksheet('After Service Report')
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
        # sheets.merge_range(0, 0, 2, 23, 'After-Service PSF Report', format0)
        sheets.write(1, 1, 'Month', format21)
        sheets.write(1, 0, 'Customer Name', format21)
        sheets.write(1, 2, 'Conatct Person Name', format21)
        sheets.write(1, 3, 'VIN', format21)
        sheets.write(1, 4, 'Registration Number', format21)
        sheets.write(1, 5, 'RO Number', format21)
        sheets.write(1, 6, 'RO Type', format21)
        sheets.write(1, 7, 'RO Creation Date', format21)
        sheets.write(1, 8, 'RO Closed Date', format21)
        sheets.write(1, 9, 'Delivery Date', format21)
        sheets.write(1, 10, 'Model', format21)
        sheets.write(1, 11, 'Model Variant', format21)
        sheets.write(1, 12, 'Mileage Out', format21)
        sheets.write(1, 13, 'Repeat Repair Yes/No', format21)
        sheets.write(1, 14, 'Voice of Customer', format21)
        sheets.write(1, 15, 'SA Name', format21)
        sheets.write(1, 16, 'Pick Up and Drop', format21)
        sheets.write(1, 17, 'PSF Date', format21)
        sheets.write(1, 18, 'Contact Status', format21)
        if questions_list:
            q_rw = 19
            for quest in questions_list:
                # print(quest.question)
                sheets.write(1, q_rw, quest.question, format21)
                q_rw += 1
        sheets.write(1, 31, 'Satisfaction Status', format21)
        sheets.write(1, 32, 'Voice of Customer', format21)
        sheets.write(1, 33, 'Complaint Classification |', format21)
        sheets.write(1, 34, 'Complaint Classification ||', format21)
        sheets.write(1, 35, 'CRM Remarks', format21)
        sheets.write(1, 36, 'Solution Provided', format21)
        sheets.write(1, 37, 'Person Responsible', format21)
        sheets.write(1, 38, 'Complaint Close Date', format21)
        sheets.write(1, 39, 'Ageing', format21)
        sheets.write(1, 40, 'Model group', format21)

        row = 2
        column = 0
        sl = 0

        for recs in data:
            date_object = fields.Date.from_string(recs.date_deadline)
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
            invoice = recs.invoice_id
            helpdesk_ticket = self.env['helpdesk.ticket'].search([('activity_source_id', '=', recs.id)])

            sheets.write(row, column, recs.res_name, format11)
            sheets.write(row, column + 1, month_word, format11)
            if invoice.reg_no.contact_name.name:
                sheets.write(row, column + 2, invoice.reg_no.contact_name.name, format11)
            sheets.write(row, column + 3, invoice.reg_no.vin_sn, format11)
            sheets.write(row, column + 4, invoice.reg_no.license_plate, format11)
            sheets.write(row, column + 5, invoice.origin, format11)
            if recs.psf_order_id.service_options.name:
                sheets.write(row, column + 6, recs.psf_order_id.service_options.name, format11)
            if recs.psf_order_id.appointment_date:
                appoint_date = datetime.strptime(recs.psf_order_id.appointment_date, '%Y-%m-%d %H:%M:%S')
                appointment_date = appoint_date.strftime('%d-%m-%Y')
                sheets.write(row, column + 7, appointment_date, format11)
            inv_date = datetime.strptime(invoice.create_date, '%Y-%m-%d %H:%M:%S')
            inv_create_date = inv_date.strftime('%d-%m-%Y')
            sheets.write(row, column + 8, inv_create_date, format11)
            # sheets.write(row, column + 8, invoice.create_date, format11)

            if invoice.reg_no and invoice.reg_no.model_id and invoice.reg_no.model_id.master_id:
                sheets.write(row, column + 40, invoice.reg_no.model_id.master_id.name, format11)
            else:
                sheets.write(row, column + 40, '', format11)

            if invoice.gate_pass_date:
                gate_date = datetime.strptime(invoice.gate_pass_date, '%Y-%m-%d')
                gate_pass_date = gate_date.strftime('%d-%m-%Y')
                sheets.write(row, column + 9, gate_pass_date, format11)
            sheets.write(row, column + 10, invoice.reg_no.model_id.name, format11)
            color = invoice.model.attribute_value_ids.filtered(
                lambda x: x.attribute_id.name == 'colour' or x.attribute_id.name == 'Exterior Color').ids
            if color:
                color_list = []
                for i in color:
                    attribute = self.env['product.attribute.value'].sudo().search([('id', '=', i)])
                    color_list.append(attribute.name)
                color_car = ', '.join(str(attribute) for attribute in color_list)
                sheets.write(row, column + 11, color_car, format11)
            if invoice.kilometer_out:
                sheets.write(row, column + 12, invoice.kilometer_out, format11)
            if len(invoice.reg_no.service_ids) > 2:
                if invoice.reg_no.service_ids[-2].servicetype == invoice.reg_no.service_ids[-1].servicetype:
                    if (invoice.reg_no.service_ids[-2].order.appointment_date
                            and invoice.reg_no.service_ids[-1].order.appointment_date):
                        date_1 = datetime.strptime(invoice.reg_no.service_ids[-2].order.appointment_date,
                                                   '%Y-%m-%d %H:%M:%S')
                        date_2 = datetime.strptime(invoice.reg_no.service_ids[-1].order.appointment_date,
                                                   '%Y-%m-%d %H:%M:%S')
                        final_date = ((date_2 - date_1).days)
                        if final_date < 15:
                            sheets.write(row, column + 13, 'YES', format11)
                        else:
                            sheets.write(row, column + 13, 'NO', format11)
                    else:
                        sheets.write(row, column + 13, 'NO', format11)
                else:
                    sheets.write(row, column + 13, 'NO', format11)
            else:
                sheets.write(row, column + 13, 'NO', format11)
            voc_cus = ''
            for voc in recs.psf_order_id.customer_voice_sale:
                if voc.name:
                    value_text = voc.name
                    voc_cus += value_text + ',' + ' '
            sheets.write(row, column + 14, voc_cus, format11)
            sheets.write(row, column + 15, invoice.user_id.name, format11)
            if recs.psf_order_id.pick_up_drop:
                sheets.write(row, column + 16, recs.psf_order_id.pick_up_drop, format11)
            if invoice.gate_pass_date:
                create_date = fields.Datetime.from_string(invoice.gate_pass_date)
                psf_date_calc = create_date + timedelta(days=3)
                psf_date = psf_date_calc.strftime("%d-%m-%Y")
                sheets.write(row, column + 17, psf_date, format11)
            sheets.write(row, column + 18, recs.stages, format11)
            an_cl = 19
            for question in questions_list:
                quest_vals = False
                for qst_vals in recs.response_id.user_input_line_ids:
                    # print('qst_valssss', qst_vals)
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
                                    recs.response_id.user_input_line_ids.filtered(
                                        lambda x: x.question_id.id == question.id))
                                voc_cus += str(score_rate) + 'Star' + ' ' + ','
                                sheets.write(row, column + an_cl, voc_cus, format11)
                                quest_vals = question.id
                                an_cl += 1
            sheets.write(row, column + 31, recs.survey_percentage, format11)
            questions_record = recs.response_id.user_input_line_ids
            val_text = ''
            for rec in questions_record:
                if rec.value_text:
                    value_text = rec.value_text
                    val_text += value_text + ','
            sheets.write(row, column + 32, val_text, format11)
            # print('an+%%%%%%%%%%%%%%%%%%', an + 5)
            categ_text = ''
            for ticket in helpdesk_ticket:
                if ticket.category_i_id.name:
                    categ_id_name = ticket.category_i_id.name
                    categ_text += categ_id_name + ','
                sheets.write(row, column + 33, categ_text, format11)
                if ticket.category_ii_id.name:
                    sheets.write(row, column + 34, ticket.category_ii_id.name, format11)
                if ticket.description:
                    sheets.write(row, column + 35, ticket.description, format11)

                voc_cus = ''
                for voc in ticket.sol_ids:
                    if voc.name:
                        value_text = voc.name
                        voc_cus += value_text + ',' + ' '
                sheets.write(row, column + 36, voc_cus, format11)

                if ticket.user_id.name:
                    sheets.write(row, column + 37, ticket.user_id.name, format11)
                if ticket.close_date:
                    date_close = datetime.strptime(ticket.close_date, '%Y-%m-%d')
                    close_date = date_close.strftime('%d-%m-%Y')
                    sheets.write(row, column + 38, close_date, format11)
                if ticket.create_date and ticket.close_date:
                    start_date = fields.Datetime.from_string(ticket.create_date)
                    end_date = fields.Datetime.from_string(ticket.close_date)
                    delta = end_date - start_date
                    ageing = delta.days
                    sheets.write(row, column + 39, ageing, format11)
            row += 1
            sl += 1
        workbook.close()
        output.seek(0)
        data = output.read()
        output.close()
        data = base64.encodebytes(data)
        doc_id = self.env['ir.attachment'].create(
            {'datas': data, 'name': 'Afterservice_psf_report_' + str(datetime.now().date()) + '.xls',
             'datas_fname': 'Afterservice_psf_report_' + str(datetime.now().date()) + '.xls',
             })
        return doc_id
