
// js for d3 based xy line file: graph gwebj_d3line.js

'use strict';

async function makeLineGraph(data){

    // set the dimensions and margins of the graph
    var margin = {top: 10, right: 30, bottom: 20, left: 50},
        width  = 350 - margin.left - margin.right,
        height = 200 - margin.top  - margin.bottom;

    // set the ranges
    var x = d3.scaleTime().range([0, width]);
    var y = d3.scaleLinear().range([height, 0]);

    // define the line
    var valueline = d3.line()
        .x(function(d) { return x(d.DateTime); })
        .y(function(d) { return y(d.Value); });

    // append the svg obgect to the d3xy div of the page
    // appends a 'group' element to 'svg'
    // moves the 'group' element to the top left margin
    var svg = d3.select("#linegraph")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // let data = await getData(VarIndex);
    // console.log("makeLineGraph: got data: ", data);
    // data = linedata;

    // Scale the range of the data
    x.domain(d3.extent(data, function(d) { return d.DateTime; }));
    y.domain(d3.extent(data, function(d) { return d.Value; }));

    // Add the valueline path.
    svg.append("path")
        .data([data])
        .attr("class", "line")
        .attr("stroke", "#4285f4")
        .attr("fill", "none")
        .attr("d", valueline);

    // Add the X Axis
    svg.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x).ticks(4));

    // Add the Y Axis
    svg.append("g")
        .call(d3.axisLeft(y).ticks(5));
};

