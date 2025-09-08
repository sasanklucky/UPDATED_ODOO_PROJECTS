odoo.define('ac_rms.process_stage', function (require) {
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
            route: '/process_stage_value',
            params: {
                'data': order_id,
            },
        })).then(function (data) {
            self.orgData = data;
            //console.log(self.orgData);
        });
    },
    /**
     * @override
     * @private
     */
    _render: function () {

        var self = this;
        return this._getOrgData(this.recordData.id).then(function () {
            self.$el.html(QWeb.render("process_stage_chart", self.orgData));
            self.$('[data-toggle="popover"]').each(function () {
                $(this).popover({
                    html: true,
                    title: 'Process Stage',
                    container: 'body',
                    placement: 'left',
                    trigger: 'focus',
                    content: function () {
                        var $content = $(QWeb.render('process_stage_popover_content', self.orgData));
                        return $content;
                    },
                    template: $(QWeb.render('process_stage_popover', {})),
                });
            });
        });
    },
//    start: function() {
//        var self = this;
//        //alert(this.recordData.id);
//        self._rpc({
//                route: '/process_stage_value',
//                params: {
//                    'data': this.recordData.id,
//                },
//            })
//            .done(function (records) {
//                //alert(records.stage);
//                console.log(records.stage);
//                var previous_stage = records.previous_stage
//                var current_stage = records.stage
//                var after_stage = records.after_stage
//                var count_stage = records.count_stage
//                self.$('[data-toggle="popover"]').each(function () {
//                alert("lipsa");
//                $(this).popover({
//
//                    html: true,
//
////                    title: function () {
////                        var $title = $(QWeb.render('hr_orgchart_emp_popover_title', {
////                            employee: {
////                                name: $(this).data('emp-name'),
////                                id: $(this).data('emp-id'),
////                            },
////                        }));
////                        $title.on('click',
////                            '.o_employee_redirect', _.bind(self._onEmployeeRedirect, self));
////                        return $title;
////                    },
//                    container: 'body',
//                    placement: 'left',
//                    trigger: 'focus',
////                    content: function () {
////                        var $content = $(QWeb.render('hr_orgchart_emp_popover_content', {
////                            employee: {
////                                id: $(this).data('emp-id'),
////                                name: $(this).data('emp-name'),
////                                direct_sub_count: parseInt($(this).data('emp-dir-subs')),
////                                indirect_sub_count: parseInt($(this).data('emp-ind-subs')),
////                            },
////                        }));
////                        $content.on('click',
////                            '.o_employee_sub_redirect', _.bind(self._onEmployeeSubRedirect, self));
////                        return $content;
////                    },
//                    template: $(QWeb.render('hr_orgchart_emp_popover', {'static': 'puja'})),
//                });
//            });
//                return self.$el.html(QWeb.render("process_stage_chart", {
//                previous_process : previous_stage,
//                current_process : current_stage,
//                after_process : after_stage,
//                count_process : count_stage,
//
//
//         }));
//
//
//
//            });
//
//    },


});

field_registry.add('process_stage_chart', FieldOrgChart);

return FieldOrgChart;

});
