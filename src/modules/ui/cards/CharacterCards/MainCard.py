from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy

from modules.ui.Elements import PushButton, CardFrame
from modules.Utils import format_text, format_number, color_avatar

class MainCard(CardFrame):
    def __init__(self, main_window, name="", avatar_url="", description="", author="", character_id="", chats=0,
                 voted=0, avatar_label_w=90, avatar_label_h=114):
        super().__init__()
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
        self.setLayout(card_layout)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.avatar_label)

        if self.avatar_url:
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0", self.avatar_label_w, self.avatar_label_h, 4,
                label=self.avatar_label, error_cb=lambda _: color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name))
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

        if self.author:
            author_label = QLabel(self.tr("Author: @") + self.author)
            font = author_label.font()
            font.setPointSize(8)
            author_label.setStyleSheet("color: #a2a2ac;")
            author_label.setFont(font)
            text_layout.addWidget(author_label)

        if self.description:
            description_label = QLabel(format_text(self.description, self.name))
            description_label.setWordWrap(True)
            font = description_label.font()
            font.setPointSize(10)
            description_label.setFont(font)
            fm = QFontMetrics(font)
            description_label.setMaximumHeight(fm.lineSpacing() * 4)
            text_layout.addWidget(description_label)
            self.setToolTip(format_text(self.description))

        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        text_layout.addItem(spacer)

        add_info = QLabel()
        add_info.setStyleSheet("color: #a2a2ac;")
        font = add_info.font()
        font.setPointSize(10)
        add_info.setFont(font)
        if self.chats:
            add_info.setText(add_info.text() + str(format_number(self.chats)) + self.tr(" chats"))
        if self.voted:
            add_info.setText(add_info.text() + " • " + str(format_number(self.voted)) + self.tr(" likes"))

        if add_info.text():
            text_layout.addWidget(add_info)

        self.edit_button = PushButton(self.tr("Edit"))
        self.edit_button.clicked.connect(lambda: self.mw.openCreateCharacterPage(self.character_id))

        if self.author == self.mw.username:
            card_layout.addWidget(self.edit_button, alignment=Qt.AlignmentFlag.AlignRight)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openChat(self.character_id, self.name)