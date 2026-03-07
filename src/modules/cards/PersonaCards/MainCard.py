from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel

from modules.style.Elements import PushButton, Menu, CardFrame
from modules.style.Icons import Svg
from modules.style.Utils import color_avatar
from modules.cards.PersonaCards import EditCard

class MainCard(CardFrame):
    def __init__(self, main_window, data=None, character_id=None):
        super().__init__()
        self.mw = main_window
        self.data = data
        self.char_id = character_id
        self.new = False
        self.active = False
        self.svg_icons = Svg()
        if self.data is None:
            self.data = {}
            self.new = True
        else:
            if self.char_id:
                if self.mw.user_settings.get('personaOverrides', {}).get(self.char_id) == self.data['external_id']:
                    self.active = True

        self.data['name'] = self.data.get('participant__name')
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.display_avatar = QLabel()
        self.display_avatar.setFixedSize(60, 60)
        if self.data.get("avatar_file_name"):
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.data.get("avatar_file_name")}?webp=true&anim=0",
                60, 60, 100, label=self.display_avatar,
                error_cb=lambda _: color_avatar(self.display_avatar, 60, 60, self.mw.name))
        elif self.mw.me_has_avatar:
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0",
                60, 60, 100, label=self.display_avatar,
                error_cb=lambda _: color_avatar(self.display_avatar, 60, 60, self.mw.name))
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

        self.edit_button = PushButton(self.tr("Edit"))
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
        self.mw.hideOverlay()
        self.mw.showOverlay(EditCard(self.mw, self.data, self))

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        if a0.button() == Qt.MouseButton.LeftButton:
            self.showOverlay()

    def contextMenuEvent(self, a0):
        super().contextMenuEvent(a0)
        context_menu = Menu(self)

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
