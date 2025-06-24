import sounddevice
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame)

from modules.cards import CharacterCards
from modules.style.Elements import PushButton, VerticalScrollPage, CardFrame
from modules.style.Icons import Svg
from modules.QThreads import PlayerThread, FileLoaderThread

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

