import sounddevice
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QPushButton

from modules.ui.Elements import CardFrame
from modules.ui.Icons import Svg
from modules.ui.cards.VoiceCards import _preview_controller, MainCard


class HorizontalMiniCard(CardFrame):
    def __init__(self, main_window, data):
        super().__init__()
        self.setFixedHeight(60)
        self.mw = main_window
        self.data = data
        self.svg_icons = Svg()

        self.initUI()

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        if a0.button() == Qt.MouseButton.RightButton:
            self.mw.hideOverlay()
            self.mw.showOverlay(MainCard(self.mw, self.data, search=False))

    def initUI(self):
        card_layout = QHBoxLayout()
        play_button = QPushButton()
        play_button.setIcon(self.svg_icons.play())
        play_button.setFixedWidth(40)
        play_button.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 32px;")
        play_button.clicked.connect(lambda _=False: _preview_controller(self.mw).toggle(self.data.get('previewAudioURI'), play_button))
        card_layout.addWidget(play_button)

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(text_layout, 1)

        title_label = QLabel(self.data.get("name"))
        font = title_label.font()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        description_label = QLabel(self.data.get("description"))
        font = description_label.font()
        font.setPointSize(10)
        description_label.setFont(font)
        text_layout.addWidget(description_label)

        self.setLayout(card_layout)

    def closeEvent(self, a0):
        super().closeEvent(a0)
        sounddevice.stop()
