/* custom.js */

// dfp Line chart
genC3 = function(xs, columns, regions__list, event_order__list, event_name__list){
    groups_columns = []
    checkList_len = checkedList().length  //他選的line_item數
    selected_len = checkedSelect().length //他選曝光量、點擊量、CTR
    
    // /* 用來判斷堆疊 */ 
    if(selected_len == 1 && checkList_len > 1){
        tmp = []
        for(i=1; i<=checkList_len*2; i+=2){
            tmp.push(columns[i][0])
        }
        groups_columns.push(tmp)
    }
    else if(selected_len == 2 && checkList_len > 1){
        for(i=1; i<=selected_len; i++){
            tmp = []
            for(j=1; j<=checkList_len*3; j+=3){
                tmp.push(columns[i+j-1][0])
            }
            groups_columns.push(tmp)
        }
        
    }
    else if (selected_len == 3 && checkList_len > 1){
        for(i=1; i<=selected_len; i++){
            tmp = []
            for(j=1; j<=checkList_len*4; j+=4){
                tmp.push(columns[i+j-1][0])
            }
            groups_columns.push(tmp)
        }
    }

    select_type = $('.select_type')[0].id
    if (select_type == 'nav_line'){
        draw_type = 'line'
    }else if(select_type == 'nav_bar'){
        draw_type = 'bar'
    }else if(select_type == 'nav_pie'){
        draw_type = 'pie'
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
            groups: groups_columns
        },
        bar: {width:30},
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
//畫區間
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
// 選取有打勾的
checkedList = function(){
    result = []
    $.each($('.dfp-line-item:checked'), function(index, value){
        result.push($(value).val())
    })
    return result
}
checkedSelect  = function(){
    result = []
    $.each($('.dfp_select_data:checked'), function(index, value){
        result.push($(value).val())
    })
    return result
}
// 畫線
drawLine = function(dfpLine){
    select_type = $('.select_type')[0].id
    data = {
            'checkList': checkedList(),
            'start': $('.start-date').val(),
            'end': $('.end-date').val(),
            'select_type': select_type
           }
    url = window.location.href.replace('custom_report', '@@get_dfp_report')
    $.post(
        url,
        data = data,
    ).done(function(value){
        resultArray = jQuery.parseJSON(value)
        dfpLine.xs = resultArray[0]
        selected = checkedSelect()
        debugger
        if( (select_type != 'nav_table' && select_type != 'nav_detail') &&
	    (selected.length == 0 || value == "[{}, {}]")  )
	    {
            notify({
                type: "warning", //alert | success | error | warning | info
                title: "條件輸入不足",
                position: {
                    x: "right", //right | left | center
                    y: "top" //top | bottom | center
                },
                size: "normal", //normal | full | small
                overlay: false, //true | false
                closeBtn: true, //true | false
                overflowHide: false, //true | false
                spacing: 20, //number px
                theme: "default", //default | dark-theme
                autoHide: true, //true | false
                delay: 3000, //number ms
                template: '<div class="notify"><div class="notify-text"></div></div>'
            });
	}
        //把勾選的 選光量、點擊量、CTR填入columns
        if (select_type == 'nav_pie'){
            for(key in resultArray[1]){
                if(selected[0] == 1){
                    dfpLine.columns.push(resultArray[1][key][0])
                    dfpLine.columns.push(resultArray[1][key][1])

                }
                else if(selected[0] == 2){
                    dfpLine.columns.push(resultArray[1][key][0])
                    dfpLine.columns.push(resultArray[1][key][2])
                }
            }
        }
        else{
            for(key in resultArray[1]){
                for(i=0; i<resultArray[1][key].length; i++){
                    if( i == 0 || selected.indexOf(i.toString()) != -1 ){
                        dfpLine.columns.push(resultArray[1][key][i])
                    }
                }
            }
        }
        /* 抓取event資料 */
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


getDfpTable = function(){
    data = {
        'select_type': $('.select_type')[0].id,
        'checkList': checkedList(),
        'start': $('.start-date').val(),
        'end': $('.end-date').val(),
       }
    url = window.location.href.replace('custom_report', '@@get_dfp_table')
    $.ajax({
        type: "post",
        url: url,
        data: data,
        success: function (response) {
            if(!response.startsWith("<!DOCTYPE html>")) {
                $('#line-chart').html();
            }
            else {
                $('#line-chart').html(response);
                $('#line-chart').css('max-height','100%')
            }
        }
    });
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
    $('.dfp_select_radio').hide();

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
    $('.dfp-line-item, .start-date, .end-date, .event_checkbox, .dfp_select_data, .dfp_select_radio').change(function(){
        $('.download').attr('href', '');
        dfpLine.xs = {}
        dfpLine.columns = []
        drawLine(dfpLine)
    })

    $('#nav_line, #nav_bar, #nav_pie').click(function (e) {
        dfpLine.xs = {}
        dfpLine.columns = []
        $('.dfp_select_checkbox, .datepicker, .event_checkbox , .del-btn, .del-time').show();
        $('input').prop('checked',false)
        if($(this)[0].id == 'nav_pie'){
            $('.dfp_select_radio').show();
            $('.dfp_select_checkbox').hide();
            $('.del-time, .del-btn, .event_checkbox, .datepicker').hide();
        }if($(this)[0].id == 'nav_line'){
            $('.contain_select_checkbox label:last-child').show()
        }else if($(this)[0].id == 'nav_bar'){
            $('.dfp_select_radio').hide();
            $('.dfp_select_checkbox').show();
            $('.contain_select_checkbox label:last-child').hide()
        }
        $(this).addClass('select_type')
        $(this).siblings().removeClass('select_type')
        drawLine(dfpLine)
    });

    $('.del-btn').click(function (e) {
        if( confirm('確認要刪除嘛') ){
            data = {
                'time':$('input.del-time').val(),
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
        checkList = ''
        $.each($('.dfp-line-item:checked'), function (indexInArray, valueOfElement) {
             checkList += $(this).val()+','
        });
        start = $('.start-date').val()
        end = $('.end-date').val()
        urlStr = `download_file?checkList[]=${checkList}&start=${start}&end=${end}`
        window.location.href = urlStr
    });
    $('#nav_table, #nav_detail').click(function (e) {
        $(this).addClass('select_type')
        $(this).siblings().removeClass('select_type')
        $('.dfp_select_checkbox, .datepicker, .event_checkbox , .del-btn, .del-time, .dfp_select_radio').hide();
        $('input').prop('checked',false)
    });
    $('.dfp-line-item, .dfp-select-all').change(function (e) { 
        getDfpTable()
    });
    
})
