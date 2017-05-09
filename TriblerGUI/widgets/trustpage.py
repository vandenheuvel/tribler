from PyQt5.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvas

from TriblerGUI.widgets.graphprovider import GraphProvider


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
        vlayout = self.window().network_widget.layout()
        graph_data = GraphProvider()
        self.network_graph = FigureCanvas(graph_data.provide_figure())
        vlayout.addWidget(self.network_graph)
