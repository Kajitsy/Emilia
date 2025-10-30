import base64, uuid
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QSpacerItem,
                             QSizePolicy, QWidget, QFileDialog, QApplication)

from modules.style.Elements import (CustomTextEdit, PushButton, LineEdit, CheckBox, ComboBox, VerticalScrollPage,
    CardFrame)
from modules.style.Icons import Svg
from modules.style.Utils import format_text, format_number, color_avatar
from modules.QThreads import ImageLoaderThread

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

        thread = ImageLoaderThread(self.data.get("background_image_url"), 150, 200, "cache/scenes")
        thread.radius = 4
        thread.image_loaded.connect(self.image_label.setPixmap)
        thread.start()
        self.mw.threads.append(thread)

        #text_layout = QVBoxLayout()
        #text_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        #card_layout.addLayout(text_layout, 1)

        title_label = QLabel(self.title)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(11)
        title_label.setFont(font)
        card_layout.addWidget(title_label)

        if self.author:
            #spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            #card_layout.addItem(spacer)

            author_label = QLabel(self.tr("Author: @") + self.author)
            font = author_label.font()
            font.setPointSize(8)
            author_label.setStyleSheet("color: #a2a2ac;")
            author_label.mousePressEvent = lambda _: self.mw.openUserPage(self.author)
            author_label.setCursor(Qt.CursorShape.PointingHandCursor)
            author_label.setFont(font)
            card_layout.addWidget(author_label)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
