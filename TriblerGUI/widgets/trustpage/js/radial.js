
/** Calculate position on a circle */
function radialPosition(center_x, center_y, alpha, radius) {
    return {
        x: center_x + radius * Math.cos(alpha),
        y: center_y - radius * Math.sin(alpha) // Minus because screen Y points down
    }
}

/** Calculate weighted portion of circle */
function radialWeight(ratio) {
    return (Math.PI * 2) * ratio;
}

/**
 *
 * @param weights array [0.1, 0.1, 0.2, 0.6] (fractions)
 */
function radialPositions(center_x, center_y, alpha_from, alpha_to, radius, nodeCount) {
    var result = new Array(nodeCount);
    var d_alpha = (alpha_to - alpha_from) / nodeCount;
    for(var i = 0; i < nodeCount; i++){
        var angle = alpha_from + i * d_alpha;
        result[i] = radialPosition(center_x, center_y,angle, radius);
    }
    return result;
}




function radialForce(alpha) {
  for (var i = 0, n = nodes.length, node, k = alpha * 0.1; i < n; ++i) {
    node = nodes[i];
    node.vx -= node.x * k;
    node.vy -= node.y * k;
  }
}

function setAlpha(nodes, alpha_0, alpha_1){
    var d_alpha = (alpha_1 - alpha_0)/nodes.length;
    for(var i = 0; i < nodes.length; i++){

        nodes[i].alpha = alpha_0 + d_alpha * i;
        console.log('set a of',i, nodes[i].alpha, alpha_0, alpha_1, nodes[i].public_key)
    }
}
