"""
This module is used to calculate the score for a node.
"""
BOUNDARY_VALUE = pow(10, 10)


def calculate_score(node):
    """
    Calculate the score given a node dictionary.

    The given node is in the following format:
        { "public_key": public_key, "total_up": total_up, "total_down": total_down }

    The score is calculated on a scale from 0 till 1, where 0 is the worst and 1 is the best.

    :param node: the node for which the score has to be calculated
    :return: a number between 0 and 1 which represents the score of the node.
    """
    balance = node["total_up"] - node["total_down"]
    if balance < -BOUNDARY_VALUE:
        return 0
    elif balance > BOUNDARY_VALUE:
        return 1
    else:
        return (float(balance) + BOUNDARY_VALUE) / (BOUNDARY_VALUE + BOUNDARY_VALUE)
