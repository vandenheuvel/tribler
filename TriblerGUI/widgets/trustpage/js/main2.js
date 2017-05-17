/**
 * This file creates an SVG element and draws the network using it.
 */

// Configuration
// Dimensions of the SVG
var w = 900,
    h = 400;

// Position of focus node
var center_x = 200,
    center_y = 200;

// Distance to peers
var radius = 100;

// Select the #graph DOM element and add an SVG element to it
var vis = d3.select("#graph")
    .append("svg")
    .attr("width", w)
    .attr("height", h);

// When JSON is read, update the display
d3.json("graph.json", function (data) {
    update(data.nodes);
});

/** Calculate position on a circle */
function radialPosition(center_x, center_y, alpha, radius) {
    return {
        x: center_x + radius * Math.cos(Math.PI / 2 - alpha),
        y: center_y + radius * Math.sin(Math.PI / 2 - alpha)
    }
}


/** Update the visualization using data about nodes and edges */
function update(data) {

    var num_peers = data.length;

    // Evenly distributed
    var angle = Math.PI * 2 / num_peers;

    // Add the calculated positions to the data
    var peers = data.map(function (n, i) {
        return Object.assign(n, radialPosition(center_x, center_y, i * angle, radius));
    });

    // The focus node
    var focus = {x: center_x, y: center_y, focus:true};
    var nodes = [focus].concat(peers);

    var simulation = d3.forceSimulation(nodes);
    // var xAxisForce = d3.forceX(w / 2);
    // var yAxisForce = d3.forceY(h / 2);
    // simulation.force("xAxis", xAxisForce).force("yAxis", yAxisForce);

    // var links = peers.map(function(peer, i){
    //     return {source: 0, target : i + 1}
    // });

    var links = [];
    var n = nodes.length;
    var links_peers = nodes.map(function(node, i){
       return {source: i, target: (i+1)%n}
    });
    var links_focus = nodes.map(function(node, i){
        return {source: 0, target: i}
    });

    console.log(nodes, links_peers.splice(0));
    simulation.force("link", d3.forceLink(links_peers).distance(100));
    simulation.force("link", d3.forceLink(links_focus).distance(100));




    // Draw the nodes
    var nObj = vis.selectAll("circle .nodes")
        .data(nodes)
        .enter()
        .append("svg:circle")
        .attr("class", "nodes")
        .attr("r", "10px")
        .attr("fill", "b")
        .attr("cx", w / 2).attr("cy", h / 2)
        .merge(vis)
        .call(
            d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

    nObj.attr("fill" , function(node){
        return node.focus ? "red" : "black";
    })

    function dragstarted(d) {
        simulation.restart();
        simulation.alpha(1.0);
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        d.fx = null;
        d.fy = null;
        simulation.alphaTarget(0.1);
    }

    function ticked() {

        nObj.attr("cx", function (d) {
            return d.x;
        })
            .attr("cy", function (d) {
                return d.y;
            })
    }

    simulation.on("tick", ticked);

}
