/**
 * This file creates an SVG element and draws the network using it.
 *
 * NOTE: Use a browser DOM inspection tool to see how the SVG is
 * built up and modified by this code.
 */

// Disable right mouse click functionality
document.oncontextmenu = document.body.oncontextmenu = function () { return false; };

// Set up navigation for loading data when clicking nodes
var navigation = new RadialNavigation(get_node_info);
navigation.setNeighborLevel(config.neighbor_level);
navigation.bind('response', function (data) {
    update(processData(data));
});

// Set up the radial view to display all data
var radialView = new RadialView(d3.select("#graph"), config);
radialView.initialize();
radialView.nodes.bind("click", function (node) {
    animation.stop();
    navigation.step(node.public_key);
});

// Build up the help page
var helpPage = new HelpPage(config);
helpPage.initialize();

// Set up the force simulation to move all nodes into position
var simulation = new RadialSimulation({
    radius_step: config.radius_step
});
simulation.initialize().onTick(radialView.tick);

// Set up the positioning to calculate positions for all nodes
var positioning = new RadialPositioning(navigation, simulation);
positioning.initialize();

// Set up the stepping-animation for navigating back to the user node
var animation = new RadialSteppingAnimation(radialView.nodes, navigation, config.steppingAnimation);

// Launch the visualization by loading the user as focus node
navigation.step("self");

/**
 * Update the visualization for the provided data set
 * @param {GraphData} graph
 */
function update(graph) {

    // Set the positions on all graph nodes
    positioning.setNodePositions(graph);

    // Update the view
    radialView.onNewData(graph);

    // Update the simulation
    simulation.update(positioning.tree.nodes);

}

/**
 * Play the back-to-you animation
 */
function backToYou() {
    animation.rewindHistory();
}

/**
 * Toggle the help page on button click
 */
function toggleHelpPage() {
    helpPage.toggle();
}
