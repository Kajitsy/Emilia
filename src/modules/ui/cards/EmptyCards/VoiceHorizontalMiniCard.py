from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel

from modules.ui.Elements import CardFrame

class VoiceHorizontalMiniCard(CardFrame):
    def __init__(self):
        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()

        title_label = QLabel(self.tr("And it's empty here..."))
        font = title_label.font()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        card_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        super().__init__()
        self.setEnabled(False)
        self.setFixedHeight(60)
        self.setLayout(card_layout)

    def update_theme(self):
        super().update_theme()