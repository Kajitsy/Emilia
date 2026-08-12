from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from modules.ui import TM
from modules.ui.cards.VoiceCards import MainCard, _preview_controller
from modules.ui.Elements import CardFrame, SearchLineEdit, VerticalScrollPage
from modules.ui.Icons import Svg


class SearchCard(QWidget):
    def __init__(
        self,
        main_window,
        search_character: str | None = None,
        current_voice_id="",
        current_character_id="",
    ):
        super().__init__()
        self.mw = main_window
        self.search_character = search_character
        self.current_voice_id = current_voice_id
        self.current_character_id = current_character_id
        self.setMinimumHeight(600)
        self.setFixedWidth(600)
        self.svg_icons = Svg()

        self.initUI()
        TM.theme_changed.connect(self.updateTheme)
        self.updateTheme()

        if self.search_character:
            self.mw.chat_thread.voices_search_signal.connect(self._showSearchResults)
            self.mw.chat_thread.voices_search(char_name=self.search_character)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        search_layout = QVBoxLayout()
        layout.addLayout(search_layout)

        self.search_input = SearchLineEdit(self.mw)
        self.search_input.returnPressed.connect(self.showSearchResults)
        self.search_input.setPlaceholderText(self.tr("Search"))
        search_layout.addWidget(self.search_input)

        self.search_scroll_page = VerticalScrollPage()
        self.search_scroll_viewport = self.search_scroll_page.viewport
        self.search_scroll_viewport.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.search_scroll_layout = self.search_scroll_page.layout
        search_layout.addWidget(self.search_scroll_page)

        self.setLayout(layout)

    def updateTheme(self):
        self.search_input.setIcon(QIcon(self.svg_icons.search(TM.c("icon"))))

    def openVoiceCard(self, voice_data):
        voiceCard = MainCard(
            self.mw, voice_data, self.current_character_id, self.current_voice_id
        )
        self.mw.hideOverlay()
        self.mw.showOverlay(voiceCard)

    def createCard(self, voice_data):
        card = CardFrame()
        card.mousePressEvent = lambda event: self.openVoiceCard(voice_data)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QHBoxLayout()

        play_button = QPushButton()
        play_button.setStyleSheet(
            "background-color: transparent; border: none; padding: 8px;"
        )
        play_button.clicked.connect(
            lambda _=False: _preview_controller(self.mw).toggle(
                voice_data.get("previewAudioURI"), play_button
            )
        )
        card_layout.addWidget(play_button)

        text_layout = QVBoxLayout()
        card_layout.addLayout(text_layout, 1)
        title_label = QLabel(voice_data["name"])
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        if voice_data.get("creatorInfo", {}).get("username"):
            author_label = QLabel(
                self.tr("Author: @") + voice_data.get("creatorInfo", {}).get("username")
            )

            def updateTheme():
                author_label.setStyleSheet(f"color: {TM.c('disabled_text')};")

            TM.theme_changed.connect(updateTheme)
            updateTheme()
            font = author_label.font()
            font.setPointSize(8)
            author_label.setFont(font)
            text_layout.addWidget(author_label)

        selected_label = QLabel()

        def updateTheme():
            play_button.setIcon(self.svg_icons.play(TM.c("icon")))
            selected_label.setPixmap(self.svg_icons.selected(TM.c("icon")))
            selected_label.setStyleSheet(
                f"background-color: transparent; color: {TM.c('mw_color')}; border: none; font-size: 16px;"
            )

        TM.theme_changed.connect(updateTheme)
        updateTheme()
        if self.current_voice_id == voice_data.get("id"):
            card_layout.addWidget(selected_label)

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
            self.search_scroll_layout.addWidget(
                no_results_label, 0, Qt.AlignmentFlag.AlignVCenter
            )

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
