from odoo import http, api, SUPERUSER_ID, fields, models, sql_db
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import datetime
import contextlib
import uuid
import json
import re



class WebsiteAPIController(http.Controller):

    # @http.route('/api/website_data/create_lead', type='http', auth='public', methods=['OPTIONS'], csrf=False)
    # def options_handler(self, **kwargs):
    #     # Set CORS headers
    #     headers = {
    #         'Access-Control-Allow-Origin': '*',  # Allow requests from any origin
    #         'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',  # Allowed methods
    #         'Access-Control-Allow-Headers': 'Content-Type, Api-Key',  # Allowed headers
    #     }
    #
    #     # Handle preflight OPTIONS request (CORS)
    #     if request.httprequest.method == 'OPTIONS':
    #         return http.Response('', status=200, headers=headers)



    @http.route(['/api/website_data/create_lead'], type='json', auth='public', methods=['POST'], csrf=False )
    def get_website_data(self, **post):
        false_status = False
        api_key = request.httprequest.headers.get('api_key')
        print(api_key, 'api_key')

        # Set CORS headers
        # headers = {
        #     'Access-Control-Allow-Origin': '*',  # Allow requests from any origin
        #     'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',  # Allowed methods
        #     'Access-Control-Allow-Headers': 'Content-Type, Api-Key',  # Allowed headers
        # }
        #
        # # Handle preflight OPTIONS request (CORS)
        # if request.httprequest.method == 'OPTIONS':
        #     return http.Response('', status=200, headers=headers)

        if not api_key:
            return {
                'status': false_status,
                'status_code': 401,
                'message': 'Authorization token is missing'
            }
        user = request.env['res.users'].sudo().search([('web_api_key', '=', api_key.strip())], limit=1)
        print(user, 'useruseruser')

        if not user:
            return {
                'status': false_status,
                'status_code': 401,
                'message': 'Invalid authorization token'
            }
        if user.web_api_expiry_time:
            expiry_time = fields.Datetime.from_string(user.web_api_expiry_time)
            if expiry_time < datetime.now():
                new_api_key, new_expiry = user.generate_web_api_key(user.id)
                return {
                    "status": false_status,
                    "status_code": 403,
                    "message": "Your API key has expired. A new key has been generated.",
                    "new_api_key": new_api_key,
                    "expiry_time": new_expiry
                }
        user_group = user.has_group('website_api_integration.group_website_api')
        if not user_group:
            return {
                'status': false_status,
                'status_code': 403,
                'message': "You do not have permission Access Contact Administrator"
            }
        print("called_website_api")
        request_data = request.jsonrequest.get('params')

        print(request_data,'request_datarequest_data')

        if not request_data:
            return {
                "status": false_status,
                "status_code": 400,
                "message": "Request data is empty"
            }
        website_raw_obj = request.env['website.raw.info'].sudo().create({'request_data': request_data,
                                                                            'request_time': datetime.now(),})


        print(website_raw_obj,'website_raw_obj')
        response, lead_status = self.segregate_data(request_data)

        website_raw_obj.write({
            'response_data': response,
            'response_time': datetime.now(),
            'lead_status': lead_status,
        })

        return{
            "status": True,
            "status_code": 200,
            "data": response
        }


    def segregate_data(self, request_data):
        print(request_data,'request_data')
        response = {}
        lead_status = {}

        for customer_key, customer_data in request_data.items():
            customer_name = customer_key
            try:
                customer_name = customer_data.get('contact_name', customer_key).strip()
                mobile = customer_data.get('mobile', '') or False
                phone = customer_data.get('phone', '') or False
                email_from = customer_data.get('email_from') or False
                source = customer_data.get('source') or False
                street = customer_data.get('street') or False
                city = customer_data.get('city') or False
                country = customer_data.get('country') or False
                model_code = customer_data.get('model_code') or False
                dealer_code = customer_data.get('dealercode') or False
                token = customer_data.get('token') or False
                source_reference = customer_data.get('ticket_id') or False

                dealer_setup_obj = request.env['ars.consolidation.setup'].sudo().search([('dealer_code', '=', dealer_code), ('active', '=', True)], limit=1)

                print(dealer_setup_obj,'dealer_setup_objdealer_setup_obj')
                if not dealer_setup_obj:
                    raise ValidationError("Dealer code not found in consolidated database. Please contact DMS Team.")
                # url = dealer_setup_obj.url_ip.strip()
                # if not url.startswith(('http://', 'https://')):
                #     raise ValidationError("URL must start with 'http://' or 'https://'")

                db_name = dealer_setup_obj.db_name
                username = dealer_setup_obj.user_name
                password = dealer_setup_obj.password
                with contextlib.closing(sql_db.db_connect(db_name).cursor()) as cr:
                    cr.autocommit(True)
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    res_model = env['crm.lead'].sudo()
                    if token:
                        if not dealer_code:
                            response[customer_key] = {"status": "failed",
                                                      "message": "Missing required field: dealercode"}

                            lead_status[customer_key] = 'failed'
                            continue
                        # iftoken provide update the lead

                        lead = res_model.search([('lead_token', '=', token)], limit=1)
                        if not lead:
                            response[customer_key] = {"status": "failed",
                                                       "message": "Token does not match any existing lead"}
                            lead_status[customer_key] = 'failed'
                            continue
                        # Check if the lead has a related sale order
                        sale_order = env['sale.order'].sudo().search([('opportunity_id', '=', lead.id)], limit=1)
                        if sale_order:
                            response[customer_key] = {"status": "failed",
                                                      "message": "This Lead converted to sale order, cannot update"}
                            lead_status[customer_key] = "failed"
                            continue

                        lead_values = {key: value for key, value in customer_data.items() if key not in ['token', 'dealercode']}
                        if 'model_code' in customer_data:
                            product = env['product.product'].sudo().search(
                                [('default_code', '=', model_code)], limit=1)
                            if not product:
                                raise ValueError('Please make sure the model code is belongs to this dealer.')
                            lead_values['vehicle_line'] = [(0, 0, {
                                'product_template_id': product.product_tmpl_id.id,
                                'product_id': product.id,
                                'name': product.product_tmpl_id.name
                            })]

                        lead.write(lead_values)
                        response[customer_key] = {"status": "success", "message": "Lead Updated Successfully",
                                                  "updated": True, "lead_id": lead.crm_sequence, "source_reference": lead.source_reference , "dealer_code": dealer_code}
                        lead_status[customer_key] = "Updated"
                    else:
                        # Create new Lead without token
                        required_fields = ['contact_name', 'source', 'mobile', 'street', 'country', 'city',
                                           'model_code', 'dealercode', 'email_from', 'source_reference']

                        missing_fields = [field for field in required_fields if not customer_data.get(field)]

                        if missing_fields:
                            response[customer_key] = {
                                "status": "failed",
                                "message": f"Missing required fields: {', '.join(missing_fields)}"
                            }
                            lead_status[customer_key] = 'Failed'
                            continue

                        cleaned_mobile = self.format_mobile_number(mobile=mobile)
                        print(cleaned_mobile, 'cleaned_mobile')
                        if not cleaned_mobile.isdigit():
                            raise Exception ('Enter a valid number format.')
                        partner_obj = env['res.partner'].sudo().search([('name', '=', customer_name), '|', ('mobile', '=',  cleaned_mobile), ('email', '=',  email_from)], limit=1)
                        print(partner_obj,'partner_objpartner_obj')
                        country_obj = env['res.country'].sudo().search([('name', '=', country)], limit=1)

                        if not partner_obj:
                            created_partner = env['res.partner'].sudo().create({
                                "name": customer_name,
                                "mobile": cleaned_mobile,
                                "phone": phone or False,
                                "email": email_from,
                                "city": city,
                                "country_id": country_obj.id
                            })
                        else:
                            created_partner = partner_obj

                        # source_obj = env['utm.source'].sudo().search([('name', 'ilike', 'Digital Activity')], limit=1)
                        search_terms = ['%BYD Digital%', '%BYDDigital%']
                        query = "SELECT * FROM utm_source WHERE name ILIKE ANY (%s::text[]) LIMIT 1;"
                        env.cr.execute(query, (search_terms,))  # Pass list directly, not tuple
                        source_obj = env.cr.fetchone()
                        search_medium = ['%BYD Web Portal%', '%BYDWebPortal%']
                        query_medium = "SELECT * FROM utm_medium WHERE name ILIKE ANY (%s::text[]) LIMIT 1;"
                        env.cr.execute(query_medium, (search_medium,))  # Pass list directly, not tuple
                        medium_obj = env.cr.fetchone()
                        product = env['product.product'].sudo().search([('default_code', '=', model_code)], limit=1)
                        if not product:
                            raise ValueError('Please make sure the model code is belongs to this dealer.')
                        if dealer_code:
                            company_id = env['res.company'].search([('dealer_code', '=', dealer_code)], limit=1)
                            team_type = env['crm.team'].search([('team_type', '=', 'sales'),('company_id', '=', company_id.id)], limit=1)
                            team_branch = env['branch.master.company'].search([('company_id', '=', company_id.id)])
                            # Apply filtered condition with space removal and case-insensitive match
                            team_branch_id = team_branch.filtered(lambda b: street.replace(" ", "").lower() == b.name.replace(" ", "").lower())[:1]

                        unique_token = str(uuid.uuid4())
                        new_lead = res_model.sudo().create({
                            'company_type': "individual",
                            'partner_id': created_partner.id,
                            'email_from': email_from,
                            'contact_name': customer_name,
                            'source_id': source_obj[0] if source_obj else None,
                            'medium_id': medium_obj[0] if medium_obj else None,
                            'mobile': cleaned_mobile,
                            'street': customer_data.get('street'),
                            'city': city,
                            'lead_token': unique_token,
                            'country_id': country_obj.id,
                            'phone': phone or False,
                            'model_id': product.product_tmpl_id.id,
                            'zip': customer_data.get('zip') or False,
                            'source_reference': source_reference,
                            'team_id': team_type.id,
                            'company_id': company_id.id,
                            'branch_id': team_branch_id.id,
                            'vehicle_line': [(0, 0, {
                                'product_template_id': product.product_tmpl_id.id,
                                'product_id': product.id,
                                'name': product.product_tmpl_id.name
                            })]
                        })

                        print(new_lead,'new_leadnew_lead')

                        response[customer_key] = {"status": "success",
                                                  "lead_id": new_lead.crm_sequence,
                                                  "source_reference": new_lead.source_reference,
                                                  "token": new_lead.lead_token,
                                                  "dealer_code": dealer_code}

                        lead_status[customer_key] = "Created"





            except Exception as e:
                response[customer_key] = {"status": "error", "message": str(e)}
                lead_status[customer_key] = "error"

        return response, lead_status

    @staticmethod
    def format_mobile_number(mobile: str) -> str:
        try:
            # Remove all non-digit characters
            mobile = re.sub(r"[^\d]", "", mobile)

            # Remove country code or leading zero
            if mobile.startswith("91") and len(mobile) > 10:
                mobile = mobile[2:]
            elif mobile.startswith("0") and len(mobile) > 10:
                mobile = mobile[1:]

            # Ensure it's a valid 10-digit number
            if len(mobile) != 10:
                raise ValueError("Invalid mobile number format")

            return mobile

        except Exception as e:
            return f"Error: {str(e)}"  # Returning error message instead of raising
