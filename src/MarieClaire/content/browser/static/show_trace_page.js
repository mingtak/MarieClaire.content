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
  $('.show_trace_btn').click(function (e) {    
    var select_all = $('#select_all').prop("checked");
    var url = $("#url").find("option:selected").val()
    var start_date = $('#start_date').val();
    var end_date = $('#end_date').val();
    var chosen = $(this).val();

    data = {
      'url': url,
      'start_date': start_date,
      'end_date': end_date,
      'select_all':select_all
    }

    $.ajax({
      type: "POST",
      url: PORTAL_URL + "/select_trace_page",
      data: data,
      success: function (response) {
        data = JSON.parse(response)
        $('#url').prop('disabled', '');
        $('#url').removeClass('disabled_select');
        $('input[type=checkbox]').prop('checked',false)
        if(chosen == 'line'){
          $('.show_trace_checkbox').css('display','inline-block')
          draw_line(start_date, end_date, data);
        }else if(chosen == 'pie'){
          $('.show_trace_checkbox').css('display','none')
          draw_pie(start_date, end_date, data);
        }else if(chosen == 'bar'){
          $('.show_trace_checkbox').css('display','none')
          draw_bar(start_date, end_date, data);
        }
      },
    });
  });

  function draw_line(start_date, end_date, data) {
    
    var data_list = []
    
    for(i=0;i<data.length;i++){
      data_list.push([
        data[i]['date_time'],
        parseInt(data[i]['count'])
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

    var mouse_text = d3.select("#svg").append('div')
              .attr("class", "tooltip02")
              .style("opacity", 0);

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
      .on("mouseover",function(d,i){
        d3.select(this)
          .attr("r","6")
          .attr("fill","orange")
        new_svg.append("text").attr({
          x: function() { return x(format.parse(d[0])); },
          y: function() { return y(d[1]+1); },
        })
      .attr("class","mouse_text")
      .attr('font-size','17px')
      .text(function() {
        return d[1];  // Value of the text
        });
      })
      .on("mouseout",function(d,i){
        d3.select(this)
        .attr("r","3")
        .attr("fill","black")
        d3.select('.mouse_text').remove()
      })

  $('input[type=checkbox]').change(function (e) {
    new_svg.selectAll('.event_line').remove()
    $('input[type=checkbox]').each(function(e){
      if(this.checked == true && $(this).attr('data-start')!= undefined){
        var start_date = $(this).attr('data-start').slice(0,10);
        var end_date = $(this).attr('data-end').slice(0,10);
        var title = $(this).attr('data-title');
        color_list = ["#F08A5D","#FF9A00","#FF2E63","#311D3F","#284184","#62D2A2","#04837B","#B80257"
                      ,"#F08A5D","#FF9A00","#FF2E63","#311D3F","#284184","#62D2A2","#04837B","#B80257"]

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
          .attr("x",function(d){
            time=format.parse(d[0])
            date = time.getHours()
            time.setHours(date+=1)
            return x(time)
          })
          .attr("y",e*27)
          .attr('fill',color_list[e])
          .attr('font-size','17px')
          .text(function(d) {  return d[1] })
          
        }
      })
    });
  }

  function draw_pie(start_date, end_date, data){
    
    var w = 720,                       
    h = 600,                            
    r = 170,                            
    color = d3.scale.category20c();     

    var vis = d3.select("#svg")
      .html("svg")              
      .data([data])                   
          .attr("width", w)           
          .attr("height", h)
      .append("svg:g")                
          .attr("transform", "translate(" + r + "," + r + ")")    

    var arc = d3.svg.arc()               
      .outerRadius(r);

    var pie = d3.layout.pie()           
      .value(function(d) { return d.count; });    

    var arcs = vis.selectAll("g.slice")    
      .data(pie)                          
      .enter()                    
          .append("svg:g")             
              .attr("class", "slice");    

      arcs.append("svg:path")
              .attr("fill", function(d, i) { return color(i); } ) 
              .attr("d", arc);                                   

      arcs.append("svg:text")                                     
          .attr("transform", function(d) {                   
          d.innerRadius = 0;
          d.outerRadius = r;
          return "translate(" + arc.centroid(d) + ")";        
      })
      .attr("text-anchor", "middle")
      .attr('font-size','20px')
      .text(function(d, i) {
        text=''+data[i].date_time+':'+data[i].count+'次';
        return text
      });    
  }

  function draw_bar(start_date, end_date, data){
    var data_list = []
    
    for(i=0;i<data.length;i++){
      data_list.push([
        data[i]['date_time'],
        parseInt(data[i]['count'])
      ])
    }
    var margin = {top: 20, right: 20, bottom: 70, left: 40},
    width = 720 - margin.left - margin.right,
    height = 450 - margin.top - margin.bottom;

    var	parseDate = d3.time.format("%Y-%m-%d").parse;

    var x = d3.scale.ordinal().rangeRoundBands([0, width], .05);

    var y = d3.scale.linear().range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .tickFormat(d3.time.format("%Y-%m-%d"));

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(10);

    var svg = d3.select("#svg").html("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", 
              "translate(" + margin.left + "," + margin.top + ")");

    x.domain([parseDate(data_list[0][0]),
    parseDate(data_list[data_list.length-1][0])])
    y.domain([0, d3.max(data_list, function(d) { return d[1]; })*1.3]);
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
      .selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", "-.55em")
        .attr("transform", "rotate(-90)" );

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)

    svg.selectAll("bar")
      .data(data_list)
      .enter()
      .append("rect")
        .style("fill", "steelblue")
        .attr("x", function(d) { return x(parseDate(d[0])); })
        .attr("width", x.rangeBand())
        .attr("y", function(d) { return y(d[1]); })
        .attr("height", function(d) { return height - y(d[1]); });
    };
})
