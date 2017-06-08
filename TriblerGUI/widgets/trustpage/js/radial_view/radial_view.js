/**
 * The Radial View of the Tribler Trust Graph.
 * @param svg
 * @param {Object} settings - override of the defaults
 * @constructor
 */
function RadialView(svg, settings) {

    var self = this;

    self.links = null;
    self.nodes = null;

    var defaults = {
        center_x: svg.attr("width") / 2,
        center_y: svg.attr("height") / 2,
        radius_step: config.radius_step,
        neighbor_level: config.neighbor_level
    };

    self.config = Object.assign({}, defaults, settings || {});

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
        tooltip = new RadialToolTip();

        tooltip.initialize();

        self.nodes.bind("click", function (node) {
            handle_node_click(node.public_key)
        });

        self.nodes.bind("mouseover", function (targetNode) {
            tooltip.displayNodeData(targetNode);
            tooltip.show();

            self.links.applyHighlight(function (d) {
                return d.source.public_key === targetNode.public_key
                    || d.target.public_key === targetNode.public_key;
            });
        });

        self.nodes.bind("mousemove", function () {
            tooltip.moveTo(d3.event.pageX, d3.event.pageY);
        });

        self.nodes.bind("mouseout", function () {
            self.links.unapplyHighlight();
            tooltip.hide();
        });

        self.links.bind("mouseover", function (link) {
            tooltip.displayLinkData(link);
            tooltip.show();
        });

        self.links.bind("mousemove", function () {
            tooltip.moveTo(d3.event.pageX, d3.event.pageY);
        });

        self.links.bind("mouseout", function () {
            tooltip.hide();
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
