from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from modules.ui import TM
from modules.ui.Elements import CardFrame, PushButton
from modules.Utils import color_avatar, format_number, format_text


class ListCard(CardFrame):
    def __init__(self, main_window, data, avatar_label_w=70, avatar_label_h=70):
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.data = data
        self.avatar_url = self.data.get("avatar_file_name", "")
        self.name = self.data.get("name", "")
        self.character_id = self.data.get("external_id", "")
        self.avatar_label_w = avatar_label_w
        self.avatar_label_h = avatar_label_h

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
        card_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        if self.avatar_url:
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0",
                self.avatar_label_w,
                self.avatar_label_h,
                4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(
                    self.avatar_label,
                    self.avatar_label_w,
                    self.avatar_label_h,
                    self.name,
                ),
            )
        else:
            color_avatar(
                self.avatar_label,
                self.avatar_label_w,
                self.avatar_label_h,
                self.name,
                4,
            )

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        text_layout.setSpacing(1)
        card_layout.addLayout(text_layout, 1)

        title_label = QLabel(self.name)
        title_label.setWordWrap(True)
        title_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        if self.data.get("title"):
            clean_title = str(self.data.get("title", "")).replace("\n", " ").strip()
            self.description_label = QLabel(
                format_text(clean_title, self.name)
            )
            self.description_label.setWordWrap(False)
            self.description_label.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
            )
            font = self.description_label.font()
            font.setPointSize(9)
            self.description_label.setFont(font)
            text_layout.addWidget(self.description_label)

        self.add_info = QLabel()
        font = self.add_info.font()
        font.setPointSize(9)
        self.add_info.setFont(font)
        if self.data.get("participant__num_interactions"):
            self.add_info.setText(
                self.add_info.text()
                + str(format_number(self.data.get("participant__num_interactions")))
                + self.tr(" chats")
            )

        if self.add_info.text():
            text_layout.addWidget(self.add_info)

        self.chat_button = PushButton(self.tr("Chat"))
        self.chat_button.clicked.connect(
            lambda: self.mw.openChat(self.character_id, self.name)
        )
        card_layout.addWidget(self.chat_button, alignment=Qt.AlignmentFlag.AlignRight)

        super().__init__()
        self.setLayout(card_layout)
        if self.data.get("title"):
            self.setToolTip(format_text(self.data.get("title")))

    def update_theme(self):
        super().update_theme()
        self.add_info.setStyleSheet(f"color: {TM.c('disabled_text')};")
        if self.data.get("title"):
            self.description_label.setStyleSheet(f"color: {TM.c('disabled_text')};")

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openCharacter(character_id=self.data["external_id"])
