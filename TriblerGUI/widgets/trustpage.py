"""
Provides a class which initializes the Trust Display Qt elements.
"""
import os
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
<<<<<<< HEAD
from PyQt5.QtGui import QColor
=======
>>>>>>> Trust display using QtWebEngine, HTML, Javascript and D3.js
from TriblerGUI import utilities


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

        view = QWebEngineView()

        # The path to the main html file
        path = os.path.join(utilities.get_base_path(), "widgets/trustpage/index.html")

        view.setUrl(QUrl.fromLocalFile(path))
<<<<<<< HEAD
        view.page().setBackgroundColor(QColor.fromRgb(0, 0, 0, 0))
        view.show()

        vertical_layout.addWidget(view)
=======
        view.show()

        vertical_layout.addWidget(view)
>>>>>>> Trust display using QtWebEngine, HTML, Javascript and D3.js
