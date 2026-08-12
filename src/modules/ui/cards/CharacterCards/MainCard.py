from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QVBoxLayout

from modules.ui import TM
from modules.ui.Elements import CardFrame, PushButton
from modules.Utils import color_avatar, format_number, format_text


class MainCard(CardFrame):
    def __init__(
        self,
        main_window,
        name="",
        avatar_url="",
        description="",
        author="",
        character_id="",
        chats=0,
        voted=0,
        avatar_label_w=90,
        avatar_label_h=114,
    ):
        self.mw = main_window
        self.image_loader = self.mw.image_loader
        self.name = name
        self.avatar_url = avatar_url
        self.description = description
        self.author = author
        self.character_id = character_id
        self.chats = chats
        self.voted = voted
        self.avatar_label_w = avatar_label_w
        self.avatar_label_h = avatar_label_h

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.avatar_label)

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
        card_layout.addLayout(text_layout, 1)

        title_label = QLabel(self.name)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        if self.author:
            self.author_label = QLabel(self.tr("Author: @") + self.author)
            font = self.author_label.font()
            font.setPointSize(8)
            self.author_label.setFont(font)
            text_layout.addWidget(self.author_label)

        if self.description:
            clean_desc = str(self.description).replace("\n", " ").strip()
            description_label = QLabel(format_text(clean_desc, self.name))
            description_label.setWordWrap(False)
            description_label.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
            )
            font = description_label.font()
            font.setPointSize(9)
            description_label.setFont(font)
            text_layout.addWidget(description_label)

        spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        text_layout.addItem(spacer)

        self.add_info = QLabel()
        font = self.add_info.font()
        font.setPointSize(10)
        self.add_info.setFont(font)
        if self.chats:
            self.add_info.setText(
                self.add_info.text()
                + str(format_number(self.chats))
                + self.tr(" chats")
            )
        if self.voted:
            self.add_info.setText(
                self.add_info.text()
                + " • "
                + str(format_number(self.voted))
                + self.tr(" likes")
            )

        if self.add_info.text():
            text_layout.addWidget(self.add_info)

        self.edit_button = PushButton(self.tr("Edit"))
        self.edit_button.clicked.connect(
            lambda: self.mw.openCreateCharacterPage(self.character_id)
        )

        if self.author == self.mw.username:
            card_layout.addWidget(
                self.edit_button, alignment=Qt.AlignmentFlag.AlignRight
            )

        super().__init__()
        self.setLayout(card_layout)
        if self.description:
            self.setToolTip(format_text(self.description))

    def update_theme(self):
        super().update_theme()
        self.add_info.setStyleSheet(f"color: {TM.c('disabled_text')};")
        if self.author:
            self.author_label.setStyleSheet(f"color: {TM.c('disabled_text')};")

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openChat(self.character_id, self.name)
