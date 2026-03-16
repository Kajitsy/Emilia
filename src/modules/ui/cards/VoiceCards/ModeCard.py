import keyboard
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy,
                             QGraphicsDropShadowEffect)

from modules.ui.Elements import PushButton
from modules.ui.Icons import Svg
from modules.logic.QThreads import VoiceModeThread, VoiceModeThreadV2
from modules.Utils import color_avatar, format_text
from modules.ui import TM

class ModeCard(QWidget):
    def __init__(self, main_window, chat_interface, avatar_url, chat_id, character_id, voice_id, character_name):
        super().__init__()
        self.mw = main_window
        self.chi = chat_interface
        self.avatar_url = avatar_url
        self.character_id = character_id
        self.chat_id = chat_id
        self.voice_id = voice_id
        self.muted = False
        self.mute_keybind = self.mw.settings.value('microphone_mute_key_bind', 'Ctrl+M')
        self.char_name = character_name
        self.svg_icons = Svg()

        self.initUI()
        TM.theme_changed.connect(self.updateTheme)
        self.updateTheme()

        self.mw.setOutputDevice(self.mw.settings.value('output_device', 0, type=int))

        self._run()
        keyboard.add_hotkey(self.mute_keybind, self.toggleMute)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedSize(1000, 600)

        self.avatar_label = QLabel()
        if self.avatar_url:
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0",
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
        self.mute_button.clicked.connect(self.toggleMute)
        button_layout.addWidget(self.mute_button)

        self.stop_button = PushButton()
        self.stop_button.clicked.connect(self.stopThread)
        button_layout.addWidget(self.stop_button)

        self.speaking_indicator = QFrame(self)
        self.speaking_indicator.hide()

    def updateTheme(self):
        self.mute_button.setIcon(self.svg_icons.mute(TM.c("icon")))
        self.stop_button.setIcon(self.svg_icons.end_call(TM.c("icon")))

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
