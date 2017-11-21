$(function () {
  $('#start_date,#end_date').datepicker({
    dateFormat: 'yy-mm-dd',
  });
});
$(document).ready(function () {
  $('#btn').click(function (e) {
    e.preventDefault();
    var url = $("#url").find("option:selected").val();
    var start_date = $('#start_date').val();
    var end_date = $('#end_date').val();

    data = {
      'url': url,
      'start_date': start_date,
      'end_date': end_date
    }
    $.ajax({
      type: "POST",
      url: "http://localhost:8080/Plone/select_trace_page",
      data: data,
      success: function (response) {
        data = JSON.parse(response)
        console.log(data)
        drawmap(start_date, end_date, data);
      },
    });
  });

  function drawmap(start_date, end_date, data) {
    // days=DateDifference(start_date,end_date)
    
    var data_list = []
    
    for(i=0;i<data.length;i++){
      data_list.push([
        data[i]['date_time'],
        data[i]['count']
      ])
    }

    var width = 720;
    var height = 450;
    
    var border_color = "#9DE0AD";
    var fillcolor = "#EEEEEE";
    var dotcolor = "#222831";
    var line_color = '#3490DE';

    var svg = d3.select('#svg').html('svg')
              .attr('width', width)
              .attr('height', height);

    var margin = {top: 20, right: 25, bottom: 100, left: 60};
      width = width - margin.left - margin.right,
      height = height - margin.top - margin.bottom;
    var new_svg = svg.append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var format = d3.time.format("%Y-%m-%d");

    var x = d3.time.scale()
      .domain([format.parse(data_list[0][0]),
              format.parse(data_list[data_list.length-1][0])])
      .range([0, width]);

    var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom")
      .ticks(data.length-1)
      .tickFormat(d3.time.format("%Y-%m-%d"));

    var y = d3.scale.linear()
      .domain([0, d3.max(data_list,function(d){return d[1]})*1.3])
      .range([height, 0]);
    
    var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left")
      .ticks(10);
    
    var axisXGrid = d3.svg.axis()
      .scale(x)
      .orient("bottom")
      .ticks(10)
      .tickFormat("")
      .tickSize(-height, 0);

    var axisYGrid = d3.svg.axis()
      .scale(y)
      .orient("left")
      .ticks(10)
      .tickFormat("")
      .tickSize(-width, 0);
    
    svg.append('g')
      .call(axisXGrid)
      .attr({
        'fill': 'none',
        'stroke': 'rgba(0,0,0,.1)',
        'transform': 'translate(60,' + (height + 20) + ')'
      });

      svg.append('g')
      .call(axisYGrid)
      .attr({
        'fill': 'none',
        'stroke': 'rgba(0,0,0,.1)',
        'transform': 'translate(60,20)'
      });


    var line = d3.svg.line()
      .x(function(d){return x(format.parse(d[0]))})
      .y(function(d){return y(d[1])})
      .interpolate("linear");

    // Define the area
    var area = d3.svg.area()
      .x(function(d) { return x(format.parse(d[0])); })
      .y0(height)
      .y1(function(d) { return y(d[1]); })
      .interpolate("linear");
    
    new_svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .attr("class", "x axis")
      .style("fill",border_color)
      .style("font-size","1em")
      .call(xAxis)
      .selectAll("text")
      .attr("transform", "rotate(-25)")
      .style("text-anchor", "end");
    // Add the Y Axis
    new_svg.append("g")
      .attr("class", "y axis")
      .style("fill",border_color)
      .style("font-size","1.3em")
      .call(yAxis);
  
  // Add the line
    var svg_path4 = new_svg.append('path')
      .attr("d", line(data_list))
      .attr("fill","none")
      .attr("stroke-width","4px")
      .attr("stroke",line_color);
  
    do_animation(svg_path4);
  
  // Add the area
    svg_path5 = new_svg.append("path")
      .datum(data_list)
      .attr("d", area(data_list))
      .attr("fill",fillcolor)
      .attr("stroke-width","0");
    
    function do_animation(path) {
      var totalLength = path.node().getTotalLength();
      path
        .attr("stroke-dasharray", totalLength + " " + totalLength)
        .attr("stroke-dashoffset", totalLength)
        .transition()
          .duration(1500)
          .ease("linear")
          .attr("stroke-dashoffset", 0);
    }
    new_svg.selectAll("dot")
    .data(data_list)
    .enter()
    .append("circle")
    .attr("r", 3)
    .attr("cx", function(d) { return x(format.parse(d[0])); })
    .attr("cy", function(d) { return y(d[1]); })
    .attr("fill",dotcolor)
    .attr("stroke-width","0")
 }

})