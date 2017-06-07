/**
 * Configuration file for style properties of the links and nodes in the graph.
 */

var config = {
    byteUnits: ["B", "kB", "MB", "GB", "TB", "PB"],
    background: "#202020",
    link: {
        color: "#22FFD5",
        highlightColor: "#DD002A",
        strokeWidthMin: 2,
        strokeWidthMax: 10,
        opacityMinimum: 0.05,
        opacityDecrementPerLevel: 0.02,
        highlightDimmedOpacity: 0.1,
        highlightInDuration: 200,
        highlightOutDuration: 200,
        highlightOutDelay: 300
    },
    node: {
        userLabelText: "Me",
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
            cx: 0,
            cy: 0,
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
        }
    },
    tooltip: {
        background: "#FFFFFF"
    },
    neighbor_ring: {
        strokeColor: "#333333"
    },
    radius_step: 120,
    neighbor_level: 2,
    legend: {
        textColor: "#FFFFFF",
        maxWidth: 1600,
        maxHeight: 900,
        minScale: 0.75,
        scaleFactor: 95
    }
};

if (typeof module !== "undefined") {
    module.exports = config;
}
