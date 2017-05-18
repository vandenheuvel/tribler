/**
 * Process the JSON dictionary in the HTTP Response for the data used in the visualization.
 *
 * The JSON will be converted to the following format:
 * {
 *      "focus_node": "xyz",
 *      "min_page_rank": 5,
 *      "max_page_rank": 5,
 *      "nodes": [{
 *          "public_key": "xyz",
 *          "total_up": 100,
 *          "total_down": 500,
 *          "page_rank": 5
 *      }, ...],
 *          "links": [{
 *          "source_pk": "xyz",
 *          "source": {source node object},
 *          "target_pk": "xyz_n1",
 *          "target": {target node object},
 *          "amount_up": 100,
 *          "amount_down": 10,
 *          "ratio": 0.90909,
 *          "log_ratio": 0.66666
 *      }, ...]
 * }
 *
 * Note that the "nodes" list in the dictionary is in ascending order on total_up + total_down and "links" is in
 * ascending order on amount_up + amount_down.
 *
 * @param jsonData: the JSON dictionary passed on by the HTTP request
 * @returns a dictionary in the form specified above
 */
function processData(jsonData) {
    var data = JSON.parse(jsonData);
    var groupedEdges = groupBy(data.links, "source");
    var combinedEdges = [];

    // Calculate all combined edges
    data.nodes.forEach(function(node) {
        combinedEdges = combinedEdges.concat(getCombinedEdges(groupedEdges, node.public_key));
    });

    // Sort combined edges ascending on up + down
    combinedEdges = combinedEdges.sort(function(edgeOne, edgeTwo) {
        return edgeOne.amount_up + edgeOne.amount_down - edgeTwo.amount_up - edgeTwo.amount_down;
    });

    // Sort nodes ascending on up + down
    var nodes = data.nodes.sort(function(nodeOne, nodeTwo) {
        return nodeOne.total_up + nodeOne.total_down - nodeTwo.total_up - nodeTwo.total_down;
    });

    /**
     * Finds the first object in a list of objects that matches a given key-value pair
     * @param list
     * @param key
     * @param val
     * @returns {*}
     */
    function find(list, key, val){
        return list.find(function(item){
            return (typeof item === "object") && (key in item) && (item[key] === val);
        });
    }

    // Add reference to source and target object
    combinedEdges = combinedEdges.map(function (edge) {
        return Object.assign({}, edge, {
            source_pk : edge.source,
            target_pk : edge.target,
            source: find(nodes, "public_key", edge.source),
            target: find(nodes, "public_key", edge.target)
        });
    });

    var sortedPageRank = data.nodes.map(function(node) {return node.page_rank}).sort(function(pageRankOne, pageRankTwo) {
        return pageRankOne - pageRankTwo;
    });
    return {'focus_node': data.focus_node,
            'min_page_rank': sortedPageRank[0],
            'max_page_rank': sortedPageRank[sortedPageRank.length - 1],
            'nodes': nodes,
            'links': combinedEdges}
}

/**
 * Combine the directed edges between the given node and other nodes to one edge per pair.
 *
 * The attributes of the combined edges are calculated as follows:
 *  - from: node_name
 *  - to: to attribute from outgoing edge from node_name
 *  - amount_up: amount from the outgoing edge from node_name
 *  - amount_down: amount from the ingoing edge to node_name if any
 *  - ratio: amount_up / (amount_up + amount_down)
 *  - log_ratio: log(amount_up + 1) / (log(amount_up + 1) + log(amount_down + 1))
 *
 * @param groupedEdges: the dictionary of edges, grouped by "from" attribute
 * @param nodeName: the node name from which viewpoint each combine edge is created
 * @returns an array of combined edges with the described attributes
 */
function getCombinedEdges(groupedEdges, nodeName) {
    var combinedEdges = [];

    groupedEdges[nodeName].forEach(function (edge) {
        var inverseEdge = groupedEdges[edge.target].find(function(inv) {
            return inv.target === nodeName;
        });
        var up = edge.amount,
            down = 0,
            ratio = 0,
            logRatio = 0;
        if (inverseEdge !== undefined) {
            down = inverseEdge["amount"]
        }
        if (up !== 0 || down !== 0) {
            ratio = up / (up + down);
            logRatio = Math.log(up + 1) / (Math.log(up + 1) + Math.log(down + 1))
        }
        combinedEdges.push({'source': nodeName, 'target': edge['target'], 'amount_up': up, 'amount_down': down,
            'ratio': ratio, 'log_ratio': logRatio});
        groupedEdges[edge.target].splice(groupedEdges[edge['target']].indexOf(inverseEdge), 1)
    });
    return combinedEdges
}
