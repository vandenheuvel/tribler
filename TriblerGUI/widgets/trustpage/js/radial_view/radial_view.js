/**
 * The Radial View of the Tribler Trust Graph.
 * @param svg
 * @param {Object} settings - override of the defaults
 * @constructor
 */
function RadialView(svg, settings) {

    var self = this;

    var defaults = {
        center_x: svg.attr("width") / 2,
        center_y: svg.attr("height") / 2
    };

    self.links = null;
    self.nodes = null;
    self.config = Object.assign({}, defaults, settings || {});
    self.hoverTimeout = null;

    /**
     * Set-up the <svg> with rings and bind all events of nodes and links.
     */
    self.initialize = function () {

        for (var i = 1; i <= self.config.neighbor_level; i++)
            self._drawNeighborRing(self.config.radius_step * i);

        svg.append("g").attr("class", "links");
        svg.append("g").attr("class", "nodes");
        svg.append("g").attr("class", "labels");

        self.links = new RadialLinks(svg, config.link);
        self.nodes = new RadialNodes(svg, config.node);
        self.inspector = new RadialInspector(d3.select("#inspector"));

        self.nodes.bind("click", function (node) {
            handle_node_click(node.public_key)
        });

        self.nodes.bind("mouseover", function (targetNode) {
            self.delayedHover(function () {
                self.inspector.displayNodeInfo(targetNode, self.nodes);

                // Highlight links attached to target node
                self.links.applyHighlight(function (d) {
                    return d.source_pk === targetNode.public_key
                        || d.target_pk === targetNode.public_key;
                });

                // Highlight target node
                self.nodes.applyHighlight(function(node){
                    return node.public_key === targetNode.public_key;
                });
            }, self.config.hover_in_delay);
        });

        self.nodes.bind("mouseout", function () {
            self.delayedHover(function () {
                self.inspector.displayNetworkInfo();
                self.links.unapplyHighlight();
                self.nodes.unapplyHighlight();
            }, self.config.hover_out_delay);
        });

        self.links.bind("mouseover", function (targetLink) {
            self.delayedHover(function () {
                self.inspector.displayLinkInfo(targetLink);

                // Highlight target link
                self.links.applyHighlight(function (link) { return link === targetLink; });

                // Highlight nodes of target link
                self.nodes.applyHighlight(function(node){
                    return targetLink.source === node || targetLink.target === node;
                });
            }, self.config.hover_in_delay);
        });

        self.links.bind("mouseout", function () {
            self.delayedHover(function () {
                self.links.unapplyHighlight();
                self.nodes.unapplyHighlight();
                self.inspector.displayNetworkInfo();
            }, self.config.hover_out_delay);
        });

    };

    /**
     * Pass the data to the nodes and edges.
     * @param {GraphData} newGraphData
     * @param {Tree} newTreeData
     */
    self.onNewData = function (newGraphData, newTreeData) {
        self.nodes.onNewData(newGraphData, newTreeData);
        self.links.onNewData(newGraphData, newTreeData);
        self.inspector.onNewData(newGraphData, newTreeData);
    };

    /**
     * Pass the tick to the nodes and edges.
     */
    self.tick = function () {
        self.links.tick();
        self.nodes.tick();
    };

    /**
     * Return the x-coordinate of the center
     * @returns {number}
     */
    self.getCenterX = function () {
        return self.config.center_x;
    };

    /**
     * Return the y-coordinate of the center
     * @returns {number}
     */
    self.getCenterY = function () {
        return self.config.center_y;
    };

    /**
     * Call a given callback after a period of time, overwriting a previously set callback.
     *
     * Many hover events will fire, causing a callback to be assigned before the previous callback is fired. This may
     * cause conflicts in the view (flickering). Therefore, any unfired hover callback must be cancelled before a new
     * one is set.
     * @param callback
     * @param delay
     */
    self.delayedHover = function (callback, delay) {
        if (self.hoverTimeout) clearTimeout(self.hoverTimeout);

        self.hoverTimeout = setTimeout(callback, delay);
    };

    /**
     * Draw a ring around the center on which nodes can be put.
     * @param radius
     * @returns D3 Selection of a <circle.neighbor-ring> element
     */
    self._drawNeighborRing = function (radius) {
        return svg.append("circle")
            .attr("class", "neighbor-ring")
            .attr("r", 0)
            .attr("cx", self.config.center_x)
            .attr("cy", self.config.center_y)
            .attr("stroke-width", 1)
            .attr("fill", "transparent")
            .style("stroke", config.neighbor_ring.strokeColor)
            .transition()
            .duration(1000)
            .attr("r", radius);
    }

}