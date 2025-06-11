import keyboard
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout,
    QVBoxLayout, QLabel,
    QPushButton, QLineEdit,
    QScrollArea, QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy)
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QTimer, QPoint)

from modules.styles import *
from modules.QThreads import (
    PlayerThread, FileLoaderThread,
    ImageLoaderThread, VoiceModeThread)
from modules.Cards import VoiceCards

class VoiceSearch(QWidget):
    def __init__(self, main_window, search_character: str | None = None, current_voice_id="", current_character_id=""):
        super().__init__()
        self.mw = main_window
        self.search_character = search_character
        self.current_voice_id = current_voice_id
        self.current_character_id = current_character_id
        self.setMinimumHeight(600)
        self.setFixedWidth(600)
        self.svg_icons = SvgIcons()

        self.initUI()

        if self.search_character:
            self.mw.chat_thread.voices_search_signal.connect(self._showSearchResults)
            self.mw.chat_thread.voices_search(character_name=self.search_character)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        search_layout = QVBoxLayout()
        layout.addLayout(search_layout)

        search_widget = QWidget()
        search_widget.setStyleSheet(lineedit_style2())
        search_input_layout = QHBoxLayout()
        search_widget.setLayout(search_input_layout)
        search_label = QLabel()
        search_label.setPixmap(self.svg_icons.search())
        search_label.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 16px;")
        search_input_layout.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.showSearchResults)
        self.search_input.setPlaceholderText('Search')
        # self.search_input.setStyleSheet(lineedit_style())
        search_input_layout.addWidget(self.search_input)
        search_layout.addWidget(search_widget)

        self.search_scroll_area = QScrollArea()
        self.search_scroll_area.setWidgetResizable(True)
        self.search_scroll_area.setStyleSheet(scroll_style())

        self.search_cards_viewport = QWidget()
        self.search_cards_viewport.setStyleSheet("background-color: transparent; border: none;")
        self.search_cards_layout = QVBoxLayout()
        self.search_cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.search_cards_viewport.setLayout(self.search_cards_layout)
        self.search_scroll_area.setWidget(self.search_cards_viewport)
        search_layout.addWidget(self.search_scroll_area)

        self.setLayout(layout)

    def openVoiceCard(self, voice_data):
        voiceCard = VoiceCards.VoiceCard(self.mw, voice_data, self.current_character_id, self.current_voice_id)
        self.mw.hideOverlay()
        self.mw.showOverlay(voiceCard)

    def createCard(self, voice_data):
        card = QFrame()
        card.setStyleSheet(card_style())
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
            font = author_label.font()
            font.setPointSize(9)
            author_label.setFont(font)
            text_layout.addWidget(author_label)

        selected_label = QLabel()
        selected_label.setPixmap(self.svg_icons.selected())
        selected_label.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 16p")
        if self.current_voice_id == voice_data.get('id'): card_layout.addWidget(selected_label)

        card.setLayout(card_layout)
        return card

    def _showSearchResults(self, response):
        self.mw.chat_thread.voices_search_signal.disconnect()
        if response:
            for voice in response:
                card = self.createCard(voice)
                card.setFixedHeight(60)
                self.search_cards_layout.addWidget(card)
        else:
            no_results_label = QLabel(self.tr("Voices not found"))
            self.search_cards_layout.addWidget(no_results_label,0,Qt.AlignmentFlag.AlignVCenter)

    def showSearchResults(self):
        search_query = self.search_input.text().strip()
        if not search_query:
            return

        if self.search_cards_layout.layout() is not None:
            for i in reversed(range(self.search_cards_layout.layout().count())):
                item = self.search_cards_layout.layout().itemAt(i)
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
        self.svg_icons = SvgIcons()

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

        self.mute_button = QPushButton()
        self.mute_button.setIcon(self.svg_icons.mute())
        self.mute_button.setStyleSheet(icon_button_style())
        self.mute_button.clicked.connect(self.toggleMute)
        button_layout.addWidget(self.mute_button)

        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.svg_icons.end_call())
        self.stop_button.setStyleSheet(icon_button_style())
        self.stop_button.clicked.connect(self.stopThread)
        button_layout.addWidget(self.stop_button)

        self.speaking_indicator = QFrame(self)
        self.speaking_indicator.hide()

        self.mw.setOutputDevice(self.mw.settings.value('output_device', 0, type=int))

        self._run()
        keyboard.add_hotkey(self.mute_keybind, self.toggleMute)

    def toggleMute(self):
        self.muted = not self.muted
        self.thread.muted = self.muted
        if self.muted:
            self.mute_button.setIcon(self.svg_icons.muted())
        else:
            self.mute_button.setIcon(self.svg_icons.mute())

    def stopThread(self):
        if self.thread.isRunning():
            self.thread.sd_stop()
            self.thread.terminate()
            self.thread.wait()
            self.mw.hide_overlay = True
            self.mw.hideOverlay()
            keyboard.remove_hotkey(self.mute_keybind)

    def _run(self):
        self.thread = VoiceModeThread(self, self.mw.token, self.character_id, self.chat_id, self.voice_id)
        self.thread.speech_signal.connect(self.updateSpeakingIndicator)
        self.thread.speech_error_signal.connect(self.handleSpeechError)
        self.thread.user_message.connect(self._userMessage)
        self.thread.char_message.connect(self._charMessage)
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