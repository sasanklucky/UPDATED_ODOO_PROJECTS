from odoo import api, fields, models, _
from odoo.exceptions import AccessError
from lxml import etree
from openerp.osv.orm import setup_modifiers


def accessible_menus_models_users(self):
    current_menu_id = self.env.context.get('current_menu_id')
    # print(current_menu_id)
    context = self.env.context
    # print(context, 'krishna')
    current_menu_id = context.get('current_menu_id')
    if 'params' in self.env.context:
        template_action_id = self.env.context['params'].get('action')
        current_window_model = self.env['ir.actions.act_window'].search(
            [('id', '=', template_action_id)]).res_model if template_action_id else self._name
        config_group_records = self.env['res.config.settings'].sudo().search([], order='create_date desc', limit=1)
        user = self.env['res.users'].browse(self.env.uid)
        # Menus which we need to restrict
        genral_sales_menus = self.env['master.menu.restriction'].search([('general_sale_bool', 'in', [True])])
        aftersale_sales_menus = self.env['menu.restrict.aftersales'].search([('after_sales_bool', 'in', [True])])
        vehicle_sales_menus = self.env['menu.restrict.vehiclesales'].search([('vehicle_sale_bool', 'in', [True])])
        others_sales_menus = self.env['menu.restrict.othersales'].search([('others_sale_bool', 'in', [True])])
        # Storing the menus for Checking
        genral_menu_group = [menu.id for menus in genral_sales_menus for menu in menus.general_sales_menus]
        aftersale_menu_group = [menu.id for menus in aftersale_sales_menus for menu in
                                menus.after_sales_menu]
        vehicle_menu_group = [menu.id for menus in vehicle_sales_menus for menu in menus.vehicle_sales_menus]
        other_menu_group = [menu.id for menus in others_sales_menus for menu in
                            menus.others_sales_menus]
        g_sale_model = [models.model for model in genral_sales_menus for models in model.g_sale_model]
        a_sale_model = [models.model for model in aftersale_sales_menus for models in model.a_sale_model]
        v_sale_model = [models.model for model in vehicle_sales_menus for models in model.v_sale_model]
        o_sale_model = [models.model for model in others_sales_menus for models in model.o_sale_model]
        group_dic = {}
        group_dic['genral_sales'] = [{"user_in_groups":
                                          any(user in group.users for groups in config_group_records for group in
                                              groups.gsale_res_gr_ids if groups.gsale_restrict_master_data),
                                      "menus_in_group": genral_menu_group, "models_in_group": g_sale_model,
                                      "boolean_from_config": any(
                                          groups.gsale_restrict_master_data for groups in config_group_records),
                                      "boolean_from_setup": any(
                                          menus.general_sale_bool for menus in genral_sales_menus)}]
        group_dic['after_sales'] = [{"user_in_groups":
                                         any(user in group.users for groups in config_group_records for group in
                                             groups.asale_res_gr_ids if groups.asale_restrict_master_data),
                                     "menus_in_group": aftersale_menu_group, "models_in_group": a_sale_model,
                                     "boolean_from_config": any(
                                         groups.asale_restrict_master_data for groups in config_group_records),
                                     "boolean_from_setup": any(
                                         menus.after_sales_bool for menus in aftersale_sales_menus)}]
        group_dic['vehicle_sales'] = [{"user_in_groups":
                                           any(user in group.users for groups in config_group_records for group in
                                               groups.vsale_res_gr_ids if groups.vsale_restrict_master_data),
                                       "menus_in_group": vehicle_menu_group, "models_in_group": v_sale_model,
                                       "boolean_from_config": any(
                                           groups.vsale_restrict_master_data for groups in config_group_records),
                                       "boolean_from_setup": any(
                                           menus.vehicle_sale_bool for menus in vehicle_sales_menus)}]
        group_dic['other_sales'] = [{"user_in_groups":
                                         any(user in group.users for groups in config_group_records for group in
                                             groups.others_res_gr_ids if groups.other_restrict_master_data),
                                     "menus_in_group": other_menu_group, "models_in_group": o_sale_model,
                                     "boolean_from_config": any(
                                         groups.other_restrict_master_data for groups in config_group_records),
                                     "boolean_from_setup": any(menus.others_sale_bool for menus in others_sales_menus)}]
        # print(group_dic, 'group_dic')
        return [group_dic, current_window_model, template_action_id]


class UpdateMasterDataRestriction(models.TransientModel):
    _name = "master.data.restriction.wizard"

    categ_id = fields.Many2one('product.category', string='Product Category')
    model_id = fields.Many2one('product.template', string='Model')
    product_name = fields.Char('Product Name')
    shell_location = fields.Many2many('shell.location', string="Shelf Location", track_visibility='always')

    @api.model
    def _get_default_category(self):
        # Get the active product template ID from the context
        active_product_template_id = self.env.context.get('active_id')
        if active_product_template_id:
            # Retrieve the active product template record
            product_template = self.env['product.template'].browse(active_product_template_id)
            # Return the current category of the product template as default value
            return product_template.categ_id.id
        return False

    def action_master_data_res(self):
        # Add logic to restrict action based on user
        # if not self.env.user.has_group('base.group_system'):
        #     raise AccessError("You are not allowed to perform this action.")

        active_product_template_id = self.env.context.get('active_id')
        if active_product_template_id:
            product_template = self.env['product.template'].browse(active_product_template_id)
            values = {
                'categ_id': self.categ_id.id,
                'model_id': self.model_id.id,
            }
            # Check if shell_location is explicitly modified in the wizard
            if 'default_shell_location' in self.env.context:
                # Update shell_location only if modified in the wizard
                values['shell_location'] = [(6, 0, self.shell_location.ids)] if self.shell_location else False

            product_template.write(values)
        return {'type': 'ir.actions.act_window_close'}


class masterDatarestrictionByproductTemplate(models.Model):
    _inherit = "product.template"

    def action_to_open_wiz(self):
        view = self.env.ref('ac_master_data_restriction.master_data_restriction_wizard_form')
        shell_location_ids = [(6, 0, self.shell_location.ids)] if self.shell_location else []
        return {
            'name': _('Master data'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'master.data.restriction.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'context': {
                'default_categ_id': self.categ_id.id,
                'default_product_name': self.name,
                'default_model_id': self.model_id.id,
                'default_shell_location': shell_location_ids,
            },
            'target': 'new',
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        template_result = super(masterDatarestrictionByproductTemplate, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        doc = etree.XML(template_result['arch'])
        current_menu_id = self.env.context.get('current_menu_id')
        # print(self.env.context)
        # Fetch fields and set default attributes and options
        fields = self.env['product.template'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = ['price', 'pricelist_item_ids', 'sequence', 'pricelist_id']
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, template_result['fields'][field_name])

        # Flag to indicate unrestricted access
        unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_not_users_and_not_menus,'1111111111111111111')
        models_to_restrict = {'models_need_restrict':list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False,}
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict['models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
                set(model_item for value_list in
                    filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                    entry in value_list if
                    'models_in_group' in entry for model_item in entry['models_in_group']
                    )),'menus_in_group': False, 'user_in_groups': False, }
        print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             # Apply view restrictions if the user does not have full access
        #             if not users_access_menus[0]:
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     # Restrict specific fields
        #                     restricted_fields = ['price', 'pricelist_item_ids', 'sequence', 'pricelist_id']
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, template_result['fields'][field_name])
        #             break
        #         else:
        #             print('NO MENU ID OR MODEL ACCESS')
        #     else:
        #         print('NO MODEL PRESENT OR MENU ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        template_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return template_result


class ResUserCreateRestrict(models.Model):
    _inherit = 'res.users'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_user_result = super(ResUserCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                  submenu=submenu)
        doc = etree.XML(res_user_result['arch'])
        current_menu_id = self.env.context.get('current_menu_id')

        # Retrieve fields and set default attributes and options
        fields = self.env['res.users'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_user_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 if view_type == 'form':
        #                     restricted_fields = ['shell_location']
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_user_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')

        # Update the view architecture
        res_user_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_user_result


class ResCompanyCreateRestrict(models.Model):
    _inherit = 'res.company'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_company_result = super(ResCompanyCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        doc = etree.XML(res_company_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.company'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return res_company_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_company_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_company_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_company_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_company_result


class FleetVehicleCreateRestriction(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        fleet_veh_result = super(FleetVehicleCreateRestriction, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                   submenu=submenu)
        doc = etree.XML(fleet_veh_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['fleet.vehicle'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            # doc.set('create', 'false')
            doc.set('edit', 'true')
            if view_type == 'form':
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, fleet_veh_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, fleet_veh_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        fleet_veh_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return fleet_veh_result


class SourceMenuCreateRestriction(models.Model):
    _inherit = "utm.source"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(SourceMenuCreateRestriction, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['utm.source'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class UtmMediumCreateMenuRestriction(models.Model):
    _inherit = 'utm.medium'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(UtmMediumCreateMenuRestriction, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['utm.medium'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class ServiceOptionCreateMenuRestriction(models.Model):
    _inherit = 'service.options'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(ServiceOptionCreateMenuRestriction, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['service.options'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class ServiceTypeCreateMenuRestrict(models.Model):
    _inherit = 'service.type'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(ServiceTypeCreateMenuRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['service.type'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class ServiceSetupManualMenuCreateRestrict(models.Model):
    _inherit = 'service.setup.manual'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(ServiceSetupManualMenuCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['service.setup.manual'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class SaleOrderRestrictMasterData(models.Model):
    _inherit = 'sale.order'

    # sale_crm.sale_view_inherit123
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(SaleOrderRestrictMasterData, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['sale.order'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}
        user = self.env['res.users'].browse(int(self.env.context.get('uid')))
        def apply_restriction():
            # doc.set('create', 'true')
            # doc.set('edit', 'true')
            if view_type == 'form':
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'no_create': True, 'no_edit': True, 'no_create_edit': True, 'no_open': True}")
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])
        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '000000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_not_users_and_not_menus,'1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ),'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                if user:
                    if user.has_group("ac_master_data_restriction.group_custom_enable_create_button"):
                        doc.set('create', 'true')
                    else:
                        doc.set('create', 'false')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                if user:
                    if user.has_group("ac_master_data_restriction.group_custom_enable_create_button"):
                        doc.set('create', 'true')
                    else:
                        doc.set('create', 'false')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ),'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')

        # Update the view architecture
        if user:
            if user.has_group("ac_master_data_restriction.group_custom_enable_create_button"):
                doc.set('create', 'true')
            else:
                doc.set('create', 'false')
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class ProductTemplateCreateMenuRestriction(models.Model):
    _inherit = 'product.product'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        # Fetch the base view
        result = super(ProductTemplateCreateMenuRestriction, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        doc = etree.XML(result['arch'])
        context = self.env.context
        current_menu_id = context.get('current_menu_id')

        # Fetch fields and initialize default attributes and options
        fields = self.env['product.product'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Get access-related information
        groups_data = accessible_menus_models_users(self=self)
        group_dic = groups_data[0] if groups_data else {}
        current_window_model = groups_data[1] if groups_data else ''

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                restricted_fields = ['price', 'pricelist_item_ids', 'sequence', 'pricelist_id']
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Check access permissions
        # for department, access_menus in group_dic.items():
        #     if unrestricted_access:
        #         break  # Skip further checks if unrestricted access is granted
        #
        #     if current_window_model and current_menu_id:
        #         # If user has unrestricted access for this department
        #         if current_window_model in access_menus[2] and current_menu_id in access_menus[1]:
        #             if access_menus[0]:  # Full access
        #                 unrestricted_access = True
        #                 break  # No restriction needed; exit the loop
        #             elif current_window_model in access_menus[2] and not access_menus[1] and not access_menus[0]:
        #             # Restrict view if no full access
        #                 apply_restriction()
        #             else:
        #                 apply_restriction()
        #         elif access_menus[0] and current_window_model in access_menus[2]:
        #             doc.set('create', 'true')
        #             doc.set('edit', 'true')
        #             unrestricted_access = True
        #         # Restrict if model access not granted
        #         elif not access_menus[0] and current_window_model in access_menus[2]:
        #             doc.set('create', 'false')
        #             doc.set('edit', 'false')
        #     elif not current_window_model:
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # If unrestricted_access is True, reset any restrictions
        # if unrestricted_access:
        #     doc.set('create', 'true')
        #     doc.set('edit', 'true')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class ProductPricelistMenuCreateRestrict(models.Model):
    _inherit = 'product.pricelist'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(ProductPricelistMenuCreateRestrict, self).fields_view_get(view_id=view_id,
                                                                                 view_type=view_type,
                                                                                 toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['product.pricelist'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        print(menus_to_restrict, '123')
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class MenuRestrictionPurchase(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(MenuRestrictionPurchase, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['purchase.order'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            if view_type == 'form':
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'no_create': True, 'no_edit': True, 'no_create_edit': True, 'no_open': True}")
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class CrmLeadRestrictNoOpen(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        result = super(CrmLeadRestrictNoOpen, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['crm.lead'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            if view_type == 'form':
                print('inside form')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'no_create': True, 'no_edit': True, 'no_create_edit': True, 'no_open': True}")
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = ['medium_id', 'source_id', 'title', 'user_id', 'campaign_id',
        #                                          'regn_no',
        #                                          'partner_id', 'main_process_id', 'tag_ids',
        #                                          'delivery_service_advisor',
        #                                          'country_id', 'state_id',
        #                                          'crm_lead_stage']  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'no_open': True, 'no_create': True}")
        #                                 # Apply attributes
        #                                 # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                         else:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


#
class CrmLostLeadIdRestrictNoOpen(models.TransientModel):
    _inherit = 'crm.lead.lost'

    @api.model
    def fields_view_get(self, view_id="crm.crm_lead_lost_view_form", view_type='form', toolbar=False, submenu=False):
        result = super(CrmLostLeadIdRestrictNoOpen, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])
        if view_type == 'form':
            print('Heloooooo')
            for node in doc.xpath("//field[@name='lost_reason_id']"):
                node.set('options',
                         "{'no_create': True, 'no_edit': True, 'no_create_edit': True, 'no_open': True}")
                setup_modifiers(node, result['fields']['lost_reason_id'])
            for node in doc.xpath("//field[@name='child_lost_reason']"):
                node.set('options',
                         "{'no_create': True, 'no_edit': True, 'no_create_edit': True, 'no_open': True}")
                setup_modifiers(node, result['fields']['child_lost_reason'])
        result['arch'] = etree.tostring(doc)
        return result


class ArsSaleWarranty(models.Model):
    _inherit = 'ars.sale.warranty'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(ArsSaleWarranty, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['ars.sale.warranty'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return result


class ResPartnerCreateRestrict(models.Model):
    _inherit = 'res.partner'

    restrict_name_chnage = fields.Boolean("Name Change", compute="_compute_boolean", default=False)

    #
    @api.onchange('name')
    def _compute_boolean(self):
        print('function')
        user = self.env['res.users'].browse(self.env.uid)
        for rec in self:
            if rec.id:
                sale_order = self.env['sale.order'].search([('partner_id.id', '=', rec.id)])
                purchase_order = self.env['purchase.order'].search([('partner_id.id', '=', rec.id)])
            else:
                sale_order = self.env['sale.order'].search([('partner_id.name', '=', rec.name)])
                purchase_order = self.env['purchase.order'].search([('partner_id.name', '=', rec.name)])
            # group_dic = {}
            config_group_records = self.env['res.config.settings'].sudo().search([], order='create_date desc', limit=1)
            keys_to_attrs = {
                'genral_sales': ('gsale_res_gr_ids', 'gsale_restrict_master_data'),
                'after_sales': ('asale_res_gr_ids', 'asale_restrict_master_data'),
                'vehicle_sales': ('vsale_res_gr_ids', 'vsale_restrict_master_data'),
                'other_sales': ('others_res_gr_ids', 'other_restrict_master_data')
            }

            # Use dictionary comprehension to build the group_dic
            group_dic = {
                key: [
                    any(user in group.users for groups in config_group_records for group in getattr(groups, attrs[0])),
                    getattr(user.company_id, attrs[1])
                ]
                for key, attrs in keys_to_attrs.items()
            }

            print(group_dic, 'keys_to_attrs')
            checking_access = []
            for department, access in group_dic.items():
                if access[1]:
                    if access[0]:
                        checking_access.append(access[1])
            print(any(checking_access), checking_access)
            if (sale_order or purchase_order) and any(checking_access):
                rec.restrict_name_chnage = False
            elif (not sale_order or not purchase_order) and any(checking_access):
                rec.restrict_name_chnage = False
            else:
                rec.restrict_name_chnage = True
                # raise ValidationError(_("Invalid User Access. Please check."))

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_partner_result = super(ResPartnerCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        doc = etree.XML(res_partner_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.partner'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0
        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_partner_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        # print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        print(menus_to_restrict, 'userT')
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        print(menus_to_restrict, 'User F')
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_partner_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_partner_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_partner_result


class ResPartnerTitleCreateRestrict(models.Model):
    _inherit = 'res.partner.title'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_partner_title_result = super(ResPartnerTitleCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        doc = etree.XML(res_partner_title_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.partner.title'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_partner_title_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_partner_title_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_partner_title_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_partner_title_result


class ResPartnerCategoryCreateRestrict(models.Model):
    _inherit = 'res.partner.category'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_partner_category_result = super(ResPartnerCategoryCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                              submenu=submenu)
        doc = etree.XML(res_partner_category_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.partner.category'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_partner_category_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_partner_category_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_partner_category_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_partner_category_result


class ResPartnerBankCreateRestrict(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_partner_bank_result = super(ResPartnerBankCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                          submenu=submenu)
        doc = etree.XML(res_partner_bank_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.partner.bank'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_partner_bank_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_partner_bank_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_partner_bank_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_partner_bank_result


class ResBankCreateRestrict(models.Model):
    _inherit = 'res.bank'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_bank_result = super(ResBankCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                  submenu=submenu)
        doc = etree.XML(res_bank_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.bank'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_bank_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_bank_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_bank_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_bank_result


class ResCountryCreateRestrict(models.Model):
    _inherit = 'res.country'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_country_result = super(ResCountryCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        doc = etree.XML(res_country_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.country'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_country_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_country_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_country_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_country_result


class ResCountryStateCreateRestrict(models.Model):
    _inherit = 'res.country.state'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_cou_state_result = super(ResCountryStateCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
        doc = etree.XML(res_cou_state_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.country.state'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_cou_state_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_cou_state_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_cou_state_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_cou_state_result


class ResCountryGroupCreateRestrict(models.Model):
    _inherit = 'res.country.group'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_cou_group_result = super(ResCountryGroupCreateRestrict, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
        doc = etree.XML(res_cou_group_result['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['res.country.group'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_cou_group_result['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_cou_group_result['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_cou_group_result['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_cou_group_result


class StockPickingRestriction(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_stock_picking = super(StockPickingRestriction, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                    submenu=submenu)
        doc = etree.XML(res_stock_picking['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['stock.picking'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            if view_type == 'form':
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_stock_picking['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_stock_picking['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')

        # Update the view architecture
        res_stock_picking['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_stock_picking


class productUomRestriction(models.Model):
    _inherit = 'product.uom'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res_product_uom = super(productUomRestriction, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                  submenu=submenu)
        doc = etree.XML(res_product_uom['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['product.uom'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, res_product_uom['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, res_product_uom['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        res_product_uom['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return res_product_uom


class AccessRightsWizard(models.TransientModel):
    _name = 'access.rights.wizard'

    @api.model
    def grant_all_access_rights(self):
        models = self.env['ir.model'].search([])
        group_user = self.env.ref('base.group_user')

        for model in models:
            self.env['ir.model.access'].create({
                'name': f'access_{model.model}',
                'model_id': model.id,
                'group_id': group_user.id,
                'perm_read': True,
                'perm_write': True,
                'perm_create': True,
                'perm_unlink': True,
            })


class updateStockOnHandQty(models.TransientModel):
    _inherit = 'stock.change.product.qty'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        stock_on_hand_qty = super(updateStockOnHandQty, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                    submenu=submenu)
        doc = etree.XML(stock_on_hand_qty['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['stock.change.product.qty'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, stock_on_hand_qty['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, stock_on_hand_qty['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        stock_on_hand_qty['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return stock_on_hand_qty


class CrmLostReason(models.Model):
    _inherit = "crm.lost.reason"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        crm_lost_reason = super(CrmLostReason, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                  submenu=submenu)
        doc = etree.XML(crm_lost_reason['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['crm.lost.reason'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, crm_lost_reason['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Loop through groups and apply restrictions
        # for department, users_access_menus in group_dic.items():
        #     if current_window_model and current_menu_id:
        #         if current_window_model in users_access_menus[2] and current_menu_id in users_access_menus[1]:
        #             if not users_access_menus[0]:  # User does not have full access
        #                 print('Applying field restrictions')
        #                 doc.set('create', 'false')
        #                 doc.set('edit', 'false')
        #
        #                 if view_type == 'form':
        #                     restricted_fields = []  # Specify fields to exclude from restrictions, if any
        #                     for field_name in fields.keys():
        #                         if field_name not in restricted_fields:
        #                             for node in doc.xpath(f"//field[@name='{field_name}']"):
        #                                 # Apply options
        #                                 node.set('options', "{'%s': True}" % default_options[field_name])
        #                                 # Apply attributes
        #                                 node.set('attrs', "{'%s': True}" % default_attrs[field_name])
        #                                 # Setup modifiers
        #                                 setup_modifiers(node, crm_lost_reason['fields'][field_name])
        #                 break
        #         else:
        #             print('No access to template action or current model')
        #     else:
        #         print('No current model or template action ID')
        #         doc.set('create', 'false')
        #         doc.set('edit', 'false')

        # Update the view architecture
        crm_lost_reason['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return crm_lost_reason


class ProductCatagory(models.Model):
    _inherit = 'product.category'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        product_cat = super(ProductCatagory, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(product_cat['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['product.category'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            doc.set('create', 'false')
            doc.set('edit', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
                doc.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, product_cat['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Update the view architecture
        product_cat['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return product_cat


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        account_invoice_template = super(AccountInvoice, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(account_invoice_template['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['account.invoice'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            # doc.set('create', 'false')
            # doc.set('edit', 'false')
            if view_type == 'form':
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'no_create': True, 'no_edit': True, 'no_create_edit': True, 'no_open': True}")
                            # node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, account_invoice_template['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Update the view architecture
        account_invoice_template['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return account_invoice_template

class HelpdeskCategory(models.Model):
    _inherit = 'helpdesk_category_ii'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        helpdesk_category = super(HelpdeskCategory, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        doc = etree.XML(helpdesk_category['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['helpdesk_category_ii'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('editable', 'false')  # Disable inline editing
                    node.set('create', 'false')  # Disable create button
                    node.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, helpdesk_category['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Update the view architecture
        helpdesk_category['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return helpdesk_category


class HelpdeskCategoryOne(models.Model):
    _inherit = 'helpdesk_category_i'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        helpdesk_category_1 = super(HelpdeskCategoryOne, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        doc = etree.XML(helpdesk_category_1['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['helpdesk_category_i'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('editable', 'false')  # Disable inline editing
                    node.set('create', 'false')  # Disable create button
                    node.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, helpdesk_category_1['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Update the view architecture
        helpdesk_category_1['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return helpdesk_category_1

class MasterRestrictionComplintSource(models.Model):
    _inherit = 'complaint.source'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        helpdesk_category_1 = super(HelpdeskCategoryOne, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        doc = etree.XML(helpdesk_category_1['arch'])

        # Retrieve current menu ID from context
        current_menu_id = self.env.context.get('current_menu_id')

        # Fetch fields and set default attributes and options
        fields = self.env['helpdesk_category_i'].fields_get()
        default_attrs = {key: 'readonly' for key in fields.keys()}
        default_options = {key: 'no_open' for key in fields.keys()}

        # Fetch access-related data
        groups_dic = accessible_menus_models_users(self=self)
        # if not groups_dic:
        #     return fleet_veh_result  # Return as is if no group dictionary is provided

        group_dic = groups_dic[0] if groups_dic else {}
        current_window_model = groups_dic[1] if groups_dic else ''
        template_action_id = groups_dic[2] if groups_dic else 0

        def apply_restriction():
            if view_type == 'form':
                for node in doc.xpath("//tree"):
                    node.set('editable', 'false')  # Disable inline editing
                    node.set('create', 'false')  # Disable create button
                    node.set('edit', 'false')
                restricted_fields = []
                for field_name in fields.keys():
                    if field_name not in restricted_fields:
                        for node in doc.xpath(f"//field[@name='{field_name}']"):
                            # Apply options and attributes
                            node.set('options', "{'%s': True}" % default_options[field_name])
                            node.set('attrs', "{'%s': True}" % default_attrs[field_name])
                            # Setup modifiers
                            setup_modifiers(node, helpdesk_category_1['fields'][field_name])

        # Flag to indicate unrestricted access
        # unrestricted_access = False

        filtered_restriction_based_on_config_and_setup = {
            key: list(filter(lambda x: x['boolean_from_config'] and x['boolean_from_setup'], value))
            for key, value in group_dic.items()
            if value
        }
        print(filtered_restriction_based_on_config_and_setup, '00000000000000000000000')
        # Step 2: Further filter based on 'models_in_group' and not 'user_in_groups'
        filtered_data_have_models_and_not_user = {
            key: list(filter(lambda v: v['models_in_group'] and not v['user_in_groups'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        filtered_data_have_models_in_group_and_not_users_and_not_menus = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and not v['menus_in_group'], value))
            for key, value in filtered_data_have_models_and_not_user.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_not_users_and_not_menus, '1111111111111111111')
        models_to_restrict = {'models_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_not_users_and_not_menus.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )
        ), 'menus_in_group': False, 'user_in_groups': False, }
        if not models_to_restrict['menus_in_group'] and not models_to_restrict['user_in_groups'] and models_to_restrict[
            'models_need_restrict']:
            if current_window_model in models_to_restrict['models_need_restrict']:
                print('model restrict')
                apply_restriction()
        # Step:2 END

        # Step 3: Further filter with no user access an menus presnt and models presnt restrict.
        filtered_data_have_models_in_group_and_have_menus_and_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and v['user_in_groups'] and v['menus_in_group'], value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        # print(filtered_data_have_models_in_group_and_have_menus_and_users, '22222222222222222222222')
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in filtered_data_have_models_in_group_and_have_menus_and_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and menus_to_restrict[
            'menus_need_restrict']:
            if current_menu_id in menus_to_restrict['menus_need_restrict'] and current_window_model in \
                    menus_to_restrict['model_need_restrict']:
                print('menus restrict')
                doc.set('create', 'true')
                doc.set('edit', 'true')
            elif current_window_model not in menus_to_restrict['model_need_restrict']:
                doc.set('create', 'true')
                doc.set('edit', 'true')
            else:
                apply_restriction()
        # Step 4
        filtered_data_have_models_in_group_and_have_menus_and_no_users = {
            key: list(
                filter(lambda v: v['models_in_group'] and not v['user_in_groups'] and v['menus_in_group'],
                       value))
            for key, value in filtered_restriction_based_on_config_and_setup.items()
            if value
        }
        print(filtered_data_have_models_in_group_and_have_menus_and_no_users)
        menus_to_restrict = {'menus_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values()
                for
                entry in value_list if
                'menus_in_group' in entry for model_item in entry['menus_in_group']
                )
        ), 'model_need_restrict': list(
            set(model_item for value_list in
                filtered_data_have_models_in_group_and_have_menus_and_no_users.values() for
                entry in value_list if
                'models_in_group' in entry for model_item in entry['models_in_group']
                )), 'menus_in_group': False, 'user_in_groups': False, }
        # print(menus_to_restrict)
        if not menus_to_restrict['menus_in_group'] and not menus_to_restrict['user_in_groups'] and \
                menus_to_restrict[
                    'menus_need_restrict']:
            if current_window_model in menus_to_restrict['model_need_restrict']:
                apply_restriction()
        # Update the view architecture
        helpdesk_category_1['arch'] = etree.tostring(doc, pretty_print=True, encoding='unicode')
        return helpdesk_category_1