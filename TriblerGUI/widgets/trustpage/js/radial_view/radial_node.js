if (typeof require !== "undefined") {
    var config = require("../style_config.js");
    var applyEventfulMixin = require("../support/eventful_mixin.js").applyEventfulMixin;
}

/**
 * The nodes of the RadialView.
 * @param svg - the parent svg element
 * @param {Object} options - configuration overrides for the nodes
 * @constructor
 */
function RadialNodes(svg, options) {

    applyEventfulMixin(this);

    var self = this,
        defaults = {};

    self.graphData = null;
    self.config = Object.assign({}, defaults, options || {});

    /**
     * Select all <svg.node> objects in the SVG.
     */
    self.selectAll = function () {
        return svg.select(".nodes").selectAll(".node");
    };

    /**
     * Create, update and destroy the <svg.link> objects based on new data.
     * @param {GraphData} newGraphData
     */
    self.onNewData = function (newGraphData) {
        self.graphData = newGraphData;

        var update = self.selectAll()
            .data(newGraphData.nodes, function (node) {
                return node.public_key;
            });

        self.destroy(update.exit());
        self.update(update);
        self.create(update.enter());
    };

    /**
     * Create the new <svg.link> objects based on entering data.
     * @param enterSelection
     */
    self.create = function (enterSelection) {

        // Create <svg.node>
        var groups = enterSelection
            .append("svg")
            .attr("overflow", "visible")
            .attr("class", "node");

        // Append <circle> to <svg.node>
        var circles = groups
            .append("circle")
            .attr("fill", function (node) {
                return self._calculateFill(node)
            })
            .attr("r", "0")
            .style("stroke", config.node.circle.strokeColor)
            .attr("stroke-width", self.config.circle.strokeWidth)
            .attr("cx", self.config.circle.cx)
            .attr("cy", self.config.circle.cy);

        // Transition the radius of the circles
        circles.transition()
            .duration(1000)
            .attr("r", function (node) {
                return self._calculateRadius(node)
            });

        // Append a <text> element to it
        groups
            .append("text")
            .attr("dominant-baseline", "central")
            .attr("text-anchor", "middle")
            .style("font-family", self.config.publicKeyLabel.fontFamily)
            .style("font-size", self.config.publicKeyLabel.fontSize)
            .style("font-weight", self.config.publicKeyLabel.fontWeight)
            .style("fill", self.config.publicKeyLabel.color)
            .text(function (d) {
                return d.public_key.substr(-self.config.publicKeyLabel.characters);
            });

        // Transparent circle to capture mouse events
        groups
            .append("circle")
            .style("fill-opacity", "0")
            .attr("r", function (node) {
                return self._calculateRadius(node) + self.config.circle.strokeWidth;
            })
            .attr("cx", self.config.circle.cx)
            .attr("cy", self.config.circle.cy)
            .style("cursor", self.config.circle.cursor)
            .on("click", self.getEventHandlers("click"))
            .on("mouseover", self.getEventHandlers("mouseover"))
            .on("mousemove", self.getEventHandlers("mousemove"))
            .on("mouseout", self.getEventHandlers("mouseout"));
    };

    /**
     * Update existing <svg.link> objects based on updated data.
     * @param updateSelection
     */
    self.update = function (updateSelection) {};

    /**
     * Destroy existing <svg.link> objects based on exiting data.
     * @param exitSelection
     */
    self.destroy = function (exitSelection) {
        exitSelection.remove();
    };

    /**
     * Update the positions of the nodes on each tick.
     */
    self.tick = function () {
        self.selectAll()
            .attr("x", function (d) { return d.x; })
            .attr("y", function (d) { return d.y; });
    };

    /**
     * Compute the radius of the node.
     * @param {GraphNode} node - the node to compute the size of
     * @returns the radius of the node
     */
    self._calculateRadius = function (node) {
        var nodeTraffic = node.total_up + node.total_down - self.graphData.traffic_min;
        var slope = (self.config.circle.maxRadius - self.config.circle.minRadius) * self.graphData.traffic_slope;
        return self.config.circle.minRadius + (slope * nodeTraffic)
    };

    /**
     * Get the color of a node based on the page rank score of the node
     * @param {GraphNode} node - the node to get the color for
     * @returns the color of the node
     */
    self._calculateFill = function (node) {
        // Use D3 color scale to map floats to colors
        var nodeColor = d3.scaleLinear()
            .domain(self.config.color.domain)
            .range(self.config.color.range);

        // Map relative to the minimum and maximum page rank of the graph
        var rank_difference = self.graphData.max_page_rank - self.graphData.min_page_rank;
        if (rank_difference === 0) {
            return nodeColor(1);
        }

        return nodeColor((node.page_rank - self.graphData.min_page_rank) / rank_difference);
    };

}

/**
 * Export functions so Mocha can test it
 */
if (typeof module !== 'undefined') {
    module.exports = {
        RadialNodes: RadialNodes
    };
}
