import sounddevice
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from modules.ui import TM
from modules.ui.cards.VoiceCards import MainCard, _preview_controller
from modules.ui.Elements import CardFrame
from modules.ui.Icons import Svg


class HorizontalMiniCard(CardFrame):
    def __init__(self, main_window, data):
        self.mw = main_window
        self.data = data
        self.svg_icons = Svg()

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()
        self.play_button = QPushButton()
        self.play_button.setFixedWidth(40)
        self.play_button.clicked.connect(
            lambda _=False: _preview_controller(self.mw).toggle(
                self.data.get("previewAudioURI"), self.play_button
            )
        )
        card_layout.addWidget(self.play_button)

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

        super().__init__()
        self.setFixedHeight(60)
        self.setLayout(card_layout)

    def update_theme(self):
        super().update_theme()
        self.play_button.setIcon(self.svg_icons.play(TM.c("icon")))
        self.play_button.setStyleSheet(
            f"background-color: transparent; color: {TM.c('mw_color')}; border: none; font-size: 32px;"
        )

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        if a0.button() == Qt.MouseButton.RightButton:
            self.mw.hideOverlay()
            self.mw.showOverlay(MainCard(self.mw, self.data, search=False))

    def closeEvent(self, a0):
        super().closeEvent(a0)
        sounddevice.stop()
