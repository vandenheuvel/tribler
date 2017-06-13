"""
Provides a class which initializes the Network Trust Display Qt elements.
"""
import os
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget
from TriblerGUI import utilities

TRUST_NETWORK_HTML_PATH = os.path.join(utilities.get_base_path(), "widgets/trustpage/index.html")


class TrustPageNetwork(QWidget):
    """
    The logic of the Network Trust Display.
    """

    def __init__(self):
        """
        Create a new Network Trust Display.
        """
        QWidget.__init__(self)
        self.network_graph = None

    def initialize_trust_page(self):
        """
        Load the pyplot graph into the QWidget.
        """
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
            vertical_layout = self.window().network_widget.layout()

            view = QWebEngineView()

            view.setUrl(QUrl.fromLocalFile(TRUST_NETWORK_HTML_PATH))
            view.page().setBackgroundColor(QColor.fromRgb(0, 0, 0, 0))
            view.show()

            vertical_layout.addWidget(view)
        except ImportError:
            # In the case QWebEngineView is not available, render the graph trust page.
            pass
