/**
 * The tooltip that provides information when hovering nodes or links.
 */

if(typeof require !== "undefined") {
    var config = require("../style_config.js");
}

function RadialToolTip() {

    var self = this;

    /**
     * Build the tooltip and add it to the body.
     */
    self.initialize = function () {
        d3.select("body").append("div")
            .attr("class", "hoverInfoLabel")
            .attr("id", "hoverInfoLabel")
            .style("opacity", config.node.hoverLabel.opacity)
            .style("display", "none")
            .append("table").attr("class", "hoverInfoTable");
    };

    /**
     * Select the tooltip.
     */
    self.select = function () {
        return d3.select(".hoverInfoLabel");
    };

    /**
     * Show the tooltip.
     */
    self.show = function () {
        self.select().style("display", "block");
    };

    /**
     *  Hide the tooltip.
     */
    self.hide = function () {
        self.select().style("display", "none");
    };

    /**
     * Move the tooltip to position x, y.
     * @param {number} x
     * @param {number} y
     */
    self.moveTo = function (x, y) {
        self.select().style("left", x + "px").style("top", y + "px");
    };

    /**
     * Put the node information in the tooltip.
     * @param {GraphNode} node - the node data to display
     */
    self.displayNodeData = function (node) {
        // The quantity descriptions and their corresponding values
        var quantities = [
            ["Public key", "..." + node.public_key.substr(node.public_key.length - config.node.hoverLabel.publicKeyCharacters)],
            ["Page rank score", node.page_rank.toFixed(config.node.hoverLabel.pageRankDecimals)],
            ["Total uploaded", formatBytes(node.total_up)],
            ["Total downloaded", formatBytes(node.total_down)]
        ];

        // Update the label with the information corresponding to the node
        self.setContents(quantities);
        self.setBackground(config.tooltip.background);
    };

    /**
     * Put the link information in the tooltip.
     * @param {GraphLink} link - the link to get the information of
     */
    self.displayLinkData = function (link) {
        // The quantity descriptions and the corresponding values
        var quantities = [
            ["Uploaded by ..." + link.target_pk.substr(-config.node.hoverLabel.publicKeyCharacters), formatBytes(link.amount_up)],
            ["Uploaded by ..." + link.source_pk.substr(-config.node.hoverLabel.publicKeyCharacters), formatBytes(link.amount_down)]
        ];

        // Update the label with the information corresponding to the link
        self.setContents(quantities);
        self.setBackground(config.link.color);
    };

    /**
     * Set the background color of the tooltip.
     * @param {String} color
     */
    self.setBackground = function (color) {
        self.select().style("background-color", color);
    };

    /**
     * Put the given quantities and values in the tooltip.
     * @param {String[][]} quantities - n by 2 array with the data to display.
     */
    self.setContents = function (quantities) {
        var table = self.select().select("table.hoverInfoTable");

        table.selectAll('tr').remove();

        var rows = table
            .selectAll("tr")
            .data(quantities)
            .enter().append("tr");

        // Set the quantity description in the first column, the quantity value in the second column
        var cell1 = rows.append("td").attr("class", "quantity").html(function (d) {return d[0]});
        var cell2 = rows.append("td").html(function (d) {return d[1]});
    };

}
