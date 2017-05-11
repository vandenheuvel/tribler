"""
Provides a class which encapsulates the graph construction logic.
"""
from __future__ import division
import math
import networkx as nx



class GraphProvider():
    """
    Provides the matplotlib figure of the network.
    """

    def __init__(self):
        self.peers = None

    def provide_figure(self, data):
        """
        Provide the matplotlib figure computed from the multichain data.
        TODO: add actual multichain data implementation, dummy data is inserted for now.
        
        :return: the matplotlib figure
        """
        graph = nx.Graph()

        up_down = [(item["amount_up"], item["amount_down"]) for item in data["edges"]]
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
        self.peers = [polar_to_cartesian(center_x, center_y, radius, x * relative_angle) for x in range(node_count)]

        def draw_node(pos, color):
            """ Draw a networkx node with a specified color """
            nx.draw_networkx_nodes(graph, [pos], nodelist=[0], node_color=color)

        def draw_edge(node_a, node_b, up, down):
            """ Draw an edge with labels and separator between nodes a and b, given their exchange up and down """
            ratio = up / (up + down)
            nx.draw_networkx_edges(graph, [node_a, node_b], [(0, 1)])
            nx.draw_networkx_edge_labels(graph, [node_a, node_b], {(0, 1): `up` + "M"}, label_pos=(ratio) / 2, rotate=False)
            nx.draw_networkx_edge_labels(graph, [node_a, node_b], {(1, 0): `down` + "M"}, label_pos=(1 - ratio) / 2,
                                         rotate=False)
            nx.draw_networkx_edge_labels(graph, [node_a, node_b], {(0, 1): "|"}, label_pos=ratio)

        # Draw the focus nodes
        draw_node(focus_node, 'g')

        # Draw the first level neighbors and edges to them
        for x in range(node_count):
            draw_node(self.peers[x], 'g')
            draw_edge(focus_node, self.peers[x], up_down[x][0], up_down[x][1])

        return

    def handle_mouseclick(self, event):
        (cursor_x, cursor_y) = (event.xdata, event.ydata)

        for node in self.peers:
            distance = pow(cursor_x - node[0], 2) + pow(cursor_y - node[1], 2)
            if distance < 0.5:
                print "you clicked node: ", node
