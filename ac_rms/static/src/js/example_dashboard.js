odoo.define('ac_rms.example_dashboard', function (require) {
"use strict";

var ControlPanelMixin = require('web.ControlPanelMixin');
var Widget = require('web.Widget');
var core = require('web.core');
var ajax = require('web.ajax');


var SplitAction = Widget.extend(ControlPanelMixin, {
    title: core._t('Bank reconciliation'),
    template: 'cre_dashboard1',

        events: {
            "click .cre_start_submit": "CreStartRedirect",
            "click .cre_finish_submit": "CreFinishRedirect",
        },
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
               console.log(records.count_mytask.ids);
                $('.w3-circle4e').html(records.count_mytask.cre_process_len);
                $('.w3-circle5e').html(records.count_mytask.app_len);
                $('.w3-circle6e').html(records.count_mytask.turnup_len);
                $('.w3-circle7e').html(records.count_mytask.walk_in_count);
                $('.w3-circlesa').html(records.count_mytask.cre_sa_process_len);
                $('.w3-circle3e').html(records.count_mytask.cre_app_count);
                $('.w3-circleex').html(records.count_mytask.cre_walkin_count);
                $('.w3-circle8e').html(records.count_mytask.delivery_process_len);
                $('.w3-circle9e').html(records.count_mytask.len_cancel_click);
                $('.w3-circle11e').html(records.count_mytask.len_app_till_click);
                $('.w3-circle13e').html(records.count_mytask.len_wip_click);
                $('.w3-circle12e').html(records.count_mytask.len_waiting_for_delivery_click);


                //var url =  '/web#action= '+ records.count_mytask.tree;
                //$('#action_tree').attr('href',url);
                //$('#action_tree').attr('href',url);
                $('#my_pending_task').find('tbody').empty();
                $('#action_app').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'app_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                            //console.log($('.modal_rows_task').html());
                        }
                    });
                });
                $('#action_turnup').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'turnup_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });
                $('#action_walkin').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'walkin_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });
                $('#action_delivered').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'delivered_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#action_returned_vehicle').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'return_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#action_app_till').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'app_till_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#action_waiting_for_delivery').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'waiting_delivery_clk'}).then(function (data) {
                        if(data){
                            $('#my_pending_task').find('tbody').append(data.count_mytask.html_txt);
                        }
                    });
                });

                $('#action_wip').click(function(e) {
                    $('#my_pending_task').find('tbody').empty();
                    ajax.jsonRpc("/all_count_click", 'call', {'clk_type':'wip_clk'}).then(function (data) {
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

                /*function open_form(current_id,current_model){
                        alert('oo');
                }*/
            });

    },


    CreStartRedirect: function (e) {
        e.stopImmediatePropagation();
        var start_current_id = e.currentTarget.childNodes[1].innerHTML;
        var model_name = e.currentTarget.childNodes[2].innerHTML;
        return ajax.jsonRpc('/start_button', 'call', {
             'start_click_id': start_current_id,'model_name':model_name})
        .then(function (data) {
            //console.log('start',data['model']);
            if(data['model']){
                //console.log(e.currentTarget);
                e.currentTarget.parentNode.innerHTML = '<button style="height: 20px;width: 41px;background-color: #0d5f11;;font-weight: bold; border-color: #0d5f11; font-size: 13px;white-space: unset;padding: 0px;" type="submit" class="btn btn-success cre_finish_submit" id="cre_start">Finish<span class="order_id" style="display: none;">'+start_current_id+'</span><span class="form_model" style="display: none;">'+data['model']+'</span></button>'
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
            tag: 'dashboard1'
            });
//            location.reload(true);
            //e.currentTarget.innerHTML = ''
        });
    },

});

core.action_registry.add('dashboard1', SplitAction);

return {
    SplitAction: SplitAction,

};


});