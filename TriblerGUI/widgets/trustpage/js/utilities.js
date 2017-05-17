/**
 * Filters the nodes on which the given force is applied using a provided filter callback.
 *
 * @param force
 * @param filter function (nodes) {}
 */
function filterForceNodes(force, filter) {
    var init = force.initialize;
    force.initialize = function (nodes) {
        init(nodes.filter(filter));
    }
}

/**
 * List the neighbors of a node with a provided public key
 * @param edges
 * @param neighborPK
 * @returns {Array}
 */
function listNeighborsOf(edges, neighborPK) {
    var neighbors = [];
    for (var i = 0; i < edges.length; i++) {
        var n = null;
        if (edges[i].source == neighborPK)
            n = edges[i].target;
        else if (edges[i].target == neighborPK)
            n = edges[i].source;

        if (n && neighbors.indexOf(n) == -1) {
            neighbors.push(n);
        }
    }
    return neighbors;
}