odoo.define('web_export_view', function (require) {
    "use strict";

    var core = require('web.core');
    var Sidebar = require('web.Sidebar');
    var session = require('web.session');
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
                                self.on_sidebar_export_treeview_xls);
                        }
                    });
            }
        },

        on_sidebar_export_treeview_xls: function () {
    var self = this;
    var view = this.getParent();

    // Fetch allowed models from the Python method
    return this._rpc({
        route: '/web/export/get_allowed_models',
        params: {},
    }).then(function (mode_restrict) {
        console.log(mode_restrict, 'mode_restrict', view.modelName);
        if (mode_restrict.includes(view.modelName)) {
            self.do_warn(
                _t("Export Restricted"),
                _t("You are not allowed to export data for this model.")
            );
            return;
        }

        // Proceed with export logic
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
                export_columns_names.push(view.$el.find(column_header_selector)[0].textContent);
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
                }),
            },
            complete: $.unblockUI,
            error: c.rpc_error.bind(c),
        });
    });
},


    });
});
