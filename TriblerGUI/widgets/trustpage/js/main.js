/**
 * This file creates an SVG element and draws the network using it.
 */

// TODO: think about how to split this in different javascipt files
// TODO: start using JSDoc and setup some CI tool to check
// TODO: choose a testing framework and start writing tests

// Distance to peers
var radius = 100;

// Select the svg DOM element
var svg = d3.select("svg"),
    width = +svg.attr("width"),
    height = +svg.attr("height");

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) { return d.public_key; }).distance(100).strength(0.1))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2));

function new_data(data) {
    console.log(data);
    update(JSON.parse(data));
}

// change this public key and get a different graph:
get_node_info(35, new_data);

function update(graph) {

    var link = svg.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(graph.links)
        .enter().append("line")
        .attr("stroke-width", 2)
        .style("stroke", "rgb(255,255,255)");

    var node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(graph.nodes)
        .enter().append("circle")
        .attr("fill", "rgb(230,115,0)")
        .attr("r", "10")
        .on("click", function(d) { handle_node_click(d.public_key) });

    var text = svg.append("g").attr("class", "labels").selectAll("g")
        .data(graph.nodes)
        .enter().append("g");

    text.append("text")
        .attr("x", 12)
        .attr("y", 12)
        .style("font-family", "sans-serif")
        .style("font-size", "12")
        .style("fill", "#ffff00")
        .text(function(d) { return d.public_key; });

    simulation
        .nodes(graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.links);

    function ticked() {
        link
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        node
            .attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; });

        text
            .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
    }
}

function handle_node_click(public_key) {
    console.log(public_key);
    //get_node_info(public_key, new_data)
}
