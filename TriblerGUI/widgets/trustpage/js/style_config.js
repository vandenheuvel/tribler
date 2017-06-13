/**
 * Configuration file for style properties of the links and nodes in the graph.
 */

var config = {
    byteUnits: ["B", "kB", "MB", "GB", "TB", "PB"],
    background: "#202020",
    hoverInDelay: 0,
    hoverOutDelay: 500,
    link: {
        color: "#22FFD5",
        highlightColor: "#DD002A",
        strokeWidthMin: 2,
        strokeWidthMax: 10,
        opacityMinimum: 0.05,
        opacityDecrementPerLevel: 0.02,
        highlightDimmedOpacity: 0.1,
        highlightInDuration: 200,
        highlightOutDuration: 1000
    },
    node: {
        userLabelText: "You",
        publicKeyLabel: {
            color: "#202020",
            fontSize: "10px",
            fontFamily: "sans-serif",
            fontWeight: "bold",
            characters: 3
        },
        circle: {
            minRadius: 15,
            maxRadius: 25,
            cursor: "pointer",
            strokeWidth: 3,
            strokeColor: "#202020"
        },
        color: {
            domain: [0, 0.5, 1],
            range: ["#FF1D3E", "#F9FF15", "#0CFF18"]
        },
        hoverLabel: {
            publicKeyCharacters: 5,
            pageRankDecimals: 4,
            opacity: 0.85
        },
        highlightDimmedOpacity: 0.5,
        highlightInDuration: 200,
        highlightOutDuration: 1000,
        // TODO: Move these configuration items to the core
        upDownDifferenceDomain: {
            min: -100,
            max: 500
        }
    },
    tooltip: {
        background: "#FFFFFF"
    },
    neighbor_ring: {
        strokeColor: "#333333"
    },
    radius_step: 120,
    neighbor_level: 2
};

if (typeof module !== "undefined") {
    module.exports = config;
}
