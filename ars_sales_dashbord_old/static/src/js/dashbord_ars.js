odoo.define('java_test.vklm', function (require) {
"use strict";

require('web.dom_ready');
var core = require('web.core');
var field_utils = require('web.field_utils');
var KanbanView = require('web.KanbanView');
var KanbanModel = require('web.KanbanModel');
var KanbanRenderer = require('web.KanbanRenderer');
var KanbanController = require('web.KanbanController');
var session = require('web.session');
var view_registry = require('web.view_registry');
var Widget = require('web.Widget');
//var Model = require('web.Model');

var QWeb = core.qweb;
var _t = core._t;
var _lt = core._lt;
var ArsSetupBarRenderer = KanbanRenderer.extend({
events: {
        'click .o_ars_dashboard_action': 'on_ars_dashboard_action_clicked',
        'click .o_target_to_set': 'on_ars_dashboard_target_clicked',

            },
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------
       fetch_data: function() {
        // Overwrite this function with useful data
        return $.when();
    },
    _render: function () {
        var super_render = this._super;
        var self = this;
         return this.fetch_data().then(function(result){
            self.show_demo = result && result.nb_opportunities === 0;
            var values = self.state.dashboardValues;

            var sales_dashboard = QWeb.render('ars_crm_dashbord_header.ars_new_dashboard', {
                widget: this,
                show_demo: self.show_demo,
                values: values,
            });
            super_render.call(self);
            $(sales_dashboard).prependTo(self.$el);
        });

        /*return this._super.apply(this, arguments).then(function () {
            var values = {};
            var account_dashboard = QWeb.render('java_test.client_new_dashboard', {
                widget: self,
                values: values,
            });
            self.$el.prepend(account_dashboard);
        });*/
    },
        on_ars_dashboard_action_clicked: function(ev){
        ev.preventDefault();

        var $action = $(ev.currentTarget);
        var action_name = $action.attr('name');
        var action_extra = $action.data('extra');
        var additional_context = {};

        // TODO: find a better way to add defaults to search view
        if (action_name === 'calendar.action_calendar_event') {
            additional_context.search_default_mymeetings = 1;
        } else if (action_name === 'crm.crm_lead_action_activities') {
            if (action_extra === 'today') {
                additional_context.search_default_today = 1;
            } else if (action_extra === 'this_week') {
                additional_context.search_default_this_week = 1;
            } else if (action_extra === 'overdue') {
                additional_context.search_default_overdue = 1;
            }
        } else if (action_name === 'crm.action_your_pipeline') {
            if (action_extra === 'overdue') {
                additional_context['search_default_overdue'] = 1;
            } else if (action_extra === 'overdue_opp') {
                additional_context['search_default_overdue_opp'] = 1;
            }
        } else if (action_name === 'crm.crm_opportunity_report_action_graph') {
            additional_context.search_default_won = 1;
        }

        this.do_action(action_name, {additional_context: additional_context});
    },

    on_change_input_target: function(e) {
        var self = this;
        var $input = $(e.target);
        var target_name = $input.attr('name');
        var target_value = $input.val();

        if(isNaN(target_value)) {
            this.do_warn(_t("Wrong value entered!"), _t("Only Integer Value should be valid."));
        } else {
//            this._updated = new Model('crm.lead')
//                            .call('modify_target_sales_dashboard', [target_name, parseInt(target_value)])
//                            .then(function() {
//                                return self.render();
//                            });
            var Result = $.when(this._rpc({
                    model: 'crm.lead',
                    method: 'modify_target_sales_dashboard',
                    args: [target_name, parseInt(target_value)],
                }));
        }
    },

    on_ars_dashboard_target_clicked: function(ev){
        if (this.show_demo) {
            // The user is not allowed to modify the targets in demo mode
            return;
        }

        var self = this;
        var $target = $(ev.currentTarget);
        var target_name = $target.attr('name');
        var target_value = $target.attr('value');

        var $input = $('<input/>', {type: "text"});
        $input.attr('name', target_name);
        if (target_value) {
            $input.attr('value', target_value);
        }
        $input.on('keyup input', function(e) {
            if(e.which === $.ui.keyCode.ENTER) {
                self.on_change_input_target(e);
            }
        });
        $input.on('blur', function(e) {
            self.on_change_input_target(e);
        });

        $.when(this._updated).then(function() {
            $input.replaceAll(self.$('.o_target_to_set[name=' + target_name + ']')) // the target may have changed (re-rendering)
                  .focus()
                  .select();
        });
    },

    render_monetary_field: function(value, currency_id) {
        var currency = session.get_currency(currency_id);
        var digits_precision = currency && currency.digits;
        value = formats.format_value(value || 0, {type: "float", digits: digits_precision});
        if (currency) {
            if (currency.position === "after") {
                value += currency.symbol;
            } else {
                value = currency.symbol + value;
            }
        }
        return value;
    },
});
var ArsModelsetup= KanbanModel.extend({
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------
events: {
        'click .o_ars_dashboard_action': 'on_link_ars_datas',
        'click .o_target_to_set': 'on_dashboard_target_clicked',

            },
    /**
     * @override
     */
    init: function () {
        this.dashboardValues = {};
        this.currency_id = 0;
        this._super.apply(this, arguments);
    },
     get: function (localID) {
        var result = this._super.apply(this, arguments);
        if (this.dashboardValues[localID]) {
            result.dashboardValues = this.dashboardValues[localID];
        }
        return result;
    },


    /**
     * @œverride
     * @returns {Deferred}
     */
    load: function () {
        return this._loadDashboard(this._super.apply(this, arguments));
    },
    /**
     * @œverride
     * @returns {Deferred}
     */
    reload: function () {
        return this._loadDashboard(this._super.apply(this, arguments));
    },
  _fetchDashboardData: function ()
  {
        return $.when(this._rpc({
                    model: 'crm.lead',
                    method: 'retrieve_ars_sales_dashboard',
                    args: [],
                }));
  },
   _loadDashboard: function (super_def) {
        var self = this;
        var dashboard_def = this._fetchDashboardData();
        console.log('working javascript');
        console.log(dashboard_def);
        return $.when(super_def, dashboard_def).then(function (id, dashboardValues) {
            self.dashboardValues[id] = dashboardValues;
            self.currency_id = dashboard_def.currency_id;
            return id;
        });
    },
});




var ArsDashboardView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Model: ArsModelsetup,
        Renderer: ArsSetupBarRenderer,
    }),


    display_name: _lt('Dashboard'),
    icon: 'fa-dashboard',
    searchview_hidden: false,


});

view_registry.add('java_test_check', ArsDashboardView);

return {
    Model: ArsModelsetup,
    Renderer: ArsSetupBarRenderer,

};

});