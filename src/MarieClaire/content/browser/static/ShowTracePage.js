$(function () {
  $('#start_date,#end_date').datepicker({
    dateFormat: 'yy-mm-dd',
  });
});
$(document).ready(function () {
  $('#btn').click(function (e) {
    e.preventDefault();
    var url = $('#url').val();
    var start_date = $('#start_date').val();
    var end_date = $('#end_date').val();
    data = {
      'url': url,
      'start_date': start_date,
      'end_date': end_date
    }
    $.ajax({
      type: "POST",
      url: "http://localhost:8080/Plone/selectTracePage",
      data: data,
      success: function (response) {
        data = JSON.parse(response)
        drawmap();
      },
    });
  });

  function drawmap() {
    var data = [{
        x: 0,
        y: 38
      },
      {
        x: 20,
        y: 27
      },
      {
        x: 40,
        y: 56
      },
      {
        x: 60,
        y: 34
      },
      {
        x: 80,
        y: 41
      },
      {
        x: 100,
        y: 35
      },
      {
        x: 120,
        y: 100
      },
      {
        x: 140,
        y: 57
      },
      {
        x: 160,
        y: 36
      },
      {
        x: 180,
        y: 41
      }
    ];

    var width = 720,
      height = 450;

    var s = d3.select('#s');

    s.attr({
      'width': 800,
      'height': 500,
    }).style({
      'border': '1px dotted #ccc'
    });

    var minX = d3.min(data, function (d) {
      return d.x
    });
    var maxX = d3.max(data, function (d) {
      return d.x
    });
    var minY = d3.min(data, function (d) {
      return d.y
    });
    var maxY = d3.max(data, function (d) {
      return d.y
    });
    
    var scaleX = d3.scale.linear()
      .range([0, width])
      .domain([minX, maxX]);

    var scaleY = d3.scale.linear()
      .range([height, 0])
      .domain([0, maxY]);

    //line
    var line = d3.svg.line()
      .x(function (d) {
        return scaleX(d.x);
      }).y(function (d) {
        return scaleY(d.y);
      });

    //area
    var area = d3.svg.area()
      .x(function (d) {
        return scaleX(d.x);
      })
      .y0(height)
      .y1(function (d) {
        return scaleY(d.y);
      });

    s.append('path')
      .attr({
        'd': line(data),
        'stroke': '#06c',
        'fill': 'none',
        'transform': 'translate(35,20)'
      });

    s.append('path')
      .attr({
        'd': area(data),
        'fill': 'rgba(0,150,255,.1)',
        'transform': 'translate(35,20)'
      });

    //axis
    var axisX = d3.svg.axis()
      .scale(scaleX)
      .orient("bottom")
      .ticks(10);

    var axisY = d3.svg.axis()
      .scale(scaleY)
      .orient("left")
      .ticks(5);

    //grid
    var axisXGrid = d3.svg.axis()
      .scale(scaleX)
      .orient("bottom")
      .ticks(10)
      .tickFormat("")
      .tickSize(-height, 0);

    var axisYGrid = d3.svg.axis()
      .scale(scaleY)
      .orient("left")
      .ticks(10)
      .tickFormat("")
      .tickSize(-width, 0);

    // Axis Grid line
    s.append('g')
      .call(axisXGrid)
      .attr({
        'fill': 'none',
        'stroke': 'rgba(0,0,0,.1)',
        'transform': 'translate(35,' + (height + 20) + ')'
      });

    s.append('g')
      .call(axisYGrid)
      .attr({
        'fill': 'none',
        'stroke': 'rgba(0,0,0,.1)',
        'transform': 'translate(35,20)'
      });

    // Axis 
    s.append('g')
      .call(axisX)
      .attr({
        'fill': 'none',
        'stroke': '#000',
        'transform': 'translate(35,' + (height + 20) + ')'
      }).selectAll('text')
      .attr({
        'fill': '#000',
        'stroke': 'none',
      }).style({
        'font-size': '11px'
      });

    s.append('g')
      .call(axisY)
      .attr({
        'fill': 'none',
        'stroke': '#000',
        'transform': 'translate(35,20)'
      }).selectAll('text')
      .attr({
        'fill': '#000',
        'stroke': 'none',
      }).style({
        'font-size': '10px'
      });
  }
});
