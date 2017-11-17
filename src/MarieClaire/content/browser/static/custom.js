$('#event_list,#ads_list,#custom_list').click(function (e) { 
    e.preventDefault();
    console.log(e)
    url = e.currentTarget.id
    $('.manage_iframe').attr('src', url);
});
$(document).ready(function () {
    $('#start_date,#end_date').datepicker({
        dateFormat: 'yy-mm-dd',
      });
});
