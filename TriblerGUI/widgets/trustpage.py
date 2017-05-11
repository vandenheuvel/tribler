"""
Provides a class which initializes the Trust Display Qt elements.
"""
from PyQt5.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvas

from TriblerGUI.widgets.network_model import NetworkModel
from TriblerGUI.widgets.graph_provider import GraphProvider
from matplotlib import pyplot

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
        self.network_model = None
        self.graph_provider = None
        self.fig = None

    def initialize_trust_page(self):
        """
        Load the pyplot graph into the QWidget.
        """

        # Instantiate the network model with the user as focus node
        self.network_model = NetworkModel(focus_node=u"30")

        # Instantiate the graph provider
        self.graph_provider = GraphProvider()

        # Make the figure and a canvas for the graph provider to draw on
        self.fig = pyplot.figure()
        ax = self.fig.add_subplot(111)
        self.network_graph = FigureCanvas(self.fig)

        # Add the canvas to the view
        self.window().network_widget.layout().addWidget(self.network_graph)

        # Load the data
        self.reload_trust_display()

    def reload_trust_display(self):
        """ Ask the Network Model to reload and call back to the render_trust_display """
        self.network_model.retrieve_display_information(self.render_trust_display)

    def render_trust_display(self, data):
        print data
        """ The callback used by the Network Model """
        self.graph_provider.provide_figure(data)

        #vertical_layout.addWidget(self.network_graph)
