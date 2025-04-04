from PyQt6.QtWidgets import (
    QApplication, QColorDialog,
    QWidget, QHBoxLayout,
    QVBoxLayout,QLabel,
    QPushButton, QMenu,
    QScrollArea, QFrame,
    QSizePolicy, QSpacerItem)
from PyQt6.QtGui import QMouseEvent, QAction
from PyQt6.QtCore import (
    QPropertyAnimation,
    QEasingCurve, QRect,
    QSettings, QTimer)
from datetime import datetime

from modules.QCustom import ClickableFrame, CustomTextEdit
from modules.QThreads import (
    PlayerThread, FileLoaderThread,
    ImageLoaderThread)
from modules.styles import *
from modules.Voice import VoiceMode, VoiceSearch

class MessageBubble(QFrame):
    def __init__(self, mw, parent, text, is_user=False):
        super().__init__()
        self.main_window = mw
        self.parent = parent
        self.is_user = is_user
        layout = QVBoxLayout()
        self.turn_id = None
        self.message_label = QLabel(text)
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(int(parent.width()/2.25))

        layout.addWidget(self.message_label)
        self.setLayout(layout)
        self.adjustSize()
        self.setMinimumHeight(self.height())

class ChatInterface(QWidget):
    def __init__(self, main_window, character_name, character_id, chat_id: str | None = None):
        super().__init__()
        self.mw = main_window
        self.character_name = character_name
        self.character_id = character_id
        self.chat_id = chat_id
        self.character = None
        self.cis_visible = False
        self.voice_id = None
        self.svg_icons = SvgIcons()

        self.voice_enabled = False

        self.chat_settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Emilia", self.character_id)
        self.char_back_message = self.chat_settings.value('colors/char_back_message', '#26272b')
        self.char_text_message = self.chat_settings.value('colors/char_text_message', '#e8eaed')
        self.user_back_message = self.chat_settings.value('colors/user_back_message', '#303136')
        self.user_text_message = self.chat_settings.value('colors/user_text_message', '#e8eaed')

        self.available_models = {
            "MODEL_TYPE_FAST": {
                "name": self.tr("Meow"),
                "description": self.tr("Quick wits, faster words"),
                "plus": False,
                "beta": False
            },
            "MODEL_TYPE_BALANCED": {
                "name": self.tr("Roar"),
                "description": self.tr("Mix of speed & smarts"),
                "plus": False,
                "beta": False
            },
            "MODEL_TYPE_SMART": {
                "name": self.tr("Nyan"),
                "description": self.tr("Smart and more thoughtful"),
                "plus": True,
                "beta": False
            },
            "MODEL_TYPE_FAMILY_FRIENDLY": {
                "name": self.tr("Goro"),
                "description": self.tr("Less spicy"),
                "plus": False,
                "beta": True
            }
        }
        self.messages = []

        self.initUI()
        self.createRightSidebar()

        # self.mw.chat_thread.message_signal.connect(lambda message: self.addMessage(message['candidates'][0]['raw_content'], message['turn_key']['turn_id'], is_user=False))
        self.mw.chat_thread.message_signal.connect(self.charMessageSignal)
        self.mw.chat_thread.user_message_signal.connect(self.userMessageSignal)

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.top_bar_frame, self.top_bar_layout = self.createTopBar()
        self.mw.top_bar_stacked_widget.setFixedHeight(75)
        self.mw.t_bar.setStyleSheet(top_bar_style())
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar_frame)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar_frame)

        main_area_layout = QHBoxLayout()

        self.messages_area = QScrollArea()
        self.messages_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setStyleSheet(scroll_style())
        self.messages_area.verticalScrollBar().rangeChanged.connect(self.scrollToBottomIfNeeded)
        self.messages_content = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_content)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_area.setWidget(self.messages_content)
        main_area_layout.addWidget(self.messages_area)

        self.layout.addLayout(main_area_layout)

        input_widget = QWidget()
        input_layout = QHBoxLayout()
        input_widget.setLayout(input_layout)
        self.message_input = CustomTextEdit()
        self.message_input.setFixedHeight(32)
        self.message_input.horizontalScrollBar().setVisible(False)
        self.message_input.verticalScrollBar().setVisible(False)
        self.message_input.textChanged.connect(self.startFormat)
        self.message_input.setStyleSheet(lineedit_style())
        self.message_input.keyPress = lambda: self.sendMessage()
        self.format_timer = QTimer()
        self.format_timer.setSingleShot(True)
        self.format_timer.timeout.connect(self.formatUserMessage)
        input_layout.addWidget(self.message_input, alignment=Qt.AlignmentFlag.AlignBottom)
        send_button = QPushButton()
        send_button.setIcon(self.svg_icons.send())
        send_button.setStyleSheet(icon_button_style())
        send_button.clicked.connect(self.sendMessage)
        input_layout.addWidget(send_button, alignment=Qt.AlignmentFlag.AlignBottom)
        call_button = QPushButton()
        call_button.setIcon(self.svg_icons.call())
        call_button.setStyleSheet(icon_button_style())
        call_button.clicked.connect(self.callCharacter)
        input_layout.addWidget(call_button, alignment=Qt.AlignmentFlag.AlignBottom)
        self.layout.addWidget(input_widget)

        self.setLayout(self.layout)

        if self.chat_id:
            self.mw.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
            self.mw.chat_thread.get_chat_by_id_signal.connect(self._getChatById)
            self.mw.chat_thread.get_history(self.chat_id)
            self.mw.chat_thread.get_chat_by_id(self.chat_id)
        else:
            self.mw.chat_thread.chat_signal.connect(self._getChat)
            self.mw.chat_thread.get_chat(self.character_id)

        if not self.character:
            self.mw.chat_thread.get_char_signal.connect(self._getCharacter)
            self.mw.chat_thread.get_character(self.character_id)
        self.mw.chat_thread.voice_override_signal.connect(self._voiceOverride)
        self.mw.chat_thread.voice_override(self.character_id)

    def createTopBar(self):
        header_frame = QWidget()
        header_frame.hideEvent = lambda event: self.mw.t_bar.setStyleSheet(None)
        header_frame.setFixedHeight(75)
        header_layout = QHBoxLayout()

        self.header_character_frame = QWidget()
        header_layout.addWidget(self.header_character_frame)
        self.header_character_frame.setVisible(False)
        header_character_layout = QHBoxLayout()
        self.header_character_frame.setLayout(header_character_layout)

        self.header_avatar_label = QLabel()
        self.header_avatar_label.setFixedSize(40, 40)
        header_character_layout.addWidget(self.header_avatar_label)

        header_char_text_layout = QVBoxLayout()
        header_char_text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_character_layout.addLayout(header_char_text_layout)
        self.header_name_label = QLabel()
        header_char_text_layout.addWidget(self.header_name_label)
        self.header_author_label = QLabel()
        header_char_text_layout.addWidget(self.header_author_label)

        header_layout.addStretch(1)

        self.toggle_info_button = QPushButton()
        self.toggle_info_button.setIcon(self.svg_icons.show_right_sidebar())
        self.toggle_info_button.setStyleSheet(icon_button_style())
        self.toggle_info_button.clicked.connect(self.toggleCharacterInfoSidebar)
        self.toggle_info_button.setEnabled(False)
        header_layout.addWidget(self.toggle_info_button)

        header_frame.setLayout(header_layout)
        return header_frame, header_layout

    def createRightSidebar(self):
        self.character_info_sidebar = QFrame(self)
        self.character_info_sidebar.setFixedWidth(230)
        self.character_info_sidebar.setFixedHeight(self.mw.height() - 230)
        self.character_info_sidebar.setStyleSheet(character_info_sidebar_style())
        self.char_info_layout = QVBoxLayout()
        self.character_info_sidebar.setLayout(self.char_info_layout)
        self.char_info_layout.setContentsMargins(10, 10, 10, 10)
        self.character_info_sidebar.setVisible(False)

        main_info_about_char_frame = QFrame()
        self.char_info_layout.addWidget(main_info_about_char_frame)
        self.char_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_info_about_char_layout = QHBoxLayout()
        main_info_about_char_frame.setLayout(main_info_about_char_layout)

        text_info_about_char = QVBoxLayout()
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(70, 70)
        main_info_about_char_layout.addWidget(self.avatar_label, 0, Qt.AlignmentFlag.AlignLeft)

        main_info_about_char_layout.addLayout(text_info_about_char)
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        text_info_about_char.addWidget(self.name_label, 0, Qt.AlignmentFlag.AlignLeft)
        self.author_label = QLabel()
        self.author_label.setWordWrap(True)
        text_info_about_char.addWidget(self.author_label, 0, Qt.AlignmentFlag.AlignLeft)
        self.chats_label = QLabel()
        self.chats_label.setWordWrap(True)
        text_info_about_char.addWidget(self.chats_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.social_buttons_frame = QFrame()
        self.char_info_layout.addWidget(self.social_buttons_frame)
        social_buttons_layout = QHBoxLayout()
        self.social_buttons_frame.setLayout(social_buttons_layout)

        share_char_button = QPushButton()
        share_char_button.setStyleSheet(icon_button_style())
        share_char_button.setIcon(self.svg_icons.share())
        share_char_button.clicked.connect(self.shareCharacter)
        social_buttons_layout.addWidget(share_char_button, 1, Qt.AlignmentFlag.AlignLeft)

        self.like_button = QPushButton()
        self.like_button.setIcon(self.svg_icons.like())
        self.like_button.setStyleSheet(icon_button_style())
        self.like_button.clicked.connect(self.likeCharacter)
        social_buttons_layout.addWidget(self.like_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.dislike_button = QPushButton()
        self.dislike_button.setIcon(self.svg_icons.dislike())
        self.dislike_button.setStyleSheet(icon_button_style())
        self.dislike_button.clicked.connect(self.dislikeCharacter)
        social_buttons_layout.addWidget(self.dislike_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.char_info_layout.addWidget(self.title_label)

        self.create_new_chat_button = QPushButton(self.tr("New Chat"))
        self.create_new_chat_button.setIcon(self.svg_icons.new_chat())
        self.create_new_chat_button.setStyleSheet(button_style())
        self.create_new_chat_button.clicked.connect(self.createNewChat)
        self.char_info_layout.addWidget(self.create_new_chat_button, alignment=Qt.AlignmentFlag.AlignLeft)

        character_voice_button_layout = QHBoxLayout()
        character_voice_button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.char_info_layout.addLayout(character_voice_button_layout)
        self.enable_char_voice_button = QPushButton()
        self.enable_char_voice_button.setIcon(self.svg_icons.no_voice())
        self.enable_char_voice_button.clicked.connect(self.enableVoice)
        self.enable_char_voice_button.setStyleSheet(icon_button_style())
        character_voice_button_layout.addWidget(self.enable_char_voice_button)

        self.select_char_voice_button = QPushButton(self.tr("Voice"))
        self.select_char_voice_button.clicked.connect(self.searchVoice)
        self.select_char_voice_button.setStyleSheet(button_style())
        character_voice_button_layout.addWidget(self.select_char_voice_button)

        self.select_char_voice_label = QLabel()
        character_voice_button_layout.addWidget(self.select_char_voice_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.history_button = QPushButton(self.tr("History"))
        self.history_button.setIcon(self.svg_icons.history())
        self.history_button.setStyleSheet(button_style())
        self.history_button.clicked.connect(self.showChats)
        self.char_info_layout.addWidget(self.history_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.chat_theme_button = QPushButton(self.tr("Chat Theme"))
        self.chat_theme_button.setIcon(self.svg_icons.colors())
        self.chat_theme_button.setStyleSheet(button_style())
        self.chat_theme_button.clicked.connect(self.openColorPickerOverlay)
        self.char_info_layout.addWidget(self.chat_theme_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # self.greeting_title = QLabel()
        # self.greeting_title.setWordWrap(True)
        # self.char_info_layout.addWidget(self.greeting_title, alignment=Qt.AlignmentFlag.AlignBottom)

        self.chat_style_button = QPushButton(self.tr("Chat Style"))
        self.chat_style_button.setIcon(self.svg_icons.style())
        self.chat_style_button.setStyleSheet(button_style())
        self.chat_style_button.clicked.connect(self.openModelOverlay)
        self.char_info_layout.addWidget(self.chat_style_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.character_info_sidebar.setGeometry(self.width(), 0, 230, self.height() - 230)

    def userMessageSignal(self, response):
        message = next((x for x in reversed(self.messages) if x.is_user), None)
        message.turn_id = response['turn']['turn_key']['turn_id']
        message.customContextMenuRequested.disconnect()
        message.customContextMenuRequested.connect(lambda pos, mb=message: self.showContextMenu(pos, mb))

    def charMessageSignal(self, response):
        command = response['command']
        if command == 'add_turn':
            self.addMessage(format_text(response['turn']['candidates'][0]['raw_content'], self.mw.username), response['turn']['turn_key']['turn_id'],is_user=False)
        elif command == 'update_turn':
            message = next((x for x in reversed(self.messages) if x.turn_id == response['turn']['turn_key']['turn_id']), None)
            message.message_label.setText(format_text(response['turn']['candidates'][0]['raw_content'], self.mw.username))
            message.adjustSize()
            message.setMinimumHeight(message.message_label.height() + 15)

    def openModelOverlay(self):
        overlay_widget = QWidget()
        overlay_widget.setFixedWidth(350)
        overlay_widget.setFixedHeight(450)
        overlay_layout = QVBoxLayout()
        overlay_widget.setLayout(overlay_layout)

        choose_label = QLabel(self.tr("Choose a model to influence the style of your chat"))
        overlay_layout.addWidget(choose_label, alignment=Qt.AlignmentFlag.AlignLeft)

        f_page = QWidget()
        f_page_layout = QVBoxLayout(f_page)
        f_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        f_page.setLayout(f_page_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(scroll_style())

        models_widget = QWidget()
        models_widget.setStyleSheet("background-color: transparent; border: none;")
        models_layout = QVBoxLayout()
        models_layout.setContentsMargins(10, 10, 10, 10)
        models_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        models_widget.setLayout(models_layout)
        overlay_layout.addWidget(f_page)

        scroll_area.setWidget(models_widget)
        f_page_layout.addWidget(scroll_area)

        card_list = []
        self.overlay_selected_model_type = self.preferred_model_type
        def createCard(model_type, name, icon, description, plus, beta):
            card = ClickableFrame()
            card.setObjectName(model_type)
            card.default_style = card_style()
            card.press_style = card_pressed_style()
            card.setStyleSheet(card_style())
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.mousePress = lambda: onCardClicked(card)

            card_layout = QHBoxLayout()

            icon_label = QLabel()
            icon_label.setPixmap(icon)
            icon_label.setFixedSize(40, 40)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(icon_label)

            text_layout = QVBoxLayout()
            text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            card_layout.addLayout(text_layout, 1)

            name_label = QLabel(name)
            name_label.setWordWrap(True)
            name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            text_layout.addWidget(name_label)

            description_label = QLabel(description)
            description_label.setFont(QFont("Arial", 9))
            description_label.setWordWrap(True)
            description_label.setStyleSheet("color: #a2a2ac")
            text_layout.addWidget(description_label)

            card_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))

            if plus:
                plus_label = QLabel("C.AI+")
                card_layout.addWidget(plus_label)
            elif beta:
                beta_label = QLabel()
                beta_label.setPixmap(self.svg_icons.beta(pixmap_ret=True))
                card_layout.addWidget(beta_label)

            card.setLayout(card_layout)
            return card

        def onCardClicked(clicked_card: ClickableFrame):
            for c in card_list:
                c.setStyleSheet(c.default_style)
            clicked_card.setStyleSheet(clicked_card.press_style)
            self.overlay_selected_model_type = clicked_card.objectName()

            if self.overlay_selected_model_type == self.preferred_model_type:
                apply_button.setText(self.tr("Continue chat"))
            else:
                apply_button.setText(self.tr("Start new chat"))

        for model_type in self.mw.available_models:
            card = createCard(model_type,
                              self.available_models.get(model_type).get('name'),
                              self.svg_icons.model_type_icon(model_type, pixmap_ret=True),
                              self.available_models.get(model_type).get('description'),
                              self.available_models.get(model_type).get('plus'),
                              self.available_models.get(model_type).get('beta'))
            # card.mousePress = lambda: onCardClicked(card)
            if model_type == self.preferred_model_type: card.setCheckable(True)
            models_layout.addWidget(card)
            card_list.append(card)

        def apply():
            if self.overlay_selected_model_type != self.preferred_model_type:
                self.createNewChat(self.overlay_selected_model_type)
            self.mw.hideOverlay()
            self.hideCharacterInfoSidebar()

        buttons_layout = QHBoxLayout()

        apply_button = QPushButton(self.tr("Continue chat"))
        apply_button.setStyleSheet(button_style())
        apply_button.clicked.connect(apply)
        buttons_layout.addWidget(apply_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ufac_layout = QHBoxLayout()
        # ufac_label = QLabel(self.tr("Use for all chats"))
        # ufac_layout.addWidget(ufac_label)
        # ufac_button = CheckablePushButton()
        # ufac_layout.addStretch(1)
        # ufac_layout.addWidget(ufac_button)

        overlay_layout.addLayout(buttons_layout)
        self.mw.showOverlay(overlay_widget)
        pass

    def openColorPickerOverlay(self):
        color_picker_widget = QWidget()
        color_picker_widget.setFixedWidth(250)
        color_picker_widget.setFixedHeight(200)
        color_picker_layout = QVBoxLayout()
        color_picker_widget.setLayout(color_picker_layout)

        color_pickers_frame = QWidget()
        color_pickers_layout = QVBoxLayout()
        color_pickers_frame.setLayout(color_pickers_layout)

        char_text_message_layout = QHBoxLayout()
        char_text_message_label = QLabel(self.tr("Character Text Color:"))
        self.char_text_message_picker = QPushButton()
        self.char_text_message_picker.setStyleSheet(f"background-color: {self.char_text_message};")
        self.char_text_message_picker.clicked.connect(self.pickCharTextMessageColor)
        char_text_message_layout.addWidget(char_text_message_label, alignment=Qt.AlignmentFlag.AlignLeft)
        char_text_message_layout.addWidget(self.char_text_message_picker, alignment=Qt.AlignmentFlag.AlignRight)
        color_pickers_layout.addLayout(char_text_message_layout)

        char_back_message_layout = QHBoxLayout()
        char_back_message_label = QLabel(self.tr("Character Background Color:"))
        self.char_back_message_picker = QPushButton()
        self.char_back_message_picker.setStyleSheet(f"background-color: {self.char_back_message};")
        self.char_back_message_picker.clicked.connect(self.pickCharBackMessageColor)
        char_back_message_layout.addWidget(char_back_message_label, alignment=Qt.AlignmentFlag.AlignLeft)
        char_back_message_layout.addWidget(self.char_back_message_picker, alignment=Qt.AlignmentFlag.AlignRight)
        color_pickers_layout.addLayout(char_back_message_layout)

        user_text_message_layout = QHBoxLayout()
        user_text_message_label = QLabel(self.tr("User Text Color:"))
        self.user_text_message_picker = QPushButton()
        self.user_text_message_picker.setStyleSheet(f"background-color: {self.user_text_message};")
        self.user_text_message_picker.clicked.connect(self.pickUserTextMessageColor)
        user_text_message_layout.addWidget(user_text_message_label, alignment=Qt.AlignmentFlag.AlignLeft)
        user_text_message_layout.addWidget(self.user_text_message_picker, alignment=Qt.AlignmentFlag.AlignRight)
        color_pickers_layout.addLayout(user_text_message_layout)

        user_back_message_layout = QHBoxLayout()
        user_back_message_label = QLabel(self.tr("User Background Color:"))
        self.user_back_message_picker = QPushButton()
        self.user_back_message_picker.setStyleSheet(f"background-color: {self.user_back_message};")
        self.user_back_message_picker.clicked.connect(self.pickUserBackMessageColor)
        user_back_message_layout.addWidget(user_back_message_label, alignment=Qt.AlignmentFlag.AlignLeft)
        user_back_message_layout.addWidget(self.user_back_message_picker, alignment=Qt.AlignmentFlag.AlignRight)
        color_pickers_layout.addLayout(user_back_message_layout)
        color_picker_layout.addWidget(color_pickers_frame, alignment=Qt.AlignmentFlag.AlignTop)

        buttons_layout = QHBoxLayout()
        apply_button = QPushButton(self.tr("Apply"))
        apply_button.setStyleSheet(button_style())
        apply_button.clicked.connect(self.applyColors)
        buttons_layout.addWidget(apply_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        restore_button = QPushButton(self.tr("Restore"))
        restore_button.setStyleSheet(button_style())
        restore_button.clicked.connect(self.restoreDefaultColors)
        buttons_layout.addWidget(restore_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        color_picker_layout.addLayout(buttons_layout)

        self.mw.showOverlay(color_picker_widget)

    def restoreDefaultColors(self):
        data = {
            "char_back_message": "#26272b",
            "char_text_message": "#e8eaed",
            "user_back_message": "#303136",
            "user_text_message": "#e8eaed"
        }
        for key, value in data.items():
            self.chat_settings.setValue(f"colors/{key}", value)
            setattr(self, key, value)
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item.widget():
                if item.widget().objectName() == 'user_message':
                    self.setBackMessageColor(item.widget(), self.user_back_message)
                    self.setTextMessageColor(item.widget(), self.user_text_message)
                elif item.widget().objectName() == 'char_message':
                    self.setBackMessageColor(item.widget(), self.char_back_message)
                    self.setTextMessageColor(item.widget(), self.char_text_message)
        self.mw.hideOverlay()

    def pickCharBackMessageColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.char_back_message_picker.setStyleSheet(f"background-color: {color.name()};")

    def pickCharTextMessageColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.char_text_message_picker.setStyleSheet(f"background-color: {color.name()};")

    def pickUserBackMessageColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.user_back_message_picker.setStyleSheet(f"background-color: {color.name()};")

    def pickUserTextMessageColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.user_text_message_picker.setStyleSheet(f"background-color: {color.name()};")

    def applyColors(self):
        self.char_back_message = self.char_back_message_picker.styleSheet().split(": ")[1][:-1]
        self.char_text_message = self.char_text_message_picker.styleSheet().split(": ")[1][:-1]
        self.user_back_message = self.user_back_message_picker.styleSheet().split(": ")[1][:-1]
        self.user_text_message = self.user_text_message_picker.styleSheet().split(": ")[1][:-1]
        data = {
            'char_back_message': self.char_back_message,
            'char_text_message': self.char_text_message,
            'user_back_message': self.user_back_message,
            'user_text_message': self.user_text_message
        }
        for key, value in data.items():
            self.chat_settings.setValue(f"colors/{key}", value)
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item.widget():
                if item.widget().objectName() == 'user_message':
                    self.setBackMessageColor(item.widget(), self.user_back_message)
                    self.setTextMessageColor(item.widget(), self.user_text_message)
                elif item.widget().objectName() == 'char_message':
                    self.setBackMessageColor(item.widget(), self.char_back_message)
                    self.setTextMessageColor(item.widget(), self.char_text_message)
        self.mw.hideOverlay()

    def startFormat(self):
        text = self.message_input.toPlainText()
        line_count = text.count('\n')
        line_count += text.count('<br>') + 1 if text else 1
        height = line_count * self.message_input.fontMetrics().lineSpacing() + 16
        self.message_input.setFixedHeight(height)
        self.format_timer.start(500)

    def formatUserMessage(self):
        self.message_input.blockSignals(True)
        text = self.message_input.toPlainText()
        cursor = self.message_input.textCursor()
        position = cursor.position()
        replacements = [
            (r"`(.*?)`", r'<span style="color: gray;">`<code>\1</code>`</span>'),
            (r"\*\*\*(.*?)\*\*\*", r'<span style="color: gray;">***<b><i>\1</i></b>***</span>'),
            (r"\*\*(.*?)\*\*", r'<span style="color: gray;">**<b>\1</b>**</span>'),
            (r"\*(.*?)\*", r'<span style="color: gray;">*<i>\1</i>*</span>'),
            ("\n", "<br>"),
        ]

        for pattern, replacement, *flags in replacements:
            text = re.sub(pattern, replacement, text, flags=flags[0] if flags else 0)
        line_count = text.count('<br>') + 1 if text else 1
        height = line_count * self.message_input.fontMetrics().lineSpacing() + 16
        # self.message_input.setFixedHeight(height)
        if text != self.message_input.toPlainText():
            self.message_input.setHtml(text)
            cursor.setPosition(position)
            self.message_input.setTextCursor(cursor)
        self.message_input.blockSignals(False)

    def showChats(self):
        def openChat(self, character_id, character_name, chat_id):
            self.mw.hideOverlay()
            self.mw.openChat(character_id, character_name, chat_id)

        def createCard(self, data):
            card = QFrame()
            card.setStyleSheet(card_style())
            card.mousePressEvent = lambda event: openChat(self, self.character_id, self.character_name, data.get('chat_id'))
            card.setCursor(Qt.CursorShape.PointingHandCursor)

            card_layout = QVBoxLayout()

            current_chat = QLabel(self.tr("Current Chat"))
            current_chat.setStyleSheet("color: #3a4671; font-size: .875rem;")
            if self.chat_id == data.get('chat_id'):
                card_layout.addWidget(current_chat, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            timestamp = data.get('preview_turns')[0].get('last_update_time')
            formatted_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y.%m.%d %H:%M:%S')
            chat_time = QLabel(formatted_time)

            chat_time.setStyleSheet("color: #dbdbdb; font-size: 12px;")
            card_layout.addWidget(chat_time, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            chat_text = QLabel(data.get('preview_turns')[0].get('candidates')[0].get('raw_content'))
            chat_text.setStyleSheet("color: #a2a2ac; font-size: 14px;")
            chat_text.setWordWrap(True)
            card_layout.addWidget(chat_text)

            card.setLayout(card_layout)
            return card

        def showChats(self, chats):
            for data in chats:
                card = createCard(self, data)
                self.chats_cards_layout.addWidget(card)
            self.mw.chat_thread.character_chats_signal.disconnect()

        chats_history_widget = QWidget()
        chats_history_layout = QVBoxLayout()
        chats_history_widget.setFixedSize(500, 600)
        chats_history_widget.setLayout(chats_history_layout)

        chats_scroll_area = QScrollArea()
        chats_scroll_area.setWidgetResizable(True)
        chats_scroll_area.setStyleSheet(scroll_style())

        chats_cards_viewport = QWidget()
        self.chats_cards_layout = QVBoxLayout()
        chats_cards_viewport.setStyleSheet("background-color: transparent; border: none;")
        self.chats_cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        chats_cards_viewport.setLayout(self.chats_cards_layout)
        chats_scroll_area.setWidget(chats_cards_viewport)
        chats_history_layout.addWidget(chats_scroll_area)

        self.mw.showOverlay(chats_history_widget)

        self.mw.chat_thread.character_chats_signal.connect(lambda chats: showChats(self, chats))
        self.mw.chat_thread.get_character_chats(self.character_id)

    def _getVoice(self, response):
        voice_name = response.get('voice', {}).get('name', '')
        self.select_char_voice_label.setText(f"{voice_name}")

    def searchVoice(self):
        search_widget = VoiceSearch(self.mw, self.character_name, self.voice_id, self.character_id)
        self.mw.hideOverlay()
        self.mw.showOverlay(search_widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.cis_visible:
            self.character_info_sidebar.setGeometry(self.width() - self.character_info_sidebar.width(), 0, 200, self.height() - 200)
        else:
            self.character_info_sidebar.setGeometry(self.width(), 0, 200, self.height() - 200)
        self.character_info_sidebar.setFixedHeight(self.mw.height() - 200)

    def showCharacterInfoSidebar(self):
        self.character_info_sidebar.show()
        geom = self.character_info_sidebar.geometry()
        self.animation = QPropertyAnimation(self.character_info_sidebar, b"geometry")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.setStartValue(geom)
        self.animation.setEndValue(QRect(geom.x() - self.character_info_sidebar.width(), geom.y(), geom.width(), geom.height()))
        self.animation.start()

    def toggleCharacterInfoSidebar(self):
        if self.cis_visible:
            self.hideCharacterInfoSidebar()
            self.cis_visible = False
        else:
            self.showCharacterInfoSidebar()
            self.cis_visible = True

    def hideCharacterInfoSidebar(self):
        geom = self.character_info_sidebar.geometry()
        self.animation = QPropertyAnimation(self.character_info_sidebar, b"geometry")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.setStartValue(geom)
        self.animation.setEndValue(QRect(geom.x() + self.character_info_sidebar.width(), geom.y(), geom.width(), geom.height()))
        self.animation.finished.connect(self.character_info_sidebar.hide)
        self.animation.start()

    def callCharacter(self):
        self.mw.hide_overlay = False
        vsmode = VoiceMode(self.mw, self, self.character.get('avatar_file_name'), self.chat_id, self.character_id, self.voice_id, self.character_name)
        vsmode.closeEvent = lambda event: setattr(self.mw, 'hide_overlay', True)
        self.mw.showOverlay(vsmode)

    def _playVoice(self, content):
        thread = PlayerThread(content)
        self.mw.threads.append(thread)
        thread.start()

    def _voiceProcess(self, response):
        replayUrl = response['replayUrl']
        thread = FileLoaderThread(replayUrl)
        self.mw.threads.append(thread)
        thread.file.connect(self._playVoice)
        thread.start()

    def enableVoice(self):
        self.voice_enabled = True
        self.enable_char_voice_button.setIcon(self.svg_icons.with_voice('#7d9aff'))
        self.enable_char_voice_button.disconnect()
        self.enable_char_voice_button.clicked.connect(self.disableVoice)
        self.mw.chat_thread.replay_signal.connect(self._voiceProcess)

    def disableVoice(self):
        self.voice_enabled = False
        self.enable_char_voice_button.setIcon(self.svg_icons.no_voice())
        self.enable_char_voice_button.disconnect()
        self.enable_char_voice_button.clicked.connect(self.enableVoice)
        self.mw.chat_thread.replay_signal.disconnect()

    def _voiceOverride(self, response):
        self.mw.chat_thread.voice_override_signal.disconnect()
        self.voice_id = response.get('voice_id')
        if not self.voice_id:
            self.enable_char_voice_button.setVisible(False)
            self.select_char_voice_button.setText(self.tr("Search Voice"))
        else:
            self.mw.chat_thread.get_voice_signal.connect(self._getVoice)
            self.mw.chat_thread.get_voice(self.voice_id)

    def _createNewChat(self, botanswer):
        self.clearMessages()
        if self.mw.recent_chats:
            for i in range(self.mw.recent_chat_layout.count()):
                item = self.mw.recent_chat_layout.itemAt(i)
                if item and item.widget() and item.widget().objectName() == self.chat_id:
                    recent_card = item.widget()
                    self.mw.recent_chat_layout.removeWidget(recent_card)
                    self.mw.recent_chat_layout.insertWidget(0, recent_card)
                    break

        self.chat_id = botanswer[0]['chat_id']
        recent_card.mousePressEvent = lambda event: self.mw.openChat(self.character_id, self.character_name, self.chat_id)
        recent_card.setObjectName(self.chat_id)
        self.mw.chat_thread.new_chat_created_signal.disconnect()
        self.mw.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
        self.mw.chat_thread.get_chat_by_id_signal.connect(self._getChatById)
        self.mw.chat_thread.get_history(self.chat_id)
        self.mw.chat_thread.get_chat_by_id(self.chat_id)

    def createNewChat(self, model_type=None):
        if model_type is None:
            model_type = self.preferred_model_type
        self.mw.chat_thread.new_chat(self.character_id, self.chat_id, model_type)
        self.mw.chat_thread.new_chat_created_signal.connect(self._createNewChat)

    def dislikeCharacter(self):
        self.like_button.setIcon(self.svg_icons.like())
        if self.vote == False:
            self.vote = None
            self.mw.chat_thread.character_vote(self.character_id, None)
            self.dislike_button.setIcon(self.svg_icons.dislike())
        else:
            self.vote = False
            self.mw.chat_thread.character_vote(self.character_id, False)
            self.dislike_button.setIcon(self.svg_icons.disliked())

    def likeCharacter(self):
        self.dislike_button.setIcon(self.svg_icons.dislike())
        if self.vote:
            self.vote = None
            self.mw.chat_thread.character_vote(self.character_id, None)
            self.like_button.setIcon(self.svg_icons.like())
        else:
            self.vote = True
            self.mw.chat_thread.character_vote(self.character_id, True)
            self.like_button.setIcon(self.svg_icons.liked())

    def shareCharacter(self):
        QApplication.clipboard().setText(f'https://character.ai/chat/{self.character_id}')
        self.mw.showNotification(self.tr("Link copied to clipboard"))

    def _getCharacter(self, character):
        self.mw.chat_thread.get_char_signal.disconnect()
        self.voted = character.get('voted', {}).get('voted', False)
        self.vote = character.get('voted', {}).get('vote', None)
        self.character = character.get('character', {})

        if self.character.get('avatar_file_name'):
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.character.get('avatar_file_name') + '?webp=true&anim=0', 70, 70)
            load_avatar_thread.image_loaded.connect(self.avatar_label.setPixmap)
            load_avatar_thread.radius = 4
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.avatar_label, 70, 70, self.character_name, 4)

        if self.character.get('avatar_file_name'):
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.character.get('avatar_file_name') + '?webp=true&anim=0', 40, 40)
            load_avatar_thread.image_loaded.connect(self.header_avatar_label.setPixmap)
            load_avatar_thread.radius = 4
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.header_avatar_label, 40, 40, self.character_name, 4)

        self.name_label.setText(f"<b>{self.character_name}</b>")
        self.header_name_label.setText(f"<b>{self.character_name}</b>")

        self.author_label.setText("<i>"+self.tr("Author: @") + self.character.get('participant__user__username', self.tr('Unknown')) + "</i>")
        self.author_label.mousePressEvent = lambda x: self.mw.openUserPage(self.character.get('participant__user__username', 'Unknown'))
        self.header_author_label.setText("<i>"+self.tr("Author: @") + self.character.get('participant__user__username', self.tr('Unknown')) + "</i>")
        self.header_author_label.mousePressEvent = lambda x: self.mw.openUserPage(self.character.get('participant__user__username', 'Unknown'))

        self.chats_label.setText(str(format_number(self.character.get('participant__num_interactions', 0))) + self.tr(" chats"))

        if self.voted:
            if self.vote == True:
                self.like_button.setIcon(self.svg_icons.liked())
            elif self.vote == False:
                self.dislike_button.setIcon(self.svg_icons.disliked())

        self.title_label.setText(self.character.get('title'))
        self.toggle_info_button.setEnabled(True)
        self.header_character_frame.setVisible(True)

    def _addMessagesFromHistory(self, turns):
        self.clearMessages()
        self.mw.chat_thread.get_history_signal.disconnect()
        for turn in turns:
            for candidate in turn.get('candidates', []):
                if candidate.get('is_final', False):
                    self.addMessage(candidate.get('raw_content', ''), turn.get('turn_key', {}).get('turn_id', ''), turn.get('author', {}).get('is_human', False))

    def _getChat(self, chat):
        self.mw.chat_thread.chat_signal.disconnect()
        if chat:
            for chats in chat:
                self.chat_id = chats.get('chat_id')
            self.mw.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
            self.mw.chat_thread.get_chat_by_id_signal.connect(self._getChatById)
            self.mw.chat_thread.get_history(self.chat_id)
            self.mw.chat_thread.get_chat_by_id(self.chat_id)
        else:
            self.mw.chat_thread.new_chat_created_signal.connect(self._newChatCreated)
            self.mw.chat_thread.new_chat(self.character_id)

    def _getChatById(self, data):
        self.mw.chat_thread.get_chat_by_id_signal.disconnect()
        self.chat_data = data.get('chat', {})
        self.preferred_model_type = self.chat_data.get('preferred_model_type', 'MODEL_TYPE_BALANCED')

    def _newChatCreated(self, botanswer):
        self.clearMessages()
        self.mw.chat_thread.new_chat_created_signal.disconnect()
        self.chat_id = botanswer[0]['chat_id']
        self.mw.chat_thread.get_char_signal.connect(self._getCharacter)
        self.mw.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
        self.mw.chat_thread.get_chat_by_id_signal.connect(self._getChatById)
        self.mw.chat_thread.get_history(self.chat_id)
        self.mw.chat_thread.get_chat_by_id(self.chat_id)
        self.mw.chat_thread.get_character(self.character_id)
        self.mw.chat_thread.get_recent_chats()

    def clearMessages(self):
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
            elif item and item.spacerItem():
                pass

        self.messages_layout.update()
        self.messages_content.update()
        self.messages_area.verticalScrollBar().setValue(0)

    def addMessage(self, text, turn_id, is_user=False):
        message_bubble = MessageBubble(self.mw, self, format_text(text), is_user)
        message_bubble.turn_id = turn_id
        message_bubble.setStyleSheet(
            f"background-color: {self.user_back_message if is_user else self.char_back_message}; border-radius: 4px;")
        message_bubble.message_label.setStyleSheet(
            f"color: {self.user_text_message if is_user else self.char_text_message};")
        message_bubble.setObjectName('user_message' if is_user else 'char_message')
        message_bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        message_bubble.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        message_bubble.customContextMenuRequested.connect(lambda pos, mb=message_bubble: self.showContextMenu(pos, mb))

        self.messages_layout.addWidget(message_bubble, 1,
                                       Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft)
        self.messages_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        self.messages.append(message_bubble)
        return message_bubble

    def setBackMessageColor(self, message, color):
        message.setStyleSheet(f"background-color: {color}; border-radius: 4px;")

    def setTextMessageColor(self, message, color):
        message.message_label.setStyleSheet(f"color: {color};")

    def scrollToBottomIfNeeded(self, minimum, maximum):
        self.messages_area.verticalScrollBar().setValue(maximum)

    def sendMessage(self):
        text = self.message_input.toPlainText()
        if text:
            self.addMessage(text, "", is_user=True)
            self.message_input.setHtml('<span style="color: white;"></span>')
            self.mw.chat_thread.send_message(self.character_id, self.chat_id, text, self.voice_enabled)

    def _copyChat(self, data):
        self.mw.chat_thread.copy_chat_signal.disconnect()
        self.mw.openChat(self.character_id, self.character_name, data.get('new_chat_id'))
        self.mw.showNotification(self.tr("New chat started"))

    def copyChat(self, turn_id):
        self.mw.chat_thread.copy_chat_signal.connect(self._copyChat)
        self.mw.chat_thread.copy_chat(self.chat_id, turn_id)

    def _turnRemove(self, data):
        self.mw.showNotification(self.tr("The message was deleted"))
        self.mw.chat_thread.turn_remove_signal.disconnect()

    def turnRemove(self, turn_id):
        turn_ids = [turn_id]
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item and item.widget() and item.widget().turn_id == turn_id:
                self.mw.chat_thread.turn_remove_signal.connect(self._turnRemove)
                self.mw.chat_thread.turn_remove(self.chat_id, turn_ids)
                item.widget().deleteLater()
            elif item and item.spacerItem():
                pass

    def showContextMenu(self, pos, message_bubble):
        def copy(text):
            QApplication.clipboard().setText(text)
            self.mw.showNotification(self.tr("Message copied to clipboard"))

        context_menu = QMenu(self)
        context_menu.setStyleSheet(menu_style())

        copy_action = QAction(self.tr("Copy Message"), self)
        copy_action.triggered.connect(lambda event: copy(message_bubble.message_label.text()))
        context_menu.addAction(copy_action)

        if message_bubble.turn_id:
            delete_action = QAction(self.tr("Delete Message"), self)
            delete_action.triggered.connect(lambda event: self.turnRemove(message_bubble.turn_id))
            context_menu.addAction(delete_action)

            new_chat_here_action = QAction(self.tr("New chat from here"), self)
            new_chat_here_action.triggered.connect(lambda event: self.copyChat(message_bubble.turn_id))
            context_menu.addAction(new_chat_here_action)

        context_menu.exec(message_bubble.mapToGlobal(pos))

    def mousePressEvent(self, event: QMouseEvent):
        if self.cis_visible:
            global_click_pos = event.globalPosition().toPoint()
            sidebar_global_pos = self.character_info_sidebar.mapToGlobal(self.character_info_sidebar.rect().topLeft())
            sidebar_rect = QRect(sidebar_global_pos, self.character_info_sidebar.size())
            if not sidebar_rect.contains(global_click_pos):
                self.cis_visible = False
                self.hideCharacterInfoSidebar()

        super().mousePressEvent(event)

    def toggleLeftSidebar(self):
        self.mw.left_sidebar_hide_user = not self.mw.left_sidebar_hide_user
        if self.mw.left_sidebar_hide_user and self.mw.left_sidebar_hide_auto:
            self.mw.left_sidebar_visible = True
        else:
            self.mw.left_sidebar_visible = not self.mw.left_sidebar_visible
        self.mw.left_sidebar.setVisible(self.mw.left_sidebar_visible)
        self.mw.top_bar_collapse_button.setVisible(not self.mw.left_sidebar_visible)
        self.collapse_button.setVisible(not self.mw.left_sidebar_visible)