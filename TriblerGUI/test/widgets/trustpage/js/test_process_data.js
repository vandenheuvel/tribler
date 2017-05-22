/**
 * This file tests the process_data.js file with unit tests
 */
assert = require('assert');
process_data = require('../../../../widgets/trustpage/js/process_data.js');

describe('process_data.js', function() {
      describe('getCombinedLinks', function() {
              it('test whether empty list is returned when no links for nodeName exists', function() {
                  assert.deepEqual([], process_data.getCombinedLinks([], "test"));
              });

              it('test whether link is correctly created without inverse link and without links leaving target node',
                  function() {
                  var groupedLinks = {
                      "test": [{
                          "from": "test",
                          "to": "nottest",
                          "amount": 100
                      }]
                  };
                  var expectedLinks = [{
                      "source": "test",
                      "target": "nottest",
                      "amount_up": 100,
                      "amount_down": 0,
                      "ratio": 1,
                      "log_ratio": 1
                  }];
                  assert.deepEqual(expectedLinks, process_data.getCombinedLinks(groupedLinks, "test"))
              });

              it('test whether link is correctly created without inverse link', function() {
                 var groupedLinks = {
                      "test": [{
                          "from": "test",
                          "to": "nottest",
                          "amount": 100
                      }],
                     "nottest": []
                  };
                  var expectedLinks = [{
                      "source": "test",
                      "target": "nottest",
                      "amount_up": 100,
                      "amount_down": 0,
                      "ratio": 1,
                      "log_ratio": 1
                  }];
                  assert.deepEqual(expectedLinks, process_data.getCombinedLinks(groupedLinks, "test"))
              });

              it('test whether link is correctly created', function() {
                                var groupedLinks = {
                      "test": [{
                          "from": "test",
                          "to": "nottest",
                          "amount": 100
                      }],
                     "nottest": [{
                          "from": "nottest",
                          "to": "test",
                          "amount": 100
                     }]
                  };
                  var expectedLinks = [{
                      "source": "test",
                      "target": "nottest",
                      "amount_up": 100,
                      "amount_down": 100,
                      "ratio": 0.5,
                      "log_ratio": 0.5
                  }];
                  assert.deepEqual(expectedLinks, process_data.getCombinedLinks(groupedLinks, "test"))

              })
            });
});
