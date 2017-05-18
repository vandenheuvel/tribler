/**
 * This file creates an SVG element and draws the network using it.
 *
 * NOTE: Use a browser DOM inspection tool to see how the SVG is
 * built up and modified by this code.
 */

// TODO: think about how to split this in different javascipt files
// TODO: start using JSDoc and setup some CI tool to check
// TODO: choose a testing framework and start writing tests


// Update the visualization
function onNewData(data) {
    state.request_pending = false;
    update(processData(data));
}

// Distance to peers
var radius = 200;

// Select the svg DOM element
var svg = d3.select("#graph"),
    width = +svg.attr("width"),
    height = +svg.attr("height");

// Append groups for links, nodes, labels.
// Order is important: drawed last is on top.
svg.append("g").attr("class", "links");
svg.append("g").attr("class", "nodes");
svg.append("g").attr("class", "labels");

// Selector for the nodes
function getNodes() {
    return svg
        .select(".nodes")
        .selectAll(".node");
}

// Selector for the links
function getLinks() {
    return svg
        .select(".links")
        .selectAll("line")
}

var state = {
    request_pending: false,
    x: width / 2,
    y: height / 2,
    focus_pk: 30,
    focus_node: null,
    nodes: []
};

// Fetch the data
get_node_info(state.focus_pk, onNewData);

// Set up the force simulation
var simulation = d3.forceSimulation()

// Centering force (used for focus node)
    .force("center", d3.forceCenter(state.x, state.y))

    // Centering the neighbor nodes (radial layout)
    .force("neighbor_x", d3.forceX(getRadialPosition(0)).strength(.5))
    .force("neighbor_y", d3.forceY(getRadialPosition(1)).strength(.5))

    // The update function for every tick of the clock
    .on("tick", tick);

// Only apply the centering force on the focus node
filterForceNodes(simulation.force("center"), function (n, i) {
    return n.public_key == state.focus_pk;
});

// Only apply the neighbor force on the neighbors
filterForceNodes(simulation.force("neighbor_x"), function (n, i) {
    return n.public_key != state.focus_pk;
});

filterForceNodes(simulation.force("neighbor_y"), function (n, i) {
    return n.public_key != state.focus_pk;
});

/**
 * Update the visualization for the provided data set
 * @param graph
 */
function update(graph) {

    // console.log("Updating the visualization", graph);
    console.log("Focus on", graph.focus_node);

    // Restart simulation
    simulation.restart();

    // Update the state

    // Make hash of nodes
    state.nodes = [];
    graph.nodes.forEach(function (node) {
        state.nodes[node.public_key] = node;
    });

    // Set the focus node
    state.focus_pk = +graph.focus_node;
    state.focus_node = graph.nodes.filter(function (node) {
        return node.public_key == state.focus_pk;
    })[0];

    // List the neighbors in each node
    graph.nodes.forEach(function (node) {
        node.neighbors = listNeighborsOf(graph.links, node.public_key).map(function (pk) {
            return state.nodes[pk];
        });
    });

    // Start in the center
    var nodeCount = graph.nodes.length - 1;
    var alpha_0 = Math.PI / 2;
    var scale = .5;
    var dAlpha = Math.PI * 2 / nodeCount;

    // All nodes start in the center (slightly off)
    graph.nodes.forEach(function (node, i) {
        node.x = width / 2 + Math.random();
        node.y = height / 2 + Math.random();
    });

    // Set the angles of all neighbors
    setAlpha(state.focus_node.neighbors, alpha_0, alpha_0 * 5);

    // Create the new nodes, remove the old
    // var nodeSelection = getNodes().data(graph.nodes);
    var nodes = drawNodes(graph.nodes);

    // Create the new links, remove the old
    var linksWithNodes = graph.links.map(function (link) {
        return {
            source: state.nodes[link.source],
            target: state.nodes[link.target]
        }
    });

    var linkSelection = getLinks().data(linksWithNodes)
    var links = drawLinks(linkSelection.enter());
    linkSelection.exit().remove();

    simulation.nodes(graph.nodes)

    // Reset the alpha to 1 (full energy)
    simulation.alpha(1);
}

/**
 * Update the positions of the links and nodes on every tick of the clock
 */
function tick() {
    getLinks()
        .attr("x1", function (d) {
            return d.source.x;
        })
        .attr("y1", function (d) {
            return d.source.y;
        })
        .attr("x2", function (d) {
            return d.target.x;
        })
        .attr("y2", function (d) {
            return d.target.y;
        });

    getNodes()
        .attr("x", function (d) {
            return d.x;
        })
        .attr("y", function (d) {
            return d.y;
        });
}

/**
 * Make a new request when a node is clicked
 * @param public_key
 */
function handle_node_click(public_key) {
    if(state.request_pending){
        console.warning("Request pending, ignore new request");
    } else {
        state.request_pending = true;
        get_node_info(public_key, onNewData)
    }
}

/**
 * Draw the links
 * @param selection
 * @returns {*}
 */
function drawLinks(selection) {
    var links = selection
        .append("line")
        .attr("stroke-width", 2)
        .style("stroke", "rgb(255,255,255)");

    return links;
}

/**
 * Draw the nodes and their labels
 * @param selection
 * @returns {*}
 */
function drawNodes(data) {

    // Always remove existing nodes before adding new ones
    getNodes().remove();

    var selection = getNodes().data(data).enter();

    // Create an <svg.node> element.
    var groups = selection
        .append("svg")
        .attr("overflow", "visible")
        .attr("class", "node");

    // Append a <circle> element to it.
    groups
        .append("circle")
        .attr("fill", "rgb(230,115,0)")
        .attr("r", "20")
        .attr("cx", 0)
        .attr("cy", 0)
        .on("click", function (d) {
            handle_node_click(d.public_key)
        });

    // Append a <text> element to it
    groups
        .append("text")
        .attr("x", 24)
        .attr("y", 24)
        .style("font-family", "sans-serif")
        .style("font-size", "12")
        .style("fill", "#ffff00")
        .text(function (d) {
            return d.public_key;
        });

    // Return the group of <svg.node>
    return groups;

}

/**
 *
 * @param dimension (0: x, 1: y)
 */
function getRadialPosition(dimension) {
    return function (node) {
        var pos = radialPosition(state.x, state.y, node.alpha, radius);
        return dimension === 0 ? pos.x : pos.y;
    }
}
