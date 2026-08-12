from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from modules.ui import TM
from modules.ui.Elements import CardFrame


class ListCard(CardFrame):
    def __init__(self, main_window, data):
        self.mw = main_window
        self.data = data
        self.title = self.data.get("name")
        self.author = self.data.get("author")

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(text_layout)

        title_label = QLabel(self.title)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        self.author_label = QLabel(self.tr("Author: @") + self.author)
        self.author_label.setWordWrap(True)
        font = self.author_label.font()
        font.setPointSize(8)
        # self.author_label.mousePressEvent = lambda _: self.mw.openUserPage(self.author)
        self.author_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.author_label.setFont(font)
        text_layout.addWidget(self.author_label)

        super().__init__()
        self.setLayout(card_layout)

    def update_theme(self):
        super().update_theme()
        self.author_label.setStyleSheet(f"color: {TM.c('disabled_text')};")

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.hideOverlay()
        self.mw.openThemeOverlay(self.data.get("theme_id"))
