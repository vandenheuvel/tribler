/**
 * This file creates an SVG element and draws the network using it.
 *
 * NOTE: Use a browser DOM inspection tool to see how the SVG is
 * built up and modified by this code.
 */

// TODO: start using JSDoc and setup some CI tool to check
// TODO: choose a testing framework and start writing tests

// Update the visualization
function onNewData(data) {
    state.request_pending = false;
    update(processData(data));
}

// Distance to peers
var radius_step = config.radius_step,
    neighbor_level = 2;

// Select the svg DOM element
var svg = d3.select("#graph"),
    width = +svg.attr("width"),
    height = +svg.attr("height");

var state = {
    request_pending: false,
    x: width / 2,
    y: height / 2,
    focus_pk: "self",
    previous_angle: 0,
    previous_focus_pk: null,
    focus_node: null,
    nodes: []
};

// Append groups for links, nodes, labels.
// Order is important: drawed last is on top.

for (var i = 1; i <= neighbor_level; i++)
    drawNeighborRing(svg, state.x, state.y, radius_step * i);

svg.append("g").attr("class", "links");
svg.append("g").attr("class", "nodes");
svg.append("g").attr("class", "labels");

// The label that appears when the user hovers over a node or link
hoverInfoLabel = d3.select("body").append("div")
    .attr("class", "hoverInfoLabel")
    .attr("id", "hoverInfoLabel")
    .style("opacity", 0);
hoverInfoLabel.append("table").attr("class", "hoverInfoTable");

// Fetch the data
get_node_info(state.focus_pk, neighbor_level, onNewData);

var simulation = new RadialSimulation({
    center_x : state.x,
    center_y : state.y,
    radius_step : config.radius_step
});

simulation.initialize()
    .onTick(tick);

/**
 * Update the visualization for the provided data set
 * @param {GraphData} graph
 */
function update(graph) {

    console.log(graph);

    // Copy positions from old nodes to new ones;
    state.nodes.forEach(function (node) {
        var new_local = graph.local_keys.indexOf(node.public_key);
        if (new_local >= 0) {
            var new_node = graph.nodes[new_local];
            new_node.x = node.x;
            new_node.y = node.y;
        }
    });

    // Set the focus node
    state.focus_pk = graph.focus_node.public_key;
    state.focus_node = graph.focus_node;
    state.nodes = graph.nodes;
    state.data = graph;

    // Position all new nodes at the focus node
    graph.nodes.forEach(function (node, i) {
        if (!('x' in node)) {
            node.x = state.focus_node.x || state.x;
            node.y = state.focus_node.y || state.y;
        }
    });

    // Make a tree from the graph
    state.tree = graphToTree(graph.focus_node);
    state.tree.nodes.forEach(function (treeNode) {
        treeNode.graphNode.treeNode = treeNode;
    });

    // Position all nodes on a circle
    applyRecursiveAlphaByDescendants(state.tree.root, 0, 2 * Math.PI, simulation.getCenterFix());

    // Maintain orientation between previous and current focus node
    if (state.previous_focus_pk) {
        var target_angle = state.previous_angle + Math.PI;
        var previous_focus = state.tree.nodes.find(function (node) {
            return node.graphNode.public_key === state.previous_focus_pk;
        });
        if (previous_focus) {
            var correction = target_angle - previous_focus.alpha;
            state.tree.nodes.forEach(function (node) {
                node.alpha += correction;
            });
        }
    }

    // Draw all nodes
    var nodes = drawNodes(svg, graph, function (d) {
        handle_node_click(d.public_key)
    }, hoverInfoLabel);

    // Do not display the label after the graph is updated
    hoverInfoLabel.style("display", "none");

    // Draw all links
    var links = drawLinks(svg, graph, hoverInfoLabel);

    simulation.update(state.tree.nodes);

}

/**
 * Returns the point x on line x0 to x1 at a given fraction
 * @param x0
 * @param x1
 * @param ratio
 * @returns x
 */
function xAtFraction(x0, x1, ratio) {
    return x0 + (x1 - x0) * ratio;
}

/**
 * Calculate the distance in pixels between nodes
 * @param nodeA
 * @param nodeB
 * @returns {number} - the distance in pixels
 */
function nodeDistance(nodeA, nodeB) {
    return Math.sqrt(Math.pow(nodeB.x - nodeA.x, 2) + Math.pow(nodeB.y - nodeA.y, 2));
}

/**
 * Update the positions of the links and nodes on every tick of the clock
 */
function tick() {

    var linkSource = svg.select(".links").selectAll(".link-source");
    var linkTarget = svg.select(".links").selectAll(".link-target");

    // Part of line at the source
    linkSource
        .attr("x1", function (d) { return d.source.x; })
        .attr("y1", function (d) { return d.source.y; })
        .attr("x2", function (d) { return xAtFraction(d.source.x, d.target.x, 1 - d.ratio - 1 / Math.max(1, nodeDistance(d.source, d.target))); })
        .attr("y2", function (d) { return xAtFraction(d.source.y, d.target.y, 1 - d.ratio - 1 / Math.max(1, nodeDistance(d.source, d.target))); })

    // Part of line at the target
    linkTarget
        .attr("x1", function (d) { return xAtFraction(d.target.x, d.source.x, d.ratio - 1 / Math.max(1, nodeDistance(d.source, d.target))); })
        .attr("y1", function (d) { return xAtFraction(d.target.y, d.source.y, d.ratio - 1 / Math.max(1, nodeDistance(d.source, d.target))); })
        .attr("x2", function (d) { return d.target.x; })
        .attr("y2", function (d) { return d.target.y; })
        // .style("opacity", function(d){return d.source.highlight || d.target.highlight ? 1 : getLinkOpacity(d)})


    selectNodes(svg)
        .attr("x", function (d) { return d.x; })
        .attr("y", function (d) { return d.y; });
}

/**
 * Make a new request when a node is clicked
 * @param public_key
 */
function handle_node_click(public_key) {
    if (state.request_pending) {
        console.log("Request pending, ignore new request");
    } else {
        if (public_key !== state.focus_pk) {
            state.request_pending = true;

            // Store the previous focus node and its angle
            var lk = state.data.local_keys.indexOf(public_key);
            var newNode = state.data.nodes[lk];
            var newTreeNode = find(state.tree.nodes, 'graphNode', newNode);
            state.previous_focus_pk = state.focus_pk;
            state.previous_angle = newTreeNode.alpha;

            get_node_info(public_key, neighbor_level, onNewData)
        }
    }
}
