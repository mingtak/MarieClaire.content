// Replace with your view ID.
// var VIEW_ID = '166020368';
// Query the API and print the results to the page.
// function queryReports() {
//     start = $('.start-date').val();
//     end = $('.end-date').val();

//     gapi.client.request({
//     path: '/v4/reports:batchGet',
//     root: 'https://analyticsreporting.googleapis.com/',
//     method: 'POST',
//     body: {
//         reportRequests: [
//         {
//             viewId: VIEW_ID,
//             dateRanges: [
//             {
//                 startDate: '2017-12-01',
//                 endDate: '2017-12-08'
//             }
//             ],
//             metrics: [
//             {'expression': 'ga:sessionDuration'},
//             {'expression': 'ga:users'}
//             ]
//         }
//         ]
//     }
//     }).then(displayResults, console.error.bind(console));
// }

// function displayResults(response) {
//     // var formattedJson = JSON.stringify(response.result, null, 2);
//     // debugger
//     // console.log(formattedJson)
//     len = response.result["reports"][0]["columnHeader"]["metricHeader"]["metricHeaderEntries"]["length"]
//     ga_arry = {}
//     name_arr = []
//     for(i=0;i<len;i++){
//         name = response.result["reports"][0]["columnHeader"]["metricHeader"]["metricHeaderEntries"][i]['name'].split('ga:')[1]
//         value = response.result['reports'][0]["data"]["totals"][0]["values"][i]
//         ga_arry[name] = value
//     }

//     url = window.location.href.replace('welcome', 'save_ga_data')    
//     $.ajax({
//         type: "POST",
//         url: url,
//         data: ga_arry,
//         success: function (response) {
//         }
//     });
// }

// $('.queryReports').click(function (e) { 
//     queryReports()
// });

$(document).ready(function () {

    var dfpLine = new Vue({
        el: '#ga_chart',
        data: {
            message: 'Hello Vue!',
            xs: {'aaa': 11111},
            columns: []
        }
    })
});

$('.ga_send').click(function (e) { 
    start = $('.start-date').val();
    end = $('.end-date').val();
    url = window.location.href.replace('ga_draw', 'get_ga_data')
    data = {
        'start': start,
        'end': end 
    }
    $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: function (response) {
            console.log(response)
        }
    });
});