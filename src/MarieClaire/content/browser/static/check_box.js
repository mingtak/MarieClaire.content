$(document).ready(function () {
    $("#check_all").change(function () {
        $("input:checkbox").prop('checked', $(this).prop("checked"));
    });
});
