$(document).ready(function () {
    $('.check_box').hide();
    $('.check_del_span').click(function (e) {
        $(this).siblings().toggle()
        $('.hide').hide();
    });
    $('.go_back').click(function (e) { 
        e.preventDefault();
        $('.check_box').hide();
    });
});
