/**
 * Draw the legend based on the current visible network.
 * Handle clicks to show and hide the legend.
 */

/**
 * Draw the legend based on the quantitative data of the graph currently visible
 * @param data the data of the graph
 */
function drawLegend (data) {
    var svg = d3.select("#legend");

    // Link size

    var linkSize = d3.scaleLinear()
        .domain([data.min_transmission, data.max_transmission])
        .range([config.link.strokeWidthMin, config.link.strokeWidthMax]);

    svg.append("g")
        .attr("class", "legendSizeLink")
        .attr("fill", config.legend.textColor)
        .attr("transform", "translate(10, 20)");

    var legendSizeLink = d3.legendSize()
        .classPrefix("linkSize")
        .title("Data over connection")
        .scale(linkSize)
        .shape("line")
        .labelWrap(70)
        .shapeWidth(70)
        .shapePadding(15)
        .labelOffset(20)
        .labels(function(i) {
            return formatBytes(i.generatedLabels[i.i], 3);
        });

    applyLegendStyle(legendSizeLink);

    svg.select(".legendSizeLink")
        .call(legendSizeLink);

    // Data transmission nodes

    var nodeSize = d3.scaleLinear()
        .range([config.node.circle.minRadius, config.node.circle.maxRadius]);

    var traffic_diff = data.traffic_max - data.traffic_min;

    svg.append("g")
        .attr("class", "legendSizeNode")
        .attr("transform", "translate(10, 105)");

    console.log("Node size:" + nodeSize);

    var legendSizeNode = d3.legendSize()
        .classPrefix("nodeSize")
        .title("Data transmitted")
        .scale(nodeSize)
        .shape("circle")
        .labelWrap(70)
        .shapePadding(43)
        .labelOffset(20)
        .labels(function(i) { return formatBytes(data.traffic_min + i.i * traffic_diff, 3); });

    applyLegendStyle(legendSizeNode);

    svg.select(".legendSizeNode")
        .call(legendSizeNode);

    // Trust colors

    var nodeColorScale = d3.scaleLinear()
        .domain(config.node.color.domain)
        .range(config.node.color.range);

    range = [];
    for (var i = 0; i < 6; i++) {
        range.push(nodeColorScale(i/6, data));
    }

    var nodeColor = d3.scaleOrdinal()
        .domain(["Freerider", "Unreliable", "Neutral", "Reliable", "Trusted"])
        .range(range);

    svg.append("g")
        .attr("class", "legendNodeColor")
        .attr("fill", config.legend.textColor)
        .attr("transform", "translate(10, 220)");

    var legendNodeColor = d3.legendColor()
        .classPrefix("nodeColor")
        .title("Reputation")
        .shape("path", d3.symbol().type(d3.symbolCircle).size(1000)())
        .shapeWidth(30)
        .shapePadding(50)
        .scale(nodeColor);

    applyLegendStyle(legendNodeColor);

    svg.select(".legendNodeColor")
        .call(legendNodeColor);

    var title = document.getElementsByClassName("nodeColorlegendTitle")[0];
    var translate = document.createAttribute("transform");
    translate.value = "translate(0, -10)";
    title.setAttributeNode(translate);
}

/**
 * Applies the right ordering to the legend items.
 * @param legend item to apply format to
 */
function applyLegendStyle(legend) {
    legend
        .ascending(true)
        .orient("horizontal")
        .labelAlign("middle")
}


/**
 * Make the legend slide in and out on clicking the button.
 */
var hidden = true;
function switchLegend() {
    d3.select("#legendContainer")
        .transition()
        .duration(250)
        .style("left", function() {
            hidden = !hidden;
            if (hidden) return "10px";
            return "-435px";
        });

    if (hidden) document.getElementById("showLegendButtonDiv").innerHTML = "&#9664;";
    else document.getElementById("showLegendButtonDiv").innerHTML = "&#9654;";
}

/**
 * Callback for when the window is resized.
 * Currently only resizes the legend.
 */
function resizeWindow() {
    var w = Math.min(window.innerWidth, config.legend.maxWidth);
    var h = Math.min(window.innerHeight, config.legend.maxHeight);

    var widthScale = w / config.legend.maxWidth;
    var heightScale = h / config.legend.maxHeight;

    var scale = Math.max(config.legend.minScale, Math.min(widthScale, heightScale));

    d3.select("#legendContainer")
        .style("zoom", (scale * config.legend.scaleFactor) + "%");
}