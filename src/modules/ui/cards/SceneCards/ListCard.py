from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel

from modules.ui import TM
from modules.ui.Elements import PushButton, CardFrame
from modules.Utils import format_text

class ListCard(CardFrame):
    def __init__(self, main_window, data):
        super().__init__()
        self.mw = main_window
        self.data = data
        self.title = self.data.get('title')

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()

        self.image_label = QLabel()
        self.image_label.setFixedSize(110, 140)
        card_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.mw.image_loader.load(self.data.get("background_image_url"), 110, 140, 4,
                                  label=self.image_label, cache_dir="cache/scenes")

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

        if self.data.get('description'):
            description_label = QLabel(format_text(self.data.get('description')))
            description_label.setWordWrap(True)
            description_label.setStyleSheet(f"color: #{TM.c('disabled_text')};")
            font = description_label.font()
            font.setPointSize(9)
            description_label.setFont(font)
            fm = QFontMetrics(font)
            description_label.setMaximumHeight(fm.lineSpacing() * 3)
            text_layout.addWidget(description_label)
            self.setToolTip(format_text(self.data.get('title')))

        if self.data.get('creator_username') == self.mw.username:
            edit_button = PushButton(self.tr("Edit"))
            edit_button.clicked.connect(lambda: self.mw.openCreateScenePage(self.data.get('scene_id')))
            card_layout.addWidget(edit_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(card_layout)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openScene(self.data)