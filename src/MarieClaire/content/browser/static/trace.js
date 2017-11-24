$(document).ready(function () {
    var href = document.location.href;
    data={"url":href, "title":document.title}
    $.ajax({
        type: "POST",
        url: PORTAL_URL + "/save_trace_page",
        data: data,
        success: function(){
        },
    });
});
