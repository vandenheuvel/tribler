/**
 * Settings file for user settings of the visualization
 */

var settings = {
    hoverLabelVisible : true
};

/**
 * Update the settings when changed by the user
 * @param checkbox the checkbox which is altered
 */
function settingsChanged(checkbox) {
    settings[checkbox.name] = checkbox.checked;
}
