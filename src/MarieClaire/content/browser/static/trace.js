$(document).ready(function () {
    var href = document.location.href;
    console.log(href);
    data={"url":href}
    $.ajax({
        type: "POST",
        url: "http://localhost:8080/Plone/save_trace_page",
        data: data,
        success: function(){
            console.log('send work')
        },
    });
});