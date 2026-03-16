from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel

from modules.ui import TM
from modules.ui.Elements import CardFrame
from modules.Utils import format_number, color_avatar

class ListCard(CardFrame):
    def __init__(self, main_window, data):
        self.mw = main_window
        self.data = data
        self.username = self.data.get('username')

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()

        self.image_label = QLabel()
        self.image_label.setFixedSize(70, 70)
        card_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        if self.data.get('account__avatar_file_name'):
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.data.get('account__avatar_file_name')}?webp=true&anim=0",
                70, 70, 4, label=self.image_label, cache_dir="cache/users",
                error_cb=lambda _: color_avatar(self.image_label, 70, 70, self.username, 4))
        else:
            color_avatar(self.image_label, 70, 70, self.username, 4)

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(text_layout)

        title_label = QLabel(self.username)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        if self.data.get('character_info', {}):
            stat_layout = QHBoxLayout()
            stat_layout.setContentsMargins(0, 0, 0, 0)
            stat_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            if self.data.get('character_info', {}).get('num_interactions'):
                self.interactions_label = QLabel(format_number(self.data.get('character_info', {}).get('num_interactions')) + self.tr(" Chats"))
                font = self.interactions_label.font()
                font.setPointSize(10)
                self.interactions_label.setFont(font)
                stat_layout.addWidget(self.interactions_label)

            if self.data.get('character_info', {}).get('num_interactions') and self.data.get('character_info', {}).get('num_characters'):
                self.span_label = QLabel("•")
                font = self.span_label.font()
                font.setPointSize(10)
                self.span_label.setFont(font)
                stat_layout.addWidget(self.span_label)

            if self.data.get('character_info', {}).get('num_characters'):
                self.characters_label = QLabel(format_number(self.data.get('character_info', {}).get('num_characters')) + self.tr(" Characters"))
                font = self.characters_label.font()
                font.setPointSize(10)
                self.characters_label.setFont(font)
                stat_layout.addWidget(self.characters_label)
            text_layout.addLayout(stat_layout)

        super().__init__()
        self.setLayout(card_layout)

    def update_theme(self):
        super().update_theme()
        if self.data.get('character_info', {}):
            if self.data.get('character_info', {}).get('num_interactions'):
                self.interactions_label.setStyleSheet(f"color: {TM.c('disabled_text')};")

            if self.data.get('character_info', {}).get('num_interactions') and self.data.get('character_info', {}).get('num_characters'):
                self.span_label.setStyleSheet(f"color: {TM.c('disabled_text')};")

            if self.data.get('character_info', {}).get('num_characters'):
                self.characters_label.setStyleSheet(f"color: {TM.c('disabled_text')};")

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openUserPage(self.username)