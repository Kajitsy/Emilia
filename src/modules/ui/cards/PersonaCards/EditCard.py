import base64

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from modules.ui.Elements import CheckBox, CustomTextEdit, LineEdit, PushButton
from modules.Utils import color_avatar


class EditCard(QFrame):
    def __init__(self, main_window, data=None, list_card=None):
        super().__init__()
        self.setFixedSize(500, 200)

        self.mw = main_window
        self.data = data
        self.list_card = list_card
        self.new = False
        self.temp_link = ""

        if data is None:
            self.data = {}
            self.new = True
        self.is_def = self.data.get("external_id") == self.mw.user_settings.get(
            "default_persona_id"
        )
        self.ex_id = self.data.get("external_id")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        fh_layout = QHBoxLayout()
        layout.addLayout(fh_layout)

        self.display_name_edit = LineEdit()
        self.display_name_edit.setPlaceholderText(self.tr("Display Name"))
        self.display_name_edit.setText(self.data.get("participant__name"))
        self.display_name_edit.textChanged.connect(
            lambda text: self.data.update({"name": text})
        )
        self.display_name_edit.setMaxLength(20)
        fh_layout.addWidget(self.display_name_edit)

        self.display_avatar = QLabel()
        self.display_avatar.mousePressEvent = lambda _: self.selectAvatar()
        self.display_avatar.setFixedSize(60, 60)
        if self.data.get("avatar_file_name"):
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.data.get("avatar_file_name")}?webp=true&anim=0",
                60,
                60,
                100,
                label=self.display_avatar,
                error_cb=lambda _: color_avatar(
                    self.display_avatar, 60, 60, self.mw.name
                ),
            )
        elif self.mw.me_has_avatar:
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0",
                60,
                60,
                100,
                label=self.display_avatar,
                error_cb=lambda _: color_avatar(
                    self.display_avatar, 60, 60, self.mw.name
                ),
            )
        else:
            color_avatar(self.display_avatar, 60, 60, self.mw.name)
        fh_layout.addWidget(self.display_avatar)

        self.background_edit = CustomTextEdit()
        self.background_edit.setPlaceholderText(self.tr("Background"))
        self.background_edit.setText(self.data.get("definition"))
        self.background_edit.textChanged.connect(self.textChanged)
        self.background_edit.setFixedHeight(32)
        self.background_edit.horizontalScrollBar().setVisible(False)
        self.background_edit.verticalScrollBar().setVisible(False)
        layout.addWidget(self.background_edit)

        make_default_layout = QHBoxLayout()
        make_default_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(make_default_layout)

        self.make_default_checkbox = CheckBox()
        if self.ex_id == self.mw.user_settings.get("default_persona_id"):
            self.make_default_checkbox.setChecked(True)
        make_default_layout.addWidget(self.make_default_checkbox, 0)
        self.make_default_label = QLabel(self.tr("Make default for new chats"))
        make_default_layout.addWidget(self.make_default_label)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.remove_button = PushButton(self.tr("Remove"))
        self.remove_button.clicked.connect(lambda _: self.removePerson())
        button_layout.addWidget(self.remove_button)

        self.save_button = PushButton(self.tr("Save"))
        self.save_button.clicked.connect(self.saveSettings)
        button_layout.addWidget(self.save_button)

    def selectAvatar(self):
        def uploaded(link):
            self.temp_link = link
            self.data["avatar_rel_path"] = link
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{link}?webp=true&anim=0",
                60,
                60,
                100,
                label=self.display_avatar,
                error_cb=lambda _: color_avatar(
                    self.display_avatar, 60, 60, self.mw.name
                ),
            )

        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if file_path.endswith(".png"):
                file_type = "png"
            elif file_path.endswith((".jpg", ".jpeg")):
                file_type = "jpeg"
            elif file_path.endswith(".bmp"):
                file_type = "bmp"

            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            self.mw.chat_thread.upload_avatar_signal.connect(uploaded)
            self.mw.chat_thread.upload_avatar(file_type, encoded)

    def textChanged(self):
        text = self.background_edit.toPlainText()
        line_count = text.count("\n")
        line_count += text.count("<br>") + 1 if text else 1
        height = line_count * self.background_edit.fontMetrics().lineSpacing() + 16
        self.data.update({"definition": self.background_edit.toPlainText()})
        self.background_edit.setFixedHeight(height)
        self.setFixedHeight(self.layout().sizeHint().height())
        if len(text) > 750:
            self.background_edit.setPlainText(text[:750])
            cursor = self.background_edit.textCursor()
            cursor.setPosition(750)
            self.background_edit.setTextCursor(cursor)

    def removePerson(self):
        self.mw.chat_thread.remove_persona(self.data)
        if self.list_card:
            self.list_card.deleteLater()
        self.mw.hideOverlay()

    def saveSettings(self):
        if self.make_default_checkbox.isChecked():
            self.mw.user_settings["default_persona_id"] = self.ex_id
            self.mw.chat_thread.update_user_settings(self.mw.user_settings)
        elif not self.make_default_checkbox.isChecked() and self.is_def:
            self.mw.user_settings["default_persona_id"] = ""
            self.mw.chat_thread.update_user_settings(self.mw.user_settings)

        if self.new:
            self.mw.chat_thread.create_persona(
                self.temp_link, "", self.data.get("definition"), self.data.get("name")
            )
        else:
            self.mw.chat_thread.update_persona_signal.connect(self._updateUserPersona)
            self.mw.chat_thread.update_persona(self.data)
        self.mw.hideOverlay()

    def _updateUserPersona(self, data):
        self.mw.chat_thread.update_persona_signal.disconnect()
        self.data = data
        if self.list_card:
            self.list_card.data = self.data
            self.list_card.display_name_label.setText(self.data.get("name"))
            self.list_card.background_label.setText(self.data.get("definition"))
            if self.data["external_id"] == self.mw.user_settings.get(
                "default_persona_id"
            ):
                self.list_card.is_default_label.setVisible(True)
            else:
                self.list_card.is_default_label.setVisible(False)
            if self.data.get("avatar_file_name"):
                self.mw.image_loader.load(
                    f"https://characterai.io/i/80/static/avatars/{self.data.get("avatar_file_name")}?webp=true&anim=0",
                    60,
                    60,
                    100,
                    label=self.display_avatar,
                    error_cb=lambda _: color_avatar(
                        self.display_avatar, 60, 60, self.mw.name
                    ),
                )
            elif self.mw.me_has_avatar:
                self.mw.image_loader.load(
                    f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0",
                    60,
                    60,
                    100,
                    label=self.display_avatar,
                    error_cb=lambda _: color_avatar(
                        self.display_avatar, 60, 60, self.mw.name
                    ),
                )
            else:
                color_avatar(self.list_card.display_avatar, 60, 60, self.mw.name)
