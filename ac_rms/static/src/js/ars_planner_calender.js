odoo.define('ac_rms.script', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    var base = require('web_editor.base');
    var global_count = 0;
    var run_interval = 0;

	$(document).ready(function() {

        $('#from_date').change(function() {
            $('#fm_date').val($('#from_date').val())
            });
        $('#to_date').change(function() {
            $('#en_date').val($('#to_date').val())
            });
        
        $("#external-events").on( "click",".bay_events", function(e) {
        	
        	if ($(this).hasClass('select')) {
                $(this).removeClass('select').addClass('deselect');
                $(this).prev().prop("checked", false);
            	$(this).children().css({"background":"#b9cbc7"});
            }
            else {
                $(this).removeClass('deselect').addClass('select');
                $(this).prev().prop("checked", true);
            	$(this).children().css({"background":"#5e9898"});
            }

        });
        $("#tech-events").on( "click",".res_div", function(e) {
        	if ($(this).hasClass('select')) {
                $(this).removeClass('select').addClass('deselect');
                $(this).prev().prop("checked", false);
            	$(this).children().css({"background":"#b9cbc7"});
            }
            else {
                $(this).removeClass('deselect').addClass('select');
                $(this).prev().prop("checked", true);
            	$(this).children().css({"background":"#5e9898"});
            }
        });
	  
		
	    function myFunction(val){
	          //console.log($('.fc-time-area').find('.fc-content').find('table th').html());
              $('.fc-time-area').find('.fc-content').find('table th').each(function(index,e) {
                    var time = $(this).text();
                    var res_digit = time.slice(0,-2);
                    var res_am_pm = time.slice(-2);
                    if(res_am_pm == 'pm'){
                        if(res_digit != 12){
                            res_digit = parseInt(res_digit) + 12
                        }
                    }
                    else{
                        if(res_digit == 12){
                            res_digit = 0
                        }
                    }
                    var dt = new Date();
                    var hour = dt.getHours();
                    var min = dt.getMinutes();
                    if (hour == res_digit){
                        var current_distance = parseInt($(this).width()) - 1
                        var distance = parseInt(current_distance)
                        var width_min = distance/60;
                        var min_wid = min * width_min;
                        var left = (index * distance) + (index * 2) + min_wid;
                        $('.current_time').css("left", left+'px');
                    }
              });
              var update_view = $("#view :selected").val();
              if (update_view != undefined){
                  var show_resource = $(".showall").text();
                  var button_text = $(".fc-showall-button").text();
                  ajax.jsonRpc("/resource_planner/get", 'call', { 'view': update_view,'showall':show_resource,'button_text':button_text}).then(function(data) {
                      if(data){
                          $('#calendar').fullCalendar('removeEvents');
                          $('#calendar').fullCalendar('addEventSource', data['events']);
                          $('#calendar').fullCalendar('rerenderEvents');
                      }
                  });
              }
	    }



	    setInterval(function() { myFunction(); }, 60000);
	    setInterval(function() {
	    	if(run_interval == 0){
	    		console.log(run_interval);
	    		myFunction();
	    		run_interval = run_interval + 1;

	    	}
	    }, 600);

	    $("#technician_task").on( "click","#select_tech_chkbx", function(e) {
            var table= $(e.target).closest('table');
            $('td input:checkbox',table).each(function() {
                $(this).prop("checked", true);
            });
        });

        


        $('.break_reason_btn').click(function(e) {
            var radioValue = $("input[name='b']:checked").val();
            if(radioValue){
                if (radioValue == 'shiftend'){
                    var confrm = confirm("Do you want to end the Shift");
                    if(!confrm){
                        return false;
                    }
                }
    //            alert(radioValue);
                if (radioValue == 'others'){
                    //console.log($('#breakreason').html());
                    var x = $('#breakreason').val();
                    if (x == "") {
                        alert("Please mention Break Reason");
                        return false;
                        }
                    }
                var context = {'brk_typ':radioValue, 'brk_reason':x};
                  ajax.jsonRpc("/tech_break", 'call', {'brk_typ':radioValue, 'brk_reason':$('#breakreason').val()}).then(function(data) {
                      /*if(result.length){
                          if (result == 'logout'){
                              var url = '/web/login';
                              window.location.href = url;
                          }
                          else{alert(result);}*/

                         $('#break_task_modal_dialog').modal('hide').data( 'bs.modal', null )
                    /* }*/
                    //  if (result.result){
                         //window.location.reload();
                    // }
                  });
                  $('#break_task_modal_dialog').modal('hide').data( 'bs.modal', null );

                }
        });
          $('#others').click(function(){
              $('.break-class').toggleClass('hidden').prop('required',true);
          });
         $('.opt').click(function(){
              $('.break-class').addClass('hidden').prop('required',false);
          });

	    $('#break_dialog_id').click(function(e){
            $('#break_task_modal_dialog').find('input[type="radio"]').prop('checked',false);
             var brk = $('#break_task_modal_dialog').find('#breakreason');
             brk.val('');
             brk.addClass('hidden')
             //$('#break_task_modal_dialog').modal('show')
             /*new Model("resume").call("check_shifend_time", [[]], {'context': {}}).done(function(result) {
                 if(result.length){
                     if (result == "yes"){
                         $('#break_task_modal_dialog').find('.shiftend').prop('disabled',false)

                     }
                     else{
                         $('#break_task_modal_dialog').find('.shiftend').prop('disabled',true)
                     }
                 }
              });*/
             $('#break_task_modal_dialog').modal('show')
             /*new Model("resume").call("chech_break_rec", [[]], {'context': {}}).done(function(result) {
                 if(result.length){
                     alert(result);
                     $('#break_task_modal_dialog').modal('hide').data( 'bs.modal', null )
                 }
                 else{

                     $('#break_task_modal_dialog').modal('show')
                 }
              });*/

        });

        //console.log($("#jobstoppage_task").html());
	    $("#jobstoppage_task").on( "change","#stage_chkbx", function(e) {
	        //alert('kk');
            $('#approve_task').attr("disabled", false);
            $('#reject_task').attr("disabled", false);
            $('#approve_tasks').attr("disabled", false);
	        $('#reject_tasks').attr("disabled", false);
	    });

	    $("#jobstoppage_task").on('click', '#approve_task', function () {
	        var a = [];
            $("input[type='checkbox']:checked").each(function() {
                 a.push(parseInt(this.value));
            });
            ajax.jsonRpc("/tech_realease_approve", 'call', { 'tasks': a}).then(function(data) {
              if(data){
                  if(data['msg']){
                      alert(data['msg']);
                      $('#jobstoppage_task').block({});
                  
                  }else{
                       $('#jobstoppage_task').modal('hide');
                  }
                  window.location.reload();
              }
            });
	    });

	    $("#jobstoppage_task").on('click', '#reject_task', function () {
	        var a = [];
            $("input[type='checkbox']:checked").each(function() {
                 a.push(parseInt(this.value));
            });
            ajax.jsonRpc("/tech_realease_reject", 'call', { 'tasks': a}).then(function(data) {
              if(data){
                  if(data['msg']){
                      alert(data['msg']);
                      $('#jobstoppage_task').block({});

                  }else{
                       $('#jobstoppage_task').modal('hide');
                  }
                  window.location.reload();
              }
            });
	    });




        $("#drawer").find("#drawer-content").find("div#jobstoppage_allocation").click(function(e){
            var project_task = $(this).find('.job_stappage_id').text();
            //alert(project_task);
            ajax.jsonRpc("/jobstopage_bucket_clk", 'call', { 'project_task': project_task}).then(function(data) {
                 $("#jobstoppage_task").empty();
                 $("#jobstoppage_task").append(data['result']);
                 $("#jobstoppage_task").modal('show');
            });
        });

        $("#techallocation").draggable({});
       // console.log('PP',$('#techallocation').html());

//        $("table#techallocation_table input[name^='select']").on('change',function (e) {
          /*function check_box_onchng(){
            alert('ll');
             var count1 = 0;
             $('#taskconfirm').attr("disabled", true);
             $.each($("table#techallocation_table input[name^='select']:checked"), function() {
                count1 += 1;
                if(count1 > 1) {
                    $('#taskconfirm').attr("disabled", false);
                }
                else if (count1 == 1){
                    $('#taskconfirm').attr("disabled", false);
                }
                else{
                    $('#taskconfirm').attr("disabled", true);
                }
             });
        }*/

        $("#technician_task").on('click', '#start_task', function () {
                  var $start = $(this);
                  var a = [];
                  $('#technician_task').block({
                    message: '<img src="/ac_rms/static/src/img/loadingimage.gif" />',
                    css:{width:'10%'}
                    });
                  $("input[type='checkbox']:checked").each(function() {
                      a.push(parseInt(this.value));
                  });
                  var context = {'task_ids': a}
                  /*this._rpc({
                        model: 'project.task',
                        method: 'allocate_start',
                        args: [context],
                    })
                    .then(function (result) {*/
                  //new Model("start").call("allocate_start", [[]], {'context': context}).done(function(data) {

                  ajax.jsonRpc("/tech_start", 'call', { 'tasks': a}).then(function(data) {
                  	if(data){
                  		if(data['msg']){
                  			alert(data['msg']);
                            $('#technician_task').block({});
                  		}
                  	}else{
              			$modal.modal('hide');
              		}
              		window.location.reload();
                  });

              });


        $("#technician_task").on('click', '#pause_task', function () {
                if ($('#pause_task_modal').hasClass("clicked-once")) {

              		$('#pause_task_modal').css('display','none');
              		$('#pause_task_modal').removeClass("clicked-once");
              		$('#break_task_modal').removeClass("brk-clicked-once");
                  }
                else {
                  	$('#break_task_modal').removeClass("brk-clicked-once");
                  	$('#break_task_modal').css('display','none');
                  	$('#pause_task_modal').addClass("clicked-once");
                  	var $pause = $(this);
                      var a = [];
                      $("input[type='checkbox']:checked").each(function() {
                          a.push(parseInt(this.value));
                          $('#pause_task_modal').css('display','block');
                      });

//              var $start = $(this);
//              var a = [];
//              $('#technician_task').block({
//                message: '<img src="/ac_rms/static/src/img/loadingimage.gif" />',
//                css:{width:'10%'}
//              });
//              $("input[type='checkbox']:checked").each(function() {
//                 a.push(parseInt(this.value));
//              });
            $(document).on('change', 'input[name="onhold"]', function() {
                $('.on_hold').addClass('hidden');
                $('.pause_reason').attr('disabled',false);
               if ($('#Others').prop('checked') == true) {
                    $('#'+$(this).val()).removeClass('hidden');
                }
            });
            $("#technician_task").on('click', '.pause_reason', function () {
                var allVals = [];
                  $('#ckbx :checked').each(function() {
                    allVals.push($(this).val());
                  });
                var other_brk_rsn = $('#otherreason').val();
                if ($('#Others').prop('checked') == true && other_brk_rsn == "") {
                    alert("Please enter the remarks...!");
                    return false;
                }
                var on_hold_value = ''
                $('input[name="onhold"]').each(function() {
                    if ($(this).prop('checked') == true){
                         on_hold_value = $(this).attr('data-option')
                    }
                });
            var decision_brk_rsn = $('#otherreason').val();
            var approve_brk_rsn = $('#otherreason').val();
            var parts_brk_rsn = $('#otherreason').val();
            var diagonis_brk_rsn = $('#otherreason').val();
            var a = [];
              $("input[type='checkbox']:checked").each(function() {
                  a.push(parseInt(this.value));
                  });
//               alert(on_hold_value);
//               alert(other_brk_rsn);
               var context = {'task_ids': a,'brk_reason':allVals, 'onhold':on_hold_value, 'otherreason':other_brk_rsn,
                            'decisionreason':decision_brk_rsn, 'custapprove':approve_brk_rsn, 'waitparts':parts_brk_rsn,
                            'waitdiagonis':diagonis_brk_rsn}
               ajax.jsonRpc("/tech_pause", 'call', { 'tasks': a, 'onhold': on_hold_value, 'otherreason': other_brk_rsn}).then(function(data) {
                      if(data){
                        if(data['msg']){
                            alert(data['msg']);
                            $('#technician_task').block({});
                        }
                      }
                      else{
                           $('#technician_task').modal('hide');
                      }
                    window.location.reload();
               });

               });

               }
        });


//        $(document).on('change', 'input[name="onhold"]', function() {
//                $('.on_hold').addClass('hidden');
//                $('.pause_reason').attr('disabled',false);
//               if ($('#Others').prop('checked') == true) {
//                    $('#'+$(this).val()).removeClass('hidden');
//                }
//                console.log($(this).val());
//
//
//        });
//        $("#technician_task").on('click', '.pause_reason', function () {
//            var allVals = [];
//              $('#ckbx :checked').each(function() {
//                allVals.push($(this).val());
//              });
//            var other_brk_rsn = $('#otherreason').val();
//            if ($('#Others').prop('checked') == true && other_brk_rsn == "") {
//                alert("Please enter the remarks...!");
//                return false;
//            }
//            var on_hold_value = ''
//            $('input[name="onhold"]').each(function() {
//                if ($(this).prop('checked') == true){
//                     on_hold_value = $(this).attr('data-option')
//                }
//            });
//        var decision_brk_rsn = $('#otherreason').val();
//        var approve_brk_rsn = $('#otherreason').val();
//        var parts_brk_rsn = $('#otherreason').val();
//        var diagonis_brk_rsn = $('#otherreason').val();
//        var a = [];
//          $("input[type='checkbox']:checked").each(function() {
//              a.push(parseInt(this.value));
//          });
//        var context = {'task_ids': a,'brk_reason':allVals, 'onhold':on_hold_value, 'otherreason':other_brk_rsn,
//                        'decisionreason':decision_brk_rsn, 'custapprove':approve_brk_rsn, 'waitparts':parts_brk_rsn,
//                        'waitdiagonis':diagonis_brk_rsn}
//            alert(on_hold_value);
//            alert(other_brk_rsn);
//            console.log(context);
//            ajax.jsonRpc("/tech_pause", 'call', context).then(function(data) {
////                alert(data);
////                if(data){
////                    if(data['msg']){
////                        alert(data['msg']);
////                        $('#technician_task').block({});
////                    }
////                  }
////                  else{
////                       $('#technician_task').modal('hide');
////                  }
////                window.location.reload();
//
//            });
//            });





        /*var counter = 0;
          $("#technician_task").on('click', '#pause_task', function () {
            if ($('#pause_task_modal').hasClass("clicked-once")) {

                $('#pause_task_modal').css('display','none');
                $('#pause_task_modal').removeClass("clicked-once");
                $('#break_task_modal').removeClass("brk-clicked-once");
              }
              else {
                $('#break_task_modal').removeClass("brk-clicked-once");
                $('#break_task_modal').css('display','none');
                $('#pause_task_modal').addClass("clicked-once");
                var $pause = $(this);
                  var a = [];
                  $("input[type='checkbox']:checked").each(function() {
                      a.push(parseInt(this.value));
                      $('#pause_task_modal').css('display','block');
                  });
                  *//*new Model("break.reason").call("get_breaks", [[]], {'context': {}}).done(function(data) {
                    if (data){
                        if(counter<=0){
                            data['break'].forEach(function(entry) {
                                if (entry != 'Break'){
                                        var strVal = entry.replace(/ /g,'');
                                    var cb = document.createElement( "input" );
                                        cb.type = "checkbox";
                                        cb.id = strVal;
                                        cb.value = entry;
                                     var text = document.createTextNode( entry );
                                     document.getElementById( 'ckbx' ).appendChild( cb );
                                     document.getElementById( 'ckbx' ).appendChild( text );
                                     var br = document.createElement( "br" );
                                     document.getElementById( 'ckbx' ).appendChild( br );
                                }

                                //$("<option></option>", {value:entry, text: entry}).appendTo('#brk_opt');

                            });
                            counter++;
                        }

                        if(data.hasOwnProperty('other')){
                            data['other'].forEach(function(entry) {
                                if (entry != 'Break'){
                                    $("<option></option>",
                                         {value: entry, text: entry})
                                        .appendTo('#other_break');
                                }

                                //$("<option></option>", {value:entry, text: entry}).appendTo('#brk_opt');

                            });
                            counter++;
                        }
                    }
                  });*//*



               $("#technician_task").on('change', '#Others', function() {
                    $('.other-class').toggleClass('hidden');
                });

                $("#technician_task").on('change', 'input[name="onhold"]', function() {
                    //$('.on_hold').addClass('hidden');
                    $('.pause_reason').attr('disabled',false);
                    *//*$('#'+$(this).val()).removeClass('hidden');*//*

                });

                  *//*$(".pause_reason").click(function(){
                    var allVals = [];
                      $('#ckbx :checked').each(function() {
                        allVals.push($(this).val());
                      });
                    var other_brk_rsn = $('#otherreason').val();
                    var context = {'task_ids': a,'brk_reason':allVals, 'otherreason':other_brk_rsn}
                     *//**//*new Model("resume").call("allocate_resume", [[]], {'context': context}).done(function() {
                     });*//**//*
                     var a = [];
                      $('#technician_task').block({
                        message: '<img src="/ac_rms/static/src/img/loadingimage.gif" />',
                        css:{width:'10%'}
                      });
                      $("input[type='checkbox']:checked").each(function() {
                         a.push(parseInt(this.value));
                      });
                       var context = {'task_ids': a}
                       ajax.jsonRpc("/tech_pause", 'call', { 'tasks': a}).then(function(data) {
                              if(data){
                                if(data['msg']){
                                    alert(data['msg']);
                                    $('#technician_task').block({});
                                }
                              }
                              else{
                                   $('#technician_task').modal('hide');
                              }
                            window.location.reload();
                       });
                     //$modal.modal('hide');
                  });*//*
              }

          });*/

        $("#technician_task").on('click', '#finish_task', function () {
                  var $start = $(this);
                  var a = [];
                  $('#technician_task').block({
                    message: '<img src="/ac_rms/static/src/img/loadingimage.gif" />',
                    css:{width:'10%'}
                    });
                  $("input[type='checkbox']:checked").each(function() {
                      a.push(parseInt(this.value));
                  });
                  var event = $('.tech_event').text();

                  var context = {'task_ids': a,'event':event}
                  /*this._rpc({
                        model: 'project.task',
                        method: 'allocate_start',
                        args: [context],
                    })
                    .then(function (result) {*/
                  //new Model("start").call("allocate_start", [[]], {'context': context}).done(function(data) {

                  ajax.jsonRpc("/tech_finish", 'call', { 'tasks': a,'event':event}).then(function(data) {
                  	if(data){
                  		/*if(data['msg']){
                  			alert(data['msg']);
                            $('#technician_task').block({});
                  		}*/
                  		ajax.jsonRpc("/tech_finish_time_sheet", 'call', { 'tasks':data['tasks'],'event':data['event']}).then(function(result) {
                  			if(result){
                  				console.log('success');
                  			}
                  		});
                  	}else{
              			$('#technician_task').modal('hide');
              		}
              		window.location.reload();
                  });

              });

        function find_selected_boxes(e){
            var mul_text = [];
            $('td input:checkbox',e).each(function() {
                if($(this).is(":checked")){
                    mul_text.push($(this).parent().next('td').next('td').next('td').html().trim());
                }
            });
            var array_dis = myFunc(mul_text);
            if(array_dis && mul_text != ''){
                validate_tech_buttons(mul_text[0]);
            }
            else{
                $('#start_task').attr("disabled", true);
                $('#pause_task').attr("disabled", true);
                $('#finish_task').attr("disabled", true);
            }
        }

        function validate_tech_buttons(val){
            var val0 = [false,true,true]; /*New*/
            var val1 = [true,false,false]; /*In Progress*/
            var val2 = [false,true,true]; /*Break*/
            var val3 = [true,true,true]; /*Hold*/
            var val4 = [false,true,true]; /*Reject*/
            var val5 = [true,true,true]; /*Approve*/
            var val6 = [true,true,true]; /*Finish*/
            var val7 = [true,true,true]; /*Shiftend*/
            var val8 = [false,true,true]; /*Allocated*/

            var all_tech_buttons = $('.tech_popup_header_section').find("button");
            all_tech_buttons.each(function(index) {
                if(val == 'Waiting to Start'){
                    $(this).attr("disabled", val0[index]);
                }if(val == 'In Progress'){
                    $(this).attr("disabled", val1[index]);
                }if(val == 'Break'){
                    $(this).attr("disabled", val2[index]);
                }if(val == 'Job Stoppage'){
                    $(this).attr("disabled", val3[index]);
                }if(val == 'Rejected'){
                    $(this).attr("disabled", val4[index]);
                }if(val == 'Approved'){
                    $(this).attr("disabled", val5[index]);
                }if(val == 'Done'){
                    $(this).attr("disabled", val6[index]);
                }if(val == 'Shiftend'){
                    $(this).attr("disabled", val7[index]);
                }if(val == 'Allocated'){
                    $(this).attr("disabled", val8[index]);
                }

            });
        }

        //Technician Popup Checkbox onchange
        $("#technician_task").on( "change","#stage_chkbx", function(e) {
            var table = $(this).parent().parent().parent().parent();
            find_selected_boxes(table);
        });

        function myFunc(arr){
            var x= arr[0];
            return arr.every(function(item){
                return item=== x;
            });
          }

        //Technician Popup Select ALL
        var clk_count = 0;
        $("#technician_task").on( "click","#select_tech_chkbx", function(e) {
            //console.log('selectall',e.target);
            var table= $(e.target).closest('table');
            if(clk_count == 0){
                clk_count = 1;
                $('td input:checkbox',table).each(function() {
                    $(this).prop("checked", true);
                });
                find_selected_boxes(table);

            }else{
              $('td input:checkbox',table).each(function() {
                  $(this).prop("checked", false);
                  $('#start_task').attr("disabled", true);
                  $('#pause_task').attr("disabled", true);
                  $('#finish_task').attr("disabled", true);
              });
             clk_count = 0;
            }
        });

        $("#techallocation").on('click','td.tr_clone_add', function(e, data) {
            //console.log($(this).closest('#start_date').html());
            //console.log(data);
            tr_clone_add($(this), data, 'onclick');
            $('.btn-color-plus').css("background-color", "#fff !important");
            $('.btn-color-plus').css("color", "#2e6da4");
            $('.tr_clone_minus').css("background-color", "#fff !important");
            $('.tr_clone_minus').css("color", "#d9534f");
          });


        function tr_clone_add(e, data, dbl){
            var button_top = $('.tawindow').css('top');
            var split_button_top = button_top.split('px');
            var parseint_top = parseInt(split_button_top[0]) + 50
            $('#taskconfirm').css({'top': parseint_top + 'px'});

            if (e.closest('td').find('#addnew').prop('disabled') == true){
                return false;
            }
            var $tr = e.closest('.tech_labour_date_tr');
            var $clone = $tr.clone(true, false);
            $clone.find('.tr_clone_add').remove();
            $clone.addClass('clone_class');
            $clone.append('<td width="5%" class="pln-min"><button class="btn btn-danger tr_clone_minus" id="addnew" name="removerow" type="button"><i class="fa fa-minus minus-icon"/></button><span class="valid hidden">no</span></td>');
            $clone.find('.clone-no-add').css('visibility','hidden');
            //$clone.find('.clone-no-add').remove();
               // console.log(data);
           
            if (dbl=='onclick'){
                    $clone.find('#bay_select').val(e.parent().find('#bay_select').val());
                    $clone.find('#bay_select').attr("disabled",true);
                }
            //console.log(data);
            if(data){
                    $clone.find('#bay_select').val(data['bay']);
                    $clone.find('#bay_select').attr("disabled",true);
                    $clone.find('#tech_select').val(data['tech']);
                    $clone.find('.st_date').val(data['text1']);
                    $clone.find('.en_date').val(data['text2']);
                    $clone.find('.clone_class').remove();
                }
           
            $tr.after($clone);
        
            $('#techallocation').on('click',"div.input-group span.fa-calendar", function(e){
                $(e.currentTarget).parents().eq(1).find('#start_date').focus();
            });

            $('#techallocation').on('click',"div.input-group > span", function(e){
                $(e.currentTarget).parents().eq(1).find('#start_date').focus();
            });

            $("div.input-group span.fa-calendar").on('click', function(e) {
                $(e.currentTarget).parents().eq(1).find('#end_date').focus();
                //Add a comment to this line

            });

            $("div.input-group > span").on('click', function(e) {
                $(e.currentTarget).parents().eq(1).find('#end_date').focus();
            });

            $clone.find('button.tr_clone_minus').on('click', function() {
                $(this).closest('.tech_labour_date_tr').remove();
                var button_top = $('.tawindow').css('top');
                var split_button_top = button_top.split('px');
                var parseint_top = parseInt(split_button_top[0]) - 50
                $('#taskconfirm').css({'top': parseint_top + 'px'});
            });

        };


        $('#techallocation').on('click','.selectallclass1', function(e){
            selectall($(this));
          });

        $('#fi-details-table').on('click','.selectallclass1', function(e){
            selectall($(this));
          });

        $('#techallocation').on('click','.test_cls', function(e){
            test_cls($(this));
        });

        $('#fi-details-table').on('click','.test_cls', function(e){
            test_cls($(this));
        });

        function test_cls(data){
            var e = data;
            var cur_obj = e;
            e.parent().next().find('td:first-child input[type=checkbox]').each(function() {
            if(cur_obj.text()=="Select All"){
                $(this).parent().find('input[type=checkbox]').prop('checked', true);
            }
             else{
                $(this).parent().find('input[type=checkbox]').prop('checked', false);
             }
            });

            if(cur_obj.text()=="Select All") {
                cur_obj.text('Remove All');
            }
            else{
                cur_obj.text('Select All');
            }
        }

        function selectall(e){
            var id = e.parent().attr('id');
            var text1;
            var text2;
            var bay;
            var tech;
            var option;
            var valid;
            var shift;
            var count = 1;
            var prev = '';
            var current = '';
            var original = {};
            var clone = {};
            var clone_cnt = 0;
            //console.log(e.parent().next().find('td:first-child input[type=checkbox]'));
            e.parent().next().find('td:first-child input[type=checkbox]').each(function() {
//                    alert('totalcheckbox');
                   if ($(this).is(":checked")) {
//                        alert('checked');
                       //console.log($(this).parent().parent().parent().html());
                       //to differtiate the clone or original line
                       if ($(this).parent().parent().parent().hasClass('clone_class')){
                               //alert('clone');
                               prev = current;
                               current = 'clone'
                           }
                           else{
                                //alert('original');
                               prev = current;
                               current = 'original'
                           }

                       //increment when the next line original line
                       if((prev == 'original' || prev == 'clone') && current == 'original' && count >=1){
                           count++;
                       }
                       //Parent values to copy for child records
                       //alert(count);
                       if (count == 1){
//                            alert('count1');
                           clone_cnt =  clone_cnt +1;
                           //console.log($(this).parents().parents().parents().find('#bay_select').val());
                           //shift = $(this).parents().eq(1).find('.shift_select_line').val();
                           //console.log($(this).parent().parent().parent().find('#tech_select').val());
                           bay = $(this).parent().parent().parent().find('#bay_select').val();
                           tech = $(this).parent().parent().parent().find('#tech_select').val();
                           //alert(tech);
                           text1 = $(this).parent().parent().parent().find('.st_date').val();
                           text2 = $(this).parent().parent().parent().find('.en_date').val();
                           valid = $(this).parent().parent().parent().find('.valid').text()
                           //finding minus button hidden/visible
                           var minus_button = $(this).parents().parents().parents().find('.tr_clone_minus');
                          // console.log(minus_button);
                           var t = false
                           var isVisible = minus_button.is(':visible');
                           if (isVisible === true) {
                               t = true
                            } else {
                               t = false
                            }
                            //alert(current);
                           if (!current || current=='original'){
                                original[1] = {'bay':bay, 'tech':tech, 'text1':text1, 'text2':text2, 'option':$(this).parents().parents().parents().find('#tech_select').html(),'valid':valid}
                           }
                           else{
                                //alert('kk');
                                //console.log(bay);
                               //getting all clone record values..
                               clone[clone_cnt] = {'bay':bay, 'tech':tech, 'text1':text1, 'text2':text2,
                                'option':$(this).parents().parents().parents().find('#tech_select').html()}
                           }

                       }else{
                            //alert('countgreater1');
                           //assigning for remainig check boxes..
                           /*shift = $(this).parents().parents().parents().find('.shift_select_line');*/
                           bay = $(this).parent().parent().parent().find('#bay_select');
                           tech = $(this).parent().parent().parent().find('#tech_select');
                           text1 = $(this).parent().parent().parent().find('.st_date');
                           text2 = $(this).parent().parent().parent().find('.en_date');
                           valid = $(this).parent().parent().parent().find('.valid');
                            if (current=='original'){
                                //alert(original);
                                /*var status = $(this).parents().eq(1).find('.tr_status').text();
                                var trim_status = status.trim();
                                if(trim_status == 'In Progress'){
                                    text2.val(original[1]['text2']);
                                    $(this).parent().parent().nextAll('.clone_class').remove();
                                }
                                else{*/
                                    /*shift.val(original[1]['shift']);*/
                                    //alert('clone');
                                bay.val(original[1]['bay']);
                                tech.html(original[1]['option']);
                                tech.val(original[1]['tech']);
                                text1.val(original[1]['text1']);
                                text2.val(original[1]['text2']);
                                valid.text(original[1]['valid'])
                                // to remove all cloned TR when clicked on assign again
                                //console.log('aaa'+$(this).parent().parent().parent().nextAll('.clone_class').html());
                                $(this).parent().parent().parent().nextAll('.clone_class').remove()
                               /* }*/
                             }
                            for(var c in clone){
                                //alert('pp');
                                var r = $(this).parent().parent().parent();
                               //console.log(r);
                                //console.log(clone[c]);
                                var new_clone = tr_clone_add(r, clone[c]);
                                //var new_clone = $(this).parent().next('td').next('td').next('td').next('td').next('td').trigger('click',[clone[c]]);

                            }

                       }


                   }

                   else{
                      if ($(this).parents().eq(1).next('tr').hasClass('clone_class')){
                          $(this).parents().eq(1).next('tr').closest('td').find("input[name='default_select']").prop('checked',false);                       }
                  }
                });
          };

        $("td.tr_clone_add").on('click', function(e, data) {
             $('.btn-color-plus').css("background-color", "#fff !important");
             $('.btn-color-plus').css("color", "#2e6da4");
             $('.tr_clone_minus').css("background-color", "#fff !important");
             $('.tr_clone_minus').css("color", "#d9534f");
           });

        $(".icon-clk-search").on('click',function(){
            $('#myTags > li > input').focus();
        });

        var expanded = false;
        $("#drawer-handle").click(function () {
            if (expanded = !expanded) {
                $("#drawer-content").animate({ "margin-right": 0 },    "slow");
            } else {
                $("#drawer-content").animate({ "margin-right": -1150 }, "slow");
            }
        });

        var fi_expanded = false;
        $("#fi-handle").click(function () {
            ajax.jsonRpc("/fi_process_details/get", 'call', {}).then(function(data) {
                if(data){
                    $('#fi_tasks').text(data['fi_waiting_counts']);
                    $('#fi_waiting_counts').text(data['fi_waiting_counts']);
                    $('#fi_in_progress_counts').text(data['fi_in_progress_counts']);
                    $('#fi_rejected_counts').text(data['fi_rejected_counts']);
                    $('#fi_completed_counts').text(data['fi_completed_counts']);
                    $('#fi_in_progress_id').text(data['fi_in_progress_ids']);
                    $('#fi_waiting_id').text(data['fi_waiting_ids']);
                    $('#fi_rejected_id').text(data['fi_rejected_ids']);
                    $('#fi_completed_id').text(data['fi_completed_ids']);
                    $('#fi_task_id').text(data['fi_waiting_ids']);

                }
            });
            if (fi_expanded = !fi_expanded) {
                $("#fi-content").animate({ "margin-right": 0 },    "slow");
            } else {
                $("#fi_detail_container").css("display", "none");
                $("#fi-content").animate({ "margin-right": -1150 }, "slow");
            }
        });


        /*$(".task-img").click(function () {
            *//*$('html, body').animate({
                scrollTop: $("#fi-details-table").find("#fi_details_tbl").offset().top
            }, 1000);*//*
            var fi_waiting_ids = $('#fi_waiting_id').text();
            if(fi_waiting_ids.indexOf(',') > -1){
                var fi_ids = fi_waiting_ids.split(',');
            }
            else{
                var fi_ids = [fi_waiting_ids]
            }
            ajax.jsonRpc("/fi_details", 'call', {'waiting_ids':fi_ids,'fi_ids':'','current_color':'#f5474d;','status':''}).then(function(data) {
                     $('#fi-details-table').empty();
                     if(data['html_data']){
                        $('#fi-details-table').append(data['html_data']);
                     }
                });

        });*/

        $('#fi-details-table').on('click',".close-x", function(e){
            $("#fi_detail_container").css("display", "none");
         });
        $(".fi_plannner_btn").click(function (e) {
            $("#fi_detail_container").css("display", "block");
            e.preventDefault();
            var fi_ids = ''
            var sec_child = $(this).find('a span:nth-child(3)').text();
            var current_color = $(this).css('background-color');
            /*var fi_waiting_id = $('#fi_waiting_id').text();*/
            /*console.log('this_obj',$(this));*/
            var status = false;
            if($(this).text().indexOf('FI Completed') > -1){
                status = true;
            }
//            var fi_in_progress_ids = $('#fi_in_progress_id').text();
//            var fi_rejected_ids = $('#fi_rejected_id').text();
//            var fi_completed_ids = $('#fi_completed_id').text();
            /*if($(this).text().indexOf('FI Waiting') > -1){
                if(fi_waiting_id.indexOf(',') > -1){
                    var fi_ids = fi_waiting_id.split(',');
                }
                else{
                    var fi_ids = [fi_waiting_id]
                }
            }
            else{*/
            if(sec_child.indexOf(',') > -1){
                var fi_ids = sec_child.split(',');
                //console.log('coming',fi_ids);
            }
            else{
                var fi_ids = [sec_child]
            }
            /*}*/
            ajax.jsonRpc("/fi_details", 'call',{'waiting_ids':'','fi_ids':fi_ids,'current_color':current_color,'status':status}).then(function(data) {
                     $('#fi-details-table').empty();
                     if(data['html_data']){
                        var display_html = '<span class="close-x">X</span>'+data['html_data'];
                        $('#fi-details-table').append(display_html);
                        /*$('html, body').animate({
                            scrollTop: $("#fi-details-table").offset().top
                        }, 1000);*/
                        /*$("#fi_detail_container").animate({height:"100px"});*/


                     }
                });

        });

        /*$('html, body').animate({
            scrollTop: $("#fi_detail").offset().top
        }, 1000);*/

        $('#fi-details-table').on('click',".fistart", function(e){
            var button_text = $(this).text();
            $.each($(this).parent().parent().find('table').find('input[name^="inner-chckbox"]:checked'), function() {
                var status = $(this).parent().parent().parent().find('td:eq(4)').find("select option:selected").val();
                var task_ids = $(this).parent().parent().parent().find('td:eq(1)').find("#task_ids").val();
                ajax.jsonRpc("/final_inspection_start", 'call',{'status':status,'task_ids':task_ids,'button_text':button_text}).then(function(data) {
                    if(data['start']){
                        $('#taskstart').text('Finish');
                    }
                    if(data['finish']){
                        alert("Final Inspection Completed");
                        location.reload();
                    }
                });
            });
        });

        /*$('#fi-details-table').on('click',".fifinish", function(e){
            var button_text = $(this).text();
            *//*$('.fifinish').css("display", "block");
            $('.fistart').css("display", "none");*//*
            $.each($(this).parent().parent().find('table').find('input[name^="inner-chckbox"]:checked'), function() {
                var status = $(this).parent().parent().parent().find('td:eq(4)').find("select option:selected").val();
                var task_ids = $(this).parent().parent().parent().find('td:eq(1)').find("#task_ids").val();
                ajax.jsonRpc("/final_inspection_start", 'call',{'status':status,'task_ids':task_ids,'button_text':button_text}).then(function(data) {
                    if(data['start']){
                        $('.fifinish').css("display", "none");
                        $('.fistart').css("display", "none");
                    }
                });
            });
        });*/


        $('#techallocation').on('click',".all_btn", function(e){
            var order_ids = $(this).find('.all_ids').text();
            ///(order_ids);
            var background_color = $(this).css('background-color');
            //var table_chk = $('#baytech-allocation-table').html();
//            if(table_chk == ''){
                ajax.jsonRpc("/bay-tech-popup/get", 'call', { 'orders': order_ids,'color_header':background_color}).then(function(data) {
                    $('#baytech-allocation-table').empty();
                    if(data['html_data']){
                        $('#baytech-allocation-table').append(data['html_data']);
                    }
                });
//            }
            /*else{
                    $('#baytech-allocation-table').empty();
                }*/

        });


        $('#techallocation').on('click',".regn_clk", function(e){
            var order = $(this).parent().find(".order").val();
            var context = {'order_id':order};
            var chk = $('#task_'+order).html();

            if(chk == ''){
                ajax.jsonRpc("/bay-tech-popup/vehicle-details", 'call', context).then(function(data) {
                     $('#task_'+order).empty();
                     if(data['vehicle_details_data']){
                        $('#task_'+order).append(data['vehicle_details_data']);
                     }
                });
            }
            else{
                $('#task_'+order).empty();
            }
        });

        $('#Dblclick').on('click',".reg_no", function(e){
            //alert("coming");
            $('#task_dobule_clk').empty();
            var order_id = $("#regn").html();
            var context = {'order_id':order_id};
            ajax.jsonRpc("/dbl_clk_popup", 'call', context).then(function(data) {
                $('#task_dobule_clk').empty();
                if(data['vehicle_html']){
                    $('#task_dobule_clk').append(data['vehicle_html']);
                }
            });
        });

        //console.log($('#resource_planner').html());
        $('#fi-details-table').on('click',".fi_regn_clk", function(e){
            var order = $(this).parent().find(".order").val();
            var status = $(this).parent().find(".status").val();
            var context = {'order_id':order,'status':status};
            var chk = $('#task_'+order).html();

            if(chk == ''){
                ajax.jsonRpc("/fi_task_details", 'call', context).then(function(data) {
                     $('#task_'+order).empty();
                     if(data['vehicle_details_data']){
                        $('#task_'+order).append(data['vehicle_details_data']);
                     }
                });
            }
            else{
                $('#task_'+order).empty();
            }
        });


        function ajaxserviceplanner(method, data, e) {
                $.ajax({
                    url: "/resource_planner/" + method,
                    type: "POST",
                    dataType: 'json',
                    data: JSON.stringify({params: {result: data}}),
                    contentType: 'application/json',
                }).done(function(result) {
                    if(result){
                        //alert('00');
                       $.ajax({
                            url: "/timesheet_record_ins",
                            type: "POST",
                            dataType: 'json',
                            data: JSON.stringify({params: {result:data}}),
                            contentType: 'application/json',
                        }).done(function(result) {


                        });
                        window.location.reload();

                    }
                   
                });
              
            }
//Double click
        $('#Dblclick').on('click','.tawindow_dbl', function(e){
        	var ta_values = new Array();
        	var labour_data = []
        	var labour_table = $(this).parent().parent().find('table#dbl_alloc_table tr.modal_rows');
        	labour_table.each(function() {
        		if($(this).find('td:eq(0)').find('input[name^="inner-chckbox"]').prop("checked") == true){
        			var order_id = $(this).find('td:eq(0)').find('.dbl_order').text();
        			alert(order_id);
        			 var labour_table_tr_data = []
                     labour_table_tr_data.push({
                         'bay_name': $(this).find('td:eq(2)').find("select option:selected").val(),
                         'technicain': $(this).find('td:eq(3)').find("select option:selected").val(),
                         'start_date': $(this).find('td:eq(4)').find(".st_date").val(),
                         'end_date': $(this).find('td:eq(5)').find(".en_date").val(),
                         'order_id':order_id,
                         'task_id':$(this).find('td:eq(1)').find("#task_ids").val(),
                     });


                 labour_data.push({
                     'order':order_id,
                     'data': labour_table_tr_data,

                 });
        		}
                
                
        	});
        	ta_values.push({
                'labour': labour_data,

            });
        	ajaxserviceplanner('bay_tech_update', ta_values, e);
        });
//end
        //console.log($('#techallocation').on('click','.selectallclass1', function(e){);
        $('#techallocation').on('click','.tawindow', function(e){
//        $('#techallocation').find('.tawindow').on('click',function (e) {
            //alert('hh');
             var count = 0;
             $.each($("table#techallocation_table input[name^='select']:checked"), function() {
                count += 1;
             });
             if(count > 1) {
                    alert('Multiple records are selected !! Only, one record can be selected to confirm.');
                    return false;
                }
            //var check = datetimevalidation('#techallocation');
            var check = true;
            var valid_lines = []
            //var valid = bay_tech_validation('#techallocation');
            if (check == true){
                //alert('cc');
                var ta_values = new Array();

                $.each($("table#techallocation_table input[name^='select']:checked"), function() {
                    //alert('oo');
                    $('#taskconfirm').attr("disabled", false);
                    $('#taskconfirm1').attr("disabled", false);
                    var labour_data = []
                    //console.log($(this).parent().next().find('.order').val());
                    var labour_table = $(this).parent().parent().next().find('table#alloc_table tr.modal_rows');
                    var order_id = $(this).parent().next().find('.order').val()
                    //console.log(labour_table);
                    labour_table.each(function() {
                     if($(this).find('td:eq(0)').find('input[name^="inner-chckbox"]').prop("checked") == true){
                        var labour_table_tr_data = []
                            labour_table_tr_data.push({
                                'bay_name': $(this).find('td:eq(2)').find("select option:selected").text(),
                                'technicain': $(this).find('td:eq(3)').find("select option:selected").text(),
                                'start_date': $(this).find('td:eq(4)').find(".st_date").val(),
                                'end_date': $(this).find('td:eq(5)').find(".en_date").val(),
                                'order_id':order_id,
                                'task_id':$(this).find('td:eq(1)').find("#task_ids").val(),
                            });


                        labour_data.push({
                            'order':order_id,
                            'data': labour_table_tr_data,

                        });
                       }
                    });
                    ta_values.push({
                        'labour': labour_data,

                    });
                    //console.log(ta_values)
                });

                /*if (!valid_lines.indexOf("no")){
                    alert("Bay / Technician is not Available.")
                    return false;
                }*/
                // loader after validation
                /*$('#techallocation').block({
                    message: '<h3><img src="/wms/static/src/img/ajax-loader.gif" />Just a moment...</h3>',
                    css: { border: '3px solid #a00' }
                });*/
                //console.log(ta_values);
                ajaxserviceplanner('bay_tech', ta_values, e);

            }
            else {
                e.stopPropagation();
            }
        });

        /*$('#techallocation').on( "click","#datetimepicker1", function(e) {
            $(this).datetimepicker({
                    icons: {
                        time: "fa fa-clock-o",
                        date: "fa fa-calendar",
                        up: "fa fa-arrow-up",
                        down: "fa fa-arrow-down"
                    }
                });

        });

        $('#techallocation').on( "click","#datetimepicker2", function(e) {
            $(this).datetimepicker({
                    icons: {
                        time: "fa fa-clock-o",
                        date: "fa fa-calendar",
                        up: "fa fa-arrow-up",
                        down: "fa fa-arrow-down"
                    }
                });

        });*/


        /*$('#techallocation').on( "click","#datetimepicker1", function(e) {
            $('#st_date').intimidatetime().intimidatetime('open');
        });
        $('#techallocation').on( "click","#datetimepicker2", function(e) {
            $('#en_date').intimidatetime().intimidatetime('open');
        });*/
        //alert(new Date());
        //var date_time = moment().format("MM DD YYYY LT");
        //alert(date_time);

        //var date_time = dateFormat(new Date(), "MM/dd/yyyy hh:mm TT");
        var dateNow = new Date();

        $('#techallocation').on( "click",".st_date", function(e) {
            $('.st_date').intimidatetime({format:'MM/dd/yyyy hh:mm TT'}).intimidatetime('open');
        });
        $('#techallocation').on( "click",".en_date", function(e) {
            $('.en_date').intimidatetime({format:'MM/dd/yyyy hh:mm TT'}).intimidatetime('open');
        });

        $('#techallocation').on( "click",".start_datetime", function(e) {
//            console.log($(this));
            //alert('oo');
//            console.log('p1',$('.start_datetime').parent().parent().find('.st_date'));
//            console.log('p2',$('.st_date'));
            $('.start_datetime').intimidatetime({format:'MM/dd/yyyy hh:mm TT'}).intimidatetime('open');
//            $('.st_date').focus();
        });
        $('#techallocation').on( "click",".end_datetime", function(e) {
            $('.end_datetime').intimidatetime({format:'MM/dd/yyyy hh:mm TT'}).intimidatetime('open');

        });

	    /*$('*[name=tech_start_date]').val('');
         $("div.input-group span.fa-calendar").on('click', function(e) {
            $(e.currentTarget).parents().eq(1).find('#start_date').focus();
            });

         $("div.input-group > span").on('click', function(e) {
            $(e.currentTarget).parents().eq(1).find('#start_date').focus();
            });

         //$('*[name=tech_end_date]').appendDtpicker({'closeOnSelected':true,"dateFormat": "DD/MM/yyyy hh:mm"});
         $('*[name=tech_end_date]').val('');
         $("div.input-group span.fa-calendar").on('click', function(e) {
            $(e.currentTarget).parents().eq(1).find('#end_date').focus();
            });

         $("div.input-group span.input-group-addon").on('click', function(e) {
            $(e.currentTarget).parents().eq(1).find('#end_date').focus();
            });


        // $('*[name=test_start_date]').appendDtpicker({'closeOnSelected':true,"dateFormat": "DD/MM/yyyy hh:mm"});
         $('*[name=test_start_date]').val('');
         $("div.input-group span.fa-calendar").on('click', function(e) {
            $(e.currentTarget).parents().eq(1).find('#start_date').focus();
            });
        $("div.input-group span.input-group-addon").on('click', function(e) {
            $(e.currentTarget).parents().eq(1).find('#start_date').focus();
            });        // $('*[name=test_end_date]').appendDtpicker({'closeOnSelected':true,"dateFormat": "DD/MM/yyyy hh:mm"});$('*[name=test_end_date]').val('');
         $("div.input-group span.fa-calendar").on('click', function(e) {
            $(e.currentTarget).parents().eq(1).find('#end_date').focus();
            });

         $("div.input-group span.input-group-addon").on('click', function(e) {
            $(e.currentTarget).parents().eq(1).find('#end_date').focus();
            });*/

	    $(".reg-ok").on('click',function(){
           var x = $('#regno_vehicle').val();
           if (x.length < 4){
               alert("Please Enter Last 4 Digit Or Complete Vehicle No");

            }
           else{
                $('#security').submit();
                }

       });

    $("#walkin_submit").on('click',function(){
    var float_value = /^[-+]?[0-9]+\.[0-9]+$/;
    var mileage = $('#walkin_kilo').val();

        if (mileage !== "" && mileage <= 0) {
            alert("Please Enter Numeric No");
        }
        else if (mileage !== "" && !$.isNumeric(mileage)) {
            alert("Please Enter Numeric No");
        }
        else if (mileage.match(float_value)) {
            alert("Please Enter Numeric No");
        }
        else{
            $('#security_walkin').submit()
           }
    });

    $("#appointment_submit").on('click',function(){
    var float_value = /^[-+]?[0-9]+\.[0-9]+$/;
    var mileage = $('#kilo').val();

        if (mileage !== "" && mileage <= 0) {
            alert("Please Enter Numeric No");
            return false
        }
        else if (mileage !== "" && !$.isNumeric(mileage)) {
            alert("Please Enter Numeric No");
            return false
        }
        else if (mileage.match(float_value)) {
            alert("Please Enter Numeric No");
            return false
        }
        else{
            $('#form_app').submit()
           }
    });


    //security front view all Button click
    $(".sec_clk_count_app").on('click',function(){
        $('.sec_clk_count_app').submit();
    });
    $(".sec_clk_count_turnup").on('click',function(){
        $('.sec_clk_count_turnup').submit();
    });
    $(".sec_clk_count_walkin").on('click',function(){
        $('.sec_clk_count_walkin').submit();

    });
    $(".sec_clk_count_delivered").on('click',function(){
        $('.sec_clk_count_delivered').submit();

    });

    $(".sec_clk_count_testdrive").on('click',function(){
        $('.sec_clk_count_testdrive').submit();
    });

    $(".icon-clk-search").on('click',function(){
        $('#myTags > li > input').focus();
        e.preventDefault();
        $('#myTags > li > input').focus();
    });



       $("#testdrive_submit").on('click',function(){
//        var float_value = /^[-+]?[0-9]+\.[0-9]+$/;
//        var premileage = $('#testdrive_prekilo').val();
////            (premileage);
//        var mileage = $('#testdrive_kilo').val();
////            alert(mileage);
//            if (mileage <= 0) {
//                alert("Please Enter Numeric No");
//            }
//            else if (!$.isNumeric(mileage)) {
//                alert("Please Enter Numeric No");
//            }
//            else if (mileage < premileage) {
//                alert("Entered Mileage cannot be less than the last Mileage Out");
//            }else if (!mileage){
//            	alert("Mileage can not be null.");
//            }
//            else if (mileage.match(float_value)) {
//                alert("Please Enter Numeric No");
//            }
//            else{
                $('#security_testdrive').submit();

//            }
   });



//    $(".cre_clk_count").on('click',function(){
//        $('.cre_clk_count').submit();
//    });

//    $(".cre_frontdesk_clk_count").on('click',function(){
//        $('.cre_frontdesk_clk_count').submit();
//    });
//
//    $(".sa_clk_count").on('click',function(){
//        $('.sa_clk_count').submit();
//    });
//
//    $(".sa_preparation_clk_count").on('click',function(){
//        $('.sa_preparation_clk_count').submit();
//    });


    $(".open_form").on('click',function(){
        var id = $(this).attr('id');
        ajax.jsonRpc("/action_open_form", 'call', {'ids':id})
        .then(function (data) {
            $('#display_form').css('display','block');
            if (data){
                $('#name').text(data.doc);
                $('#reg').text(data.regn);
                $('#vin_no').text(data.vin);
                $('#model_no').text(data.model);
                $('#customer').text(data.customer);
                $('#mobile').text(data.mobile);
                $('#appo').text(data.appointment);
                $('#del').text(data.delivery);
                $('#res').text(data.sa);
                $('#type').text(data.type);
                $('html,body').animate({scrollTop: $("#id1").offset().top},'slow');
            }
        });

    });

	
 // page is now ready, initialize the calendar...
	//$('#calendar').fullCalendar();
	$('#external-events .fc-event').each(function() {
//	    alert('pp');
	      // store data so the calendar knows to render an event upon drop
	      $(this).data('event', {
	    	t_resourceId : $(this).attr('id'),  
	        title: $.trim($(this).text()), // use the element's text as the event title
	        stick: true // maintain when user navigates (see docs on the renderEvent method)
	      });

	      // make the event draggable using jQuery UI
	      $(this).draggable({
	        zIndex: 999,
	        revert: true,      // will cause the event to go back to its
	        revertDuration: 0  //  original position after the drag
	      });

	    });
	
	$('#group_filter .fc-event').each(function() {
	      // store data so the calendar knows to render an event upon drop
	      $(this).data('event', {
	        title: $.trim($(this).text()), // use the element's text as the event title
	        stick: true // maintain when user navigates (see docs on the renderEvent method)
	      });

	      // make the event draggable using jQuery UI
	      $(this).draggable({
	        zIndex: 999,
	        revert: true,      // will cause the event to go back to its
	        revertDuration: 0  //  original position after the drag
	      });

	    });
	
	var selected_view = $("#view :selected").val();
	//alert(selected_view);
	if (selected_view != undefined){
	    resource_planner_ajaxcall(selected_view)
	    setInterval(function() { resource_planner_ajaxcall(selected_view); }, 60000);
	}
	$('#skill_grp').on('change', function() {
		var skill = this.value;
		var IDs = [];
		$("#group_filter").find(".res_div").each(function(){ IDs.push(parseInt(this.id)); });
		//console.log(IDs);
		ajax.jsonRpc("/resource_planner/tech_skill_grp", 'call', { 'skill': skill,'tech_id': IDs}).then(function(data) {
			if(data){
				$('#group_filter').html(data['grp']);
				$('#group_filter .fc-event').each(function() {
					//alert('yyy');
				      // store data so the calendar knows to render an event upon drop
				      $(this).data('event', {
				        title: $.trim($(this).text()), // use the element's text as the event title
				        stick: true // maintain when user navigates (see docs on the renderEvent method)
				      });

				      // make the event draggable using jQuery UI
				      $(this).draggable({
				        zIndex: 999,
				        revert: true,      // will cause the event to go back to its
				        revertDuration: 0  //  original position after the drag
				      });

				    });
			}
		});
	});
	

	function resource_planner_ajaxcall(view) {
        var show_resource = $(".showall").text();
        var button_text = $(".fc-showall-button").text();
        try {
		    ajax.jsonRpc("/resource_planner/get", 'call', { 'view': view,'showall':show_resource,'button_text':button_text}).then(function(data) {
			if (data['status']){
				//console.log(data['events']);
				$('#calendar').fullCalendar({
					  now: new Date(),
				      editable: true, // enable draggable events
				      droppable: true,
				      aspectRatio: 1.8,
				      scrollTime: '00:00', // undo default 6am scrollTime
				      contentHeight: 375,
				      header: {
				        left: 'today prev,next showall',
				        center: 'title',
				        right: 'timelineDay,timelineThreeDays,agendaWeek,month,listWeek'
				      },
				      customButtons: {
                          showall: {
                            text: 'Show All',
                            click: function() {
                              var selected_view = $("#view :selected").val();
                              var showall = "True"
                              var showall_value =  $(".showall").text(showall);
                              var button_text = $(".fc-showall-button").text();
                              if (button_text == 'Show Own'){
                                location.reload();
                              }
                              ajax.jsonRpc("/resource_planner/get", 'call', { 'view': selected_view,'showall':showall_value.text(),'button_text':button_text}).then(function(data) {
                                  if(data){
                                      $(".fc-showall-button").text('Show Own');
                                      for(var i=0;i <= data.resource.length;i++){
                                        $('#calendar').fullCalendar( 'addResource',data.resource[i],scroll );
                                      }

                                      $('#calendar').fullCalendar('removeEvents');
                                      $('#calendar').fullCalendar('addEventSource', data['events']);
                                      $('#calendar').fullCalendar('rerenderEvents');
                                  }
                              });
                            }
                          },
                        },
				      defaultView: 'timelineDay',
				      views: {
				        timelineThreeDays: {
				          type: 'timeline',
				          duration: { days: 3 }
				        }
				      },
				      eventOverlap: true,
				      resourceColumns: [
				          {group: true,labelText: "Resource's",field: 'resource'},
				          {labelText: 'Entry Type',field: 'title'},
				        ],
				      resources:data['resource'],
				      events:data['events'],
				      eventClick: function(calEvent, jsEvent, view) {
                        if(calEvent['event_type'] == 'plan'){
                        ajax.jsonRpc("/resource_planner/chip_clk", 'call', {'event_id':calEvent.id}).then(function(data) {
                              //console.log(data);
                              if (data['status']){
                                if (data['clk'] == 'dbl'){
                                       $('#task_dobule_clk').empty();
                                       $('#regn').html(data['order_id']);
                                       $('.reg_no').html(data['reg_no']);
                                       //$('.time_unit').html(data['reg_no']);
                                       $('.repair_order').html(data['repair_order']);
                                       $('.delivery_datetime').html(data['delivery_datetime']);
                                       $('.service_advisor').html(data['service_advisor']);

                                       $('#Dblclick').modal('show');
                                  }
                                  if (data['clk'] == 'single'){
                                      $('#technician_task').empty();
                                      $('#technician_task').append(data['result']);
                                      $('#technician_task').modal('show');
                                      $('#regn').html(data['order_id']);
                                  }

                              }
                          });
                        }
                        //*alert('Event: ' + calEvent.title);
                        //alert('Coordinates: ' + jsEvent.pageX + ',' + jsEvent.pageY);
                        //alert('View: ' + view.name);

                        // change the border color just for fun
                        //$(this).css('border-color', 'red');

                      },
                      viewRender: function(view,element){
                    	  if (global_count == 0){
				    	        var tr_length = $('.fc-time-area').find('.fc-content').find('.fc-rows').find('table tr').length;
				    	        var td_height = $('.fc-view').find('.fc-body').find('.fc-time-area').find('.fc-content').height();
				    	        var total_length = tr_length * tr_length
				    	        var all_len = total_length * total_length
				    	        var height = td_height + all_len
				    	        var pixel_height = height + 'px;'
				    	        var first_height = 0;
				    	        var index_count = 0;
	                              $('.fc-resource-area').find('.fc-content').find('.fc-widget-content').each(function(index,e) {
	                              	
	                              	if(index == 0){
	                              		first_height = $(this).height();
	                              	}
	                              	index_count = index;
	                              });
                              var act_height = first_height * (index_count/2);
                              var act_height_px = act_height + 'px;'
				    	       $('.fc-time-area').find('.fc-content').find('table td:first').append('<span style="background: rgb(255, 54, 0);position: absolute;z-index: 999;width:1px;display:block;height:'+act_height_px+'top: 0px;color: white;" class="current_time">.</span>');

				    	      // $('.fc-time-area').find('.fc-content').find('table th').each(function(index,e) {
                                  //var time = $(this).text();
                                  //var res_digit = time.slice(0,-2);
                                 // var res_am_pm = time.slice(-2);
                                  //if(res_am_pm == 'pm'){
                                      //if(res_digit != 12){
                                          //res_digit = parseInt(res_digit) + 12
                                     //}
                                 // }
                                  //else{
                                     // if(res_digit == 12){
                                          //res_digit = 0
                                     // }
                                  //}
                                  //var dt = new Date();
                                  //var hour = dt.getHours();

                                  //var min = dt.getMinutes();
                                  //if (hour == res_digit){
                                  	  //var current_distance = parseInt($(this).width()) * 2
                                    //  var distance = parseInt(current_distance)
                                     // var width_min = distance/60;
                                     // var min_wid = min * width_min;
                                      //var left = (index * distance) + (index * 4) + min_wid;
                                     // $('.current_time').css("left", left+'px');
                                 // }
				    	      //});

				    	    }
				    	    global_count += 1
				    	
                      },
                      eventResize: function(event, delta, revertFunc) {
				          console.log('EVENT',event.event_type);
				          if (event.event_type == 'actual'){
				                location.reload();

				          }
				          else{
                              if (confirm("Are you Sure, do you want to confirm?")) {
                                  ajax.jsonRpc("/resource_planner/event_extended", 'call', { 'stop':event.end.format(),'id':event.id}).then(function(data) {
                                       if (data['status']){
                                            ajax.jsonRpc("/resource_planner/event_extend_timesheet", 'call', { 'stop':event.end.format(),'event_id':event.id}).then(function(data) {
                                                if (data['status']){
                                                    location.reload();
                                                }
                                            });
                                       }
//                                      if (data['status']){
//                                          location.reload();
//                                      }
                                  });
//                                  ajax.jsonRpc("/resource_planner/event_extended", 'call', { 'stop':event.end.format(),'id':event.id}).then(function(data) {
//                                      if (data['status']){
//                                          ajax.jsonRpc("/resource_planner/event_extend_timesheet", 'call', { 'stop':event.end.format(),'id':event.id}).then(function(data) {
//                                              if (data['status']){
//                                                  location.reload();
//                                              }
//                                          });
//                                      }
//                                  });
                              }
				          }
				          /*if (!confirm("is this okay?")) {
				              revertFunc();
				          }*/
				          	
				      },
				      drop: function(date, jsEvent, ui, resourceId) {
				          //console.log(jsEvent);
				          //console.log(ui);
				    	  //var checkedValue = $('.tech_select:checked').val();
				    	  //alert('ll');
				    	  var self = $(this);
				    	  //console.log($(this).prev().prop('checked'));
				    	  var bay_tech_details = [];
				    	  //if($(this).prev()[0].className == 'bay_select'){
				    		  var is_tech = false;
				    		  $("input:checkbox[class=tech_select]:checked").each(function () {
				    			  var task_details = {}
				    			  is_tech = true;
				    			  //if(self.prev()[0].className == 'tech_select'){
				    				  task_details['title'] = $(this).next().text();
					    			  task_details['res_id'] = $(this).next().attr('id');
					    			  $("input:checkbox[class=bay_select]:checked").each(function () {
					    				  task_details['ro_id'] = $(this).next().attr('rid');
					    			  });		  
				    			  //}
				    			  
				    			  
				    			  bay_tech_details.push(task_details);
					          });
				    	 // }
				    	  /*if($(this).prev()[0].className == 'tech_select'){*/
				    		  
				    		  $("input:checkbox[class=bay_select]:checked").each(function () {
				    			  var task_details1 = {}
					              //alert("Id: " + $(this).attr("id") + " Value: " + $(this).val());
					    		  //console.log($(this).next().attr('rid'));
				    			  task_details1['title'] = $(this).next().text();
				    			  task_details1['res_id'] = $(this).next().attr('id');
				    			  task_details1['ro_id'] = $(this).next().attr('rid');
				    			  bay_tech_details.push(task_details1);
					          });
				    	  /*}*/
				    	  //console.log('ro_details',bay_tech_details);
				          var title = $(this).text();
                          var res_id = $(this).attr('id');
                          var ro_id = $(this).attr('rid');
				          var selected_view = $("#view :selected").val();
				          ajax.jsonRpc("/resource_planner/get_event_types", 'call', {'selected_view':selected_view}).then(function(data) {
                                if(data['activity_types']){
                                    var types = data['activity_types']
                                    var type_with_checkbox = ''
                                    if(types.length <= 1){
                                        if(types.length >= 1){
                                            var types = types[0]
                                        }
                                        else{
                                            var types = false;
                                        }
                                        //if(res_id){
                                          //ajax.jsonRpc("/resource_planner/external_event_tech", 'call', {'start':date.format(),'resourceId':res_id,'title':title,'event_type':types}).then(function(data) {
                                              //if (data['status']){
                                                 // location.reload();
                                              //}
                                          //});
                                          //}else{
                                              ajax.jsonRpc("/resource_planner/external_event", 'call', {'start':date.format(),'resourceId':resourceId,'ro_details':bay_tech_details,'event_type':types}).then(function(data) {
                                                  if (data['status']){
                                                	  ajax.jsonRpc("/resource_planner/external_event_timesheet", 'call', {'start':date.format(),'resourceId':resourceId,'ro_details':data['ro_details'],'event_type':types}).then(function(data) {
                                                          if (data['status']){
                                                        	  location.reload();
                                                          }
                                                      });
                                                  }
                                              });
                                          //}
                                    }
                                    else{
                                        $.each(types, function( index, value ) {
                                            type_with_checkbox += "<input type='radio' id='radio-box"+index+"' name='type_radio' value='"+value+"'/>"+value+"<br/>"

                                        });
                                        $("#confirm-box").append(type_with_checkbox);
                                        $("#confirm-box").dialog({
                                            'title': 'Confirm!',
                                            'buttons': {
                                                'Confirm': function(event) {
                                                      var radioValue = $("input[name='type_radio']:checked").val();
                                                      if(res_id){
                                                          ajax.jsonRpc("/resource_planner/external_event_tech", 'call', {'event_type':radioValue,'start':date.format(),'resourceId':res_id,'title':title}).then(function(data) {
                                                              if (data['status']){
                                                                  location.reload();
                                                              }
                                                          });
                                                      }else{
                                                          ajax.jsonRpc("/resource_planner/external_event", 'call', {'event_type':radioValue,'start':date.format(),'resourceId':resourceId,'title':title,'ro_id':ro_id}).then(function(data) {
                                                              if (data['status']){
                                                                  location.reload();
                                                              }
                                                          });
                                                      }
                                                },
                                                'Cancel': function(event) {
                                                    $( this ).dialog( "close" ).addClass("dialog-close");
                                                    location.reload();
                                                }
                                            }
                                        });

                                       }
                                       //location.reload();
                                    }
                                 });

				          // is the "remove after drop" checkbox checked?

				          if ($('#drop-remove').is(':checked')) {
				            // if so, remove the element from the "Draggable Events" list
				            $(this).remove();
				          }
				        },
				        eventReceive: function(event) { // called when a proper external event is dropped
				          //console.log(event.start);
				          //console.log(event.title);
				          //console.log(event.resourceId);
				          //console.log('eventReceive', event);
				        },
				        eventDrop: function(event) { // called when an event (already on the calendar) is moved
				          //console.log('eventDrop', event);
				        },
				        eventDrop: function(event, delta, revertFunc) {
					    	  //console.log(event);
					    	  //console.log(delta._milliseconds);
					          //alert(event.title + " was dropped on " + event.start.format());
					          //var confirm = confirm("Are you sure about this change?");
					          //alert(confirm);
					          if (confirm("Are you sure about this change?")) {
					              //revertFunc(event.title,event.start.format(),event.end.format());
					        	  ajax.jsonRpc("/resource_planner/update_event", 'call', { 'event_id': event.id,'start':event.start,'stop':false,'resourceId':event.resourceId,'duration':delta._milliseconds}).then(function(data) {
					        		  if (data['status']){
					        			  location.reload();
					        		  }
					        	  });
					          }

					      },
				      eventRender: function(event, element) {
				    	    $(element).tooltip({title: event.title});
				    	    
				    	},
				    	/*eventAfterRender: function(event, element, view) {
                          $(element).css('width','10px');
                        }*/

                        /*eventAfterAllRender: function(view){
                            alert(view.timeGrid);
                            if (moment().isBetween(view.start, view.end)) {
                                alert(moment.duration(moment() - view.start));
                                var scrollSlots = moment.duration(moment() - view.start) / moment.duration(view.viewSpec.overrides.slotDuration);
                                //alert(scrollSlots);
                                var slotWidth = view.timeGrid.slotWidth;
                                //alert(slotWidth);
                                var scroll = {left: 50050};
                                view.addScroll(scroll);
                            }
                          },*/
				    });
				//window.location.href = '/resource_planner';
			}
		});
		}
		catch(err) {
            console.log(err);
        }
	}
	
	function revertFunc(title,start,end){
		alert(title);
	}

	var date_input=$('input[name="date"]'); //our date input has the name "date"
    var container=$('.bootstrap-iso form').length>0 ? $('.bootstrap-iso form').parent() : "body";
    var options={
        format: 'dd/mm/yyyy',
        container: container,
        todayHighlight: true,
        autoclose: true,
      };
    date_input.datepicker(options);


    $(".sb-icon-search").click(function (e) {
            e.preventDefault();
            $('#myTags').animate({width: 'toggle'}).focus();
            $('#myTags > li > input').focus();
        });


    $(".go_back").on('click',function(){
        window.history.back();
    });


    $(".appointments").on('click',function(){
        var order_ids = $(this).next('td').find('div').html();
        var date = $(".hidden-div").text();
        //var hold_order_id = $(this).parent().find('.margin-td').next('td').next('td').next('td').text();
        var context = {'orders': order_ids,'date':date};
            ajax.jsonRpc("/all-list-vehicle-details", 'call', context).then(function(data) {
                var url = data['urls']
                window.location.href = url
            });
    });
    $(".app_walk").on('click',function(){
            var app_walk_id = $(this).parent().find('.'+$(this).attr('id')).html();
            var context = {'app_walk_id': app_walk_id};
            ajax.jsonRpc("/all-list-timeslot", 'call', context).then(function(data) {
               var url = data['urls']
               window.location.href = url
            });
    });

});
});