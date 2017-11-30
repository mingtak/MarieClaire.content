/* custom.js */

checkedList = function(){
    result = []
    $.each($('.dfp-order:checked'), function(index, value){
        result.push($(value).val())
    })
    return result
}


$(document).ready(function(){
    var dfpLine = new Vue({
        el: '#dfp-line',
        data: {
            message: 'Hello Vue!',
            xs: {'aaa': 11111},
            columns: []
        }
    })

    $('#dfp-select-all').click(function(){
        if($(this).is(':checked')){
            $('input.dfp-order').prop('checked', true)
            data = {'orderList': checkedList()}
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
        }else{
            $('input.dfp-order').prop('checked', false)
        }
    })

// dfp Line chart
genC3 = function(xs, columns){
var chart = c3.generate({
    bindto: '#line-chart',
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


})
