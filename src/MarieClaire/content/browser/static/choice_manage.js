$('#event_list,#ads_list,#custom_list').click(function (e) { 
    e.preventDefault();
    console.log(e)
    url = e.currentTarget.id
    $('.manage_iframe').attr('src', url);
});

