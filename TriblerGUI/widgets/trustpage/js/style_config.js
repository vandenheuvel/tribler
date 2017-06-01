/**
 * Configuration file for style properties of the links and nodes in the graph.
 */

var config = {
    link : {
        colorLinkSource : "#ffff00",
        colorLinkTarget : "#ff0000",
        strokeWidthMin : 6,
        strokeWidthMax : 10
    },
    node : {
        publicKeyLabel : {
            color : "#000000",
            fontSize : "14",
            fontFamily : "sans-serif",
            fontWeight : "bold",
            characters : 3
        },
        circle : {
            radius : 20,
            cx : 0,
            cy : 0,
            cursor : "pointer"
        },
        color : {
            domain : [0, 0.5, 1],
            range : ["red", "yellow", "green"]
        },
        hoverLabel : {
            publicKeyCharacters : 5,
            pageRankDecimals : 4,
            opacityOnNode : 1,
            opacityOnEdge : 0.8
        }
    },
    radius_step: 120
};

if (typeof module !== "undefined") {
    module.exports = config;
}
