/**
 * These methods are concerned with drawing and styling SVG elements
 */

if (typeof require !== "undefined") {
    var config = require("./style_config.js");
}

/**
 * Select all <svg.node> elements in .nodes
 * @returns D3 Selection of <svg.node> elements
 */
function selectNodes(svg) {
    return svg
        .select(".nodes")
        .selectAll(".node");
}

/**
 * Format a byte value depending on its size.
 *
 * @param bytes
 */
function formatBytes(bytes) {

    var sizes = config.byteUnits;

    var i = 0;

    while (bytes >= Math.pow(10, (i + 1) * 3) && (i + 1) < sizes.length) i++;

    return parseFloat(Math.round((1.0 * bytes) / Math.pow(10, (i - 1) * 3)) / 1000).toPrecision(4) + " " + sizes[i];
}

/**
 * Draw the nodes and their labels
 * @param svg the svg from the body
 * @param data the JSON data of the graph
 * @param on_click the function that responds to the click
 * @param hoverInfoLabel the label to display the information in
 * @returns D3 Selection of <svg.node> elements
 */
function drawNodes(svg, data, on_click, hoverInfoLabel) {

    // Always remove existing nodes before adding new ones
    var all = selectNodes(svg).data(data.nodes, function (d) {
            return d.public_key;
        }),
        exit = all.exit(),
        enter = all.enter();

    // Remove exit nodes
    exit.remove();

    // Create an <svg.node> element.
    var groups = enter
        .append("svg")
        .attr("overflow", "visible")
        .attr("class", "node");

    // Append a <circle> element to it
    var circles = groups
        .append("circle")
        .attr("fill", function (d) {
            return getNodeColor(d, data)
        })
        .attr("r", "0")
        .style("stroke", config.background)
        .attr("stroke-width", config.node.circle.strokeWidth)
        .attr("cx", config.node.circle.cx)
        .attr("cy", config.node.circle.cy);

    // Transition the radius of the circles
    circles.transition()
        .duration(1000)
        .attr("r", function (d) {
            return getNodeRadius(d, data)
        });

    // Append a <text> element to it
    groups
        .append("text")
        .attr("dominant-baseline", "central")
        .attr("text-anchor", "middle")
        .style("font-family", config.node.publicKeyLabel.fontFamily)
        .style("font-size", config.node.publicKeyLabel.fontSize)
        .style("font-weight", config.node.publicKeyLabel.fontWeight)
        .style("fill", config.node.publicKeyLabel.color)
        .text(function (d) {
            return d.public_key.substr(-config.node.publicKeyLabel.characters);
        });

    // Transparent circle to capture mouse events
    groups
        .append("circle")
        .style("fill-opacity", "0")
        .attr("r", function (d) {
            return getNodeRadius(d, data) + config.node.circle.strokeWidth;
        })
        .attr("cx", config.node.circle.cx)
        .attr("cy", config.node.circle.cy)
        .style("cursor", config.node.circle.cursor)
        .on("click", on_click)
        .on("mouseover", function (d) {
            mouseOverNode(d, data, hoverInfoLabel);
            var public_key = d.public_key;
            applyLinkHighlight(function (d) {
                return d.source.public_key === public_key || d.target.public_key === public_key;
            })
        })
        .on("mousemove", function () {
            hoverInfoLabel
                .style("left", d3.event.pageX + "px")
                .style("top", d3.event.pageY + "px");
        })
        .on("mouseout", function (d) {
            d3.select(".hoverInfoLabel").select("table.hoverInfoTable").selectAll("tr").remove();
            hoverInfoLabel.style("opacity", 0);
            unapplyLinkHighlight();
        });

    // Return the group of <svg.node>
    return groups;
}

/**
 * Highlights all links for which the filter function returns true, dims the others
 * @param filterFunction
 */
function applyLinkHighlight(filterFunction) {
    selectLinks(svg)
        .transition()
        .duration(config.link.highlightInDuration)
        .style("opacity", function (d) {
            return filterFunction(d) ? 1 : config.link.highlightDimmedOpacity
        });
}

/**
 * Restores the original opacity of all links
 */
function unapplyLinkHighlight() {
    selectLinks(svg)
        .transition()
        .delay(config.link.highlightOutDelay)
        .duration(config.link.highlightOutDuration)
        .style("opacity", function (d) {
            return getLinkOpacity(d);
        });
}

/**
 * Compute the radius of the node.
 * @param node the node to compute the size of
 * @param data data to get information from
 * @returns the radius of the node
 */
function getNodeRadius(node, data) {
    var nodeTraffic = node.total_up + node.total_down - data.traffic_min;
    var slope = (config.node.circle.maxRadius - config.node.circle.minRadius) * data.traffic_slope;
    return config.node.circle.minRadius + (slope * nodeTraffic)
}

/**
 * Show the node information when the mouse enters a node
 * @param nodeData the node to get the information of
 * @param data the JSON data of the graph
 * @param hoverInfoLabel the label to display the information in
 */
function mouseOverNode(nodeData, data, hoverInfoLabel) {
    // The quantity descriptions and their corresponding values
    var quantities = [
        ["Public key", "..." + nodeData.public_key.substr(nodeData.public_key.length - config.node.hoverLabel.publicKeyCharacters)],
        ["Page rank score", nodeData.page_rank.toFixed(config.node.hoverLabel.pageRankDecimals)],
        ["Total uploaded", formatBytes(nodeData.total_up)],
        ["Total downloaded", formatBytes(nodeData.total_down)]
    ];

    // Update the label with the information corresponding to the node
    setHoverInfoLabelContents(quantities, hoverInfoLabel);
    hoverInfoLabel.style("background-color", getNodeColor(nodeData, data));
    showHoverInfoLabel(hoverInfoLabel);
}

/**
 * Make the information label visible
 * @param hoverInfoLabel the label to make visible
 */
function showHoverInfoLabel(hoverInfoLabel) {
    hoverInfoLabel
        .style("opacity", config.node.hoverLabel.opacity)
        .style("display", "block");
}

/**
 * Get the color of a node based on the page rank score of the node
 * @param quantities array with the quantities to display and their values
 * @param hoverInfoLabel the label to display the information in
 */
function setHoverInfoLabelContents(quantities, hoverInfoLabel) {
    var table = d3.select(".hoverInfoLabel").select("table.hoverInfoTable");

    var rows = table
        .selectAll("tr")
        .data(quantities)
        .enter().append("tr");

    // Set the quantity description in the first column, the quantity value in the second column
    var cell1 = rows.append("td").attr("class", "quantity").html(function (d) {return d[0]});
    var cell2 = rows.append("td").html(function (d) {return d[1]});
}

/**
 * Get the color of a node based on the page rank score of the node
 * @param node the node to get the color for
 * @param data the JSON data of the graph
 * @returns the color of the node
 */
function getNodeColor(node, data) {
    // Use D3 color scale to map floats to colors
    var nodeColor = d3.scaleLinear()
        .domain(config.node.color.domain)
        .range(config.node.color.range);

    // Map relative to the minimum and maximum page rank of the graph
    var rank_difference = data.max_page_rank - data.min_page_rank;
    if (rank_difference === 0) {
        return nodeColor(1);
    }

    return nodeColor((node.page_rank - data.min_page_rank) / rank_difference);
}

/**
 * Select all <svg.link> elements in .links
 * @returns D3 Selection of <svg.link> elements
 */
function selectLinks(svg) {
    return svg
        .select(".links")
        .selectAll(".link")
}

/**
 * Draw the links upon given data
 * A link between two nodes is composed of two parts, representing the amount of data uploaded and downloaded
 * @param svg the svg from the body
 * @param data the JSON data of the graph
 * @param hoverInfoLabel the label to display the information in
 * @returns D3 Selection of <svg.link> elements
 */
function drawLinks(svg, data, hoverInfoLabel) {
    selectLinks(svg).remove();

    // All lines, identified by source and target public_key
    var all = selectLinks(svg).data(data.links, function (l) {
        return l.source.public_key + "" + l.target.public_key
    });

    // Remove exit lines
    all.exit().remove();

    var links = all.enter()
        .append("svg")
        .attr("class", "link")
        .style("opacity", "0");

    // The source part of the link
    links.append("line")
        .attr("class", "link-source")
        .style("stroke", config.link.color);

    // The target part of the link
    links.append("line")
        .attr("class", "link-target")
        .style("stroke", config.link.color);

    // Functionality for the composed link
    links
        .style("stroke", config.link.color)
        .attr("stroke-width", function (d) {
            return getStrokeWidth(d, data);
        })
        .on("mouseover", function (d) {
            mouseOverLink(d, this, hoverInfoLabel);
            applyLinkHighlight(function (link) {
                return link === d;
            })
        })
        .on("mousemove", function () {
            hoverInfoLabel
                .style("left", d3.event.pageX + "px")
                .style("top", d3.event.pageY + "px");
        })
        .on("mouseout", function () {
            d3.select(".hoverInfoLabel").select("table.hoverInfoTable").selectAll("tr").remove();
            hoverInfoLabel.style("opacity", 0);
            unapplyLinkHighlight();
        });

    links.transition()
        .duration(1000)
        .style("opacity", function (d) {
            return getLinkOpacity(d);
        });

    return links;
}

/**
 * Calculate the link opacity.
 *
 * For parent-child links the opacity decreases with the distance to
 * the focus node. For other links the opacity is always at a minimum.
 *
 * @param link
 * @returns {number} opacity
 */
function getLinkOpacity(link) {
    var t1 = link.source.treeNode,
        t2 = link.target.treeNode,
        minDepth = Math.min(t1.depth, t2.depth),
        opacityByDepth = 1 - minDepth * config.link.opacityDecrementPerLevel;
    return (t1.parent === t2 || t2.parent === t1) ? Math.max(opacityByDepth, config.link.opacityMinimum) : config.link.opacityMinimum;
}

/**
 * Show the link information when the mouse enters a link
 * @param linkData the link to get the information of
 * @param linkObject the link object of the html
 * @param hoverInfoLabel the label to display the information in
 */
function mouseOverLink(linkData, linkObject, hoverInfoLabel) {
    // The quantity descriptions and the corresponding values
    var quantities = [
        ["Uploaded by ..." + linkData.target_pk.substr(-config.node.hoverLabel.publicKeyCharacters), formatBytes(linkData.amount_up)],
        ["Uploaded by ..." + linkData.source_pk.substr(-config.node.hoverLabel.publicKeyCharacters), formatBytes(linkData.amount_down)]
    ];

    // Update the label with the information corresponding to the link
    setHoverInfoLabelContents(quantities, hoverInfoLabel);
    hoverInfoLabel.style("background-color", d3.select(linkObject).style("stroke"));
    showHoverInfoLabel(hoverInfoLabel);
}

/**
 * Get the stroke width based on the total amount of transmitted data over the link,
 * relative to the other links in the graph
 * @param link the link to get the width for
 * @param data the JSON data of the graph
 * @returns the width of the link
 */
function getStrokeWidth(link, data) {
    // The difference between the minimum and maximum data links
    var transmissionDifference = data.max_transmission - data.min_transmission;

    // The difference between the minimum and maximum stroke width
    var widthDifference = config.link.strokeWidthMax - config.link.strokeWidthMin;

    // If exactly the same amount is transmitted between all peers, return the middle of the width interval
    if (transmissionDifference === 0)
        return (config.link.strokeWidthMax + config.link.strokeWidthMin) / 2;

    // The total transmission of the current link
    var linkTotal = link.amount_up + link.amount_down;

    // The fraction of the current link in the network
    var fraction = (linkTotal - data.min_transmission) / transmissionDifference;

    // The width based on the fraction and the interval
    return fraction * widthDifference + config.link.strokeWidthMin;
}

/**
 * Draw a ring around the center on which nodes can be put.
 * @param svg
 * @param center_x
 * @param center_y
 * @param radius
 * @returns D3 Selection of a <circle.neighbor-ring> element
 */
function drawNeighborRing(svg, center_x, center_y, radius) {
    return svg.append("circle")
        .attr("class", "neighbor-ring")
        .attr("r", 0)
        .attr("cx", center_x)
        .attr("cy", center_y)
        .attr("stroke-width", 1)
        .attr("fill", "transparent")
        .style("stroke", "#333333")
        .transition()
        .duration(1000)
        .attr("r", radius)
}

if (typeof module !== "undefined") {
    module.exports = {
        getStrokeWidth: getStrokeWidth,
        getNodeRadius: getNodeRadius,
        formatBytes: formatBytes
    };
}
