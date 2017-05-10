"""
Provides a class which encapsulates the graph construction logic.
"""
from __future__ import division
import math
import networkx as nx
from matplotlib import pyplot


class GraphProvider():
    """
    Provides the matplotlib figure of the network.
    """

    def provide_figure(self):
        """
        Provide the matplotlib figure computed from the multichain data.
        TODO: add actual multichain data implementation, dummy data is inserted for now.
        
        :return: the matplotlib figure
        """
        G = nx.Graph()

        """ Dummy data of a focus node and its peers """
        up_down = [(50, 50), (91, 100), (52, 10), (20, 44), (1, 76), (17, 36)]
        node_count = len(up_down)

        # The focus node
        center_x = 1
        center_y = 1
        focus_node = (center_x, center_y)

        def polar_to_cartesian(base_x, base_y, radius, alpha):
            return (base_x + radius * math.cos(math.pi / 2 - alpha),
                    base_y - radius * math.sin(math.pi / 2 - alpha))

        # Radius of first level neighbors
        radius = 1

        # Angle between neighbors
        relative_angle = (2 * math.pi) / node_count

        # Compute position of peers
        peers = [polar_to_cartesian(center_x, center_y, radius, x * relative_angle) for x in range(node_count)]

        def draw_node(pos, color):
            """ Draw a networkx node with a specified color """
            nx.draw_networkx_nodes(G, [pos], nodelist=[0], node_color=color)

        def draw_edge(node_a, node_b, up, down):
            """ Draw an edge with labels and separator between nodes a and b, given their exchange up and down """
            ratio = up / (up + down)
            nx.draw_networkx_edges(G, [node_a, node_b], [(0, 1)])
            nx.draw_networkx_edge_labels(G, [node_a, node_b], {(0, 1): `up` + "M"}, label_pos=(ratio) / 2, rotate=False)
            nx.draw_networkx_edge_labels(G, [node_a, node_b], {(1, 0): `down` + "M"}, label_pos=(1 - ratio) / 2,
                                         rotate=False)
            nx.draw_networkx_edge_labels(G, [node_a, node_b], {(0, 1): "|"}, label_pos=ratio)

        # Start drawing the figure
        fig = pyplot.figure()
        ax = fig.add_subplot(111)

        # Draw the focus nodes
        draw_node(focus_node, 'g')

        # Draw the first level neighbors and edges to them
        for x in range(node_count):
            draw_node(peers[x], 'g')
            draw_edge(focus_node, peers[x], up_down[x][0], up_down[x][1])
            
        return fig
