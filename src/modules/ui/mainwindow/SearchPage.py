from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from modules import ChatThread, Svg
from modules.logic.QThreads import DiscordRPCThread
from modules.ui import TM
from modules.ui.cards import CharacterCards, SceneCards, UserCards
from modules.ui.Elements import (
    SearchLineEdit,
    SortComboBox,
    TabButton,
    VerticalScrollPage,
)
from modules.Utils import sort_items


class SearchPage(QWidget):
    def __init__(self, main_window, search="character"):
        super().__init__(main_window)
        self.mw = main_window
        self.search = search
        self.chat_thread: ChatThread | None = self.mw.chat_thread
        self.discord_thread: DiscordRPCThread | None = self.mw.discord_thread
        self.svg_icons = Svg()
        self.setStyleSheet("background-color: transparent; border: none;")
        self.raw_char_data = []
        self.raw_scene_data = []
        self.raw_user_data = []

        self.initUI()
        if self.mw.drpc_enable and self.mw.drpc_show_current_page:
            self.discord_thread.update(details=self.tr("Search characters..."))

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)
        self.chars_scroll_area, cards_viewport, self.chars_cards_layout = (
            self.createScrollPage()
        )
        self.stacked_widget.addWidget(self.chars_scroll_area)
        self.scenes_scroll_area, cards_viewport, self.scenes_cards_layout = (
            self.createScrollPage()
        )
        self.stacked_widget.addWidget(self.scenes_scroll_area)
        self.users_scroll_area, cards_viewport, self.users_cards_layout = (
            self.createScrollPage()
        )
        self.stacked_widget.addWidget(self.users_scroll_area)

        self.layout.addWidget(
            self.stacked_widget, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.setLayout(self.layout)

        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.mw.top_bar_stacked_widget.setFixedHeight(70)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def changeSearch(self, search):
        self.search = search
        if search == "character":
            self.stacked_widget.setCurrentWidget(self.chars_scroll_area)
            self.search_bar.returnPressed.disconnect()
            self.search_bar.returnPressed.connect(self.showCharSearchResults)
            self.showCharSearchResults()
        elif search == "scene":
            self.stacked_widget.setCurrentWidget(self.scenes_scroll_area)
            self.search_bar.returnPressed.disconnect()
            self.search_bar.returnPressed.connect(self.showSceneSearchResults)
            self.showSceneSearchResults()
        elif search == "user":
            self.stacked_widget.setCurrentWidget(self.users_scroll_area)
            self.search_bar.returnPressed.disconnect()
            self.search_bar.returnPressed.connect(self.showUserSearchResults)
            self.showUserSearchResults()

    def createScrollPage(self):
        scroll_page = VerticalScrollPage()
        scroll_page.setFixedWidth(700)
        scroll_viewport = scroll_page.viewport
        scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        return scroll_page, scroll_viewport, scroll_layout

    def on_sort_changed(self):
        if self.search == "character" and self.raw_char_data:
            self.renderCharacters(self.raw_char_data)
        elif self.search == "scene" and self.raw_scene_data:
            self.renderScenes(self.raw_scene_data)
        elif self.search == "user" and self.raw_user_data:
            self.renderUsers(self.raw_user_data)

    def showCharSearchResults(self):
        search_query = self.search_bar.text().strip()
        if not search_query:
            return

        self.chars_scroll_area.deleteLater()
        self.chars_scroll_area, cards_viewport, self.chars_cards_layout = (
            self.createScrollPage()
        )
        self.stacked_widget.addWidget(self.chars_scroll_area)
        self.stacked_widget.setCurrentWidget(self.chars_scroll_area)

        self.chat_thread.character_search_signal.connect(self.characterPopulate)
        self.chat_thread.character_search(search_query)

    def characterPopulate(self, data):
        self.chat_thread.character_search_signal.disconnect()
        self.raw_char_data = data or []
        self.renderCharacters(self.raw_char_data)

    def renderCharacters(self, data):
        while self.chars_cards_layout.count():
            item = self.chars_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sort_mode = self.sort_box.currentData() if hasattr(self, "sort_box") else "default"
        sorted_data = sort_items(data, sort_mode)

        if sorted_data:
            for character in sorted_data:
                card = CharacterCards.MainCard(
                    self.mw,
                    character.get("participant__name"),
                    character.get("avatar_file_name"),
                    character.get("title", "").replace("\n", ""),
                    character.get("user__username"),
                    character.get("external_id"),
                    character.get("participant__num_interactions", 0),
                    0,
                    70,
                    70,
                )
                card.setFixedHeight(87)
                self.chars_cards_layout.addWidget(card)
        else:
            no_results_label = QLabel(self.tr("Characters not found"))
            font = no_results_label.font()
            font.setBold(True)
            font.setPointSize(20)
            no_results_label.setFont(font)
            self.chars_cards_layout.addWidget(
                no_results_label, alignment=Qt.AlignmentFlag.AlignHCenter
            )

    def showSceneSearchResults(self):
        search_query = self.search_bar.text().strip()
        if not search_query:
            return

        self.scenes_scroll_area.deleteLater()
        self.scenes_scroll_area, cards_viewport, self.scenes_cards_layout = (
            self.createScrollPage()
        )
        self.stacked_widget.addWidget(self.scenes_scroll_area)
        self.stacked_widget.setCurrentWidget(self.scenes_scroll_area)

        self.chat_thread.scene_search_signal.connect(self.scenePopulate)
        self.chat_thread.scene_search(search_query)

    def scenePopulate(self, data):
        self.chat_thread.scene_search_signal.disconnect()
        self.raw_scene_data = data or []
        self.renderScenes(self.raw_scene_data)

    def renderScenes(self, data):
        while self.scenes_cards_layout.count():
            item = self.scenes_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sort_mode = self.sort_box.currentData() if hasattr(self, "sort_box") else "default"
        sorted_data = sort_items(data, sort_mode)

        if sorted_data:
            for scene in sorted_data:
                card = SceneCards.ListCard(self.mw, scene)
                card.setFixedHeight(140)
                self.scenes_cards_layout.addWidget(card)
        else:
            no_results_label = QLabel(self.tr("Scenes not found"))
            font = no_results_label.font()
            font.setBold(True)
            font.setPointSize(20)
            no_results_label.setFont(font)
            self.scenes_cards_layout.addWidget(
                no_results_label, alignment=Qt.AlignmentFlag.AlignHCenter
            )

    def showUserSearchResults(self):
        search_query = self.search_bar.text().strip()
        if not search_query:
            return

        self.users_scroll_area.deleteLater()
        self.users_scroll_area, cards_viewport, self.users_cards_layout = (
            self.createScrollPage()
        )
        self.stacked_widget.addWidget(self.users_scroll_area)
        self.stacked_widget.setCurrentWidget(self.users_scroll_area)

        self.chat_thread.user_search_signal.connect(self.userPopulate)
        self.chat_thread.user_search(search_query)

    def userPopulate(self, data):
        self.chat_thread.user_search_signal.disconnect()
        self.raw_user_data = data or []
        self.renderUsers(self.raw_user_data)

    def renderUsers(self, data):
        while self.users_cards_layout.count():
            item = self.users_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sort_mode = self.sort_box.currentData() if hasattr(self, "sort_box") else "default"
        sorted_data = sort_items(data, sort_mode)

        if sorted_data:
            for user in sorted_data:
                card = UserCards.ListCard(self.mw, user)
                card.setFixedHeight(87)
                self.users_cards_layout.addWidget(card)
        else:
            no_results_label = QLabel(self.tr("Users not found"))
            font = no_results_label.font()
            font.setBold(True)
            font.setPointSize(20)
            no_results_label.setFont(font)
            self.users_cards_layout.addWidget(
                no_results_label, alignment=Qt.AlignmentFlag.AlignHCenter
            )

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(70)
        top_bar_layout = QVBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar.setLayout(top_bar_layout)

        self.search_bar = SearchLineEdit(self.mw)
        self.search_bar.blockSignals(True)
        self.search_bar.setIcon(QIcon(self.svg_icons.search(TM.c("icon"))))
        self.search_bar.setText(self.mw.search_bar.text())
        self.search_bar.setPlaceholderText(self.tr("Search"))
        self.search_bar.returnPressed.connect(self.showCharSearchResults)
        top_bar_layout.addWidget(self.search_bar, alignment=Qt.AlignmentFlag.AlignTop)
        self.search_bar.blockSignals(False)

        tab_frame = QWidget()
        tab_frame.setFixedWidth(700)
        self.tab_layout = QHBoxLayout(tab_frame)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)

        self.character_tab_button = TabButton(self.tr("Characters"))
        self.character_tab_button.clicked.connect(
            lambda: self.scene_tab_button.setChecked(False)
        )
        self.character_tab_button.clicked.connect(
            lambda: self.user_tab_button.setChecked(False)
        )
        self.character_tab_button.clicked.connect(
            lambda: self.changeSearch("character")
        )
        self.tab_layout.addWidget(self.character_tab_button)
        self.user_tab_button = TabButton(self.tr("Users"))
        self.user_tab_button.clicked.connect(
            lambda: self.character_tab_button.setChecked(False)
        )
        self.user_tab_button.clicked.connect(
            lambda: self.scene_tab_button.setChecked(False)
        )
        self.user_tab_button.clicked.connect(lambda: self.changeSearch("user"))
        self.tab_layout.addWidget(self.user_tab_button)
        self.scene_tab_button = TabButton(self.tr("Scenes"))
        self.scene_tab_button.clicked.connect(
            lambda: self.character_tab_button.setChecked(False)
        )
        self.scene_tab_button.clicked.connect(
            lambda: self.user_tab_button.setChecked(False)
        )
        self.scene_tab_button.clicked.connect(lambda: self.changeSearch("scene"))
        self.tab_layout.addWidget(self.scene_tab_button)

        self.tab_layout.addStretch()

        self.sort_box = SortComboBox(self, include_likes=False)
        self.sort_box.setFixedWidth(160)
        self.sort_box.currentIndexChanged.connect(self.on_sort_changed)
        self.tab_layout.addWidget(self.sort_box)

        if self.search == "character":
            self.character_tab_button.setChecked(True)
            self.stacked_widget.setCurrentWidget(self.chars_scroll_area)
        elif self.search == "scene":
            self.character_tab_button.setChecked(True)
            self.stacked_widget.setCurrentWidget(self.scenes_scroll_area)
        elif self.search == "user":
            self.user_tab_button.setChecked(True)
            self.stacked_widget.setCurrentWidget(self.users_scroll_area)

        top_bar_layout.addWidget(tab_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        return top_bar, top_bar_layout

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.deleteLater()
