odoo.define('ars_after_sales.warranty_stage', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var concurrency = require('web.concurrency');
var core = require('web.core');
var field_registry = require('web.field_registry');

var QWeb = core.qweb;
var _t = core._t;

var FieldOrgChart = AbstractField.extend({


    init: function () {
        this._super.apply(this, arguments);
        this.dm = new concurrency.DropMisordered();
    },

    _getOrgData: function (order_id) {
        var self = this;
        return this.dm.add(this._rpc({
            route: '/warranty_stage_value',
            params: {
                'data': order_id,
            },
        })).then(function (data) {
            self.orgData = data;

        });
    },
    /**
     * @override
     * @private
     */
    _render: function () {

        var self = this;
        return this._getOrgData(this.recordData.id).then(function () {
            self.$el.html(QWeb.render("warranty_stage_chart", self.orgData));

        });
    },

});

field_registry.add('warranty_stage_chart', FieldOrgChart);

return FieldOrgChart;

});
