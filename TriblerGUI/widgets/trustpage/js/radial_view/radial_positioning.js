/**
 * Turns the graph into a tree and positions (using an angle) all GraphNodes.
 * @param {RadialNavigation} navigation
 * @param {RadialSimulation} simulation
 * @constructor
 */
function RadialPositioning(navigation, simulation, options) {

    var self = this,
        defaults = {};

    self.config = Object.assign({}, defaults, options || {});
    self.nodes = [];
    self.focus_pk = null;
    self.orientation = 0;

    /**
     * Make all necessary binds.
     */
    self.initialize = function () {

        navigation.bind("before-step", function (new_public_key) {
            var new_focus_node = find(self.nodes, "public_key", new_public_key);
            self.orientation = new_focus_node ? new_focus_node.treeNode.alpha || 0 : 0;
        });
    };

    /**
     * Add the tree nodes and angles to all nodes in this view.
     * @param {GraphData} newGraphData
     */
    self.setNodePositions = function (newGraphData) {

        // Copy positions from node to node
        self.nodes.forEach(function (node) {
            var new_node = find(newGraphData.nodes, "public_key", node.public_key);

            if (new_node) {
                new_node.x = node.x;
                new_node.y = node.y;
            }
        });

        // Position all new nodes at the focus node
        newGraphData.nodes.forEach(function (node) {
            if (!('x' in node)) {
                node.x = newGraphData.focus_node.x || 0;
                node.y = newGraphData.focus_node.y || 0;
            }
        });

        // Make a tree from the graph
        var tree = graphToTree(newGraphData.focus_node);

        // Bind each tree node to its graph node
        tree.nodes.forEach(function (treeNode) {
            treeNode.graphNode.treeNode = treeNode;
        });

        // Position all nodes on a circle
        applyRecursiveAlphaByDescendants(tree.root, 0, 2 * Math.PI, simulation.getCenterFix());

        // Find the new angle of the old focus node
        var target_angle = (self.orientation + Math.PI),
            old_focus_node = self.focus_pk ? find(newGraphData.nodes, "public_key", self.focus_pk) : null,
            current_angle = old_focus_node ? old_focus_node.treeNode.alpha || 0 : 0,
            correction = target_angle - current_angle;

        // Maintain orientation between previous and current focus node
        tree.nodes.forEach(function (node) {
            node.alpha += correction;
        });

        // Remember the current focus, tree and nodes
        self.focus_pk = newGraphData.focus_pk;
        self.tree = tree;
        self.nodes = newGraphData.nodes;

    };

}
