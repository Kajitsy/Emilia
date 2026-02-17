from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QSpacerItem,
                             QSizePolicy, QWidget)

from modules.cards.CharacterCards import ClickableMiniCard
from modules.cards.CreateScenesCards import ChoiceStep, CreatePage
from modules.style.Elements import PushButton, VerticalScrollPage, CardFrame
from modules.style.Utils import format_text

class MainCard(CardFrame):
    def __init__(self, main_window, data):
        super().__init__()
        self.mw = main_window
        self.data = data
        self.title = self.data.get('title')
        self.author = self.data.get('creator_username')

        self.initUI()

    def initUI(self):
        card_layout = QVBoxLayout()
        self.setLayout(card_layout)

        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 200)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addWidget(self.image_label)

        self.mw.image_loader.load(self.data.get("background_image_url"), 150, 200, 4,
                                  label=self.image_label, cache_dir="cache/scenes")

        #text_layout = QVBoxLayout()
        #text_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        #card_layout.addLayout(text_layout, 1)

        title_label = QLabel(self.title)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(11)
        title_label.setFont(font)
        card_layout.addWidget(title_label)

        if self.author:
            #spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            #card_layout.addItem(spacer)

            author_label = QLabel(self.tr("Author: @") + self.author)
            font = author_label.font()
            font.setPointSize(8)
            author_label.setStyleSheet("color: #a2a2ac;")
            author_label.mousePressEvent = lambda _: self.mw.openUserPage(self.author)
            author_label.setCursor(Qt.CursorShape.PointingHandCursor)
            author_label.setFont(font)
            card_layout.addWidget(author_label)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openScene(self.data)

class ListCard(CardFrame):
    def __init__(self, main_window, data):
        super().__init__()
        self.mw = main_window
        self.data = data
        self.title = self.data.get('title')

        self.initUI()
        #self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

    def initUI(self):
        card_layout = QHBoxLayout()

        self.image_label = QLabel()
        self.image_label.setFixedSize(110, 140)
        card_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.mw.image_loader.load(self.data.get("background_image_url"), 110, 140, 4,
                                  label=self.image_label, cache_dir="cache/scenes")

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(text_layout)

        title_label = QLabel(self.title)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        if self.data.get('description'):
            description_label = QLabel(format_text(self.data.get('description')))
            description_label.setWordWrap(True)
            description_label.setStyleSheet("color: #a2a2ac;")
            font = description_label.font()
            font.setPointSize(9)
            description_label.setFont(font)
            fm = QFontMetrics(font)
            description_label.setMaximumHeight(fm.lineSpacing() * 3)
            text_layout.addWidget(description_label)
            self.setToolTip(format_text(self.data.get('title')))

        if self.data.get('creator_username') == self.mw.username:
            edit_button = PushButton(self.tr("Edit"))
            edit_button.clicked.connect(lambda: self.mw.openCreateScenePage(self.data.get('scene_id')))
            card_layout.addWidget(edit_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(card_layout)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openScene(self.data)

class MainPage(QWidget):
    def __init__(self, main_window, data={}, scene_id=None):
        super().__init__()
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.chat_thread = self.mw.chat_thread
        self.data = data
        self.scene_id = scene_id
        if self.data:
            self.scene_id = self.data['scene_id']
        else:
            self.chat_thread.get_scene_by_id_signal.connect(self._getScene)
            self.chat_thread.get_scene_by_id(self.scene_id)

        self.current_character = None
        self.current_card = None
        self.character_cards = []

        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.initUI()
        if self.data:
            self.loadUI()

    def initUI(self):
        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        fhs_page = VerticalScrollPage()
        fhs_page.setStyleSheet("background-color: transparent; border: none;")
        fhs_page.setFixedWidth(600)
        fhs_layout = fhs_page.layout

        self.image_label = QLabel()
        self.image_label.setFixedSize(290, 260)
        fhs_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel()
        hg_font = self.title_label.font()
        hg_font.setPointSize(13)
        self.title_label.setFont(hg_font)
        self.title_label.setWordWrap(True)
        fhs_layout.addWidget(self.title_label)

        self.author_label = QLabel()
        self.author_label.setStyleSheet("color: #a2a2ac;")
        font = self.author_label.font()
        font.setPointSize(8)
        self.author_label.setFont(font)
        self.author_label.setWordWrap(True)
        fhs_layout.addWidget(self.author_label)

        self.description_label = QLabel("")
        self.description_label.setStyleSheet("color: #a2a2ac;")
        font = self.description_label.font()
        font.setBold(True)
        font.setPointSize(11)
        self.author_label.setFont(font)
        self.description_label.setWordWrap(True)
        fhs_layout.addWidget(self.description_label)

        fhs_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))

        self.simchars_label = QLabel(self.tr("Select character"))
        self.simchars_label.setFont(hg_font)
        fhs_layout.addWidget(self.simchars_label)

        selchar_page = VerticalScrollPage()
        self.selchar_layout = selchar_page.layout
        fhs_layout.addWidget(selchar_page)

        self.start_button = PushButton(self.tr("Start the scene"))
        self.start_button.clicked.connect(self.startScene)
        self.start_button.setEnabled(False)
        fhs_layout.addWidget(self.start_button, 0, Qt.AlignmentFlag.AlignHCenter)

        main_layout.addWidget(fhs_page)
        self.setLayout(main_layout)

    def loadUI(self):
        self.mw.image_loader.load(
            self.data.get("background_image_url"), 290, 260, 4,
            label=self.image_label, cache_dir="cache/scenes")
        self.title_label.setText(self.data.get("title"))
        self.author_label.setText(self.tr("Author: @") + self.data.get("creator_username"))
        self.author_label.mousePressEvent = lambda _: self.mw.openUserPage(self.data.get("creator_username"))
        self.author_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.description_label.setText(format_text(self.data.get('description')))
        self.description_label.adjustSize()

        for char in self.mw.recent_chats:
            card = ClickableMiniCard(self.mw, char.get('character_name'), char.get('character_id'), char.get('character_avatar_uri'))
            card.setFixedHeight(80)
            card.mousePress = lambda _, c=card: self._selCharacter(c)
            card.chat_id = char['chat_id']
            self.selchar_layout.addWidget(card)
            self.character_cards.append(card)

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(0)
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def _getScene(self, response):
        self.chat_thread.get_scene_by_id_signal.disconnect()
        self.data = response
        self.loadUI()

    def _selCharacter(self, card):
        for c in self.character_cards:
            c.setCheckable(False)

        card.setCheckable(True)

        self.current_card = card
        self.current_character = card.character_id
        self.start_button.setEnabled(True)

    def startScene(self):
        self.chat_thread.new_chat_created_signal.connect(self._createNewChat)
        self.chat_thread.new_chat(self.current_character, self.current_card.chat_id, scene_id=self.scene_id)

    def _createNewChat(self, botanswer):
        self.chat_thread.new_chat_created_signal.disconnect()
        self.mw.openChat(self.current_character, self.current_card.name, botanswer['chat']['chat_id'], scene_id=self.scene_id)

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.deleteLater()