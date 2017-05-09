import networkx as nx
from matplotlib import pyplot


class GraphProvider():
    """
    Provides the pyplot figure of the network.
    """

    def provide_figure(self):
        """
        Provide the pyplot figure computed from the multichain data.
        TODO: add actual multichain data implementation.
        :return: the pyplot figure.
        """
        G = nx.Graph()
        pos = [(2, 2), (1, 1), (2, 3), (3, 1)]  # positions for all nodes

        fig = pyplot.figure()
        ax = fig.add_subplot(111)
        nx.draw_networkx_nodes(G, pos,
                               nodelist=[0],
                               node_color='r',
                               node_size=800)
        nx.draw_networkx_nodes(G, pos,
                               nodelist=[1, 2, 3],
                               node_color='b',
                               node_size=500)

        nx.draw_networkx_edges(G, pos, [(0, 1), (0, 2), (0, 3)])
        return fig
