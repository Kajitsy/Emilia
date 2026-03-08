import sounddevice
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame

from modules.ui.cards import CharacterCards
from modules.ui.Elements import PushButton, VerticalScrollPage
from modules.ui.Icons import Svg
from modules.ui.cards.VoiceCards import _preview_controller
from modules.ui import TM

class MainCard(QFrame):
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
        TM.theme_changed.connect(self.updateTheme)
        self.updateTheme()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        voice_frame = QFrame()
        layout.addWidget(voice_frame, 0, Qt.AlignmentFlag.AlignTop)
        voice_layout = QHBoxLayout()
        voice_frame.setLayout(voice_layout)

        self.play_button = QPushButton()
        self.play_button.setFixedWidth(40)
        self.play_button.clicked.connect(lambda _=False: _preview_controller(self.mw).toggle(self.data.get('previewAudioURI'), self.play_button))
        voice_layout.addWidget(self.play_button)

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

        self.sha_voice_button = PushButton()
        self.sha_voice_button.clicked.connect(self.voiceOverrideShare)
        button_layout.addWidget(self.sha_voice_button, alignment=Qt.AlignmentFlag.AlignLeft)

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

    def updateTheme(self):
        self.sha_voice_button.setIcon(self.svg_icons.share(TM.c("disabled_text")))
        self.play_button.setIcon(self.svg_icons.play(TM.c("disabled_text")))
        self.play_button.setStyleSheet(f"background-color: transparent; color: {TM.c('mw_color')}; border: none; font-size: 32px;")

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
