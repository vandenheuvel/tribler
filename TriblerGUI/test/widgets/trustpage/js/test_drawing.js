/**
 * This file tests the drawing.js file with unit tests
 */

assert = require("assert");
config = require("TriblerGUI/widgets/trustpage/js/style_config.js");
drawing = require("TriblerGUI/widgets/trustpage/js/drawing.js");

describe("drawing.js", function () {
    describe('formatBytes', function () {
        it('should return correct formats', function () {
            var data = [
                [0, "0.000 B"],
                [999, "999.0 B"],
                [1000, "1.000 kB"],
                [1001, "1.001 kB"],
                [9999, "9.999 kB"],
                [20000, "20.00 kB"],
                [200000, "200.0 kB"],
                [1000000, "1.000 MB"],
                [1001000, "1.001 MB"],
                [9999000, "9.999 MB"],
                [1000000000, "1.000 GB"],
                [1001000000, "1.001 GB"],
            ];

            data.forEach(function (set) {
                assert.equal(drawing.formatBytes(set[0]), set[1]);
            });
        });
    });

    describe("getStrokeWidth", function () {
        var data = {
            "min_transmission": 40,
            "max_transmission": 100
        };
        it("total link data halfway between min and max transmission", function () {
            var link = {
                "amount_up": 30,
                "amount_down": 40
            };
            assert.equal((config.link.strokeWidthMax + config.link.strokeWidthMin) / 2,
                drawing.getStrokeWidth(link, data));
        });
        it("total link data equal to max transmission", function () {
            var link = {
                "amount_up": 60,
                "amount_down": 40
            };
            assert.equal(config.link.strokeWidthMax, drawing.getStrokeWidth(link, data));
        });
        it("total link data equal to min transmission", function () {
            var link = {
                "amount_up": 15,
                "amount_down": 25
            };
            assert.equal(config.link.strokeWidthMin, drawing.getStrokeWidth(link, data));
        });
    });

    describe("getStrokeWidth", function () {
        it("the middle of the interval is returned as the stroke width if the difference is 0", function () {
            var data = {
                "min_transmission": 100,
                "max_transmission": 100
            };
            assert.equal((config.link.strokeWidthMax + config.link.strokeWidthMin) / 2,
                drawing.getStrokeWidth(null, data));
        });
    });

    describe("getNodeRadius", function () {
        it("the minimal node size is returned when the node has the least amount of traffic", function () {
            var data = {
                "traffic_slope": 1,
                "traffic_min": 1
            };
            var node = {
                "total_up": 0,
                "total_down": 1
            };
            assert.equal(config.node.circle.minRadius, drawing.getNodeRadius(node, data))
        });
    });
});
