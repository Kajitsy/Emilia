from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel

from modules.ui.Elements import PushButton, CardFrame
from modules.Utils import format_text, format_number, color_avatar

class ListCard(CardFrame):
    def __init__(self, main_window, data, avatar_label_w=70, avatar_label_h=70):
        super().__init__()
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.data = data
        self.avatar_url = self.data.get('avatar_file_name', '')
        self.name = self.data.get('name', '')
        self.character_id = self.data.get('external_id', '')
        self.avatar_label_w = avatar_label_w
        self.avatar_label_h = avatar_label_h

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()
        self.setLayout(card_layout)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
        card_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        if self.avatar_url:
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0", self.avatar_label_w, self.avatar_label_h, 4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name))
        else:
            color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name, 4)

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(text_layout, 1)

        title_label = QLabel(self.name)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        if self.data.get('title'):
            description_label = QLabel(format_text(self.data.get('title'), self.name))
            description_label.setWordWrap(True)
            description_label.setStyleSheet("color: #a2a2ac;")
            font = description_label.font()
            font.setPointSize(9)
            description_label.setFont(font)
            fm = QFontMetrics(font)
            description_label.setMaximumHeight(fm.lineSpacing())
            text_layout.addWidget(description_label)
            self.setToolTip(format_text(self.data.get('title')))

        add_info = QLabel()
        add_info.setStyleSheet("color: #a2a2ac;")
        font = add_info.font()
        font.setPointSize(10)
        add_info.setFont(font)
        if self.data.get('participant__num_interactions'):
            add_info.setText(add_info.text() + str(format_number(self.data.get('participant__num_interactions'))) + self.tr(" chats"))

        if add_info.text():
            text_layout.addWidget(add_info)

        self.chat_button = PushButton(self.tr("Chat"))
        self.chat_button.clicked.connect(lambda: self.mw.openChat(self.character_id, self.name))
        card_layout.addWidget(self.chat_button, alignment=Qt.AlignmentFlag.AlignRight)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openCharacter(character_id=self.data["external_id"])