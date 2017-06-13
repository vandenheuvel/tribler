/**
 * This file tests the radial_link.js file with unit tests
 */

assert = require("assert");
radial_node = require("TriblerGUI/widgets/trustpage/js/radial_view/radial_node.js");

describe("radial_node.js", function () {

    describe("getNodeRadius", function () {
        var nodes = new radial_node.RadialNodes(null, {
            circle: {
                minRadius : 15,
                maxRadius : 25,
            }
        });

        it("the minimal node size is returned when the node has the least amount of traffic", function () {
            nodes.graphData = {
                "traffic_slope": 1,
                "traffic_min": 1
            };
            var node = {
                "total_up": 0,
                "total_down": 1
            };
            assert.equal(15, nodes._calculateRadius(node));
        });
    });

});
