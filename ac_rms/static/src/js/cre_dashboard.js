odoo.define('ac_rms.cre_dashboard', function (require) {
"use strict";

var ControlPanelMixin = require('web.ControlPanelMixin');
var Widget = require('web.Widget');
var core = require('web.core');


var SplitAction = Widget.extend(ControlPanelMixin, {
    title: core._t('Bank reconciliation'),
    template: 'cre_dashboard',

//    init: function(parent, record) {
//
//
//    },
    start: function() {
        var self = this;
        self._rpc({
                route: '/cre_login',
                params: {
                },
            })
            .done(function (records) {
//                console.log(records.count_mytask.tree);
                $('.w3-circle4').html(records.count_mytask.waiting_at_reception_count);
//                $('.w3-circle4').html(records.count_mytask.tree);
                /*var url =  '/web#action= '+ records.count_mytask.tree;
                $('#action_tree').attr('href',url);*/



            });

    },
});

core.action_registry.add('dashboard', SplitAction);

return {
    SplitAction: SplitAction,

};


});