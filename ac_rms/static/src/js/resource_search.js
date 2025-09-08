$( document ).ready(function() {
    //console.log( "ready!sssss" );
    myTags = $('#techmyTags');
    var search_tag = '';
    console.log(myTags);
    myTags.tagit({
        afterTagAdded: function (evt, ui) {
            if (!ui.duringInitialization) {
                //console.log(ui);
                //console.log(ui.tag);
                search_tag = 'techmyTags';
                search('techmyTags');
            }
        },
        afterTagRemoved: function (evt, ui) {
            search('techmyTags');
        }
    });
    $('#chkBoth').click(function () {
        console.log($(this).html());
        search();
    });
    var filter = ''
    var search = function (search_type) {
        if ($('#techmyTags').find('.tagit-label').length) {

            $("#resource-search tbody .tech_modal_rows").hide();
            $(".resource-search-sect tbody .tech_modal_rows").hide();
            var toShow = [];

            $('.tagit-label').each(function () {
                var parent_id = $(this).parent().parent().attr('id');

                if(parent_id == search_type){

                    filter = $(this).text();
                    value_time_stamp = $('#tech-search-value').text();
                    if(value_time_stamp.trim() == 'Tech Time Stamp'){

                            $(".resource-search-sect tbody .tech_modal_rows").each(function () {
                            //console.log($(this),filter);

                            if ($(this).text().search(new RegExp(filter, "i")) >= 0) {
                                toShow.push($(".resource-search-sect tbody .tech_modal_rows").index(this));
                            }
                        });
                        }

                }
                else{
                $("#resource-search tbody .tech_modal_rows").each(function () {
                    //console.log('testt..',$(this),filter);
                    if ($(this).text().search(new RegExp(filter, "i")) > 0) {
                        toShow.push($("#resource-search tbody .tech_modal_rows").index(this));
                    }
                });
                }
            });
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
            if ($('#techmyTags').find('.tagit-label').length > 1) {
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
                if(value_time_stamp.trim() == 'Tech Time Stamp'){
                    $(".resource-search-sect tbody .tech_modal_rows").eq(value).fadeIn();
                }
                else{
                    $("#resource-search tbody .tech_modal_rows").eq(value).fadeIn();
                }
            });


        } else {
            if(value_time_stamp.trim() == 'Tech Time Stamp'){
                $(".resource-search-sect tbody .tech_modal_rows").fadeIn();
            }
            else{
                $("#resource-search tbody .tech_modal_rows").fadeIn();
            }
        }
    }
});