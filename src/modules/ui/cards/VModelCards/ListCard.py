from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from modules.ui.Elements import CardFrame
from modules.Utils import color_avatar


class ListCard(CardFrame):
    def __init__(self, main_window, icon_path, name):
        super().__init__()
        self.mw = main_window
        self.image_loader = self.mw.image_loader
        self.icon_path = icon_path
        self.name = name

        self.avatar_label_w = 70
        self.avatar_label_h = 70

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()
        self.setLayout(card_layout)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
        card_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        if self.icon_path:
            self.image_loader.load(
                self.icon_path,
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
