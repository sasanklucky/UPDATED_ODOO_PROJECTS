import json
import logging
from odoo import http
from odoo.http import request
from odoo import fields, http, SUPERUSER_ID

_logger = logging.getLogger(__name__)
import odoo.addons.survey.controllers.main as main


class WebsiteSurvey(main.WebsiteSurvey):
    @http.route(['/survey/submit/<model("survey.survey"):survey>'], type='http', methods=['POST'], auth='public',
                website=True)
    def submit(self, survey, **post):
        _logger.debug('Incoming data: %s', post)
        page_id = int(post['page_id'])
        questions = request.env['survey.question'].search([('page_id', '=', page_id)])

        # Answer validation
        errors = {}
        for question in questions:
            answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
            errors.update(question.validate_question(post, answer_tag))

        ret = {}
        if len(errors):
            # Return errors messages to webpage
            ret['errors'] = errors
        else:
            # Store answers into database
            try:
                user_input = request.env['survey.user_input'].sudo().search([('token', '=', post['token'])], limit=1)
            except KeyError:  # Invalid token
                return request.render("website.403")
            user_id = request.env.user.id if user_input.type != 'link' else SUPERUSER_ID

            for question in questions:
                answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
                request.env['survey.user_input_line'].sudo(user=user_id).save_lines(user_input.id, question, post,
                                                                                    answer_tag)

            go_back = post['button_submit'] == 'previous'
            next_page, _, last = request.env['survey.survey'].next_page(user_input, page_id, go_back=go_back)
            vals = {'last_displayed_page_id': page_id}
            if next_page is None and not go_back:
                vals.update({'state': 'done'})
                mail_activity_model = request.env['mail.activity']
                activity_id = mail_activity_model.search([('response_id', '=', user_input.id)])
                if activity_id:
                    questions = activity_id.response_id.user_input_line_ids.mapped('question_id')
                    # question_marks = questions.mapped('labels_ids.quizz_mark')
                    # score = activity_id.response_id.quizz_score / sum(question_marks) * 100
                    score = activity_id.response_id.quizz_score / (len(questions) * 100) * 100
                    param = request.env['ir.config_parameter'].sudo()
                    survey_percentage = param.get_param('ars_mail_survey.survey_percentage')

                    if score < float(survey_percentage):
                        mail_activity_model.create_helpdesk_ticket(activity_id)
                    #     vals = {
                    #         'name': 'Post Sales Follow up Complaint' if activity_id.invoice_type == 'sales' else 'Post Service Follow up Complaint' if activity_id.invoice_type == 'after_sales' else ' ',
                    #         'user_id': activity_id.user_id.id,
                    #         'partner_id': request.env['res.partner'].browse(activity_id.res_id).id,
                    #         'partner_email': request.env['res.partner'].browse(activity_id.res_id).email,
                    #         'activity_source_id' : activity_id.id
                    #     }
                    #     request.env['helpdesk.ticket'].sudo().create(vals)
                    #     activity_id.write({'stages':'ticket_created'})
                    else:
                        activity_id.write({'stages': 'survey_done'})
            else:
                vals.update({'state': 'skip'})
            user_input.sudo(user=user_id).write(vals)
            ret['redirect'] = '/survey/fill/%s/%s' % (survey.id, post['token'])
            if go_back:
                ret['redirect'] += '/prev'
        return json.dumps(ret)
