import sounddevice, base64
from PyQt6.QtGui import QAction, QFontMetrics
from PyQt6.QtWidgets import (
    QApplication,
    QWidget, QHBoxLayout,
    QVBoxLayout, QLabel,
    QPushButton,
    QScrollArea, QFrame,
    QLineEdit, QMenu, QCheckBox, QSpacerItem, QSizePolicy, QFileDialog)

from modules.QCustom import CustomTextEdit
from modules.styles import *
from modules.QThreads import (
    PlayerThread, FileLoaderThread,
    ImageLoaderThread)

class VoiceCards:
    class VoiceCard(QWidget):
        def __init__(self, main_window, data, character_id="", current_voice_id="", search=True):
            super().__init__()
            self.setFixedSize(500, 200)

            self.mw = main_window
            self.data = data
            self.character_id = character_id
            self.current_voice_id = current_voice_id
            self.search = search
            self.svg_icons = SvgIcons()

            self.iss = self.data.get('id') == self.current_voice_id

            self.initUI()

        def initUI(self):
            layout = QVBoxLayout()
            self.setLayout(layout)

            voice_frame = QFrame()
            layout.addWidget(voice_frame, 0, Qt.AlignmentFlag.AlignTop)
            voice_layout = QHBoxLayout()
            voice_frame.setLayout(voice_layout)

            play_button = QPushButton()
            play_button.setIcon(SvgIcons().play())
            play_button.setFixedWidth(40)
            play_button.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 32px;")
            play_button.clicked.connect(lambda event: play(self.data.get('previewAudioURI')))
            voice_layout.addWidget(play_button)

            def set_play():
                try:
                    play_button.setIcon(self.svg_icons.play())
                    play_button.clicked.connect(lambda event: play(self.data.get('previewAudioURI')))
                except: pass

            def set_pause(thread):
                try:
                    play_button.setIcon(self.svg_icons.pause())
                    play_button.clicked.connect(lambda event: thread.stop())
                except: pass

            def _play(dataa):
                thread = PlayerThread(dataa)
                thread.play_signal.connect(lambda: set_pause(thread))
                thread.stop_signal.connect(lambda: set_play())
                self.mw.threads.append(thread)
                thread.start()

            def play(url):
                thread = FileLoaderThread(url)
                self.mw.threads.append(thread)
                thread.file.connect(lambda data: _play(data))
                thread.start()

            text_frame = QFrame()
            text_layout = QVBoxLayout()
            text_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            text_frame.setLayout(text_layout)
            voice_layout.addWidget(text_frame)
            self.name_label = QLabel(self.data.get('name'))
            self.description_label = QLabel(self.data.get('description'))
            self.description_label.setWordWrap(True)
            self.author_label = QLabel()
            text_layout.addWidget(self.name_label, 0, Qt.AlignmentFlag.AlignTop)
            text_layout.addWidget(self.description_label, 0, Qt.AlignmentFlag.AlignTop)
            text_layout.addWidget(self.author_label, 0, Qt.AlignmentFlag.AlignBottom)

            button_frame = QFrame()
            button_layout = QHBoxLayout()
            button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            button_frame.setLayout(button_layout)
            voice_layout.addWidget(button_frame, 0, Qt.AlignmentFlag.AlignBottom)

            sha_voice_button = QPushButton()
            sha_voice_button.setIcon(self.svg_icons.share())
            sha_voice_button.setStyleSheet(button_style())
            sha_voice_button.clicked.connect(self.voiceOverrideShare)
            button_layout.addWidget(sha_voice_button, alignment=Qt.AlignmentFlag.AlignLeft)

            sel_voice_button = QPushButton(self.tr("Select"))
            sel_voice_button.setStyleSheet(button_style())
            sel_voice_button.clicked.connect(self.voiceOverrideSelect)

            rem_voice_button = QPushButton(self.tr("Remove"))
            rem_voice_button.setStyleSheet(button_style())
            rem_voice_button.clicked.connect(self.voiceOverrideRemove)

            if self.character_id:
                button_layout.addWidget(sel_voice_button if not self.iss else rem_voice_button, 0)

            character_page = QWidget()
            character_page_layout = QVBoxLayout(character_page)

            recent_label = QLabel("<b>"+self.tr("Try with latest chat")+"</b>")

            character_scroll_area = QScrollArea()
            character_scroll_area.setWidgetResizable(True)
            character_scroll_area.setStyleSheet(scroll_style())

            character_container = QWidget()
            character_container.setStyleSheet("background-color: transparent; border: none;")
            self.character_layout = QVBoxLayout()
            self.character_layout.setContentsMargins(0, 0, 0, 0)
            self.character_layout.setSpacing(0)
            character_container.setLayout(self.character_layout)

            character_scroll_area.setWidget(character_container)
            if not self.search:
                for chat in self.mw.recent_chats:
                    card = self.createCard(chat.get('name'), chat.get('avatar_file_name'), chat.get('character_id'), chat.get('id'))
                    self.character_layout.addWidget(card)
                layout.addWidget(recent_label, alignment=Qt.AlignmentFlag.AlignHCenter)
                layout.addWidget(character_scroll_area)
                self.setFixedSize(500, 750)
            character_page.setLayout(character_page_layout)

        def createCard(self, name, avatar_url, character_id, chat_id=""):
            def openChat():
                self.mw.chat_thread.voice_override_update_signal.connect(_openChat)
                self.mw.chat_thread.voice_override_update(character_id, self.data.get('id'))
            def _openChat(data):
                self.mw.openChat(character_id, name, chat_id)
                self.mw.hideOverlay()
            card = CharacterCards.MiniCard(self.mw, name, character_id, avatar_url, chat_id)
            card.mousePressEvent = lambda _: openChat()
            return card

        def voiceOverrideShare(self):
            QApplication.clipboard().setText(f'https://character.ai/?voiceId={self.data.get('id')}')
            self.mw.showNotification(self.tr("Link copied to clipboard"))

        def voiceOverrideRemove(self):
            self.mw.chat_thread.voice_override_delete_signal.connect(self._voiceOverrideRemove)
            self.mw.chat_thread.voice_override_delete(self.character_id)

        def voiceOverrideSelect(self):
            self.mw.chat_thread.voice_override_update_signal.connect(self._voiceOverrideSelect)
            self.mw.chat_thread.voice_override_update(self.character_id, self.data.get('id'))

        def _voiceOverrideRemove(self, response):
            self.mw.chat_thread.voice_override_delete_signal.disconnect()
            self.mw.current_chat_interface.voice_id = None
            self.mw.current_chat_interface.select_char_voice_label.setText("")
            self.mw.current_chat_interface.enable_char_voice_button.setVisible(False)
            self.mw.hideOverlay()

        def _voiceOverrideSelect(self, response):
            self.mw.chat_thread.voice_override_update_signal.disconnect()
            self.mw.current_chat_interface.voice_id = self.data.get('id')
            self.mw.current_chat_interface.select_char_voice_label.setText(f"{self.data.get('name')}")
            self.mw.current_chat_interface.enable_char_voice_button.setVisible(True)
            self.mw.hideOverlay()

        def closeEvent(self, a0):
            super().closeEvent(a0)
            sounddevice.stop()

    class HorizontalMiniVoiceCard(QFrame):
        def __init__(self, main_window, data):
            super().__init__()
            self.setFixedHeight(60)
            self.setStyleSheet(card_style())
            self.mousePressEvent = lambda event: self.openVoiceCard()
            self.setCursor(Qt.CursorShape.PointingHandCursor)

            self.main_window = main_window
            self.data = data
            self.svg_icons = SvgIcons()

            self.initUI()

        def openVoiceCard(self):
            vcard = VoiceCards.VoiceCard(self.main_window, self.data, search=False)
            self.main_window.showOverlay(vcard)

        def initUI(self):
            card_layout = QHBoxLayout()
            play_button = QPushButton()
            play_button.setIcon(self.svg_icons.play())
            play_button.setFixedWidth(40)
            play_button.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 32px;")
            play_button.clicked.connect(lambda event: play(self.data.get('previewAudioURI')))
            card_layout.addWidget(play_button)

            def set_play():
                try:
                    play_button.setIcon(self.svg_icons.play())
                    play_button.clicked.connect(lambda event: play(self.data.get('previewAudioURI')))
                except:
                    pass

            def set_pause(thread):
                try:
                    play_button.setIcon(self.svg_icons.pause())
                    play_button.clicked.connect(lambda event: thread.stop())
                except:
                    pass

            def _play(dataa):
                thread = PlayerThread(dataa)
                thread.play_signal.connect(lambda: set_pause(thread))
                thread.stop_signal.connect(lambda: set_play())
                self.main_window.threads.append(thread)
                thread.start()

            def play(url):
                thread = FileLoaderThread(url)
                self.main_window.threads.append(thread)
                thread.file.connect(lambda dataa: _play(dataa))
                thread.start()

            text_layout = QVBoxLayout()
            text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            card_layout.addLayout(text_layout, 1)

            title_label = QLabel(self.data.get("name"))
            font = title_label.font()
            font.setPointSize(12)
            font.setBold(True)
            title_label.setFont(font)
            text_layout.addWidget(title_label)

            description_label = QLabel(self.data.get("description"))
            font = description_label.font()
            font.setPointSize(10)
            description_label.setFont(font)
            text_layout.addWidget(description_label)

            self.setLayout(card_layout)

        def closeEvent(self, a0):
            super().closeEvent(a0)
            sounddevice.stop()

class PersonaCards:
    class OverlayCard(QFrame):
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

    class ListCard(QFrame):
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
                self.is_default_label.setVisible(self.data['external_id'] == self.mw.user_settings.get('default_persona_id'))

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
            self.mw.showOverlay(PersonaCards.OverlayCard(self.mw, self.data, self))

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

class CharacterCards:
    class MainCard(QFrame):
        def __init__(self, main_window, name="", avatar_url="", description="", author="", character_id="", chats=0, voted=0, avatar_label_w=90, avatar_label_h=114):
            super().__init__()
            self.mw = main_window
            self.name = name
            self.avatar_url = avatar_url
            self.description = description
            self.author = author
            self.character_id = character_id
            self.chats = chats
            self.voted = voted
            self.avatar_label_w = avatar_label_w
            self.avatar_label_h = avatar_label_h

            self.setStyleSheet(card_style())
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.mousePressEvent = lambda _: self.mw.openChat(self.character_id, self.name, None)

            self.initUI()

        def initUI(self):
            card_layout = QHBoxLayout()
            self.setLayout(card_layout)

            self.avatar_label = QLabel()
            self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
            self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(self.avatar_label)

            if self.avatar_url:
                load_avatar_thread = ImageLoaderThread(
                    "https://characterai.io/i/80/static/avatars/" + self.avatar_url + '?webp=true&anim=0', self.avatar_label_w,
                    self.avatar_label_h)
                load_avatar_thread.image_loaded.connect(self.avatar_label.setPixmap)
                load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name, 4))
                load_avatar_thread.radius = 4
                load_avatar_thread.start()
                self.mw.threads.append(load_avatar_thread)
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
                author_label.setFont(font)
                text_layout.addWidget(author_label)

            if self.description:
                description_label = QLabel(format_text(self.description, self.name))
                description_label.setWordWrap(True)
                font = description_label.font()
                font.setPointSize(9)
                description_label.setFont(font)
                fm = QFontMetrics(font)
                description_label.setMaximumHeight(fm.lineSpacing() * 4)
                text_layout.addWidget(description_label)
                self.setToolTip(format_text(self.description))

            spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            text_layout.addItem(spacer)

            add_info = QLabel()
            font = add_info.font()
            font.setPointSize(10)
            add_info.setFont(font)
            if self.chats:
                add_info.setText(add_info.text() + str(format_number(self.chats)) + self.tr(" chats"))
            if self.voted:
                add_info.setText(add_info.text() + " • " + str(format_number(self.voted)) + self.tr(" likes"))

            if add_info.text():
                text_layout.addWidget(add_info)

    class MiniCard(QFrame):
        def __init__(self, main_window, character_name, character_id, avatar_url, chat_id=None):
            super().__init__()
            self.mw = main_window
            self.name = character_name
            self.character_id = character_id
            self.avatar_url = avatar_url
            self.chat_id = chat_id

            self.setStyleSheet(card_style())
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.mousePressEvent = lambda _: self.mw.openChat(self.character_id, self.name, self.chat_id)

            self.initUI()

        def initUI(self):
            card_layout = QHBoxLayout()
            self.setLayout(card_layout)

            self.avatar_label = QLabel()
            self.avatar_label.setFixedSize(54, 54)
            self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(self.avatar_label)

            if self.avatar_url:
                load_avatar_thread = ImageLoaderThread(
                    "https://characterai.io/i/80/static/avatars/" + self.avatar_url + '?webp=true&anim=0', 54, 54)
                load_avatar_thread.image_loaded.connect(self.avatar_label.setPixmap)
                load_avatar_thread.radius = 4
                load_avatar_thread.start()
                self.mw.threads.append(load_avatar_thread)
            else:
                color_avatar(self.avatar_label, 54, 54, self.name, 4)

            title_label = QLabel(self.name)
            font = title_label.font()
            font.setBold(True)
            font.setPointSize(16)
            title_label.setFont(font)
            card_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter)