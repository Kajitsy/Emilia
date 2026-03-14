from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from modules.ui.Elements import VerticalScrollPage, SearchLineEdit
from modules.ui.Icons import Svg
from modules.ui import TM
from . import ListCard

class SearchCard(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.setMinimumHeight(600)
        self.setFixedWidth(600)
        self.svg_icons = Svg()

        self.initUI()
        TM.theme_changed.connect(self.updateTheme)
        self.updateTheme()

        self.mw.chat_thread.get_themes_signal.connect(self._showSearchResults)
        self.mw.chat_thread.get_themes()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        search_layout = QVBoxLayout()
        layout.addLayout(search_layout)

        self.search_input = SearchLineEdit(self.mw)
        self.search_input.returnPressed.connect(self.showSearchResults)
        self.search_input.setPlaceholderText(self.tr('Search'))
        search_layout.addWidget(self.search_input)

        self.search_scroll_page = VerticalScrollPage()
        self.search_scroll_viewport = self.search_scroll_page.viewport
        self.search_scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
        self.search_scroll_layout = self.search_scroll_page.layout
        search_layout.addWidget(self.search_scroll_page)

        self.setLayout(layout)

    def updateTheme(self):
        self.search_input.setIcon(QIcon(self.svg_icons.search(TM.c('icon'))))

    def _showSearchResults(self, response):
        self.mw.chat_thread.get_themes_signal.disconnect()
        if response:
            for theme in response:
                card = ListCard(self.mw, theme)
                card.setFixedHeight(60)
                self.search_scroll_layout.addWidget(card)
        else:
            no_results_label = QLabel(self.tr("Themes not found"))
            self.search_scroll_layout.addWidget(no_results_label, 0, Qt.AlignmentFlag.AlignVCenter)

    def showSearchResults(self):
        search_query = self.search_input.text().strip()
        if not search_query:
            return

        if self.search_scroll_layout.layout() is not None:
            for i in reversed(range(self.search_scroll_layout.layout().count())):
                item = self.search_scroll_layout.layout().itemAt(i)
                if item is not None and item.widget() is not None:
                    item.widget().setParent(None)

        self.mw.chat_thread.get_themes_signal.connect(self._showSearchResults)
        self.mw.chat_thread.get_themes(search_query)
