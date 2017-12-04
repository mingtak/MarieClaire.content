/* custom.js */

// dfp Line chart
genC3 = function(xs, columns){

    console.log(columns)
    if(columns.length > 40){
        height = 1000
    }else{
        height = null
    }

    var chart = c3.generate({
        bindto: '#line-chart',
        size: {
            height: height,
        },
        data: {
            xs: xs,
            columns: columns,
            labels: true
        },
        axis: {
            x: {
                type: 'timeseries',
                tick: {
                    format: '%Y-%m-%d'
                }
            }
        }
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
    $('#dfp-select-all').click(function(){
        if($(this).is(':checked')){
            $('input.dfp-order').prop('checked', true)
            drawLine(dfpLine)

        }else{
            $('input.dfp-order').prop('checked', false)
            dfpLine.xs = {}
            dfpLine.columns = []
            genC3(dfpLine.xs, dfpLine.columns)
        }
    })

    // 單選, 時間改變
    $('.dfp-order, .start-date, .end-date').change(function(){
        dfpLine.xs = {}
        dfpLine.columns = []
        drawLine(dfpLine)
    })

})
