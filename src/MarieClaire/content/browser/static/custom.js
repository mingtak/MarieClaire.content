/* custom.js */

// dfp Line chart
genC3 = function(xs, columns, regions__list, event_order__list, event_name__list){
    groups_columns = []
    for(i=1;i<columns.length;i+=4){
        groups_columns.push(columns[i][0])
    }

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
        bindto: '#line-chart',
        size: {
            height: 500,
        },
        data: {
            xs:xs,
            columns: columns,
            labels: true,
            type: draw_type,
            groups: [groups_columns]
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
// 選取有打勾的項目
checkedList = function(){
    result = []
    $.each($('.dfp-order:checked'), function(index, value){
        result.push($(value).val())
    })
    return result
}

// 畫線
drawLine = function(dfpLine){
    data = {'orderList': checkedList(),
            'start': $('.start-date').val(),
            'end': $('.end-date').val()
           }
    url = window.location.href.replace('custom_report', '@@get_dfp_report')
    $.post(
        url,
        data = data,
    ).done(function(value){
        resultArray = jQuery.parseJSON(value)
        dfpLine.xs = resultArray[0]
        for(key in resultArray[1]){
            for(i=0; i<resultArray[1][key].length; i++){
                dfpLine.columns.push(resultArray[1][key][i])
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
        genC3(dfpLine.xs, dfpLine.columns, regions__list, event_order__list, event_name__list)

    }).fail(function(){
        alert('Fail')
    })
}

// Line Chart, Main
$(document).ready(function(){
    // VUE
    var dfpLine = new Vue({
        el: '#dfp-line',
        data: {
            message: 'Hello Vue!',
            xs: {'aaa': 11111},
            columns: []
        }
    })

    // 全選
    $('.dfp-select-all').click(function(){
        if($(this).is(':checked')){
            $(this).parent().parent().find('input').prop('checked',true)
            drawLine(dfpLine)
        }else{
            $('input').prop('checked', false)
            dfpLine.xs = {}
            dfpLine.columns = []
            genC3(dfpLine.xs, dfpLine.columns)
        }
    })
    $('.order-btn').click(function (e) {
        $(this).siblings().toggleClass("hide_element")
    });
    // 單選, 時間改變
    $('.dfp-order, .start-date, .end-date, .event_checkbox').change(function(){
        
        $('.download').attr('href', '');
        dfpLine.xs = {}
        dfpLine.columns = []
        drawLine(dfpLine)
    })
    $('#nav_line, #nav_bar, #nav_pie').click(function (e) { 
        dfpLine.xs = {}
        dfpLine.columns = []
        drawLine(dfpLine)
    });
    $('.del-btn').click(function (e) {
        if( confirm('確認要刪除嘛') ){
            data = {
                'time':$('.del-time').val(),
                'check_list':checkedList()
            }
            url = window.location.href.replace('custom_report', '@@del_line_item')
            $.ajax({
                type: "POST",
                url: url,
                data: data,
                success: function (response) {
                    dfpLine.xs = {}
                    dfpLine.columns = []
                    drawLine(dfpLine)
                }
            });
        }
    });

    $('.download').click(function (e) {
        orderList = ''
        $.each($('.dfp-order:checked'), function (indexInArray, valueOfElement) {
             orderList += $(this).val()+','
        });
        start = $('.start-date').val()
        end = $('.end-date').val()
        urlStr = `download_file?orderList[]=${orderList}&start=${start}&end=${end}`
        window.location.href = urlStr
    });
})
