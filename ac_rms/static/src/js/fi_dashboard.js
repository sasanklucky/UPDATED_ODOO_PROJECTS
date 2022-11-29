odoo.define('ac_rms.fi_dashboard', function (require) {
"use strict";

var ControlPanelMixin = require('web.ControlPanelMixin');
var Widget = require('web.Widget');
var core = require('web.core');
var ajax = require('web.ajax');

var SplitAction = Widget.extend(ControlPanelMixin, {
    title: core._t('Bank reconciliation'),
    template: 'fi_dashboard',
        events: {
            "click .cre_start_submit": "CreStartRedirect",
            "click .cre_finish_submit": "CreFinishRedirect",
        },

//    init: function(parent, record) {
//        this._super(parent,{});
////        this.title = ''
////        this.title = parent.action_stack[0];
////        console.log(parent.action_stack);
//       // console.log(parent.action_stack[0]['title']);
//       //alert(parent.action_stack[0].title);
//        //console.log(parent.inner_action.title);
////        alert(this.title);
//
//    },

    start: function() {
        var self = this;
        self._rpc({
                route: '/fi_login_dashboard',
                params: {
                },
            })
            .done(function (records) {
//                console.log(records.count_mytask.tree);
                $('.w3-circle4s').html(records.count_mytask.fi_process_count);
//                $('.w3-circle4').html(records.count_mytask.tree);
                /*var url =  '/web#action= '+ records.count_mytask.tree;
                $('#action_tree').attr('href',url);*/

                $('#my_pending_task').find('tbody').append(records.count_mytask.html_txt)

                $('.modal_rows_task').on('click', 'td:not(.process)', function(){
                var current_id = $(this).parent().find('#click_form_id').val();
                    ajax.jsonRpc("/cre_formview", 'call', {'id':current_id})
                    .then(function (data) {
                        window.location.href = data.form
                    });
                });

            });

    },

    CreStartRedirect: function (e) {
        var start_current_id = e.currentTarget.childNodes[1].innerHTML;
//        alert(start_current_id);
        return ajax.jsonRpc('/start_button', 'call', {
             'start_click_id': start_current_id,})
        .then(function (data) {
            e.currentTarget.parentNode.innerHTML = '<button style="height: 20px;width: 40px;background-color: teal;font-weight: bold; border-color: teal; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Finish<span class="order_id" style="display: none;">'+start_current_id+'</span></button>'
        });
    },

    CreFinishRedirect: function (e) {
        var start_current_id = e.currentTarget.childNodes[1].innerHTML;
        return ajax.jsonRpc('/finish_button', 'call', {
             'start_click_id': start_current_id,})
        .then(function (data) {
            location.reload(true);
        });
    },

});

core.action_registry.add('fi_dashboard', SplitAction);

return {
    SplitAction: SplitAction,

};


});