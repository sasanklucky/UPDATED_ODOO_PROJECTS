odoo.define('ac_rms.sa_dashboard_design', function (require) {
"use strict";

var ControlPanelMixin = require('web.ControlPanelMixin');
var Widget = require('web.Widget');
var core = require('web.core');
var ajax = require('web.ajax');

var SplitAction = Widget.extend(ControlPanelMixin, {
    title: core._t('Bank reconciliation'),
    template: 'sa_dashboard',
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
                route: '/sa_login_dashboard',
                params: {
                },
            })
            .done(function (records) {
//                console.log(records.count_mytask.tree);
                $('.w3-circle4s').html(records.count_mytask.sa_process_len);
                $('.w3-circle5s').html(records.count_mytask.app_len);
                $('.w3-circle6s').html(records.count_mytask.turnup_len);
                $('.w3-circle7s').html(records.count_mytask.walk_in_count);
                $('.w3-circlesa1').html(records.count_mytask.waiting_for_sa_count);
                $('.w3-circle3s').html(records.count_mytask.sa_app_count);
                $('.w3-circleexs').html(records.count_mytask.sa_walkin_count);
                $('.w3-circle8s').html(records.count_mytask.delivery_process_len);
                $('.w3-circle9s').html(records.count_mytask.len_cancel_click);
                $('.w3-circle11s').html(records.count_mytask.len_app_till_click);
                $('.w3-circle13s').html(records.count_mytask.len_wip_click);
                $('.w3-circle12s').html(records.count_mytask.len_waiting_for_delivery_click);
                $('.w3-circle14e').html(records.count_mytask.len_hold_click);
//                $('.w3-circle4').html(records.count_mytask.tree);
                /*var url =  '/web#action= '+ records.count_mytask.tree;
                $('#action_tree').attr('href',url);*/

                $('#my_pending_task').find('tbody').empty();
                $('#sa_action_app').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'app_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });
                $('#sa_action_turnup').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'turnup_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });
                $('#sa_action_walkin').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'walkin_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });
                $('#sa_action_delivered').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'delivered_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#sa_action_returned_vehicle').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'return_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#sa_action_app_till').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'app_till_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#sa_action_waiting_for_delivery').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'waiting_delivery_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#sa_action_wip').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'wip_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#sa_action_hold').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'hold_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#my_pending_task').find('tbody').append(records.count_mytask.html_txt)

                $('.modal_rows_task').on('click', 'td:not(.process)', function(){
                var current_id = $(this).parent().find('#click_form_id').val();
                var current_model = $(this).parent().find('#click_form_model').val();
                    ajax.jsonRpc("/cre_formview", 'call', {'id':current_id,'model':current_model})
                    .then(function (data) {
                        window.location.href = data.form
                    });
                });

            });

    },

    CreStartRedirect: function (e) {
        var start_current_id = e.currentTarget.childNodes[1].innerHTML;
        var model_name = e.currentTarget.childNodes[2].innerHTML;
        return ajax.jsonRpc('/start_button', 'call', {
             'start_click_id': start_current_id,'model_name':model_name})
        .then(function (data) {
            if(data){
                e.currentTarget.parentNode.innerHTML = '<button style="height: 20px;width: 45px;background-color: #0d5f11;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Finish<span class="order_id" style="display: none;">'+start_current_id+'</span><span class="form_model" style="display: none;">'+data['model']+'</span></button>'
            }
        });
    },

    CreFinishRedirect: function (e) {
        var self = this;
        var start_current_id = e.currentTarget.childNodes[1].innerHTML;
        var model_name = e.currentTarget.childNodes[2].innerHTML;
        return ajax.jsonRpc('/finish_button', 'call', {
             'start_click_id': start_current_id,'model_name':model_name})
        .then(function (data) {
            self.do_action({
            type: 'ir.actions.client',
            tag: 'sa_dashboard'
            });
//            location.reload(true);
//            e.currentTarget.innerHTML = '<button style="height: 27px;width: 60px;background-color: teal;font-weight: bold; border-color: teal; font-size: small;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Start<span class="order_id" style="display: none;">'+start_current_id+'</span></button>'
        });
    },

});

core.action_registry.add('sa_dashboard', SplitAction);

return {
    SplitAction: SplitAction,

};


});