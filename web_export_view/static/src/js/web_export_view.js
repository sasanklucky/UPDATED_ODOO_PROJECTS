odoo.define('web_export_view', function (require) {
    "use strict";

    var core = require('web.core');
    var Sidebar = require('web.Sidebar');
    var session = require('web.session');
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');
    var crash_manager = require('web.crash_manager');

    var QWeb = core.qweb;

    var _t = core._t;

    Sidebar.include({

        _redraw: function () {
            var self = this;
            this._super.apply(this, arguments);

            if (self.getParent().renderer.viewType === 'list') {
                session.user_has_group(
                    'web_export_view.group_disallow_export_view_data_excel')
                    .then(function (has_group) {
                        if (!has_group) {
                            self.$el.find('.o_dropdown')
                                .last().append(QWeb.render(
                                    'WebExportTreeViewXls', {widget: self}));
                            self.$el.find('.export_treeview_xls').on('click',
                                self.on_sidebar_export_treeview_xls.bind(self));
                        }
                    });
            }
        },

       on_sidebar_export_treeview_xls: function () {
            var self = this;
            var view = this.getParent();
            var model_name = view.modelName;  // Get the selected model

            // Fetch allowed models
            rpc.query({
                route: '/web/export/get_allowed_models',
            }).then(function (allowed_models) {
                if (allowed_models.includes(model_name)) {
                    // If model is in allowed models, show password dialog
                    var dialog = new Dialog(self, {
                        size: 'medium',
                        $content: $('<div/>', {
                            html: '<label style="display: block; text-align: center; font-weight: bold; font-size: 16px; margin-bottom: 10px;">' +
                                      _t('Enter your password for exporting') +
                                  '</label>' +
                                  '<div style="margin-left: 200px;">' +
                                      '<input type="password" id="xls_export_password" class="form-control" ' +
                                      'style="display: block; text-align: center; width: 50%; padding: 8px; border-radius: 5px; border: 1px solid #ccc;"/>' +
                                  '</div>' +
                                  '<small class="text-muted" style="display: block; text-align: center; margin-top: 5px; font-size: 12px; color: #666;">' +
                                      _t('Hint: Use your login password.') +
                                  '</small>'
                        }),
                        buttons: [
                            {
                                text: _t('Export'),
                                classes: 'btn-primary',
                                click: function () {
                                    var password = $('#xls_export_password').val();
                                    if (!password) {
                                        self.do_notify(_t("Warning"), _("Please enter a password."));
                                        return;
                                    }

                                    // Verify password via RPC
                                    rpc.query({
                                        model: 'res.users',
                                        method: 'verify_password',
                                        args: [session.uid, password],
                                        kwargs: {},
                                    }).then(function (is_valid) {
                                        if (is_valid) {
                                            dialog.close();
                                            self._export_xls(password);  // Proceed with export
                                        } else {
                                            self.do_notify(_t("Warning"), _("Invalid password. Please try again."));
                                        }
                                    }).fail(function (err) {
                                        self.do_notify(_t("Error"), _("Error validating password."));
                                        console.error(err);
                                    });
                                }
                            },
                            {
                                text: _t('Cancel'),
                                close: true
                            }
                        ]
                    });

                    dialog.open();

            // Ensure buttons are centered
            setTimeout(function () {
                $('.modal-title').remove();  // Removes the title
                $('.modal-header').remove();
                $('.modal-footer').css({
                    'text-align': 'center'
                });
            }, 100);
                } else {
                    // If model is NOT in allowed models, proceed without password
                    self._export_unprotected_xls();
                }
            }).fail(function (err) {
                self.do_notify(_t("Error"), _("Error fetching allowed models."));
                console.error(err);
            });
       },

        _export_xls: function (password) {
            var view = this.getParent();
            var children = view.getChildren();
            var c = crash_manager;
            var export_columns_keys = [];
            var export_columns_names = [];
            var column_index = 0;
            var column_header_selector = '';
            var isGrouped = view.renderer.state.groupedBy.length > 0;

            $.each(view.renderer.columns, function () {
                if (this.tag === 'field' &&
                    (this.attrs.widget === undefined || this.attrs.widget !== 'handle')) {
                    export_columns_keys.push(column_index);
                    var css_selector_index = isGrouped ? column_index + 1 : column_index;
                    column_header_selector = '.o_list_view > thead > tr> th:not([class*="o_list_record_selector"]):eq(' + css_selector_index + ')';
                    export_columns_names.push(
                    view.$el.find(column_header_selector)[0].textContent);
                }
                ++column_index;
            });

            var export_rows = [];
            $.blockUI();
            if (children) {
                view.$el.find('.o_list_view > tbody > tr.o_data_row:has(.o_list_record_selector input[type=checkbox]:checked)')
                    .each(function () {
                        var $row = $(this);
                        var export_row = [];
                        $.each(export_columns_keys, function () {
                            var $cell = $row.find('td.o_data_cell:eq(' + this + ')');
                            var $cellcheckbox = $cell.find('.o_checkbox input:checkbox');
                            if ($cellcheckbox.length) {
                                export_row.push($cellcheckbox.is(":checked") ? _t("True") : _t("False"));
                            } else {
                                    var text = $cell.text().trim();
                                    var is_number =
                                        $cell.hasClass('o_list_number') &&
                                        !$cell.hasClass('o_float_time_cell');
                                    if (is_number) {
                                        // var db_params = _t.database.parameters;
                                        // export_row.push(parseFloat(
                                        //     text
                                        //     // Remove thousands separator
                                        //         .split(db_params.thousands_sep)
                                        //         .join("")
                                        //         // Always use a `.` as decimal
                                        //         // separator
                                        //         .replace(db_params.decimal_point,
                                        //             ".")
                                        //         // Remove non-numeric characters
                                        //         .replace(/[^\d.-]/g, "")
                                        // ));
                                        export_row.push(text);
                                    } else {
                                        export_row.push(text);
                                    }
                            }
                        });
                        export_rows.push(export_row);
                    });
            }

                session.get_file({
                    url: '/web/export/xls_view',
                    data: {
                        data: JSON.stringify({
                            model: view.modelName,
                            headers: export_columns_names,
                            rows: export_rows,
                            password: password,
                        }),
                    },
                    complete: $.unblockUI,
                    error: c.rpc_error.bind(c),
                });
        },

        _export_unprotected_xls: function() {
            // Select the first list of the current (form) view
            // or assume the main view is a list view and use that
            var view = this.getParent(),
                children = view.getChildren();
            var c = crash_manager;

            if (children) {
                children.every(function (child) {
                    if (child.field && child.field.type === 'one2many') {
                        view = child.viewmanager.views.list.controller;
                        return false;
                    }
                    if (child.field && child.field.type === 'many2many') {
                        view = child.list_view;
                        return false;
                    }
                    return true;
                });
            }
            var export_columns_keys = [];
            var export_columns_names = [];
            var column_index = 0;
            var column_header_selector = '';
            var isGrouped = view.renderer.state.groupedBy.length > 0;
            $.each(view.renderer.columns, function () {
                if (this.tag === 'field' &&
                    (this.attrs.widget === undefined ||
                        this.attrs.widget !== 'handle')) {
                    export_columns_keys.push(column_index);
                    var css_selector_index = isGrouped
                        ? column_index+1 : column_index;
                    column_header_selector = '.o_list_view > thead > tr> ' +
                        'th:not([class*="o_list_record_selector"]):eq(' +
                        css_selector_index + ')';
                    export_columns_names.push(
                        view.$el.find(column_header_selector)[0].textContent);
                }
                ++column_index;
            });
            var export_rows = [];
            $.blockUI();
            if (children) {
                // Find only rows with data
                view.$el.find('.o_list_view > tbody > tr.o_data_row:' +
                    'has(.o_list_record_selector input[type=checkbox]:checked)')
                    .each(function () {
                        var $row = $(this);
                        var export_row = [];
                        $.each(export_columns_keys, function () {
                            var $cell = $row.find(
                                'td.o_data_cell:eq('+this+')');
                            var $cellcheckbox = $cell.find(
                                '.o_checkbox input:checkbox');
                            if ($cellcheckbox.length) {
                                export_row.push(
                                    $cellcheckbox.is(":checked")
                                        ? _t("True") : _t("False")
                                );
                            } else {
                                var text = $cell.text().trim();
                                var is_number =
                                    $cell.hasClass('o_list_number') &&
                                    !$cell.hasClass('o_float_time_cell');
                                if (is_number) {
                                    // var db_params = _t.database.parameters;
                                    // export_row.push(parseFloat(
                                    //     text
                                    //     // Remove thousands separator
                                    //         .split(db_params.thousands_sep)
                                    //         .join("")
                                    //         // Always use a `.` as decimal
                                    //         // separator
                                    //         .replace(db_params.decimal_point,
                                    //             ".")
                                    //         // Remove non-numeric characters
                                    //         .replace(/[^\d.-]/g, "")
                                    // ));
                                    export_row.push(text);
                                } else {
                                    export_row.push(text);
                                }
                            }
                        });
                        export_rows.push(export_row);
                    });
            }

            session.get_file({
                url: '/web/export/unprotected/xls_view',
                data: {
                    data: JSON.stringify({
                        model: view.modelName,
                        headers: export_columns_names,
                        rows: export_rows,
                    }),
                },
                complete: $.unblockUI,
                error: c.rpc_error.bind(c),
            });
        },

    });
});
