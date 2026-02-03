import keyboard, sounddevice
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
                             QGraphicsDropShadowEffect)

from modules.cards import CharacterCards
from modules.style.Elements import PushButton, VerticalScrollPage, CardFrame, LineEdit
from modules.style.Icons import Svg
from modules.QThreads import PlayerThread, FileLoaderThread, ImageLoaderThread, VoiceModeThread, VoiceModeThreadV2
from modules.style.Utils import color_avatar, format_text

class VoiceCard(QFrame):
    def __init__(self, main_window, data, character_id="", current_voice_id="", search=True):
        super().__init__()
        self.setFixedSize(500, 200)

        self.mw = main_window
        self.data = data
        self.character_id = character_id
        self.current_voice_id = current_voice_id
        self.search = search
        self.svg_icons = Svg()

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
        play_button.setIcon(Svg().play())
        play_button.setFixedWidth(40)
        play_button.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 32px;")
        play_button.clicked.connect(lambda event: play(self.data.get('previewAudioURI')))
        voice_layout.addWidget(play_button)

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

        sha_voice_button = PushButton()
        sha_voice_button.setIcon(self.svg_icons.share())
        sha_voice_button.clicked.connect(self.voiceOverrideShare)
        button_layout.addWidget(sha_voice_button, alignment=Qt.AlignmentFlag.AlignLeft)

        sel_voice_button = PushButton(self.tr("Select"))
        sel_voice_button.clicked.connect(self.voiceOverrideSelect)

        rem_voice_button = PushButton(self.tr("Remove"))
        rem_voice_button.clicked.connect(self.voiceOverrideRemove)

        if self.character_id:
            button_layout.addWidget(sel_voice_button if not self.iss else rem_voice_button, 0)

        character_page = QWidget()
        character_page_layout = QVBoxLayout(character_page)

        recent_label = QLabel("<b>" + self.tr("Try with latest chat") + "</b>")

        character_scroll_page = VerticalScrollPage()
        character_scroll_page.viewport.setStyleSheet("background-color: transparent; border: none;")
        self.scroll_character_layout = character_scroll_page.layout

        if not self.search:
            for chat in self.mw.recent_chats:
                card = self.createCard(chat.get('name'), chat.get('avatar_file_name'), chat.get('character_id'),
                                       chat.get('id'))
                self.scroll_character_layout.addWidget(card)
            layout.addWidget(recent_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(character_scroll_page)
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

class HorizontalMiniVoiceCard(CardFrame):
    def __init__(self, main_window, data):
        super().__init__()
        self.setFixedHeight(60)
        self.main_window = main_window
        self.data = data
        self.svg_icons = Svg()

        self.initUI()

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        if a0.button() == Qt.MouseButton.RightButton:
            self.openVoiceCard()

    def openVoiceCard(self):
        vcard = VoiceCard(self.main_window, self.data, search=False)
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


class VoiceSearch(QWidget):
    def __init__(self, main_window, search_character: str | None = None, current_voice_id="", current_character_id=""):
        super().__init__()
        self.mw = main_window
        self.search_character = search_character
        self.current_voice_id = current_voice_id
        self.current_character_id = current_character_id
        self.setMinimumHeight(600)
        self.setFixedWidth(600)
        self.svg_icons = Svg()

        self.initUI()

        if self.search_character:
            self.mw.chat_thread.voices_search_signal.connect(self._showSearchResults)
            self.mw.chat_thread.voices_search(character_name=self.search_character)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        search_layout = QVBoxLayout()
        layout.addLayout(search_layout)

        self.search_input = LineEdit()
        self.search_input.setIcon(QIcon(self.svg_icons.search()))
        self.search_input.returnPressed.connect(self.showSearchResults)
        self.search_input.setPlaceholderText(self.tr('Search'))
        search_layout.addWidget(self.search_input)

        self.search_scroll_page = VerticalScrollPage()
        self.search_scroll_viewport = self.search_scroll_page.viewport
        self.search_scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
        self.search_scroll_layout = self.search_scroll_page.layout
        search_layout.addWidget(self.search_scroll_page)

        self.setLayout(layout)

    def openVoiceCard(self, voice_data):
        voiceCard = VoiceCard(self.mw, voice_data, self.current_character_id, self.current_voice_id)
        self.mw.hideOverlay()
        self.mw.showOverlay(voiceCard)

    def createCard(self, voice_data):
        card = CardFrame()
        card.mousePressEvent = lambda event: self.openVoiceCard(voice_data)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QHBoxLayout()

        play_button = QPushButton()
        play_button.setIcon(self.svg_icons.play())
        play_button.setStyleSheet("background-color: transparent; border: none; padding: 8px;")
        play_button.clicked.connect(lambda event: play(voice_data.get('previewAudioURI')))
        card_layout.addWidget(play_button)

        def set_play():
            try:
                play_button.setIcon(self.svg_icons.play())
                play_button.clicked.connect(lambda event: play(voice_data.get('previewAudioURI')))
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

        text_layout = QVBoxLayout()
        card_layout.addLayout(text_layout, 1)
        title_label = QLabel(voice_data['name'])
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        if voice_data.get('creatorInfo', {}).get('username'):
            author_label = QLabel(self.tr("Author: @") + voice_data.get('creatorInfo', {}).get('username'))
            author_label.setStyleSheet("color: #a2a2ac;")
            font = author_label.font()
            font.setPointSize(8)
            author_label.setFont(font)
            text_layout.addWidget(author_label)

        selected_label = QLabel()
        selected_label.setPixmap(self.svg_icons.selected())
        selected_label.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 16px")
        if self.current_voice_id == voice_data.get('id'): card_layout.addWidget(selected_label)

        card.setLayout(card_layout)
        return card

    def _showSearchResults(self, response):
        self.mw.chat_thread.voices_search_signal.disconnect()
        if response:
            for voice in response:
                card = self.createCard(voice)
                card.setFixedHeight(60)
                self.search_scroll_layout.addWidget(card)
        else:
            no_results_label = QLabel(self.tr("Voices not found"))
            self.search_scroll_layout.addWidget(no_results_label, 0, Qt.AlignmentFlag.AlignVCenter)

    def showSearchResults(self):
        search_query = self.search_input.text().strip()
        if not search_query:
            return

        if self.search_scroll_layout.layout() is not None:
            for i in reversed(range(self.search_scroll_layout.layout().count())):
                item = self.search_scroll_layout.layout().itemAt(i)
                if item is not None and item.widget() is not None:
                    item.widget().setParent(None)

        self.mw.chat_thread.voices_search_signal.connect(self._showSearchResults)
        self.mw.chat_thread.voices_search(search_query)


class VoiceMode(QWidget):
    def __init__(self, main_window, chat_interface, avatar_url, chat_id, character_id, voice_id, character_name):
        super().__init__()
        self.mw = main_window
        self.chi = chat_interface
        self.character_id = character_id
        self.chat_id = chat_id
        self.voice_id = voice_id
        self.muted = False
        self.mute_keybind = self.mw.settings.value('microphone_mute_key_bind', 'Ctrl+M')
        self.char_name = character_name
        self.svg_icons = Svg()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedSize(1000, 600)

        self.avatar_label = QLabel()
        if avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + avatar_url + '?webp=true&anim=0', 80, 80)
            load_avatar_thread.image_loaded.connect(self.avatar_label.setPixmap)
            load_avatar_thread.radius = 10
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.avatar_label, 80, 80, self.char_name, 10)
        self.layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.user_buttons_frame = QFrame()
        button_layout = QHBoxLayout()
        self.user_buttons_frame.setLayout(button_layout)
        self.layout.addWidget(self.user_buttons_frame, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)

        self.mute_button = PushButton()
        self.mute_button.setIcon(self.svg_icons.mute())
        self.mute_button.clicked.connect(self.toggleMute)
        button_layout.addWidget(self.mute_button)

        self.stop_button = PushButton()
        self.stop_button.setIcon(self.svg_icons.end_call())
        self.stop_button.clicked.connect(self.stopThread)
        button_layout.addWidget(self.stop_button)

        self.speaking_indicator = QFrame(self)
        self.speaking_indicator.hide()

        self.mw.setOutputDevice(self.mw.settings.value('output_device', 0, type=int))

        self._run()
        keyboard.add_hotkey(self.mute_keybind, self.toggleMute)

    def toggleMute(self):
        self.muted = not self.muted
        self.thread.set_mute(self.muted)
        if self.muted:
            self.mute_button.setIcon(self.svg_icons.muted())
        else:
            self.mute_button.setIcon(self.svg_icons.mute())

    def stopThread(self):
        if self.thread.isRunning():
            self.thread.stop_call()
            self.thread.quit()
            self.thread.wait()
            self.mw.hide_overlay = True
            self.mw.hideOverlay()
            keyboard.remove_hotkey(self.mute_keybind)

    def _run(self):
        self.thread = VoiceModeThreadV2(self, self.mw.token, self.character_id, self.chat_id, self.mw.username, self.char_name, voice_id=self.voice_id)
        self.thread.speech_signal.connect(self.updateSpeakingIndicator)
        self.thread.error_signal.connect(self.mw.showNotification)
        self.thread.start()
        self.mw.threads.append(self.thread)

    def stopErrorAnimation(self):
        if hasattr(self, 'shake_animation'):
            self.shake_animation.stop()
        self.is_error_active = False
        self.speaking_indicator.setStyleSheet(
            "background: transparent; border: 2px solid #00BFFF; border-radius: 10px;")
        effect = QGraphicsDropShadowEffect(self.speaking_indicator)
        effect.setBlurRadius(20)
        effect.setColor(QColor(0, 191, 255))
        effect.setOffset(0)
        self.speaking_indicator.setGraphicsEffect(effect)

    def updateSpeakingIndicator(self, is_user_speaking):
        if is_user_speaking:
            target_widget = self.user_buttons_frame
            target_geometry = target_widget.geometry().adjusted(-5, -5, 5, 5)
        else:
            target_widget = self.avatar_label
            target_geometry = target_widget.geometry().adjusted(-3, -3, 3, 3)

        effect = QGraphicsDropShadowEffect(self.speaking_indicator)
        effect.setBlurRadius(20)
        effect.setColor(QColor(0, 191, 255))
        effect.setOffset(0)
        self.speaking_indicator.setGraphicsEffect(effect)

        if not self.speaking_indicator.isVisible():
            self.speaking_indicator.setGeometry(target_geometry)
            self.speaking_indicator.setStyleSheet("background: transparent; border: 2px solid #00BFFF; border-radius: 10px;")
            self.speaking_indicator.show()
            self.speaking_indicator.lower()
        else:
            geom_animation = QPropertyAnimation(self.speaking_indicator, b"geometry")
            geom_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            geom_animation.setDuration(200)
            geom_animation.setStartValue(self.speaking_indicator.geometry())
            geom_animation.setEndValue(target_geometry)

            self.animation_group = QParallelAnimationGroup()
            self.animation_group.addAnimation(geom_animation)
            self.animation_group.start()
