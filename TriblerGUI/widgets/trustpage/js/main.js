/**
 * This file creates an SVG element and draws the network using it.
 *
 * NOTE: Use a browser DOM inspection tool to see how the SVG is
 * built up and modified by this code.
 */

// Update the visualization
function onNewData(data) {
    state.request_pending = false;
    update(processData(data));
}

// Select the svg DOM element
var svg = d3.select("#graph");

// Build up the radial view
var radialView = new RadialView(svg, config);
radialView.initialize();

var state = {
    request_pending: false,
    focus_pk: "self",
    previous_angle: 0,
    previous_focus_pk: null,
    focus_node: null,
    nodes: []
};

// Fetch the data
get_node_info(state.focus_pk, config.neighbor_level, onNewData);

var simulation = new RadialSimulation({
    center_x : radialView.getCenterX(),
    center_y : radialView.getCenterY(),
    radius_step : config.radius_step
});

simulation.initialize()
    .onTick(radialView.tick);

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
    graph.nodes.forEach(function (node) {
        if (!('x' in node)) {
            node.x = state.focus_node.x || radialView.getCenterX();
            node.y = state.focus_node.y || radialView.getCenterY();
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

    // Update the view
    radialView.onNewData(graph);

    // Update the simulation
    simulation.update(state.tree.nodes);
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

            get_node_info(public_key, config.neighbor_level, onNewData)
        }
    }
}
