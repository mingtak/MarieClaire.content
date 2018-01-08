$(document).ready(function () {
    $('.ga_page_title, .ga_select_checkbox, .datepicker, .event_checkbox, .del-time, .btn-danger').show();
    $('.ga_table_checkbox').hide();
    var ga_chart = new Vue({
        el: '#ga_chart',
        data: {
            message: 'Hello Vue!',
            xs: {'aaa': 11111},
            columns: [],
            raw_xs: {'aaa': 11111},
            raw_columns: []
        }
    })

    $('.ga_page_title, .start-date, .end-date, .event_checkbox, .ga_select_data').change(function(e){
        $('.download').attr('href', '');
        ga_chart.xs = {}
        ga_chart.columns = []
        gatGaData(ga_chart)
    })

    $('#nav_line, #nav_bar, #nav_pie').click(function (e) { 
        ga_chart.xs = {}
        ga_chart.columns = []

        //table
        $('.ga_page_title, .ga_select_checkbox, .datepicker, .event_checkbox, .del-time, .btn-danger').show();                
        $('.ga_table_checkbox').hide()
        //table
        $('input').prop('checked',false)
        if($(this)[0].id == 'nav_pie'){
            $('.ga_select_checkbox').hide();
        }else{
            $('.ga_select_checkbox').show();
        }
        $(this).addClass('select_type')
        $(this).siblings().removeClass('select_type')
        gatGaData(ga_chart)
    });

    $('#nav_table').click(function (e) {
        $('input').prop('checked',false)
        $('.ga_table_checkbox').show()
        $('.ga_page_title, .ga_select_checkbox, .datepicker, .event_checkbox, .del-time, .btn-danger').hide();        
    });
    $('.ga_table_checkbox').change(function (e) { 
        getGaTable()
    });

    $('.del-btn').click(function (e) {
        if( confirm('確認要刪除嘛') ){
            data = {
                'time':$('input.del-time').val(),
                'check_list':checkedList()
            }
            debugger
            url = window.location.href.replace('ga_report', '@@del_ga_data')
            $.ajax({
                type: "POST",
                url: url,
                data: data,
                success: function (response) {
                    ga_chart.xs = {}
                    ga_chart.columns = []
                    gatGaData(ga_chart)
                }
            });
        }
    });
    
    $('.download').click(function (e) {
        checkList = ''
        $.each($('.ga_page_title:checked'), function (indexInArray, valueOfElement) {
             checkList += $(this).val()+','
        });
        start = $('.start-date').val()
        end = $('.end-date').val()
        urlStr = `download_ga_file?checkList[]=${checkList}&start=${start}&end=${end}`
        window.location.href = urlStr
    });
});

gatGaData = function(ga_chart){
    start = $('.start-date').val();
    end = $('.end-date').val();
    url = window.location.href.replace('ga_report', 'get_ga_data')
    select_type = $('.select_type')[0].id
    data = {
        'checkList': checkedList(),
        'start': start,
        'end': end,
        'select_type': select_type
    }
    $.ajax({
        type: "POST",
        url: url,
        data: data,
    }).done(function(value){
        select_type = $('.active')[0].id        
        resultArray = jQuery.parseJSON(value)
        selected = checkedSelect()
        ga_chart.xs = resultArray[0]
        if (select_type == 'nav_pie'){
            for(key in resultArray[1]){
                for(i=0; i<resultArray[1][key].length; i++){
                    ga_chart.columns.push(resultArray[1][key][i])
                }
            }
        }
        else{
            for(key in resultArray[1]){
                for(i=0; i<resultArray[1][key].length; i++){
                    if( i == 0 || selected.indexOf(i.toString()) != -1 ){
                        ga_chart.columns.push(resultArray[1][key][i])
                    }
                }
            }
        }
        var regions__list = []
        var event_order__list = []
        var event_name__list = []
        $('.event_checkbox').each(function(e){
            var event_start = this.dataset.start
            var event_end = this.dataset.end
            var event_order = this.dataset.order
            var event_name = this.value
            if( $(this).is(':checked') ){
                regions__list.push({start: event_start, end: event_end, class:event_order})
                event_order__list.push(event_order)
                event_name__list.push(event_name)
                
            }
        })
        genC3(ga_chart.xs, ga_chart.columns, regions__list, event_order__list, event_name__list)
    }).fail(function(){
        alert('Fail')
    })
}
checkedList = function(){
    result = []
    $.each($('.ga_page_title:checked'), function(index, value){
        result.push($(value).val())
    })
    return result
}
checkedSelect  = function(){
    result = []
    $.each($('.ga_select_data:checked'), function(index, value){
        result.push($(value).val())
    })
    return result
}

genC3 = function(xs, columns, regions__list, event_order__list, event_name__list){
    select_type = $('.select_type')[0].id

    selected_len = checkedSelect().length
    groups_columns = []
    if (select_type != 'nav_pie'){
        if(selected_len == 2){
            for(i=1; i<=columns.length; i+=3){
                tmp = []
                for(j=1; j<=selected_len; j++){
                    if(i==1){
                        tmp.push(columns[j][0])
                    }else{
                        tmp.push(columns[i+j-1][0])
                    }
                }
                groups_columns.push(tmp)
            }
        }
        if(selected_len == 3){
            for(i=1; i<=columns.length; i+=4){
                tmp = []
                for(j=1; j<=3; j++){
                    if(i==1){
                        tmp.push(columns[j][0])
                    }else{
                        tmp.push(columns[i+j-1][0])
                    }
                }
                groups_columns.push(tmp)
            }
        }
    }

    if (select_type == 'nav_line'){
        draw_type = 'line'
    }else if(select_type == 'nav_bar'){
        draw_type = 'bar'
    }else if(select_type == 'nav_pie'){
        draw_type = 'pie'
    }

    var chart = c3.generate({
        bindto: '#ga_chart',
        size: {
            height: 500,
        },
        data: {
            xs:xs,
            columns: columns,
            labels: true,
            type: draw_type,
            groups: groups_columns
        },
        axis: {
            x: {
                type: 'timeseries',
                tick: {
                    rotate: -20,
                    format: '%Y-%m-%d'
                },
            }
        },
        regions: regions__list,
        padding:{
            bottom: 70
        },
    });
    drawRegions(event_name__list, event_order__list)
    $('.hide_adv').show()
}
drawRegions = function(event_name__list, event_order__list){
    var rectOffset = function () {
                    return  d3.select(this.parentNode).select('rect').attr("x"); };
    for(i=0; i<event_name__list.length; i++){
        d3.select('.'+event_order__list[i])
        .append("text")
        .text(event_name__list[i])
        .attr('font-size','18px')
        .attr('font-family','微軟正黑體')
        .attr("dy","20")
        .attr("dx",rectOffset)
        .style("fill-opacity", 1)
        .attr("text-anchor", "start");
    }
}

getGaTable = function(){
    data = {
        'checkList': $('.ga_table_checkbox:checked').val(),
       }
    url = window.location.href.replace('ga_report', '@@ga_table')
    $.ajax({
        type: "post",
        url: url,
        data: data,
        success: function (response) {
            $('#ga_chart').html(response);
        }
    });
}