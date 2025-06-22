import base64
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout, QFileDialog,
    QVBoxLayout, QLabel,
    QPushButton, QLineEdit,
    QMenu, QCheckBox,
    QFrame)

from modules.QCustom import CustomTextEdit
from modules.styles import *
from modules.QThreads import ImageLoaderThread

class EditOverlay(QFrame):
    def __init__(self, main_window, data=None, list_card=None):
        super().__init__()
        self.setFixedSize(500, 200)

        self.mw = main_window
        self.data = data
        self.list_card = list_card
        self.new = False
        self.temp_link = ""
        self.svg_icons = SvgIcons()

        if data is None:
            self.data = {}
            self.new = True
        self.is_def = self.data.get('external_id') == self.mw.user_settings.get('default_persona_id')
        self.ex_id = self.data.get('external_id')
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        fh_layout = QHBoxLayout()
        layout.addLayout(fh_layout)

        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText(self.tr("Display Name"))
        self.display_name_edit.setText(self.data.get('participant__name'))
        self.display_name_edit.setStyleSheet(lineedit_style())
        self.display_name_edit.textChanged.connect(lambda text: self.data.update({'name': text}))
        self.display_name_edit.setMaxLength(20)
        fh_layout.addWidget(self.display_name_edit)

        self.display_avatar = QLabel()
        self.display_avatar.mousePressEvent = lambda _: self.selectAvatar()
        self.display_avatar.setFixedSize(60, 60)
        if self.data.get("avatar_file_name"):
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.data.get("avatar_file_name") + '?webp=true&anim=0',
                60, 60)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.mw.me_avatar, 60, 60, self.mw.name))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        elif self.mw.me_has_avatar:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.mw.me_avatar + '?webp=true&anim=0',
                60, 60)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.mw.me_avatar, 60, 60, self.mw.name))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.display_avatar, 60, 60, self.mw.name)
        fh_layout.addWidget(self.display_avatar)

        self.background_edit = CustomTextEdit()
        self.background_edit.setPlaceholderText(self.tr("Background"))
        self.background_edit.setText(self.data.get('definition'))
        self.background_edit.setStyleSheet(lineedit_style())
        self.background_edit.textChanged.connect(self.textChanged)
        self.background_edit.setFixedHeight(32)
        self.background_edit.horizontalScrollBar().setVisible(False)
        self.background_edit.verticalScrollBar().setVisible(False)
        layout.addWidget(self.background_edit)

        make_default_layout = QHBoxLayout()
        make_default_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(make_default_layout)

        self.make_default_checkbox = QCheckBox()
        if self.ex_id == self.mw.user_settings.get('default_persona_id'):
            self.make_default_checkbox.setChecked(True)
        make_default_layout.addWidget(self.make_default_checkbox, 0)
        self.make_default_label = QLabel(self.tr("Make default for new chats"))
        make_default_layout.addWidget(self.make_default_label)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.remove_button = QPushButton(self.tr("Remove"))
        self.remove_button.setStyleSheet(button_style())
        self.remove_button.clicked.connect(lambda _: self.removePerson())
        button_layout.addWidget(self.remove_button)

        self.save_button = QPushButton(self.tr("Save"))
        self.save_button.setStyleSheet(button_style())
        self.save_button.clicked.connect(self.saveSettings)
        button_layout.addWidget(self.save_button)

    def selectAvatar(self):
        def uploaded(link):
            setattr(self, 'temp_link', link)
            self.data['avatar_rel_path'] = link
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + link + '?webp=true&anim=0',
                60, 60)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)

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

    def textChanged(self):
        text = self.background_edit.toPlainText()
        line_count = text.count('\n')
        line_count += text.count('<br>') + 1 if text else 1
        height = line_count * self.background_edit.fontMetrics().lineSpacing() + 16
        self.data.update({'definition': self.background_edit.toPlainText()})
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
            self.mw.user_settings['default_persona_id'] = self.ex_id
            self.mw.chat_thread.update_user_settings(self.mw.user_settings)
        elif not self.make_default_checkbox.isChecked() and self.is_def:
            self.mw.user_settings['default_persona_id'] = ""
            self.mw.chat_thread.update_user_settings(self.mw.user_settings)

        if self.new:
            self.mw.chat_thread.create_persona(self.temp_link, "", self.data.get('definition'), self.data.get('name'))
        else:
            self.mw.chat_thread.update_persona_signal.connect(self._updateUserPersona)
            self.mw.chat_thread.update_persona(self.data)
        self.mw.hideOverlay()

    def _updateUserPersona(self, data):
        self.mw.chat_thread.update_persona_signal.disconnect()
        self.data = data
        if self.list_card:
            setattr(self.list_card, 'data', self.data)
            self.list_card.display_name_label.setText(self.data.get('name'))
            self.list_card.background_label.setText(self.data.get('definition'))
            if self.data['external_id'] == self.mw.user_settings.get('default_persona_id'):
                self.list_card.is_default_label.setVisible(True)
            else:
                self.list_card.is_default_label.setVisible(False)
            if self.data.get("avatar_file_name"):
                load_avatar_thread = ImageLoaderThread(
                    "https://characterai.io/i/80/static/avatars/" + self.data.get(
                        "avatar_file_name") + '?webp=true&anim=0',
                    60, 60)
                load_avatar_thread.image_loaded.connect(self.list_card.display_avatar.setPixmap)
                load_avatar_thread.start()
                self.mw.threads.append(load_avatar_thread)
            elif self.mw.me_has_avatar:
                load_avatar_thread = ImageLoaderThread(
                    "https://characterai.io/i/80/static/avatars/" + self.mw.me_avatar + '?webp=true&anim=0',
                    60, 60)
                load_avatar_thread.image_loaded.connect(self.list_card.display_avatar.setPixmap)
                load_avatar_thread.start()
                self.mw.threads.append(load_avatar_thread)
            else:
                color_avatar(self.list_card.display_avatar, 60, 60, self.mw.name)

class MainCard(QFrame):
    def __init__(self, main_window, data=None, character_id=None):
        super().__init__()
        self.mw = main_window
        self.data = data
        self.char_id = character_id
        self.new = False
        self.active = False
        self.svg_icons = SvgIcons()
        if self.data is None:
            self.data = {}
            self.new = True
        else:
            if self.char_id:
                if self.mw.user_settings.get('personaOverrides', {}).get(self.char_id) == self.data['external_id']:
                    self.active = True

        self.data['name'] = self.data.get('participant__name')
        self.initUI()
        self.setStyleSheet(card_style())

    def initUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.display_avatar = QLabel()
        self.display_avatar.setFixedSize(60, 60)
        if self.data.get("avatar_file_name"):
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.data.get(
                    "avatar_file_name") + '?webp=true&anim=0',
                60, 60)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.mw.me_avatar, 60, 60, self.mw.name))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        elif self.mw.me_has_avatar:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.mw.me_avatar + '?webp=true&anim=0',
                60, 60)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.mw.me_avatar, 60, 60, self.mw.name))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.display_avatar, 60, 60, self.mw.name)
        layout.addWidget(self.display_avatar)

        fh_layout = QVBoxLayout()
        fh_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(fh_layout)

        top_layout = QHBoxLayout()
        fh_layout.addLayout(top_layout)
        self.display_name_label = QLabel(self.data.get('name'))
        self.is_default_label = QLabel(self.tr("Default"))
        self.is_active_label = QLabel(self.tr("Active"))
        self.is_default_label.setStyleSheet("color: #536dc6;")
        self.is_active_label.setStyleSheet("color: #536dc6;")
        top_layout.addWidget(self.display_name_label)
        top_layout.addWidget(self.is_default_label)
        top_layout.addWidget(self.is_active_label)
        self.is_default_label.setVisible(False)
        self.is_active_label.setVisible(False)
        if self.active:
            self.is_active_label.setVisible(True)
        if not self.char_id:
            self.is_default_label.setVisible(
                self.data['external_id'] == self.mw.user_settings.get('default_persona_id'))

        self.background_label = QLabel(self.data.get('definition'))
        self.background_label.setStyleSheet("color: #a2a2ac; font-size: 12px;")
        fh_layout.addWidget(self.background_label, alignment=Qt.AlignmentFlag.AlignTop)

        self.edit_button = QPushButton(self.tr("Edit"))
        self.edit_button.setStyleSheet(pushbutton_style())
        self.edit_button.clicked.connect(self.showOverlay)
        layout.addWidget(self.edit_button, alignment=Qt.AlignmentFlag.AlignRight)

    def clearDefault(self):
        def clearedDefault(data):
            if data.get('success', False):
                self.mw.showNotification(self.tr('Successfully updated your persona'))
                self.is_default_label.setVisible(False)
                self.make_default_action.setVisible(True)
                self.clear_default_action.setVisible(False)
                self.mw.user_settings = data['settings']

        self.mw.user_settings['default_persona_id'] = ""
        self.mw.chat_thread.update_user_settings(self.mw.user_settings)
        self.mw.chat_thread.update_user_settings_signal.connect(clearedDefault)

    def makeDefault(self):
        def makedDefault(data):
            if data.get('success', False):
                self.mw.showNotification(self.tr('Successfully updated your persona'))
                self.is_default_label.setVisible(True)
                self.make_default_action.setVisible(False)
                self.clear_default_action.setVisible(True)
                self.mw.user_settings = data['settings']

        self.mw.user_settings['default_persona_id'] = self.data['external_id']
        self.mw.chat_thread.update_user_settings(self.mw.user_settings)
        self.mw.chat_thread.update_user_settings_signal.connect(makedDefault)

    def removePerson(self):
        self.mw.chat_thread.remove_persona(self.data)
        self.deleteLater()

    def showOverlay(self):
        self.mw.showOverlay(EditOverlay(self.mw, self.data, self))

    def contextMenuEvent(self, a0):
        super().contextMenuEvent(a0)
        context_menu = QMenu(self)
        context_menu.setStyleSheet(menu_style())

        edit_action = QAction(self.tr("Edit"))
        edit_action.triggered.connect(self.showOverlay)
        context_menu.addAction(edit_action)

        self.clear_default_action = QAction(self.tr("Clear default"))
        self.clear_default_action.triggered.connect(self.clearDefault)
        context_menu.addAction(self.clear_default_action)

        self.make_default_action = QAction(self.tr("Make default"))
        self.make_default_action.triggered.connect(self.makeDefault)
        context_menu.addAction(self.make_default_action)

        remove_action = QAction(self.tr("Remove"))
        remove_action.triggered.connect(self.removePerson)
        context_menu.addAction(remove_action)

        if self.data['external_id'] == self.mw.user_settings.get('default_persona_id'):
            self.make_default_action.setVisible(False)
            self.clear_default_action.setVisible(True)
        else:
            self.make_default_action.setVisible(True)
            self.clear_default_action.setVisible(False)

        context_menu.exec(self.mapToGlobal(a0.pos()))
