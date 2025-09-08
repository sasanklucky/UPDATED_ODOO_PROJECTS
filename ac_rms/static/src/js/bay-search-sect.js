$( document ).ready(function() {
    //console.log( "ready!sssss" );
    myTags = $('#baymyTags');
    var search_tag = '';
    console.log(myTags);
    myTags.tagit({
        afterTagAdded: function (evt, ui) {
            if (!ui.duringInitialization) {
                search_tag = 'baymyTags';
                search('baymyTags');
            }
        },
        afterTagRemoved: function (evt, ui) {
            search('baymyTags');
        }
    });
    $('#chkBoth').click(function () {
        search();
    });
    var filter = ''
    var search = function (search_type) {
        if ($('#baymyTags').find('.tagit-label').length) {

            $("#bay-search tbody .modal_rows").hide();
            $(".bay-search-sect tbody .bay_modal_rows").hide();
            var toShow = [];

            $('.tagit-label').each(function () {
                var parent_id = $(this).parent().parent().attr('id');
                if(parent_id == search_type){
                    filter = $(this).text();
                    value_time_stamp = $('#bay-search-value').text();
                    if(value_time_stamp.trim() == 'Bay Time Stamp'){

                            $(".bay-search-sect tbody .bay_modal_rows").each(function () {
                                //console.log($(this),filter);
                                if ($(this).text().search(new RegExp(filter, "i")) >= 0) {
                                    toShow.push($(".bay-search-sect tbody .bay_modal_rows").index(this));
                                }
                            });
                        }

                }
                else{
                $("#bay-search tbody .modal_rows").each(function () {
                    //console.log('testt..',$(this),filter);
                    if ($(this).text().search(new RegExp(filter, "i")) > 0) {
                        toShow.push($("#bay-search tbody .bay_modal_rows").index(this));
                    }
                });
                }
            });
            //alert(toShow);
            /*if($(".other-search").length){
                if(toShow == ""){
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
                }
            }*/
//$('#chkBoth').prop("checked") &&
            if ($('#baymyTags').find('.tagit-label').length > 1) {

                var filterShow = [];
                var outputArray = [];
                $(toShow).each(function (i, value) {
                    if (($.inArray(value, outputArray)) == -1) {
                        outputArray.push(value);
                    }
                });
                /*$(outputArray).each(function (i, value) {
                    var index = toShow.indexOf(value);
                    toShow.splice(index, 1);
                });*/
            }

            $(toShow).each(function (i, value) {
                if(value_time_stamp.trim() == 'Bay Time Stamp'){
                    $(".bay-search-sect tbody .bay_modal_rows").eq(value).fadeIn();
                }
                else{
                    $("#bay-search tbody .bay_modal_rows").eq(value).fadeIn();
                }
            });


        } else {
            if(value_time_stamp.trim() == 'Bay Time Stamp'){
                $(".bay-search-sect tbody .bay_modal_rows").fadeIn();
            }
            else{
                $("#bay-search tbody .bay_modal_rows").fadeIn();
            }
        }
    }
});