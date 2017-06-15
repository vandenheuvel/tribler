if (typeof require !== "undefined") {
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
        var groups = enterSelection.append("svg")
            .attr("class", "node")

            // Limit surface area of <svg>
            .attr("overflow", "visible")
            .attr("width", 1)
            .attr("height", 1);

        // Append <circle.background> to <svg.node>
        var background = groups.append("circle")
            .attr("class", "background")
            .attr("fill", self.config.circle.strokeColor)
            .attr("r", function (node) { return self._calculateRadius(node, true)});

        // Append <svg.foreground> to <svg.node>
        var foreground = groups.append("svg")
            .attr("class", "foreground")

            // Limit surface area of <svg>
            .attr("overflow", "visible")
            .attr("width", 1)
            .attr("height", 1);

        // Append <circle.color> to <svg.foreground>
        foreground.append("circle")
            .attr("class", "color")
            .attr("fill", function (node) {
                return self._calculateFill(node)
            })
            .attr("stroke", self.config.circle.strokeColor)
            .attr("stroke-width", self.config.circle.strokeWidth)
            .attr("r", function (node) { return self._calculateRadius(node, false)});

        // Append <text> to <svg.foreground>
        foreground.append("text")
            .attr("dominant-baseline", "central")
            .attr("text-anchor", "middle")
            .style("font-family", self.config.publicKeyLabel.fontFamily)
            .style("font-size", self.config.publicKeyLabel.fontSize)
            .style("font-weight", self.config.publicKeyLabel.fontWeight)
            .style("fill", self.config.publicKeyLabel.color)
            .text(function (d) { return self.getNodeName(d); });

        // Transparent circle to capture mouse events
        foreground.append("circle")
            .attr("class", "events")
            .attr("fill", "transparent")
            .attr("r", function (node) { return self._calculateRadius(node, true); })
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
    self.update = function (updateSelection) {
        // Pass updated data through to all child elements using it
        updateSelection.each(function (newData) {
            var nodeElement = d3.select(this);
            nodeElement.select('.background').datum(newData);
            nodeElement.select('.foreground').datum(newData);
            nodeElement.select('.events').datum(newData);
        });
    };

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
     * Get the name of the node, either the public key or a string representing the node of the user himself.
     * @param {GraphNode} node
     * @returns {string} name of the node
     */
    self.getNodeName = function (node) {
        return node.is_user ? self.config.userLabelText : node.public_key.substr(-self.config.publicKeyLabel.characters);
    };

    /**
     * Highlights all links for which the filter function returns true, dims the others.
     * @param filterFunction
     */
    self.applyHighlight = function (filterFunction) {
        self.selectAll()
            .selectAll("svg.foreground")
            .transition()
            .duration(self.config.highlightInDuration)
            .style("opacity", function (d) {
                return filterFunction(d) ? 1 : self.config.highlightDimmedOpacity
            });
    };

    /**
     * Restores the original opacity of all links.
     */
    self.unapplyHighlight = function () {
        self.selectAll()
            .selectAll("svg.foreground")
            .transition()
            .duration(self.config.highlightOutDuration)
            .style("opacity", 1);
    };

    /**
     * Compute the radius of the node.
     * @param {GraphNode} node - the node to compute the size of
     * @param {boolean} is_background - if true, will return the radius of the background (larger than foreground)
     * @returns {number} the radius of the node
     */
    self._calculateRadius = function (node, is_background) {
        var nodeTraffic = node.total_up + node.total_down - self.graphData.traffic_min;
        var slope = (self.config.circle.maxRadius - self.config.circle.minRadius) * self.graphData.traffic_slope;
        return self.config.circle.minRadius + (slope * nodeTraffic) +
            (is_background ? self.config.circle.strokeWidth : 0);
    };

    /**
     * Get the color of a node based on the difference in total
     * amount uploaded and total amount downloaded of a node.
     * @param {GraphNode} node - the node to get the color for
     * @returns the color of the node
     */
    self._calculateFill = function (node) {
        // Use D3 color scale to map floats to colors
        var nodeColor = d3.scaleLinear()
            .domain(self.config.color.domain)
            .range(self.config.color.range);

        var difference = node.total_up - node.total_down;
        difference = Math.max(difference, self.config.upDownDifferenceDomain.min);
        difference = Math.min(difference, self.config.upDownDifferenceDomain.max);

        var rangeSize = self.config.upDownDifferenceDomain.max - self.config.upDownDifferenceDomain.min;
        return nodeColor((difference - self.config.upDownDifferenceDomain.min) / rangeSize);
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
