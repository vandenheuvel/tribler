"""
Provides a class which initializes the Trust Display Qt elements.
"""
from PyQt5.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvas

from TriblerGUI.widgets.network_model import NetworkModel
from TriblerGUI.widgets.graph_provider import GraphProvider


class TrustPage(QWidget):
    """
    The logic of the Trust Display.
    """

    def __init__(self):
        """
        Create a new Trust Display.
        """
        QWidget.__init__(self)
        self.network_graph = None

    def initialize_trust_page(self):
        """
        Load the pyplot graph into the QWidget.
        """
        vertical_layout = self.window().network_widget.layout()

        network_model = NetworkModel(focus_node=u"30")
        graph_data = GraphProvider()
        self.network_graph = FigureCanvas(graph_data.provide_figure(network_model))
        self.network_graph.mpl_connect('button_press_event', graph_data.handle_mouseclick)



        vertical_layout.addWidget(self.network_graph)
