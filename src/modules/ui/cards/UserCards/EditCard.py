import base64

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QFrame

from modules.ui.Elements import CustomTextEdit, PushButton, LineEdit
from modules.ui.Icons import Svg
from modules.Utils import color_avatar

class EditCard(QFrame):
    def __init__(self, main_window):
        super().__init__()
        self.setFixedSize(500, 250)
        self.mw = main_window
        self.svg_icons = Svg()

        self.data = {
            "avatar_rel_path": self.mw.me.get('account',{}).get('avatar_file_name'),
            "avatar_type": self.mw.me.get('account', {}).get('avatar_type'),
            "bio": self.mw.me_full.get('bio'),
            "name": self.mw.me.get('account', {}).get('name'),
            "username": self.mw.me.get('username')
        }

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        fh_layout = QHBoxLayout()
        layout.addLayout(fh_layout)

        self.display_avatar = QLabel()
        self.display_avatar.mousePressEvent = lambda _: self.selectAvatar()
        self.display_avatar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.display_avatar.setFixedSize(70, 70)
        if self.data.get("avatar_file_name"):
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.data.get('avatar_file_name')}?webp=true&anim=0",
                70, 70, 100, label=self.display_avatar,
                error_cb=lambda _: color_avatar(self.display_avatar, 70, 70, self.mw.name))
        elif self.mw.me_has_avatar:
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0",
                70, 70, 100, label=self.display_avatar,
                error_cb=lambda _: color_avatar(self.display_avatar, 70, 70, self.mw.name))
        else:
            color_avatar(self.display_avatar, 70, 70, self.mw.name)
        fh_layout.addWidget(self.display_avatar)

        names_layout = QVBoxLayout()
        fh_layout.addLayout(names_layout)

        self.display_name_label = QLabel(self.tr("Display Name"))
        names_layout.addWidget(self.display_name_label)
        self.display_name_edit = LineEdit()
        self.display_name_edit.setPlaceholderText(self.tr("Display Name"))
        self.display_name_edit.setText(self.data['name'])
        self.display_name_edit.setMaxLength(20)
        names_layout.addWidget(self.display_name_edit)

        self.username_label = QLabel(self.tr("Username"))
        names_layout.addWidget(self.username_label)
        self.username_edit = LineEdit()
        self.username_edit.setPlaceholderText(self.tr("Username"))
        self.username_edit.setText(self.data['username'])
        self.username_edit.setMaxLength(20)
        names_layout.addWidget(self.username_edit)

        self.bio_label = QLabel(self.tr("Background"))
        layout.addWidget(self.bio_label)
        self.bio_edit = CustomTextEdit()
        self.bio_edit.setPlaceholderText(self.tr("Background"))
        self.bio_edit.setText(self.data.get('bio'))
        self.bio_edit.textChanged.connect(lambda: self.textChanged(self.bio_edit, 500))
        self.bio_edit.setFixedHeight(32)
        self.bio_edit.horizontalScrollBar().setVisible(False)
        self.bio_edit.verticalScrollBar().setVisible(False)
        layout.addWidget(self.bio_edit)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.cancel_button = PushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.mw.hideOverlay)
        button_layout.addWidget(self.cancel_button)

        self.save_button = PushButton(self.tr("Save"))
        self.save_button.clicked.connect(self.saveSettings)
        button_layout.addWidget(self.save_button)

    def textChanged(self, text_edit, max_len):
        text = text_edit.toPlainText()
        line_count = text.count('\n')
        line_count += text.count('<br>') + 1 if text else 1
        height = line_count * text_edit.fontMetrics().lineSpacing() + 32
        text_edit.setFixedHeight(height)
        if len(text) > max_len:
            text_edit.setPlainText(text[:max_len])
            cursor = text_edit.textCursor()
            cursor.setPosition(max_len)
            text_edit.setTextCursor(cursor)

    def selectAvatar(self):
        def uploaded(link):
            setattr(self, 'temp_link', link)
            self.data['avatar_rel_path'] = link
            self.data['avatar_type'] = "UPLOADED"
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{link}?webp=true&anim=0",
                60, 60, 100, label=self.display_avatar)

        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if file_path.endswith(".png"):
                file_type = "png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                file_type = "jpeg"
            elif file_path.endswith(".bmp"):
                file_type = "bmp"

            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            self.mw.chat_thread.upload_avatar_signal.connect(uploaded)
            self.mw.chat_thread.upload_avatar(file_type, encoded)

    def saveSettings(self):
        self.data['bio'] = self.bio_edit.toPlainText()
        self.data['name'] = self.display_name_edit.text()
        self.data['username'] = self.username_edit.text()

        self.mw.me_full['user']['username'] = self.data['username']
        self.mw.me_full['user']['account']['name'] = self.data['name']
        self.mw.me_full['user']['account']['avatar_file_name'] = self.data['avatar_rel_path']
        self.mw.me_full['user']['account']['avatar_type'] = self.data['avatar_type']
        self.mw.me_full['bio'] = self.data['bio']

        self.mw.me['username'] = self.data['username']
        self.mw.me['account']['name'] = self.data['name']
        self.mw.me['account']['avatar_file_name'] = self.data['avatar_rel_path']
        self.mw.me['account']['avatar_type'] = self.data['avatar_type']

        self.mw.username = self.data['username']
        self.mw.name = self.data['name']
        self.mw.me_has_avatar = True if self.data['avatar_rel_path'] else False
        self.mw.me_avatar = self.data['avatar_rel_path']

        self.mw.profile_button.setText(self.mw.name)
        self.mw.welcome_label.setText(self.tr("Welcome back, ") + self.mw.name)

        self.mw.chat_thread.update_user_settings_2(self.data)
        self.mw.hideOverlay()
