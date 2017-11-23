$(function () {
  $('#start_date,#end_date').datepicker({
    dateFormat: 'yy-mm-dd',
  });
});
$(document).ready(function () {
  $('#select_all').click(function (e) { 
    $('#url').toggleClass('disabled_select');
    $('#url').prop('disabled', function(i, v) { return !v; });
  });
  $('#btn').click(function (e) {
    $('.show_trace_checkbox').css('display','inline-block')
    var select_all = $('#select_all').prop("checked");
    var url = $("#url").find("option:selected").text()
    var start_date = $('#start_date').val();
    var end_date = $('#end_date').val();

    data = {
      'url': url,
      'start_date': start_date,
      'end_date': end_date,
      'select_all':select_all
    }

    $.ajax({
      type: "POST",
      url: "http://localhost:8080/Plone/select_trace_page",
      data: data,
      success: function (response) {
        data = JSON.parse(response)
        drawmap(start_date, end_date, data);
      },
    });
  });

  function drawmap(start_date, end_date, data) {
    
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
    var fillcolor = "#CCC";
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
          .duration(1000)
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

  $('input[type=checkbox]').change(function (e) {
    new_svg.selectAll('.event_line').remove()
    $('input[type=checkbox]').each(function(e){
      if(this.checked == true && $(this).attr('data-start')!= undefined){
        var start_date = $(this).attr('data-start').slice(0,10);
        var end_date = $(this).attr('data-end').slice(0,10);
        var title = $(this).attr('data-title');
        color_list = ["#F08A5D","#00B8A9","#FF2E63","#311D3F","#88304E","#62D2A2"]

        event_date = []
        event_date.push([start_date,title+'  開始'])
        event_date.push([end_date,title+'  結束'])

        new_svg.selectAll("dot")
          .data(event_date)
          .enter()
          .append("line")
          .attr('class','event_line')
          .attr("x1", function(d) { return x(format.parse(d[0])); })
          .attr("y1",0)
          .attr("x2",function(d) { return x(format.parse(d[0])); })
          .attr("y2",height)
          .attr("stroke-width","2")
          .attr('stroke', color_list[e])
          
        new_svg.selectAll("dot")
          .data(event_date)
          .enter()
          .append("text")
          .attr('class','event_line')
          .attr("x",function(d) { return x(format.parse(d[0])); })
          .attr("y",e*25)
          .attr('fill',color_list[e])
          .attr('font-size','17px')
          .text(function(d) {  return d[1] })
      }
    })
  });
  }
})

