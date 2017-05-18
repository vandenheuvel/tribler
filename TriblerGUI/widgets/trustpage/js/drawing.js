/**
 * These methods are concerned with drawing and styling SVG elements
 */

/**
 * Select all <svg.node> elements in .nodes
 * @returns {*}
 */
function selectNodes(svg) {
    return svg
        .select(".nodes")
        .selectAll(".node");
}

/**
 * Draw the nodes and their labels
 * @param selection
 * @returns {*}
 */
function drawNodes(svg, data, on_click) {

    // Always remove existing nodes before adding new ones
    selectNodes(svg).remove();

    var selection = selectNodes(svg).data(data.nodes).enter();

    // Create an <svg.node> element.
    var groups = selection
        .append("svg")
        .attr("overflow", "visible")
        .attr("class", "node");

    // Append a <circle> element to it.
    var circles = groups
        .append("circle")
        .attr("fill", function (d) { return getNodeColor(d, data)} )
        .attr("r", "20")
        .attr("cx", 0)
        .attr("cy", 0)
        .style("cursor","pointer")
        .on("click", on_click)
        .on("mouseenter", function(){
            d3.select(this).transition().ease(d3.easeElasticOut).delay(0).duration(300).attr("r", 25);
        }).on("mouseout", function(){
            d3.select(this).transition().ease(d3.easeElasticOut).delay(0).duration(300).attr("r", 20);
        });

    // Append a <text> element to it
    groups
        .append("text")
        .attr("x", 24)
        .attr("y", 24)
        .style("font-family", "sans-serif")
        .style("font-size", "12")
        .style("fill", "#ffff00")
        .text(function (d) {
            return d.public_key;
        });

    // Return the group of <svg.node>
    return groups;

}

function getNodeColor(d, data) {
    console.log(data);
    console.log("rank: " + data.min_page_rank);
    return nodeColor((d.page_rank - data.min_page_rank) / (data.max_page_rank - data.min_page_rank))
}

var nodeColor = d3.scaleLinear()
    .domain([0, 0.5, 1])
    .range(["red", "yellow", "green"]);

/**
 * Select all <svg.link> elements in .links
 * @returns {*}
 */
function selectLinks(svg) {
    return svg
        .select(".links")
        .selectAll(".link")
}

/**
 * Draw the links upon given data
 * @param selection
 * @returns {*}
 */
function drawLinks(svg, data) {

    selectLinks(svg).remove();

    var selection = selectLinks(svg).data(data).enter();

    var links = selection
        .append("svg")
        .attr("class", "link");

    links.append("line")
        .attr("class", "link-source")
        .attr("stroke-width", 2)
        .style("stroke", "yellow");

    links.append("line")
        .attr("class", "link-target")
        .attr("stroke-width", 2)
        .style("stroke", "red");

    return links;
}
