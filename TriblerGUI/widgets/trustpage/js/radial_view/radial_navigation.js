/**
 * The Radial Navigation is responsible for loading new views and keeping track of the steps taken.
 * It can also perform a step back.
 *
 * @param {Function} requestMethod - method that performs the API request and binds the callback
 * @constructor
 */
function RadialNavigation(requestMethod) {

    applyEventfulMixin(this);

    var self = this;

    self.pending = false;
    self.current_pk = null;
    self.history = [];
    self.squash_history = true;
    self.neighbor_level = 1;

    /**
     * Focus on a new node if not already loading.
     * @param {String} public_key
     */
    self.step = function (public_key) {

        // Ignore step when pending or same key
        if (self.pending || public_key === self.current_pk) return;

        self.fire("before-step", [public_key], self);

        self.pending = true;

        // Request the data
        requestMethod(public_key, self.neighbor_level, self.onResponse);
    };

    /**
     * Return focus to the previous focus node, resetting the history.
     */
    self.stepBack = function () {

        if (self.history.length < 2) return;

        var target = self.getPreviousPublicKey();

        // Two steps back
        self.history = self.history.slice(0, -2);

        // One step forward
        self.step(target);
    };

    /**
     * This method is called when the API returns a new response.
     * @param {GraphResponseData} response
     */
    self.onResponse = function (response) {
        self.pending = false;

        // Check whether the new focus node is already in the history
        var index = self.history.indexOf(response.focus_node);

        // Squash the history or add the new step
        if (self.squash_history && index >= 0) {
            self.history = self.history.slice(0, index + 1);
        } else {
            self.history.push(response.focus_node);
        }

        self.current_pk = response.focus_node;

        self.fire("response", [response], self);
    };

    /**
     * Returns the public key of the currently focused node.
     * @returns {null|String}
     */
    self.getCurrentPublicKey = function () {
        return self.current_pk;
    };

    /**
     * Returns the public key of the previously focused node.
     * @returns {null|String}
     */
    self.getPreviousPublicKey = function () {
        return self.history.length > 1 ? self.history[self.history.length - 2] : null;
    };

    /**
     * Set the neighbor level to be used in subsequent requests.
     * @param {number} level
     */
    self.setNeighborLevel = function (level) {
        self.neighbor_level = level;
    };

}
