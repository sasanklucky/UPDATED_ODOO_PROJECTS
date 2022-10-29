odoo.define('ars_invoice_aftersales.split', function (require) {
"use strict";

var ControlPanelMixin = require('web.ControlPanelMixin');
var Widget = require('web.Widget');
var core = require('web.core');
var sidebar = require('web.ListController');
var DataExport = require('ars_invoice_aftersales.Datasplit');
var Sidebar = require('web.Sidebar');
var ListController = require('web.ListController');
var split_invoice = require('ars_invoice_aftersales.Datasplit');

var _t = core._t;


ListController.include({
        init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.hasSidebar = params.hasSidebar;
        this.toolbarActions = params.toolbarActions || {};
        this.editable = params.editable;
        this.noLeaf = params.noLeaf;
        this.selectedRecords = []; // there is no selected record by default

    },

    renderSidebar: function ($node) {
        if (this.hasSidebar && !this.sidebar) {
            var other = [{
                label: _t("Export"),
                callback: this._onExportData.bind(this)
            }];
            if (this.modelName == 'sale.order.line') {
                other.push({
                        label: _t("Split Invoice"),
                        callback: this._onSplitData.bind(this)
                    });
                  }
            if (this.archiveEnabled) {
                other.push({
                    label: _t("Archive"),
                    callback: this._onToggleArchiveState.bind(this, true)
                });
                other.push({
                    label: _t("Unarchive"),
                    callback: this._onToggleArchiveState.bind(this, false)
                });
            }
            if (this.is_action_enabled('delete')) {
                other.push({
                    label: _t('Delete'),
                    callback: this._onDeleteSelectedRecords.bind(this)
                });
            }
            this.sidebar = new Sidebar(this, {
                editable: this.is_action_enabled('edit'),
                env: {
                    context: this.model.get(this.handle, {raw: true}).getContext(),
                    activeIds: this.getSelectedIds(),
                    model: this.modelName,
                },
                actions: _.extend(this.toolbarActions, {other: other}),
            });
            this.sidebar.appendTo($node);

            this._toggleSidebar();
        }
    },

    /*Split Invoice*/
    _onSplitData: function () {
            var record = this.model.get(this.handle);
            var selected_records = this.getSelectedIds();
            //console.log(selected_records);
            //var records = _.map(this.selectedRecords, function (id) { return id; });
            //console.log(records);
            new split_invoice(this, record,selected_records).open();
        },

})



});


