/* custom.js */

// dfp Line chart
genC3 = function(xs, columns){

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
    debugger
    console.log(draw_type)
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
        regions: [
            {start: new Date('2017-07-24'), end: new Date('2017-07-28')},
        ],
        axis: {
            x: {
                type: 'category',
                tick: {
                    rotate: -20,
                    format: '%Y-%m-%d'
                },
            }
        },
        
        padding:{
            bottom: 70
        },
    });
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
        genC3(dfpLine.xs, dfpLine.columns)
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
    $('.dfp-order, .start-date, .end-date').change(function(){
        dfpLine.xs = {}
        dfpLine.columns = []
        drawLine(dfpLine)
    })
    $('#nav_line, #nav_bar, #nav_pie').click(function (e) { 
        dfpLine.xs = {}
        dfpLine.columns = []
        drawLine(dfpLine)
    });

})
