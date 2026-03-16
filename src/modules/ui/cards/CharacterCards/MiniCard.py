from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel

from modules.ui.Elements import CardFrame
from modules.Utils import color_avatar

class MiniCard(CardFrame):
    def __init__(self, main_window, character_name, character_id, avatar_url, chat_id=None):
        super().__init__()
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.name = character_name
        self.character_id = character_id
        self.avatar_url = avatar_url
        self.chat_id = chat_id

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()
        self.setLayout(card_layout)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(54, 54)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.avatar_label)

        if self.avatar_url:
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0", 54, 54, 4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, 54, 54, self.name))
        else:
            color_avatar(self.avatar_label, 54, 54, self.name, 4)

        title_label = QLabel(self.name)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(16)
        title_label.setFont(font)
        card_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openChat(self.character_id, self.name, self.chat_id)