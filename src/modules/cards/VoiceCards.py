import keyboard, sounddevice
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
                             QGraphicsDropShadowEffect)

from modules.cards import CharacterCards
from modules.style.Elements import PushButton, VerticalScrollPage, CardFrame, LineEdit, SearchLineEdit
from modules.style.Icons import Svg
from modules.QThreads import PlayerThread, FileLoaderThread, VoiceModeThread, VoiceModeThreadV2
from modules.style.Utils import color_avatar, format_text

class _VoicePreviewController:
    def __init__(self, main_window):
        self.mw = main_window
        self.svg_icons = Svg()
        self.active_loader = None
        self.active_player = None
        self.active_button = None
        self.is_playing = False
        self.is_loading = False

    def _set_button_play(self, button):
        if button:
            button.setIcon(self.svg_icons.play())

    def _set_button_pause(self, button):
        if button:
            button.setIcon(self.svg_icons.pause())

    def _reset_state(self):
        self.active_loader = None
        self.active_player = None
        self.active_button = None
        self.is_playing = False
        self.is_loading = False

    def stop(self):
        if self.active_player:
            self.active_player.stop()
        if self.active_button:
            self._set_button_play(self.active_button)
        self._reset_state()

    def toggle(self, url, button):
        if not url:
            return
        if self.active_button is button and (self.is_playing or self.is_loading):
            self.stop()
            return

        self.stop()
        self.active_button = button
        self.is_loading = True

        loader = FileLoaderThread(url)
        self.active_loader = loader
        self.mw.threads.append(loader)
        loader.file.connect(lambda data, loader_ref=loader: self._start_player(loader_ref, data))
        loader.start()

    def _start_player(self, loader, data):
        if loader is not self.active_loader:
            return
        self.is_loading = False
        player = PlayerThread(data)
        self.active_player = player
        self.mw.threads.append(player)
        player.play_signal.connect(lambda _: self._on_play(player))
        player.stop_signal.connect(lambda _: self._on_stop(player))
        player.start()

    def _on_play(self, player):
        if player is not self.active_player:
            return
        self.is_playing = True
        self._set_button_pause(self.active_button)

    def _on_stop(self, player):
        if player is not self.active_player:
            return
        self._set_button_play(self.active_button)
        self._reset_state()

def _preview_controller(main_window):
    if not hasattr(main_window, "_voice_preview_controller"):
        main_window._voice_preview_controller = _VoicePreviewController(main_window)
    return main_window._voice_preview_controller

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
        play_button.setIcon(self.svg_icons.play())
        play_button.setFixedWidth(40)
        play_button.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 32px;")
        play_button.clicked.connect(lambda _=False: _preview_controller(self.mw).toggle(self.data.get('previewAudioURI'), play_button))
        voice_layout.addWidget(play_button)

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
                card = self.createCard(chat.get('character_name'), chat.get('character_avatar_uri'), chat.get('character_id'), chat.get('chat_id'))
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
        self.mw = main_window
        self.data = data
        self.svg_icons = Svg()

        self.initUI()

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        if a0.button() == Qt.MouseButton.RightButton:
            self.mw.hideOverlay()
            self.mw.showOverlay(VoiceCard(self.mw, self.data, search=False))

    def initUI(self):
        card_layout = QHBoxLayout()
        play_button = QPushButton()
        play_button.setIcon(self.svg_icons.play())
        play_button.setFixedWidth(40)
        play_button.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 32px;")
        play_button.clicked.connect(lambda _=False: _preview_controller(self.mw).toggle(self.data.get('previewAudioURI'), play_button))
        card_layout.addWidget(play_button)

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

        self.search_input = SearchLineEdit(self.mw)
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
        play_button.clicked.connect(lambda _=False: _preview_controller(self.mw).toggle(voice_data.get('previewAudioURI'), play_button))
        card_layout.addWidget(play_button)

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
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{avatar_url}?webp=true&anim=0",
                80, 80, 10, label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, 80, 80, self.char_name, 10))
        else:
            color_avatar(self.avatar_label, 80, 80, self.char_name, 10)
        self.layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.char_msg_label = QLabel()
        self.char_msg_label.setStyleSheet("font-size: 16px;")
        self.char_msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.char_msg_label.setWordWrap(True)
        self.char_msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.char_msg_label.hide()
        self.layout.addWidget(self.char_msg_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.layout.addStretch()

        self.user_msg_label = QLabel()
        self.user_msg_label.setStyleSheet("font-size: 16px;")
        self.user_msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_msg_label.setWordWrap(True)
        self.user_msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.user_msg_label.hide()
        self.layout.addWidget(self.user_msg_label, alignment=Qt.AlignmentFlag.AlignHCenter)

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
        if self.mw.settings.value('use_old_voice_chat', False, type=bool):
            self.thread = VoiceModeThread(self, self.mw.token, self.character_id, self.chat_id, self.voice_id)
            self.thread.speech_signal.connect(self.updateSpeakingIndicator)
            self.thread.speech_error_signal.connect(self.handleSpeechError)
            self.thread.user_message.connect(self._userMessage)
            self.thread.char_message.connect(self._charMessage)
            self.thread.start()
            self.mw.threads.append(self.thread)
        else:
            self.thread = VoiceModeThreadV2(self, self.mw.token, self.character_id, self.chat_id, self.mw.username, self.char_name, self.voice_id)
            self.thread.speech_signal.connect(self.updateSpeakingIndicator)
            self.thread.error_signal.connect(self.mw.showNotification)
            if hasattr(self.chi, 'vmodel_widget'):
                self.thread.volume_signal.connect(self.chi.vmodel_widget.set_stream_volume)
            self.thread.start()
            self.mw.threads.append(self.thread)

    def _userMessage(self, text):
        self.chi.addMessage(text, "", is_user=True)
        self.chi.mw.chat_thread.chat_histories.get(self.chat_id, []).append({
            'author': {'is_human': True},
            'candidates': [{'raw_content': text, 'is_final': True}]
        })
        self.user_msg_label.setText(text)
        self.user_msg_label.show()
        QTimer.singleShot(3000, self.user_msg_label.hide)

    def _charMessage(self, message):
        raw_text = message['candidates'][0]['raw_content']
        self.chi.addMessage(raw_text, message['turn_key']['turn_id'], is_user=False)
        self.chi.mw.chat_thread.chat_histories.get(self.chat_id, []).append({
            'author': {'is_human': False},
            'candidates': [{'raw_content': raw_text, 'is_final': True}],
            'turn_key': {'chat_id': self.chat_id, 'turn_id': message['turn_key']['turn_id']}
        })
        self.animateCharacterMessage(format_text(raw_text, self.mw.username))

    def handleSpeechError(self, is_error):
        if is_error:
            self.is_error_active = True

            self.speaking_indicator.setStyleSheet(
                "background: transparent; border: 2px solid red; border-radius: 10px;")
            self.speaking_indicator.show()
            self.speaking_indicator.lower()
            effect = QGraphicsDropShadowEffect(self.speaking_indicator)
            effect.setBlurRadius(20)
            effect.setColor(QColor(255, 0, 0))
            effect.setOffset(0)
            self.speaking_indicator.setGraphicsEffect(effect)

            self.startShaking()

            QTimer.singleShot(400, self.stopErrorAnimation)

    def startShaking(self):
        original_pos = self.speaking_indicator.pos()
        self.shake_animation = QPropertyAnimation(self.speaking_indicator, b"pos")
        self.shake_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.shake_animation.setDuration(200)
        self.shake_animation.setLoopCount(2)
        self.shake_animation.setKeyValueAt(0, original_pos)
        self.shake_animation.setKeyValueAt(0.25, original_pos + QPoint(-5, 0))
        self.shake_animation.setKeyValueAt(0.5, original_pos)
        self.shake_animation.setKeyValueAt(0.75, original_pos + QPoint(5, 0))
        self.shake_animation.setKeyValueAt(1, original_pos)
        self.shake_animation.start()

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

    def animateCharacterMessage(self, full_text):
        if hasattr(self, 'char_msg_timer') and self.char_msg_timer.isActive():
            self.char_msg_timer.stop()
        self.char_msg_label.setText("")
        self.char_msg_label.show()
        self._char_message_full_text = full_text
        self._char_message_current_index = 0
        self.char_msg_timer = QTimer(self)
        self.char_msg_timer.timeout.connect(self._updateCharMessage)
        self.char_msg_timer.start(50)

    def _updateCharMessage(self):
        self._char_message_current_index += 1
        text_to_display = self._char_message_full_text[:self._char_message_current_index]
        self.char_msg_label.setText(text_to_display)
        if self._char_message_current_index >= len(self._char_message_full_text):
            self.char_msg_timer.stop()
            QTimer.singleShot(3000, self.char_msg_label.hide)

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
