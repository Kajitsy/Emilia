from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QMenu

from modules.ui.Elements import VerticalScrollPage, SearchLineEdit, PushButton
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

        search_input_layout = QHBoxLayout()
        search_layout.addLayout(search_input_layout)

        self.search_input = SearchLineEdit(self.mw)
        self.search_input.returnPressed.connect(self.showSearchResults)
        self.search_input.setPlaceholderText(self.tr('Search'))
        search_input_layout.addWidget(self.search_input)

        self.upload_button = PushButton()
        self.upload_button.setToolTip(self.tr("Upload Theme"))
        self.upload_button.clicked.connect(self.uploadTheme)
        search_input_layout.addWidget(self.upload_button)

        self.search_scroll_page = VerticalScrollPage()
        self.search_scroll_viewport = self.search_scroll_page.viewport
        self.search_scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
        self.search_scroll_layout = self.search_scroll_page.layout
        search_layout.addWidget(self.search_scroll_page)

        self.setLayout(layout)

    def updateTheme(self):
        self.search_input.setIcon(QIcon(self.svg_icons.search(TM.c('icon'))))
        self.upload_button.setIcon(self.svg_icons.share(TM.c('icon')))

    def uploadTheme(self):
        menu = QMenu(self)
        themes = TM.get_themes_name()
        for theme in themes:
            if theme in ["Dark", "Light"]:
                continue
            action = menu.addAction(theme)
            action.triggered.connect(lambda _, t=theme: self._startUpload(t))

        if not menu.actions():
            no_themes_action = menu.addAction(self.tr("No custom themes found"))
            no_themes_action.setEnabled(False)

        menu.exec(self.upload_button.mapToGlobal(self.upload_button.rect().bottomLeft()))

    def _startUpload(self, theme_name):
        self.mw.chat_thread.upload_theme_signal.connect(self._on_theme_uploaded)
        self.mw.chat_thread.upload_theme(theme_name)

    def _on_theme_uploaded(self, response):
        try:
            self.mw.chat_thread.upload_theme_signal.disconnect()
        except:
            pass

        if response.get('error'):
            error_msg = response.get('text', str(response.get('error')))
            self.mw.showNotification(self.tr("Error uploading theme: ") + error_msg)
        else:
            self.mw.showNotification(self.tr("Theme uploaded successfully!"))
            self.showSearchResults()

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
