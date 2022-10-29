$( document ).ready(function() {
    //console.log( "ready!sssss" );

    fimyTags = $('#fimyTags');
    fimyTags.tagit({
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

            $("#techallocation_table tbody .modal_rows").hide();
            $(".cls-table-search tbody .modal_rows").hide();
            var toShow = [];

            $('.tagit-label').each(function () {

                filter = $(this).text();
                value_time_stamp = $('#search-value').text();
                if(value_time_stamp.trim() == 'Time Stamp'){
                    $(".cls-table-search tbody .modal_rows").each(function () {
                        //console.log($(this),filter);
                        if ($(this).text().search(new RegExp(filter, "i")) >= 0) {
                            toShow.push($(".cls-table-search tbody .modal_rows").index(this));
                        }
                    });
                }
                else{
                $("#techallocation_table tbody .modal_rows").each(function () {
                    //console.log('testt..',$(this),filter);
                    if ($(this).text().search(new RegExp(filter, "i")) > 0) {
                        toShow.push($("#techallocation_table tbody .modal_rows").index(this));
                    }
                });
                }
            });
            /*if(toShow == ""){
                $.confirm({
                    title: '',
                    content: 'This Vehicle is not available in this category, would you like to search it on other categories.',
                    buttons: {
                        confirm: function () {
                            $('.tagit-label').each(function () {
                                filter = $(this).text();
                                //alert(filter);
                                //alert('oo');
                            });
                            //$.alert('Confirmed!');
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
                            //$.alert('Canceled!');

                        }
                    }
                });
            }*/
//$('#chkBoth').prop("checked") &&
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
                    $(".cls-table-search tbody .modal_rows").eq(value).fadeIn();
                }
                else{
                    $("#techallocation_table tbody .modal_rows").eq(value).fadeIn();
                }
            });


        } else {
            if(value_time_stamp.trim() == 'Time Stamp'){
                $(".cls-table-search tbody .modal_rows").fadeIn();
            }
            else{
                $("#techallocation_table tbody .modal_rows").fadeIn();
            }
        }
    }
});