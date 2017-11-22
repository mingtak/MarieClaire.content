$('#event_list,#ads_list,#custom_list,#post_list').click(function (e) { 
    e.preventDefault();
    url = e.currentTarget.id
    $('.manage_iframe').attr('src', url);
});

