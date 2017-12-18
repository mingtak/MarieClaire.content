$(document).ready(function () {

    var ga_chart = new Vue({
        el: '#ga_chart',
        data: {
            message: 'Hello Vue!',
            xs: {'aaa': 11111},
            columns: []
        }
    })

    $('.ga_page_title, .start-date, .end-date, .event_checkbox').change(function(){
        
        $('.download').attr('href', '');
        ga_chart.xs = {}
        ga_chart.columns = []
        gatGaData(ga_chart)
    })
    
    $('#nav_line, #nav_bar, #nav_pie').click(function (e) { 
        ga_chart.xs = {}
        ga_chart.columns = []
        gatGaData(ga_chart)

    });
    
    $('.del-btn').click(function (e) {
        if( confirm('確認要刪除嘛') ){
            data = {
                'time':$('.del-time').val(),
                'check_list':checkedList()
            }
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
    data = {
        'checkList': checkedList(),
        'start': start,
        'end': end 
    }
    $.ajax({
        type: "POST",
        url: url,
        data: data,
    }).done(function(value){
        resultArray = jQuery.parseJSON(value)
        ga_chart.xs = resultArray[0]
        for(key in resultArray[1]){
            for(i=0; i<resultArray[1][key].length; i++){
                ga_chart.columns.push(resultArray[1][key][i])
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
        if(ga_chart.columns.length == 0){
            alert('no data')
        }
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
genC3 = function(xs, columns, regions__list, event_order__list, event_name__list){
    // groups_columns = []
    // for(i=1;i<columns.length;i+=4){
    //     groups_columns.push(columns[i][0])
    // }
    
    select_type = $('.active')[0].id
    if (select_type == 'nav_line'){
        draw_type = 'line'
    }else if(select_type == 'nav_bar'){
        draw_type = 'bar'
    }else if(select_type == 'nav_pie'){
        draw_type = 'pie'
    }

    if(columns.length > 40){
        height = 1000
    }else{
        height = null
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
            // groups: [groups_columns]
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