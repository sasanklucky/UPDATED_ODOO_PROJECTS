odoo.define('ars_invoice_aftersales.Datasplit', function (require) {

"use strict";

var core = require('web.core');
var crash_manager = require('web.crash_manager');
var data = require('web.data');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var pyeval = require('web.pyeval');
var selected_records = "";
var QWeb = core.qweb;
var _t = core._t;

var DataSplit = Dialog.extend({
    template: 'split_invoice',
    events: {
        'click .create_invoices': function(e) {


            var customer = [];
            var amt_value = [];
            var per_t = [];
            $(".select_class :selected").map(function(i, el) {

                customer.push($(el).val());
            });
			$(".subtotal_value").each(function() {

				amt_value.push($(this).val());
			 });
			$(".percentage_value").each(function() {

				per_t.push($(this).val());
			 });
           /* if(p_obj){
            	for (var i=0; i< n; i++)
                {
            	//alert()
                customer.push(p_obj[i].value);
                amt_value.push(pp_obj[i].value);
             }
            }*/

             var res = $('#res_ids').html();
             var order = $('#order_id').html();
             //console.log(res);
            //var p_obj = $(e.currentTarget).parent().find('.select_class');
            //console.log(p_obj);
            //$(p_obj).each(function(){
                //var theVal = $(this).find('select option:selected').val();
                //console.log(this);
                //$(this).find('p').html(theVal);
            //});
            //console.log($(e.currentTarget).parent().find('#select_class'));
//             console.log(customer);
//             console.log(amt_value);
//             console.log(res);
//             console.log(order);
//             console.log(per_t);
            this.split_data(customer,amt_value,res,order,per_t);
        },
        'click .plus': function(e) {
            var ele = $(e.currentTarget).closest('.d_clone').clone(true);
            ele.find('.plus-symbol').replaceWith('<div class="col-xs-2 minus-symbol"><img class="minus" src="ars_invoice_aftersales/static/src/img/minus.png" style="width: 18px;height: 29px;"/></div>')
            //$(e.currentTarget).closest('.d_clone').after(ele);
            ele.find('.percentage_value').val('0%');
            ele.find('.subtotal_value').val('0');
            $(ele).insertAfter($('.d_clone').last());
        },
        'click .minus-symbol': function(e) {

            var total_percent = $(".percent")[0].value;
            var total_subtotal = $(".subtotal")[0].value;
            var changed_subtotal = $('input[class=subtotal_value]').val();
            var changed_percent = $('input[class=percentage_value]').val();
            //var deleted_percent = $('input:hidden[class=percentage_value]').val();
            var deleted_percent  = $(e.currentTarget).parent().find('.percentage_value').val();
            //var deleted_subtotal = $('input:hidden[class=subtotal_value]').val();
            var deleted_subtotal  = $(e.currentTarget).parent().find('.subtotal_value').val();
            var after_split_del_percent = deleted_percent.replace(/\%/g,'');
            var after_split_changed_percent = changed_percent.replace(/\%/g,'');
            var int_after_split_changed_percent = parseInt(after_split_changed_percent)
            var int_after_split_del_percent = parseInt(after_split_del_percent)
            var int_del_subtotal = parseInt(deleted_subtotal);
            var int_changed_subtotal = parseInt(changed_subtotal);
            int_after_split_changed_percent += int_after_split_del_percent
            var concat_percent = int_after_split_changed_percent + '%'
            document.getElementsByClassName("percentage_value")[0].value = concat_percent;
            //$('input[class=percentage_value]').val(concat_percent);
            int_changed_subtotal += int_del_subtotal
            //$('input[class=subtotal_value]').val(int_changed_subtotal);
           document.getElementsByClassName("subtotal_value")[0].value = int_changed_subtotal;
           if(deleted_percent){
                $(e.currentTarget).parent().remove();
           }



//            var percent = 0
//            alert(percent);
//            for(var i=0;i < changed_percent.length;i++){
//              alert(changed_percent);
//              if(i > 0){
//                alert(changed_percent[i]);
//                var splited_percent_value = (changed_percent[i].value).replace(/\%/g,'');
//                var trim_percent_value = splited_percent_value.trim();
//                var int_percent = parseInt(trim_percent_value);
//                percent += int_percent
//                alert(percent);
//              }
//            }
        },
    },
    init: function(parent, record,selectedRecords) {
        selected_records = selectedRecords;
        //alert(selectedRecords);
        var model = record.model;
        var res_ids = record.res_ids
        var options = {
            title: _t("Split Invoice"),
            buttons: [
                //{text: _t("Create Invoice"), click: this.split_data(res_ids), classes: "btn-primary create_invoice"},
                //{text: _t("Close"), close: true},
            ],
        };
        this._super(parent, options);
        this.records = {};
        this.record = record;
        this.exports = new data.DataSetSearch(this, 'ir.exports', this.record.getContext());

        this.row_index = 0;
        this.row_index_level = 0;
    },
    start: function() {
        var self = this;
        self._rpc({
                route: '/ars_invoice_aftersales/split/get_fields',
                params: {
                    model: self.record.model,
                    res_ids:self.record.res_ids,
                    selected_ids:selected_records,
                },
            })
            .done(function (records) {
                self.on_show_data(records);

            });

    },

    on_show_data: function(records) {
        var self = this;
        var buttn1 = '<button class="btn btn-sm btn-primary create_invoices" type="button"><span>Create Invoice</span></button>'
        var buttn2 = '<button class="btn btn-sm btn-primary" data-dismiss="modal"><span>Close</span></button>'
        this.$('.box-1').empty().append(
            $("<div/>").addClass('o_field_tree_structure')
                       .append(QWeb.render('split_invoice_data', {'order_id':records[0].order_id,'res_ids':records[0].line_ids,'customer_val': records[0].customers,'percent_val':'100%','subtotal_val':records[0].price_subtotal,'button1':buttn1,'button2':buttn2, 'debug': self.getSession().debug}))
        );

    },

    split_data: function(customers,amt,res,order,per) {
        //alert(customers);
        //alert(amt);
        //alert(res);
        var self = this;
        self._rpc({
                route: '/ars_invoice_aftersales/split/get_data',
                params: {
                    customers:customers,
                    amt:amt,
                    res_ids:res,
                    order:order,
                    per:per,
                },
            })
            .done(function (records) {
                if(records.status){
                	$('.o_technical_modal').hide();
                	$('.modal-backdrop').css('display','none');
                	self.do_action({
                        name: 'Customer Invoices',
                        res_model: 'account.invoice',
                        views: [[false, 'list'], [false, 'form']],
                        type: 'ir.actions.act_window',
                        view_type: "list",
                        view_mode: "list"
                    });
                }

            });
    },










});

return DataSplit;


});
