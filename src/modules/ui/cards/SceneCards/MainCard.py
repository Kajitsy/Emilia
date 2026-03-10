from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QLabel

from modules.ui import TM
from modules.ui.Elements import CardFrame

class MainCard(CardFrame):
    def __init__(self, main_window, data):
        super().__init__()
        self.mw = main_window
        self.data = data
        self.title = self.data.get('title')
        self.author = self.data.get('creator_username')

        self.initUI()

    def initUI(self):
        card_layout = QVBoxLayout()
        self.setLayout(card_layout)

        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 200)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addWidget(self.image_label)

        self.mw.image_loader.load(self.data.get("background_image_url"), 150, 200, 4,
                                  label=self.image_label, cache_dir="cache/scenes")

        title_label = QLabel(self.title)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(11)
        title_label.setFont(font)
        card_layout.addWidget(title_label)

        if self.author:
            author_label = QLabel(self.tr("Author: @") + self.author)
            font = author_label.font()
            font.setPointSize(8)
            author_label.setStyleSheet(f"color: {TM.c('disabled_text')};")
            author_label.mousePressEvent = lambda _: self.mw.openUserPage(self.author)
            author_label.setCursor(Qt.CursorShape.PointingHandCursor)
            author_label.setFont(font)
            card_layout.addWidget(author_label)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openScene(self.data)