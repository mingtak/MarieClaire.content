/* custom.js */
$(document).ready(function(){
    $('#dfp-select-all').click(function(){
        if($(this).is(':checked')){
            $('input.dfp-order').prop('checked', true)
        }else{
            $('input.dfp-order').prop('checked', false)
        }
    })
})

$(document).ready(function(){
alert('aaa')
    var dfpLine = new Vue({
        el: '#dfp-line',
        data: {
            message: 'Hello Vue!'
        }
    })
alert('bbb')
})
