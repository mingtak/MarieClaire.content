/* custom.js */
$(document).ready(function(){
    var dfpLine = new Vue({
        el: '#dfp-line',
        data: {
            message: 'Hello Vue!'
        }
    })
})

checkedList = function(){
    result = []
    $.each($('.dfp-order:checked'), function(index, value){
        result.push($(value).val())
    })
    return result
}


$(document).ready(function(){
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
                for(i in resultArray){
//TODO
                }

//                alert(resultArray.length)
            }).fail(function(){
                alert('Fail')
            })


        }else{
            $('input.dfp-order').prop('checked', false)
        }
    })
})
