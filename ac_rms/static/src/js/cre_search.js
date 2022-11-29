$( document ).ready(function() {
    myTags = $('#cremyTags');
    myTags.tagit({
        afterTagAdded: function (evt, ui) {
            if (!ui.duringInitialization) {
                search();
            }
        },
        afterTagRemoved: function (evt, ui) {
            search();
        }
    });
    $('#chkBoth').click(function () {
        search();
    });
    var filter = ''
    var search = function () {
        if ($('.tagit-label').length) {


            $("#my_pending_task").find("tbody .modal_rows_task").hide();
            $(".cls-table-search tbody .modal_rows_task").hide();
            var toShow = [];

            $('.tagit-label').each(function () {

                filter = $(this).text();
                value_time_stamp = $('#search-value').text();
                if(value_time_stamp.trim() == 'Time Stamp'){
                    $(".cls-table-search tbody .modal_rows_task").each(function () {
                        if ($(this).text().search(new RegExp(filter, "i")) >= 0) {
                            toShow.push($(".cls-table-search tbody .modal_rows_task").index(this));
                        }
                    });
                }
                else{
                $("#my_pending_task tbody .modal_rows_task").each(function () {
                    if ($(this).text().search(new RegExp(filter, "i")) > 0) {
                        toShow.push($("#my_pending_task tbody .modal_rows_task").index(this));
                    }
                });
                }
            });
            if($(".other-search").length){
                alert('cre_search');
                if(toShow == ""){
                    $.confirm({
                        title: '',
                        content: 'This Vehicle is not available in this category, would you like to search it on other categories.',
                        buttons: {
                            confirm: function () {
                                $('.tagit-label').each(function () {
                                    filter = $(this).text();
                                });
                                $.ajax({
                                    url: "/bay-tech-popup/get",
                                    type: "POST",
                                    dataType: 'json',
                                    data: JSON.stringify({params: {result: filter}}),
                                    contentType: 'application/json',
                                }).done(function(result) {
                                    $('#baytech-allocation-table').empty();
                                    $('#baytech-allocation-table').append(result.result.html_data);
                                });
                            },
                            cancel: function () {
                            }
                        }
                    });
                }
            }
            if ($('.tagit-label').length > 1) {
                var filterShow = [];
                var outputArray = [];
                $(toShow).each(function (i, value) {
                    if (($.inArray(value, outputArray)) == -1) {
                        outputArray.push(value);
                    }
                });
                $(outputArray).each(function (i, value) {
                    var index = toShow.indexOf(value);
                    toShow.splice(index, 1);
                });
            }

            $(toShow).each(function (i, value) {
                if(value_time_stamp.trim() == 'Time Stamp'){
                    $(".cls-table-search tbody .modal_rows_task").eq(value).fadeIn();
                }
                else{
                    $("#my_pending_task tbody .modal_rows_task").eq(value).fadeIn();
                }
            });


        } else {
            if(value_time_stamp.trim() == 'Time Stamp'){
                $(".cls-table-search tbody .modal_rows_task").fadeIn();
            }
            else{
                $("#my_pending_task tbody .modal_rows_task").fadeIn();
            }
        }
    }
});