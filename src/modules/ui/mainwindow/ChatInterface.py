import hashlib
import os, math
import ctypes, platform

from curl_cffi import CurlMime
from PyQt6.QtWidgets import (QApplication, QColorDialog, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton,
                             QFrame, QSizePolicy, QSpacerItem, QStackedWidget, QFileDialog, QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt6.QtGui import QMouseEvent, QAction, QPixmap, QColor
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QSettings, QTimer, Qt, pyqtSignal
from PyQt6.sip import isdeleted
from datetime import datetime
from PIL import Image

from modules.ui.cards import PersonaCards
from modules.ui.Elements import CustomTextEdit, ClickableFrame, PushButton, Menu, VerticalScrollPage, CardFrame
from modules.logic.QThreads import PlayerThread, FileLoaderThread, ChatThread, DiscordRPCThread
from modules.ui.Icons import Svg
from modules.Utils import format_text, format_number, color_avatar
from modules.ui.cards.VoiceCards import SearchCard, ModeCard
from modules.ui.cards.VModelCards import ViewerCard
from modules.ui import TM

class MessageBubble(QFrame):
    def __init__(self, main_window, parent, text, avatar_url, name, is_user=False, attachments=[]):
        super().__init__()
        self.mw = main_window
        self.parent = parent
        self.text = text
        self.url = avatar_url
        self.name = name
        self.is_user = is_user
        self.turn_id = None
        self.attachments = attachments
        self.setObjectName('user_message' if self.is_user else 'char_message')

        self.initUI()

    def initUI(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        layout = QVBoxLayout()
        layout_2 = QHBoxLayout()
        lw2 = QFrame()
        lw2.setLayout(layout_2)

        self.attach_image_label = QLabel()
        layout.addWidget(self.attach_image_label)
        layout.addWidget(lw2)
        if self.attachments and self.attachments[0]['type'] == "TYPE_IMAGE":
            def z(v):
                if not isdeleted(self.attach_image_label):
                    self.attach_image_label.setPixmap(v)
                    self.setMinimumHeight(0)
                    self.adjustSize()
                    self.setMinimumHeight(self.height())
            self.attach_image_label.setMinimumSize(100, 100)
            self.mw.image_loader.load(
                self.attachments[0]['url'], 100, 100, 25,
                callback=z,
                error_cb=lambda _: self.attach_image_label.setMinimumSize(0, 0))

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(24, 24)
        if self.url:
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.url}?webp=true&anim=0", 24, 24, 4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, 24, 24, self.name, 4))
        else:
            color_avatar(self.avatar_label, 24, 24, self.name, 4)

        self.m_frame = QFrame()
        self.m_frame.setObjectName("messageBubbleFrame")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.m_frame.setGraphicsEffect(shadow)
        m_layout = QVBoxLayout()
        self.m_frame.setLayout(m_layout)

        self.message_label = QLabel(self.text)
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(int(self.parent.width() / 2.25))
        self.message_label.setContentsMargins(0, 2, 0, 2)
        m_layout.addWidget(self.message_label)

        if self.is_user:
            self.message_label.setStyleSheet(f"color: {self.parent.user_text_message};")
            self.m_frame.setStyleSheet(TM.get_style("MessageBubbleFrame").replace("%%color%%", self.parent.user_back_message))
            layout_2.addWidget(self.m_frame)
            layout_2.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignTop)
        else:
            self.message_label.setStyleSheet(f"color: {self.parent.char_text_message};")
            self.m_frame.setStyleSheet(TM.get_style("MessageBubbleFrame").replace("%%color%%", self.parent.char_back_message))
            layout_2.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignTop)
            layout_2.addWidget(self.m_frame)

        self.setLayout(layout)
        self.adjustSize()
        self.setMinimumHeight(self.height())

        self.animate_entry()

    def animate_entry(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim.finished.connect(self.remove_opacity_effect)
        self.anim.start()

    def remove_opacity_effect(self):
        self.setGraphicsEffect(None)

class ChatInterface(QWidget):
    attach_signal = pyqtSignal(object)
    detach_signal = pyqtSignal(object)
    def __init__(self, main_window, character_name, character_id, chat_id: str | None = None, scene_id: str | None = None):
        super().__init__()
        self.mw = main_window
        self.chat_thread: ChatThread | None = self.mw.chat_thread
        self.discord_thread: DiscordRPCThread | None = self.mw.discord_thread
        self.character_name = character_name
        self.character_id = character_id
        self.chat_id = chat_id
        self.scene_id = scene_id
        self.scene = {}
        self.character = None
        self.cis_visible = False
        self.voice_id = None
        self.next_token = None
        self.user_personas = []
        self.avatar_labels = {}
        self.svg_icons = Svg()
        self.vmodel_show = False
        self.setObjectName("ChatInterface")
        self._detach = False

        self.voice_enabled = False

        self.show_format_buttons = self.mw.settings.value("show_format_buttons", False, type=bool)
        self.chat_settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Emilia", self.character_id)
        self.char_back_message = self.chat_settings.value('colors/char_back_message', TM.c('char_back_message'))
        self.char_text_message = self.chat_settings.value('colors/char_text_message', TM.c('char_text_message'))
        self.user_back_message = self.chat_settings.value('colors/user_back_message', TM.c('user_back_message'))
        self.user_text_message = self.chat_settings.value('colors/user_text_message', TM.c('user_text_message'))
        self.background_image = self.chat_settings.value('background_image', '')

        self.initUI()
        self.applyBackground(self.background_image)
        self.createRightSidebar()

        TM.theme_changed.connect(self.updateTheme)
        self.updateTheme()

        self.chat_thread.message_signal.connect(self.charMessageSignal)
        self.chat_thread.user_message_signal.connect(self.userMessageSignal)
        self.chat_thread.get_user_personas_signal.connect(self.getUserPersonas)
        self.chat_thread.get_scene_by_id_signal.connect(self.getScene)

    def initUI(self):
        self.layout = QHBoxLayout(self)

        chat_container_layout = QVBoxLayout()

        self.top_bar_frame, self.top_bar_layout = self.createTopBar()
        self.mw.top_bar_stacked_widget.setFixedHeight(75)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar_frame)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar_frame)

        self.messages_area = VerticalScrollPage()
        self.messages_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.messages_area.setObjectName("chatScrollArea")
        self.messages_area.viewport.setAutoFillBackground(False)
        self.messages_area.setFrameShape(QFrame.Shape.NoFrame)
        self.messages_area.verticalScrollBar().rangeChanged.connect(self.scrollToBottomIfNeeded)
        self.messages_content = self.messages_area.viewport
        self.messages_content.setObjectName("chatContent")
        self.messages_layout = self.messages_area.layout

        self.messages_overlay_container = QWidget()
        self.messages_overlay_layout = QGridLayout(self.messages_overlay_container)
        self.messages_overlay_layout.setContentsMargins(0, 0, 0, 0)

        self.messages_overlay_layout.addWidget(self.messages_area, 0, 0)

        chat_container_layout.addWidget(self.messages_overlay_container)

        input_layout = QVBoxLayout()
        self.attach_image_label = QLabel()
        self.attach_image_label.link = ""
        input_layout.addWidget(self.attach_image_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        format_toolbar = QHBoxLayout()
        format_widget = QFrame()
        format_widget.setLayout(format_toolbar)

        bold_button = PushButton(self.tr("Bold"))
        bold_button.clicked.connect(lambda: self.message_input.formatSelectedText("**", "**"))
        format_toolbar.addWidget(bold_button)
        italic_button = PushButton(self.tr("Italic"))
        italic_button.clicked.connect(lambda: self.message_input.formatSelectedText("*", "*"))
        format_toolbar.addWidget(italic_button)
        code_button = PushButton(self.tr("Code"))
        code_button.clicked.connect(lambda: self.message_input.formatSelectedText("`", "`"))
        format_toolbar.addWidget(code_button)
        format_toolbar.addStretch()

        if self.show_format_buttons:
            input_layout.addWidget(format_widget)

        send_layout = QHBoxLayout()
        send_layout.setContentsMargins(0, 0, 0, 0)
        send_widget = QFrame()
        send_widget.setLayout(send_layout)

        self.message_input = CustomTextEdit()
        self.message_input.mousePressEvent = lambda _: self.hideCharacterInfoSidebar2()
        self.message_input.setFixedHeight(32)
        self.message_input.horizontalScrollBar().setVisible(False)
        self.message_input.verticalScrollBar().setVisible(False)
        self.message_input.keyPress = lambda: self.sendMessage()

        send_layout.addWidget(self.message_input, alignment=Qt.AlignmentFlag.AlignBottom)

        self.send_message_button = PushButton()
        self.send_message_button.clicked.connect(self.sendMessage)
        send_layout.addWidget(self.send_message_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.call_char_button = PushButton()
        self.call_char_button.clicked.connect(self.callCharacter)
        if self.chat_thread.current_limits.get('voice_limit', {}).get('count_remaining', 0) == 0 and not self.mw.settings.value('use_old_voice_chat', False, type=bool):
            self.call_char_button.setEnabled(False)
            self.call_char_button.setToolTip(self.tr("Call limit exceeded"))
        send_layout.addWidget(self.call_char_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.add_image_button = PushButton()
        self.add_image_button.clicked.connect(self.selectImage)
        if self.chat_thread.current_limits.get('chat_image_attachment', {}).get('count_remaining', 0) == 0:
            self.add_image_button.setEnabled(False)
            self.add_image_button.setToolTip(self.tr("Attached message limit exceeded"))
        send_layout.addWidget(self.send_message_button, alignment=Qt.AlignmentFlag.AlignBottom)

        input_layout.addWidget(send_widget)
        chat_container_layout.addLayout(input_layout)

        self.layout.addLayout(chat_container_layout)

        self.setLayout(self.layout)
        self.chat_thread.get_char_signal.connect(self.initData)
        self.chat_thread.get_character(self.character_id)
        self.chat_thread.voice_override_signal.connect(self._voiceOverride)
        self.chat_thread.voice_override(self.character_id)
        self.chat_thread.get_user_personas()
        if self.scene_id:
            self.chat_thread.get_scene_by_id(self.scene_id)

    def updateTheme(self):
        self.send_message_button.setIcon(self.svg_icons.send(TM.c("icon")))
        self.call_char_button.setIcon(self.svg_icons.call(TM.c("icon")))
        self.add_image_button.setIcon(self.svg_icons.add_image(TM.c("icon")))
        self.toggle_info_button.setIcon(self.svg_icons.show_right_sidebar(TM.c("icon")))
        self.share_char_button.setIcon(self.svg_icons.share(TM.c("icon")))
        self.edit_char_button.setIcon(self.svg_icons.create_character(TM.c("icon")))
        self.like_button.setIcon(self.svg_icons.like(TM.c("icon")))
        self.dislike_button.setIcon(self.svg_icons.dislike(TM.c("icon")))
        self.create_new_chat_button.setIcon(self.svg_icons.new_chat(TM.c("icon")))
        self.enable_char_voice_button.setIcon(self.svg_icons.no_voice(TM.c("icon")))
        self.history_button.setIcon(self.svg_icons.history(TM.c("icon")))
        self.chat_theme_button.setIcon(self.svg_icons.colors(TM.c("icon")))
        self.choose_persona_button.setIcon(self.svg_icons.persona(TM.c("icon")))
        self.chat_style_button.setIcon(self.svg_icons.style(TM.c("icon")))

    def on_scroll(self, value):
        if value == self.messages_area.verticalScrollBar().minimum() and self.chat_next_token:
            self.handle_infinite_scroll()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, "vmodel_widget"):
                if not self.vmodel_widget.translucent:
                    self.vmodel_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def handle_infinite_scroll(self):
        old_height = self.messages_content.height()
        scrollbar = self.messages_area.verticalScrollBar()

        scrollbar.valueChanged.disconnect(self.on_scroll)
        scrollbar.rangeChanged.disconnect(self.scrollToBottomIfNeeded)

        self.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
        self.chat_thread.get_history(self.chat_id, self.chat_next_token)

        QApplication.processEvents()

        new_height = self.messages_content.height()
        delta = new_height - old_height
        scrollbar.setValue(delta)

        scrollbar.valueChanged.connect(self.on_scroll)
        scrollbar.rangeChanged.connect(self.scrollToBottomIfNeeded)

    def applyBackground(self, path):
        if path and os.path.exists(path):
            path = path.replace('\\', '/')
            self.messages_area.setStyleSheet(f"""
                #chatScrollArea {{
                    background-image: url("{path}");
                    background-repeat: no-repeat;
                    background-position: center;
                    background-attachment: fixed;
                }}
            """)
            self.messages_content.setStyleSheet("#chatContent { background: transparent; }")

        else:
            self.messages_area.setStyleSheet("#chatScrollArea {}")
            self.messages_content.setStyleSheet("#chatContent {}")

    def extract_theme_colors(self, image_path):
        try:
            img = Image.open(image_path)
            img = img.resize((150, 150))
            result = img.quantize(colors=5)
            palette = result.getpalette()

            colors = []
            for i in range(0, 15, 3):
                rgb = (palette[i], palette[i + 1], palette[i + 2])
                colors.append(rgb)

            def rgb_to_hex(rgb):
                return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

            def get_brightness(rgb):
                return (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000

            valid_colors = [c for c in colors]

            if len(valid_colors) < 2:
                valid_colors.append(valid_colors[0])

            char_rgb = valid_colors[0]

            user_rgb = valid_colors[1]

            for i in range(1, len(valid_colors)):
                c = valid_colors[i]
                dist = math.sqrt(sum([(a - b) ** 2 for a, b in zip(char_rgb, c)]))
                if dist > 30:
                    user_rgb = c
                    break

            char_hex = rgb_to_hex(char_rgb)
            user_hex = rgb_to_hex(user_rgb)

            char_text = "#ffffff" if get_brightness(char_rgb) < 130 else "#000000"
            user_text = "#ffffff" if get_brightness(user_rgb) < 130 else "#000000"

            return {
                "char_back": char_hex,
                "char_text": char_text,
                "user_back": user_hex,
                "user_text": user_text
            }

        except Exception as e:
            print(f"Error extracting colors: {e}")
            return None

    def setBackgroundFromUrl(self, url):
        if url:
            self.mw.showNotification(self.tr("Downloading background..."))
            self.mw.image_loader.load(
                url, 1280, 720, 0,
                callback=lambda _: self._onBackgroundDownloaded(os.path.join("cache/background", hashlib.md5(url.encode()).hexdigest() + ".png")),
                error_cb=lambda _: self.mw.showNotification(self.tr("Error downloading image")),
                cache_dir="cache/background")

    def _onBackgroundDownloaded(self, file_path):
        self.background_image = file_path
        self.chat_settings.setValue("background_image", file_path)
        self.applyBackground(file_path)

        theme = self.extract_theme_colors(file_path)
        if theme:
            self.char_back_message = theme['char_back']
            self.char_text_message = theme['char_text']
            self.user_back_message = theme['user_back']
            self.user_text_message = theme['user_text']

            self.chat_settings.setValue("colors/char_back_message", self.char_back_message)
            self.chat_settings.setValue("colors/char_text_message", self.char_text_message)
            self.chat_settings.setValue("colors/user_back_message", self.user_back_message)
            self.chat_settings.setValue("colors/user_text_message", self.user_text_message)

            self._update_current_chat_colors()

    def _update_current_chat_colors(self):
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item.widget():
                bubble = item.widget().currentWidget()
                if bubble.objectName() == 'user_message':
                    self.setBackMessageColor(bubble, self.user_back_message)
                    self.setTextMessageColor(bubble, self.user_text_message)
                elif bubble.objectName() == 'char_message':
                    self.setBackMessageColor(bubble, self.char_back_message)
                    self.setTextMessageColor(bubble, self.char_text_message)

    def createTopBar(self):
        header_frame = QWidget()
        header_frame.hideEvent = lambda event: self.mw.top_bar_stacked_widget.setStyleSheet(None)
        header_frame.setFixedHeight(75)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

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
        header_text_layout = QHBoxLayout()
        header_char_text_layout.addLayout(header_text_layout)
        self.header_name_label = QLabel()
        header_text_layout.addWidget(self.header_name_label)
        header_spacer_label = QLabel(" | ")
        header_spacer_label.setVisible(False)
        header_text_layout.addWidget(header_spacer_label)
        self.header_scene_title_label = QLabel()
        self.header_scene_title_label.setVisible(False)
        header_text_layout.addWidget(self.header_scene_title_label)
        if self.scene_id:
            self.header_scene_title_label.setVisible(True)
            header_spacer_label.setVisible(True)
        self.header_author_label = QLabel()
        header_char_text_layout.addWidget(self.header_author_label)

        header_layout.addStretch(1)

        self.toggle_info_button = PushButton()
        self.toggle_info_button.clicked.connect(self.toggleCharacterInfoSidebar)
        self.toggle_info_button.setEnabled(False)
        header_layout.addWidget(self.toggle_info_button)

        header_frame.setLayout(header_layout)
        return header_frame, header_layout

    def createRightSidebar(self):
        self.character_info_sidebar = QFrame(self)
        self.character_info_sidebar.setFixedWidth(230)
        self.character_info_sidebar.setFixedHeight(self.mw.height() - 230)
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

        self.share_char_button = PushButton()
        self.share_char_button.clicked.connect(self.shareCharacter)
        social_buttons_layout.addWidget(self.share_char_button, 1, Qt.AlignmentFlag.AlignLeft)

        self.edit_char_button = PushButton()
        self.edit_char_button.clicked.connect(self.editCharacter)
        social_buttons_layout.addWidget(self.edit_char_button, 1, Qt.AlignmentFlag.AlignLeft)
        self.edit_char_button.setVisible(False)

        self.like_button = PushButton()
        self.like_button.clicked.connect(self.likeCharacter)
        social_buttons_layout.addWidget(self.like_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.dislike_button = PushButton()
        self.dislike_button.clicked.connect(self.dislikeCharacter)
        social_buttons_layout.addWidget(self.dislike_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.char_info_layout.addWidget(self.title_label)

        self.create_new_chat_button = PushButton(self.tr("New Chat"))
        self.create_new_chat_button.clicked.connect(self.createNewChat)
        self.char_info_layout.addWidget(self.create_new_chat_button, alignment=Qt.AlignmentFlag.AlignLeft)

        character_voice_button_layout = QHBoxLayout()
        character_voice_button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.char_info_layout.addLayout(character_voice_button_layout)
        self.enable_char_voice_button = PushButton()
        self.enable_char_voice_button.clicked.connect(self.enableVoice)
        character_voice_button_layout.addWidget(self.enable_char_voice_button)

        self.select_char_voice_button = PushButton(self.tr("Voice"))
        self.select_char_voice_button.clicked.connect(self.searchVoice)
        character_voice_button_layout.addWidget(self.select_char_voice_button)

        self.select_char_voice_label = QLabel()
        character_voice_button_layout.addWidget(self.select_char_voice_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.history_button = PushButton(self.tr("History"))
        self.history_button.clicked.connect(self.showChats)
        self.char_info_layout.addWidget(self.history_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.chat_theme_button = PushButton(self.tr("Chat Theme"))
        self.chat_theme_button.clicked.connect(self.openColorPickerOverlay)
        self.char_info_layout.addWidget(self.chat_theme_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.choose_persona_button = PushButton(self.tr("Persona"))
        self.choose_persona_button.clicked.connect(self.openPersonaOverlay)
        self.char_info_layout.addWidget(self.choose_persona_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.chat_style_button = PushButton(self.tr("Chat Style"))
        self.chat_style_button.clicked.connect(self.openModelOverlay)
        self.char_info_layout.addWidget(self.chat_style_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.vmodel_button = PushButton(self.tr("Show VModel"))
        self.vmodel_button.clicked.connect(self.openVModelOverlay)
        if self.mw.settings.value("vmodel/use", False, type=bool):
            self.char_info_layout.addWidget(self.vmodel_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.detach_chat_button = PushButton(self.tr("Detach Chat"))
        self.detach_chat_button.clicked.connect(self.detachChat)
        self.char_info_layout.addWidget(self.detach_chat_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.character_info_sidebar.setGeometry(self.width(), 0, 230, self.height() - 230)

    def getScene(self, data):
        self.chat_thread.get_scene_by_id_signal.disconnect()
        self.scene = data
        self.header_scene_title_label.setText(self.scene["title"])
        self.header_scene_title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_scene_title_label.mousePressEvent = lambda _: self.mw.openScene(self.scene, self.scene_id)
        if self.scene.get('background_image_url'):
            self.setBackgroundFromUrl(self.scene.get('background_image_url'))

    def getUserPersonas(self, data):
        self.chat_thread.get_user_personas_signal.disconnect()
        self.user_personas = data

    def userMessageSignal(self, response):
        command = response['command']
        if command == 'add_turn':
            for i in reversed(range(self.messages_layout.count())):
                item = self.messages_layout.itemAt(i)
                widget = item.widget()
                if hasattr(widget, 'is_user') and widget.is_user:
                    message_stacked = widget
                    message = message_stacked.currentWidget()
                    message.turn_id = response['turn']['turn_key']['turn_id']
                    message.customContextMenuRequested.connect(lambda pos, mb=message: self.showContextMenu(pos, mb))
                    message.customContextMenuRequested.disconnect()
                    message.customContextMenuRequested.connect(lambda pos, mb=message: self.showContextMenu(pos, mb))
        elif command == 'update_turn':
            for i in reversed(range(self.messages_layout.count())):
                item = self.messages_layout.itemAt(i)
                widget = item.widget()
                if hasattr(widget, 'turn_id') and widget.turn_id == response['turn']['turn_key']['turn_id']:
                    message_stacked = widget
                    break

            message = message_stacked.currentWidget()

            older = []
            pci = response.get("turn", {}).get('primary_candidate_id')
            for candidate in response.get("turn", {}).get('candidates', []):
                if candidate.get('candidate_id', pci) == pci:
                    new_text = format_text(candidate.get('raw_content', ''), self.mw.username)
                    message.text = new_text
                    message.message_label.setText(new_text)
                else:
                    older.append(candidate)

            message.setMinimumHeight(0)
            message.adjustSize()

    def charMessageSignal(self, response):
        command = response['command']
        if command == 'add_turn':
            message_widget = self.addMessage(
                format_text(response['turn']['candidates'][0]['raw_content'], self.mw.username),
                response['turn']['turn_key']['turn_id'],
                is_user=False
            )
            self.startTextAnimation(message_widget.currentWidget(), response['turn']['candidates'][0]['raw_content'])

        elif command == 'update_turn':
            for i in reversed(range(self.messages_layout.count())):
                item = self.messages_layout.itemAt(i)
                widget = item.widget()
                if hasattr(widget, 'turn_id') and widget.turn_id == response['turn']['turn_key']['turn_id']:
                    message_stacked = widget
                    break

            message = message_stacked.currentWidget()
            if getattr(message.message_label, 'animation_queue'):
                self.setupAnimation(message.message_label)

            new_text = format_text(response['turn']['candidates'][0]['raw_content'], self.mw.username)
            message.text = new_text
            self.addTextToAnimation(message.message_label, new_text)

            message.setMinimumHeight(0)
            message.adjustSize()

    def setupAnimation(self, label):
        label.animation_queue = []
        label.current_text = ""
        label.current_index = 0
        label.is_animating = False
        label.target_text = ""

        label.animation_timer = QTimer()
        label.animation_timer.timeout.connect(lambda: self.animateNextChar(label))

    def startTextAnimation(self, message_widget, full_text):
        message = message_widget
        label = message.message_label

        self.setupAnimation(label)

        label.setText("")
        label.target_text = format_text(full_text, self.mw.username)
        label.current_text = label.target_text
        label.current_index = 0
        label.is_animating = True

        label.animation_timer.start(30)

    def addTextToAnimation(self, label, new_full_text):
        label.target_text = new_full_text

        if label.is_animating:
            current_length = len(label.current_text)
            label.current_text = label.target_text
        else:
            label.current_text = label.target_text
            label.current_index = len(label.text())
            label.is_animating = True
            label.animation_timer.start(30)

    def animateNextChar(self, label):
        if label.current_index < len(label.current_text):
            display_text = label.current_text[:label.current_index + 1]
            label.setText(display_text)
            label.current_index += 1

            message = label.parent()
            if message:
                message.setMinimumHeight(0)
                message.adjustSize()
                message.setMinimumHeight(message.height())
        else:
            if label.target_text != label.current_text:
                label.current_text = label.target_text
            else:
                label.animation_timer.stop()
                label.is_animating = False

    def showEvent(self, a0):
        super().showEvent(a0)
        if platform.system() == 'Windows':
            from modules.logic.WinDarkTheme import ChangeDWMAttrib, detect

            ChangeDWMAttrib(detect(self), 19, ctypes.c_int(1))
            ChangeDWMAttrib(detect(self), 20, ctypes.c_int(1))

    def detachChat(self):
        self._detach = True
        self.detach_signal.emit(True)
        self.toggle_info_button.setEnabled(False)
        self.setParent(None)
        self.setWindowTitle(self.tr("Chat with %%char%%").replace("%%char%%", self.character_name))
        self.show()
        self.hideCharacterInfoSidebar()
        self.setStyleSheet(f"""
            #ChatInterface {{
                background-color: {TM.c('mw_back')};
                color: {TM.c('text')};
            }}
            {TM.get_style('VerticalScrollArea')}
        """)

    def attach_chat(self):
        self._detach = False
        self.attach_signal.emit(True)
        self.toggle_info_button.setEnabled(True)
        self.setParent(None)
        self.setWindowTitle(self.tr("Chat with %%char%%").replace("%%char%%", self.character_name))
        self.show()
        self.hideCharacterInfoSidebar()
        self.setStyleSheet(f"""
            #ChatInterface {{
                background-color: {TM.c('mw_back')};
                color: {TM.c('text')};
            }}
            {TM.get_style('VerticalScrollArea')}
        """)

    def openVModelOverlay(self):
        if self.vmodel_show:
            self.vmodel_button.setText(self.tr("Show VModel"))
            if hasattr(self, 'vmodel_widget') and self.vmodel_widget:
                self.messages_overlay_layout.removeWidget(self.vmodel_widget)
                self.vmodel_widget.hide()
                self.vmodel_widget.deleteLater()
                self.vmodel_widget = None
        else:
            self.vmodel_button.setText(self.tr("Hide VModel"))
            def setWidget(widget):
                self.mw.hideOverlay()
                self.vmodel_widget = widget
                self.vmodel_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                self.vmodel_widget.setStyleSheet("background: transparent;")
                self.messages_overlay_layout.addWidget(self.vmodel_widget, 0, 0)


            overlay_widget = ViewerCard(self.mw)
            overlay_widget.vmodel_widget.connect(setWidget)
            overlay_widget.setFixedWidth(350)
            overlay_widget.setStyleSheet("background: transparent;")
            self.mw.showOverlay(overlay_widget)
        self.vmodel_show = not self.vmodel_show

    def openPersonaOverlay(self):
        overlay_widget = QWidget()
        overlay_widget.setFixedWidth(350)
        overlay_widget.setFixedHeight(550)
        overlay_layout = QVBoxLayout()
        overlay_widget.setLayout(overlay_layout)

        choose_label = QLabel(self.tr("Choose a persona"))
        overlay_layout.addWidget(choose_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        f_page = QWidget()
        f_page_layout = QVBoxLayout(f_page)
        f_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        f_page.setLayout(f_page_layout)
        overlay_layout.addWidget(f_page)

        scroll_page = VerticalScrollPage()
        scroll_page.viewport.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout
        f_page_layout.addWidget(scroll_page)

        card_list = []

        def updateSettings(data):
            self.chat_thread.update_user_settings_signal.disconnect()
            if data.get('success', False):
                self.mw.user_settings = data['settings']
                self.mw.showNotification(self.tr('Successfully updated your persona'))
            self.mw.hideOverlay()
            self.toggleCharacterInfoSidebar()

        def onCardClicked(clicked_card):
            if clicked_card.active:
                self.mw.user_settings['personaOverrides'][self.character_id]= ""
            else:
                self.mw.user_settings['personaOverrides'][self.character_id] = clicked_card.data['external_id']
            self.chat_thread.update_user_settings_signal.connect(updateSettings)
            self.chat_thread.update_user_settings(self.mw.user_settings)

        for persona in self.user_personas:
            card = PersonaCards.MainCard(self.mw, persona, self.character_id)
            card.mousePressEvent = lambda _: onCardClicked(card)
            scroll_layout.addWidget(card)
            card_list.append(card)

        self.mw.showOverlay(overlay_widget)

    def openModelOverlay(self):
        overlay_widget = QWidget()
        overlay_widget.setFixedWidth(350)
        overlay_widget.setFixedHeight(550)
        overlay_layout = QVBoxLayout()
        overlay_widget.setLayout(overlay_layout)

        choose_label = QLabel(self.tr("Choose a model to influence the style of your chat"))
        overlay_layout.addWidget(choose_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        f_page = QWidget()
        f_page_layout = QVBoxLayout(f_page)
        f_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        f_page.setLayout(f_page_layout)
        overlay_layout.addWidget(f_page)

        scroll_page = VerticalScrollPage()
        scroll_page.viewport.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout
        f_page_layout.addWidget(scroll_page)

        card_list = []
        self.overlay_selected_model_type = self.preferred_model_type
        def createCard(model_type, name, icon, description, plus, beta, limited):
            card = ClickableFrame()
            card.setObjectName(model_type)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.mousePress = lambda x: onCardClicked(card)

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
            font = name_label.font()
            font.setBold(True)
            font.setPointSize(12)
            name_label.setFont(font)
            text_layout.addWidget(name_label)

            description_label = QLabel(description)
            font = description_label.font()
            font.setPointSize(9)
            description_label.setFont(font)
            description_label.setWordWrap(True)
            description_label.setStyleSheet("color: #a2a2ac")
            text_layout.addWidget(description_label)

            card_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))

            if plus:
                plus_label = QLabel("C.AI+")
                card_layout.addWidget(plus_label)

            if beta:
                beta_label = QLabel()
                beta_label.setPixmap(self.svg_icons.beta(pixmap_ret=True))
                card_layout.addWidget(beta_label)

            if limited:
                limited_label = QLabel()
                limited_label.setPixmap(self.svg_icons.limited(pixmap_ret=True))
                card_layout.addWidget(limited_label)

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

        for model_type in self.mw.available_models_git:
            m_d = self.mw.available_models_git.get(model_type, {})
            _ = m_d.get('description', {})
            card = createCard(model_type,
                              m_d.get('name'),
                              self.svg_icons.model_type_icon(m_d.get('svg'), pixmap_ret=True),
                              _.get(self.mw.current_language.split("_")[0],_.get("en", "")),
                              m_d.get('plus', False),
                              m_d.get('beta', False),
                              m_d.get('limited', False))
            if model_type == self.preferred_model_type: card.setCheckable(True)
            scroll_layout.addWidget(card)
            card_list.append(card)

        def apply():
            if self.overlay_selected_model_type != self.preferred_model_type:
                self.createNewChat(self.overlay_selected_model_type)
            self.mw.hideOverlay()
            self.toggleCharacterInfoSidebar()

        buttons_layout = QHBoxLayout()

        apply_button = PushButton(self.tr("Continue chat"))
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

    def openColorPickerOverlay(self):
        def restoreDefaultColors():
            data = {
                "char_back_message": TM.c('char_back_message'),
                "char_text_message": TM.c('char_text_message'),
                "user_back_message": TM.c('user_back_message'),
                "user_text_message": TM.c('user_text_message')
            }
            self.chat_settings.setValue("background_image", "")
            self.applyBackground("")

            for key, value in data.items():
                self.chat_settings.setValue(f"colors/{key}", value)
                setattr(self, key, value)
            for i in range(self.messages_layout.count()):
                item = self.messages_layout.itemAt(i)
                if item.widget():
                    item = item.widget()
                    if item.currentWidget().objectName() == 'user_message':
                        self.setBackMessageColor(item.currentWidget(), self.user_back_message)
                        self.setTextMessageColor(item.currentWidget(), self.user_text_message)
                    elif item.currentWidget().objectName() == 'char_message':
                        self.setBackMessageColor(item.currentWidget(), self.char_back_message)
                        self.setTextMessageColor(item.currentWidget(), self.char_text_message)
            self.mw.hideOverlay()

        def pickBackgroundImage():
            file_dialog = QFileDialog()
            file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp *.gif *.bmp)")
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    path = selected_files[0]
                    self.background_image = path
                    self.chat_settings.setValue("background_image", path)
                    self.applyBackground(path)

                    theme = self.extract_theme_colors(path)
                    if theme:
                        self.char_back_message = theme['char_back']
                        self.char_text_message = theme['char_text']
                        self.user_back_message = theme['user_back']
                        self.user_text_message = theme['user_text']

                        self.char_back_message_picker.setStyleSheet(f"background-color: {self.char_back_message};")
                        self.char_text_message_picker.setStyleSheet(f"background-color: {self.char_text_message};")
                        self.user_back_message_picker.setStyleSheet(f"background-color: {self.user_back_message};")
                        self.user_text_message_picker.setStyleSheet(f"background-color: {self.user_text_message};")

                        self.chat_settings.setValue("colors/char_back_message", self.char_back_message)
                        self.chat_settings.setValue("colors/char_text_message", self.char_text_message)
                        self.chat_settings.setValue("colors/user_back_message", self.user_back_message)
                        self.chat_settings.setValue("colors/user_text_message", self.user_text_message)

                        for i in range(self.messages_layout.count()):
                            item = self.messages_layout.itemAt(i)
                            if item.widget():
                                widget = item.widget()
                                bubble = widget.currentWidget()

                                if bubble.objectName() == 'user_message':
                                    self.setBackMessageColor(bubble, self.user_back_message)
                                    self.setTextMessageColor(bubble, self.user_text_message)
                                elif bubble.objectName() == 'char_message':
                                    self.setBackMessageColor(bubble, self.char_back_message)
                                    self.setTextMessageColor(bubble, self.char_text_message)

        def clearBackgroundImage():
            self.background_image = ""
            self.chat_settings.setValue("background_image", "")
            self.applyBackground("")

        def pickCharBackMessageColor():
            color = QColorDialog.getColor()
            if color.isValid():
                self.char_back_message_picker.setStyleSheet(f"background-color: {color.name()};")

        def pickCharTextMessageColor():
            color = QColorDialog.getColor()
            if color.isValid():
                self.char_text_message_picker.setStyleSheet(f"background-color: {color.name()};")

        def pickUserBackMessageColor():
            color = QColorDialog.getColor()
            if color.isValid():
                self.user_back_message_picker.setStyleSheet(f"background-color: {color.name()};")

        def pickUserTextMessageColor():
            color = QColorDialog.getColor()
            if color.isValid():
                self.user_text_message_picker.setStyleSheet(f"background-color: {color.name()};")

        def applyColors():
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
                    item = item.widget()
                    if item.currentWidget().objectName() == 'user_message':
                        self.setBackMessageColor(item.currentWidget(), self.user_back_message)
                        self.setTextMessageColor(item.currentWidget(), self.user_text_message)
                    elif item.currentWidget().objectName() == 'char_message':
                        self.setBackMessageColor(item.currentWidget(), self.char_back_message)
                        self.setTextMessageColor(item.currentWidget(), self.char_text_message)
            self.mw.hideOverlay()

        color_picker_widget = QWidget()
        color_picker_widget.setFixedHeight(300)
        color_picker_layout = QVBoxLayout()
        color_picker_widget.setLayout(color_picker_layout)

        color_pickers_frame = QWidget()
        color_pickers_layout = QVBoxLayout()
        color_pickers_frame.setLayout(color_pickers_layout)

        char_text_message_layout = QHBoxLayout()
        char_text_message_label = QLabel(self.tr("Character Text Color:"))
        self.char_text_message_picker = QPushButton()
        self.char_text_message_picker.setStyleSheet(f"background-color: {self.char_text_message};")
        self.char_text_message_picker.clicked.connect(pickCharTextMessageColor)
        char_text_message_layout.addWidget(char_text_message_label, alignment=Qt.AlignmentFlag.AlignLeft)
        char_text_message_layout.addWidget(self.char_text_message_picker, alignment=Qt.AlignmentFlag.AlignRight)
        color_pickers_layout.addLayout(char_text_message_layout)

        char_back_message_layout = QHBoxLayout()
        char_back_message_label = QLabel(self.tr("Character Background Color:"))
        self.char_back_message_picker = QPushButton()
        self.char_back_message_picker.setStyleSheet(f"background-color: {self.char_back_message};")
        self.char_back_message_picker.clicked.connect(pickCharBackMessageColor)
        char_back_message_layout.addWidget(char_back_message_label, alignment=Qt.AlignmentFlag.AlignLeft)
        char_back_message_layout.addWidget(self.char_back_message_picker, alignment=Qt.AlignmentFlag.AlignRight)
        color_pickers_layout.addLayout(char_back_message_layout)

        user_text_message_layout = QHBoxLayout()
        user_text_message_label = QLabel(self.tr("User Text Color:"))
        self.user_text_message_picker = QPushButton()
        self.user_text_message_picker.setStyleSheet(f"background-color: {self.user_text_message};")
        self.user_text_message_picker.clicked.connect(pickUserTextMessageColor)
        user_text_message_layout.addWidget(user_text_message_label, alignment=Qt.AlignmentFlag.AlignLeft)
        user_text_message_layout.addWidget(self.user_text_message_picker, alignment=Qt.AlignmentFlag.AlignRight)
        color_pickers_layout.addLayout(user_text_message_layout)

        user_back_message_layout = QHBoxLayout()
        user_back_message_label = QLabel(self.tr("User Background Color:"))
        self.user_back_message_picker = QPushButton()
        self.user_back_message_picker.setStyleSheet(f"background-color: {self.user_back_message};")
        self.user_back_message_picker.clicked.connect(pickUserBackMessageColor)
        user_back_message_layout.addWidget(user_back_message_label, alignment=Qt.AlignmentFlag.AlignLeft)
        user_back_message_layout.addWidget(self.user_back_message_picker, alignment=Qt.AlignmentFlag.AlignRight)
        color_pickers_layout.addLayout(user_back_message_layout)
        color_picker_layout.addWidget(color_pickers_frame, alignment=Qt.AlignmentFlag.AlignTop)

        background_layout = QHBoxLayout()
        bg_label = QLabel(self.tr("Background Image:"))
        background_layout.addWidget(bg_label)

        pick_bg_button = PushButton(self.tr("Select"))
        pick_bg_button.clicked.connect(pickBackgroundImage)
        background_layout.addWidget(pick_bg_button)

        clear_bg_button = PushButton(self.tr("Clear"))
        clear_bg_button.clicked.connect(clearBackgroundImage)
        background_layout.addWidget(clear_bg_button)

        color_picker_layout.addLayout(background_layout)

        buttons_layout = QHBoxLayout()
        apply_button = PushButton(self.tr("Apply"))
        apply_button.clicked.connect(applyColors)
        buttons_layout.addWidget(apply_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        restore_button = PushButton(self.tr("Restore"))
        restore_button.clicked.connect(restoreDefaultColors)
        buttons_layout.addWidget(restore_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        color_picker_layout.addLayout(buttons_layout)

        self.mw.showOverlay(color_picker_widget)

    def selectImage(self):
        def uploaded(response):
            if response.get("status") == "OK":
                link = response['value']
                self.mw.image_loader.load(
                    link, 50, 50, 25,
                    label=self.attach_image_label, cache_dir="cache/imgs_in_chats")
                self.attach_image_label.setMinimumSize(50, 50)
                self.attach_image_label.link = link
            else:
                self.mw.showNotification(response.get("error"))

        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.xbm *.tif *.jfif *.pjp *.apng *.svgz *.jpg *.heif *.ico *.tiff *.webp *.jpeg *.heic *.gif *.svg *.png *.bmp *.pjpeg *.avif)")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            mp = CurlMime()

            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.bmp': 'image/bmp',
                '.svg': 'image/svg+xml',
                '.ico': 'image/x-icon',
                '.tiff': 'image/tiff',
                '.tif': 'image/tiff'
            }
            content_type = mime_types.get(ext, 'application/octet-stream')

            mp.addpart(
                name="image",
                content_type=content_type,
                filename=os.path.basename(file_path),
                local_path=file_path
            )

            self.mw.chat_thread.upload_image_signal.connect(uploaded)
            self.mw.chat_thread.upload_image(mp)

            self.mw.showNotification(self.tr("Uploading..."))

    def showChats(self):
        def updateTheme(card):
            card.chat_text.setStyleSheet(f"color: {TM.c('disabled_text')}; font-size: 14px;")

        def openChat(self, character_id, character_name, chat_id):
            self.mw.hideOverlay()
            self.mw.openChat(character_id, character_name, chat_id)

        def createCard(self, data):
            card = CardFrame()
            card.mousePressEvent = lambda event: openChat(self, self.character_id, self.character_name, data.get('chat_id'))
            card.setCursor(Qt.CursorShape.PointingHandCursor)

            card_layout = QVBoxLayout()

            current_chat = QLabel(self.tr("Current Chat"))
            current_chat.setStyleSheet("color: #3a4671; font-size: .875rem;")
            if self.chat_id == data.get('chat_id'):
                card_layout.addWidget(current_chat, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            timestamp = data.get('preview_turns', [{}])[0].get('last_update_time')
            if data.get('preview_turns', [{}])[0].get('last_update_time'):
                formatted_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y.%m.%d %H:%M:%S')
            else:
                formatted_time = "Unavailable"
            chat_time = QLabel(formatted_time)

            chat_time.setStyleSheet("color: #dbdbdb; font-size: 12px;")
            card_layout.addWidget(chat_time, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            chat_text = QLabel(format_text(data.get('preview_turns', [{}])[0].get('candidates', [{}])[0].get('raw_content'), self.mw.username))
            chat_text.setWordWrap(True)
            setattr(card, "chat_text", chat_text)
            card_layout.addWidget(chat_text)

            card.setLayout(card_layout)
            TM.theme_changed.connect(lambda _: updateTheme(card))
            updateTheme(card)
            return card

        def showChats(self, chats):
            for data in chats:
                card = createCard(self, data)
                self.chats_cards_layout.addWidget(card)
            self.chat_thread.character_chats_signal.disconnect()

        chats_history_widget = QWidget()
        chats_history_layout = QVBoxLayout()
        chats_history_widget.setFixedSize(500, 600)
        chats_history_widget.setLayout(chats_history_layout)

        scroll_page = VerticalScrollPage()
        scroll_page.viewport.setStyleSheet("background-color: transparent; border: none;")
        self.chats_cards_layout = scroll_page.layout
        chats_history_layout.addWidget(scroll_page)

        self.mw.showOverlay(chats_history_widget)

        self.chat_thread.character_chats_signal.connect(lambda chats: showChats(self, chats))
        self.chat_thread.get_character_chats(self.character_id)

    def _getVoice(self, response):
        voice_name = response.get('voice', {}).get('name', '')
        self.select_char_voice_label.setText(f"{voice_name}")

    def searchVoice(self):
        search_widget = SearchCard(self.mw, self.character_name, self.voice_id, self.character_id)
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
            self.hideCharacterInfoSidebar2()
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

    def hideCharacterInfoSidebar2(self):
        if self.cis_visible:
            self.hideCharacterInfoSidebar()
            self.cis_visible = False

    def callCharacter(self):
        count = self.chat_thread.current_limits.get('voice_limit', {}).get('count_remaining', 0)
        if count >> 0:
            def voicecalllimit(connected: bool):
                if connected:
                    self.chat_thread.current_limits['voice_limit']['count_remaining'] -= 1
            self.hideCharacterInfoSidebar2()
            self.mw.hide_overlay = False
            vsmode = ModeCard(self.mw, self, self.character.get('avatar_file_name'), self.chat_id, self.character_id, self.voice_id, self.character_name)
            vsmode.thread.connected_signal.connect(voicecalllimit)
            vsmode.closeEvent = lambda event: setattr(self.mw, 'hide_overlay', True)
            self.mw.showOverlay(vsmode)
        elif count == 0:
            self.mw.showNotification(self.tr("Call limit exceeded"))

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
        self.chat_thread.replay_signal.connect(self._voiceProcess)

    def disableVoice(self):
        self.voice_enabled = False
        self.enable_char_voice_button.setIcon(self.svg_icons.no_voice(TM.c("icon")))
        self.enable_char_voice_button.disconnect()
        self.enable_char_voice_button.clicked.connect(self.enableVoice)
        self.chat_thread.replay_signal.disconnect()

    def _voiceOverride(self, response):
        self.chat_thread.voice_override_signal.disconnect()
        self.voice_id = response.get('voice_id')
        if not self.voice_id:
            self.enable_char_voice_button.setVisible(False)
            self.select_char_voice_button.setText(self.tr("Search Voice"))
        else:
            self.chat_thread.get_voice_signal.connect(self._getVoice)
            self.chat_thread.get_voice(self.voice_id)

    def _createNewChat(self, botanswer):
        self.clearMessages()
        if self.mw.recent_chats:
            for i in range(self.mw.recent_chat_scroll_layout.count()):
                item = self.mw.recent_chat_scroll_layout.itemAt(i)
                if item and item.widget() and item.widget().objectName() == self.chat_id:
                    recent_card = item.widget()
                    self.mw.recent_chat_scroll_layout.removeWidget(recent_card)
                    self.mw.recent_chat_scroll_layout.insertWidget(0, recent_card)
                    break

        self.chat_id = botanswer['chat']['chat_id']
        recent_card.mousePressEvent = lambda event: self.mw.openChat(self.character_id, self.character_name, self.chat_id)
        recent_card.setObjectName(self.chat_id)
        self.chat_thread.new_chat_created_signal.disconnect()
        self.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
        self.chat_thread.get_chat_by_id_signal.connect(self._getChatById)
        self.chat_thread.get_history(self.chat_id)
        self.chat_thread.get_chat_by_id(self.chat_id)

    def createNewChat(self, model_type=None):
        if model_type is None:
            model_type = self.preferred_model_type
        self.chat_thread.new_chat(self.character_id, self.chat_id, model_type)
        self.chat_thread.new_chat_created_signal.connect(self._createNewChat)

    def dislikeCharacter(self):
        self.like_button.setIcon(self.svg_icons.like(TM.c("icon")))
        if self.vote == False:
            self.vote = None
            self.chat_thread.character_vote(self.character_id, None)
            self.dislike_button.setIcon(self.svg_icons.dislike(TM.c("icon")))
        else:
            self.vote = False
            self.chat_thread.character_vote(self.character_id, False)
            self.dislike_button.setIcon(self.svg_icons.disliked(TM.c("icon")))

    def likeCharacter(self):
        self.dislike_button.setIcon(self.svg_icons.dislike(TM.c("icon")))
        if self.vote:
            self.vote = None
            self.chat_thread.character_vote(self.character_id, None)
            self.like_button.setIcon(self.svg_icons.like(TM.c("icon")))
        else:
            self.vote = True
            self.chat_thread.character_vote(self.character_id, True)
            self.like_button.setIcon(self.svg_icons.liked(TM.c("icon")))

    def editCharacter(self):
        self.mw.openCreateCharacterPage(self.character_id)

    def shareCharacter(self):
        QApplication.clipboard().setText(f'https://character.ai/chat/{self.character_id}')
        self.mw.showNotification(self.tr("Link copied to clipboard"))

    def initData(self, character):
        self._getCharacter(character)
        if self.chat_id:
            self.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
            self.chat_thread.get_chat_by_id_signal.connect(self._getChatById)
            self.chat_thread.get_history(self.chat_id)
            self.chat_thread.get_chat_by_id(self.chat_id)
        else:
            self.chat_thread.chat_signal.connect(self._getChat)
            self.chat_thread.get_chat(self.character_id)

    def _getCharacter(self, character):
        self.chat_thread.get_char_signal.disconnect()
        self.voted = character.get('voted', {}).get('voted', False)
        self.vote = character.get('voted', {}).get('vote', None)
        self.character = character.get('character', {})
        self.character_name = self.character['name']

        if self.character.get('avatar_file_name'):
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.character.get('avatar_file_name')}?webp=true&anim=0", 70, 70, 4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, 70, 70, self.character_name, 4))
        else:
            color_avatar(self.avatar_label, 70, 70, self.character_name, 4)

        if self.character.get('avatar_file_name'):
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.character.get('avatar_file_name')}?webp=true&anim=0",
                40, 40, 4, label=self.header_avatar_label,
                error_cb=lambda _: color_avatar(self.header_avatar_label, 40, 40, self.character_name, 4))
        else:
            color_avatar(self.header_avatar_label, 40, 40, self.character_name, 4)

        self.name_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.name_label.setText(f"<b>{self.character_name}</b>")
        self.name_label.mousePressEvent = lambda x: self.mw.openCharacter(character.get('path'), self.character_id)
        self.header_name_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_name_label.setText(f"<b>{self.character_name}</b>")
        self.header_name_label.mousePressEvent = lambda x: self.mw.openCharacter(character.get('path'), self.character_id)

        self.author_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.author_label.setText("<i>"+self.tr("Author: @") + self.character.get('participant__user__username', self.tr('Unknown')) + "</i>")
        self.author_label.mousePressEvent = lambda x: self.mw.openUserPage(self.character.get('participant__user__username', 'Unknown'))
        self.header_author_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_author_label.setText("<i>"+self.tr("Author: @") + self.character.get('participant__user__username', self.tr('Unknown')) + "</i>")
        self.header_author_label.mousePressEvent = lambda x: self.mw.openUserPage(self.character.get('participant__user__username', 'Unknown'))

        self.chats_label.setText(str(format_number(self.character.get('participant__num_interactions', 0))) + self.tr(" chats"))

        if self.voted:
            if self.vote == True:
                self.like_button.setIcon(self.svg_icons.liked(TM.c("icon")))
            elif self.vote == False:
                self.dislike_button.setIcon(self.svg_icons.disliked(TM.c("icon")))

        self.title_label.setText(self.character.get('title'))
        self.toggle_info_button.setEnabled(True)
        self.header_character_frame.setVisible(True)

        if self.character.get('participant__user__username', self.tr('Unknown')) == self.mw.username:
            self.edit_char_button.setVisible(True)

        self.chat_thread.get_recommend_chars_by_id(self.character_id)

        if self.mw.drpc_enable and self.mw.drpc_show_current_page:
            if self.character.get('visibility') == "PUBLIC" and self.mw.drpc_show_chat_name:
                if self.character.get('avatar_file_name'):
                    self.discord_thread.update(
                        details=self.tr("Chatting with ") + self.character_name,
                        large_image="https://characterai.io/i/80/static/avatars/" + self.character.get('avatar_file_name') + '?webp=true&anim=0',
                        buttons=[{
                            "label": self.tr("Open character"),
                            "url": f"https://character.ai/character/{self.character['short_hash']}"
                        }]
                    )
                else:
                    self.discord_thread.update(
                        details=self.tr("Chatting with ") + self.character_name,
                        buttons=[{
                            "label": self.tr("Open character"),
                            "url": f"https://character.ai/character/{self.character['short_hash']}"
                        }]
                    )
            else:
                self.discord_thread.update(details=self.tr("Chatting"))

    def _addMessagesFromHistory(self, turns, next_token):
        self.chat_next_token = next_token
        self.clearMessages()
        self.chat_thread.get_history_signal.disconnect()
        for turn in turns:
            older = []
            pci = turn.get('primary_candidate_id')
            for candidate in turn.get('candidates', []):
                if candidate.get('candidate_id', pci) == pci:
                    self.addMessage(candidate.get('raw_content', ''), turn.get('turn_key', {}).get('turn_id', ''), turn.get('author', {}).get('is_human', False), candidate.get('attachments', []))
                else:
                    older.append(candidate)

    def _getChat(self, chat):
        self.chat_thread.chat_signal.disconnect()
        if chat:
            for chats in chat:
                self.chat_id = chats.get('chat_id')
            self.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
            self.chat_thread.get_chat_by_id_signal.connect(self._getChatById)
            self.chat_thread.get_history(self.chat_id)
            self.chat_thread.get_chat_by_id(self.chat_id)
            if self.mw.recent_chats:
                for i in range(self.mw.recent_chat_scroll_layout.count()):
                    item = self.mw.recent_chat_scroll_layout.itemAt(i)
                    if item and item.widget():
                        card = item.widget()
                        if card.objectName() == self.chat_id:
                            setattr(self, 'recent_card', card)
                            card.setStyleSheet(card.press_style)
                        break
        else:
            self.chat_thread.new_chat_created_signal.connect(self._newChatCreated)
            self.chat_thread.new_chat(self.character_id)

    def _getChatById(self, data):
        self.chat_thread.get_chat_by_id_signal.disconnect()
        self.chat_data = data.get('chat', {})
        self.preferred_model_type = self.chat_data.get('preferred_model_type', 'MODEL_TYPE_BALANCED')

    def _newChatCreated(self, botanswer):
        self.clearMessages()
        self.chat_thread.new_chat_created_signal.disconnect()
        self.chat_id = botanswer['chat']['chat_id']
        self.chat_thread.get_char_signal.connect(self._getCharacter)
        self.chat_thread.get_history_signal.connect(self._addMessagesFromHistory)
        self.chat_thread.get_chat_by_id_signal.connect(self._getChatById)
        self.chat_thread.get_history(self.chat_id)
        self.chat_thread.get_chat_by_id(self.chat_id)
        self.chat_thread.get_character(self.character_id)
        self.chat_thread.get_recent_chats()

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

    def addMessage(self, text, turn_id, is_user=False, attachments=[]):
        message_widget = QStackedWidget()
        message_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        message_widget.setStyleSheet("background: transparent;")
        message_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        message_widget.turn_id = turn_id
        message_widget.is_user = is_user
        message_bubble = self.createMessage(text, turn_id, is_user, attachments)

        self.messages_layout.addWidget(message_widget, 1,
                                       Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft)
        message_widget.addWidget(message_bubble)
        message_widget.setCurrentWidget(message_bubble)
        return message_widget

    def createMessage(self, text, turn_id, is_user=False, attachments=[]):
        if is_user:
            message_bubble = MessageBubble(self.mw, self, format_text(text), self.mw.me_avatar, self.mw.name,True, attachments)
        else:
            message_bubble = MessageBubble(self.mw, self, format_text(text), self.character.get('avatar_file_name'), self.character_name, False, attachments)
        message_bubble.turn_id = turn_id

        message_bubble.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        message_bubble.customContextMenuRequested.connect(lambda pos, mb=message_bubble: self.showContextMenu(pos, mb))
        return message_bubble

    def setBackMessageColor(self, message, color):
        message.m_frame.setStyleSheet(f"background-color: {color}; border-radius: 4px;")

    def setTextMessageColor(self, message, color):
        message.message_label.setStyleSheet(f"color: {color};")

    def scrollToBottomIfNeeded(self, minimum, maximum):
        self.messages_area.verticalScrollBar().setValue(maximum)

    def sendMessage(self):
        text = self.message_input.toPlainText()
        self.hideCharacterInfoSidebar2()
        if text:
            self.message_input.setHtml('<span style="color: white;"></span>')
            if self.attach_image_label.link:
                attachments = [{"type": "TYPE_IMAGE", "url": self.attach_image_label.link}]
                self.addMessage(text, "", is_user=True, attachments=attachments)
                self.chat_thread.send_message(self.character_id, self.chat_id, text, self.voice_enabled, str(self.voice_id), attachments)
                self.attach_image_label.link = ""
                self.attach_image_label.setMinimumSize(0,0)
                self.attach_image_label.setPixmap(QPixmap())
            else:
                self.addMessage(text, "", is_user=True)
                self.chat_thread.send_message(self.character_id, self.chat_id, text, self.voice_enabled, str(self.voice_id))
            if self.mw.recent_chats:
                for i in range(self.mw.recent_chat_scroll_layout.count()):
                    item = self.mw.recent_chat_scroll_layout.itemAt(i)
                    if item and item.widget() and item.widget().objectName() == self.chat_id:
                        recent_card = item.widget()
                        self.mw.recent_chat_scroll_layout.removeWidget(recent_card)
                        self.mw.recent_chat_scroll_layout.insertWidget(0, recent_card)
                        break

    def _copyChat(self, data):
        self.chat_thread.copy_chat_signal.disconnect()
        self.mw.openChat(self.character_id, self.character_name, data.get('new_chat_id'))
        self.mw.showNotification(self.tr("New chat started"))

    def copyChat(self, turn_id):
        self.chat_thread.copy_chat_signal.connect(self._copyChat)
        self.chat_thread.copy_chat(self.chat_id, turn_id)

    def _turnRemove(self, data):
        self.mw.showNotification(self.tr("The message was deleted"))
        self.chat_thread.turn_remove_signal.disconnect()

    def turnRemove(self, turn_id):
        turn_ids = [turn_id]
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item and item.widget() and item.widget().currentWidget().turn_id == turn_id:
                self.chat_thread.turn_remove_signal.connect(self._turnRemove)
                self.chat_thread.turn_remove(self.chat_id, turn_ids)
                item.widget().deleteLater()

    def _rewind(self, data):
        self.mw.showNotification(self.tr("Rewind successfully"))
        self.chat_thread.turn_remove_signal.disconnect()

    def rewind(self, turn_id):
        index = next((i for i, turn in enumerate(self.chat_thread.chat_histories.get(self.chat_id, [])) if turn.get('turn_key', {}).get('turn_id') == turn_id), None)
        turn_ids_for_remove = []

        if index is not None:
            for turn in self.chat_thread.chat_histories[self.chat_id][index + 1:]:
                turn_ids_for_remove.append(turn.get('turn_key', {}).get('turn_id'))
            self.chat_thread.chat_histories[self.chat_id] = self.chat_thread.chat_histories[self.chat_id][:index + 1]

        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item and item.widget() and item.widget().currentWidget().turn_id in turn_ids_for_remove:
                self.chat_thread.turn_remove_signal.connect(self._rewind)
                self.chat_thread.turn_remove(self.chat_id, turn_ids_for_remove)
                item.widget().deleteLater()

    def _turnRegenerate(self, response, turn_id, message_bubble_added):
        command = response['command']
        if command == 'update_turn':
            for i in reversed(range(self.messages_layout.count())):
                item = self.messages_layout.itemAt(i)
                widget = item.widget()
                if hasattr(widget, 'turn_id') and widget.turn_id == response['turn']['turn_key']['turn_id']:
                    message_stacked = widget
                    break

            message_stacked.turn_id = response['turn']['turn_key']['turn_id']

            if not message_bubble_added:
                message = self.createMessage(
                    format_text(response['turn']['candidates'][0]['raw_content'], self.mw.username),
                    response['turn']['turn_key']['turn_id'],
                    False
                )
                self.startTextAnimation(message, response['turn']['candidates'][0]['raw_content'])
            else:
                message = message_stacked.currentWidget()
                label = message.message_label

                if hasattr(label, 'animation_timer'):
                    label.animation_timer.stop()
                    label.is_animating = False

                new_text = format_text(response['turn']['candidates'][0]['raw_content'], self.mw.username)

                if not hasattr(label, 'is_animating'):
                    self.setupAnimation(label)
                    label.setText("")
                    label.target_text = new_text
                    label.current_text = new_text
                    label.current_index = 0
                    label.is_animating = True

                new_text = format_text(response['turn']['candidates'][0]['raw_content'], self.mw.username)
                message.text = new_text
                self.addTextToAnimation(message.message_label, new_text)

                label.animation_timer.start(30)

            message.turn_id = response['turn']['turn_key']['turn_id']
            message.setMinimumHeight(0)
            message.adjustSize()

    def turnRegenerate(self, turn_id):
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item and item.widget() and item.widget().turn_id == turn_id:
                self.chat_thread.turn_regenerate_signal.connect(self._turnRegenerate)
                self.chat_thread.turn_regenerate(self.character_id, self.chat_id, turn_id, tts_enabled=self.voice_enabled)
            elif item and item.spacerItem():
                pass

    def _editMessage(self, turn_id):
        self.chat_thread.edit_message_signal.connect(self.__editMessage)
        self.chat_thread.edit_message(self.chat_id, turn_id, self.message_input.toPlainText())

    def editMessage(self, turn_id):
        for i in reversed(range(self.messages_layout.count())):
            item = self.messages_layout.itemAt(i)
            widget = item.widget()
            if hasattr(widget, 'turn_id') and widget.turn_id == turn_id:
                message_stacked = widget
                break

        message = message_stacked.currentWidget()
        self.message_input.setText(message.text)
        self.message_input.keyPress = lambda: self._editMessage(turn_id)

    def __editMessage(self, response):
        self.chat_thread.edit_message_signal.disconnect()
        self.message_input.setText(None)
        self.message_input.keyPress = lambda: self.sendMessage()
        for i in reversed(range(self.messages_layout.count())):
            item = self.messages_layout.itemAt(i)
            widget = item.widget()
            if hasattr(widget, 'turn_id') and widget.turn_id == response['turn']['turn_key']['turn_id']:
                message_stacked = widget
                break

        message = message_stacked.currentWidget()

        pci = response.get("turn", {}).get('primary_candidate_id')
        for candidate in response.get("turn", {}).get('candidates', []):
            if candidate.get('candidate_id', pci) == pci:
                new_text = format_text(candidate.get('raw_content', ''), self.mw.username)
                message.text = new_text
                message.message_label.setText(new_text)

        message.setMinimumHeight(0)
        message.adjustSize()

    def showContextMenu(self, pos, message_bubble):
        def copy(text):
            QApplication.clipboard().setText(text)
            self.mw.showNotification(self.tr("Message copied to clipboard"))

        context_menu = Menu(self)

        copy_action = QAction(self.tr("Copy Message"), self)
        copy_action.triggered.connect(lambda event: copy(message_bubble.message_label.text()))
        context_menu.addAction(copy_action)

        if message_bubble.turn_id:
            delete_action = QAction(self.tr("Delete Message"), self)
            delete_action.triggered.connect(lambda event: self.turnRemove(message_bubble.turn_id))
            context_menu.addAction(delete_action)

            rewind_action = QAction(self.tr("Rewind to here"), self)
            rewind_action.triggered.connect(lambda event: self.rewind(message_bubble.turn_id))
            context_menu.addAction(rewind_action)

            new_chat_here_action = QAction(self.tr("New chat from here"), self)
            new_chat_here_action.triggered.connect(lambda event: self.copyChat(message_bubble.turn_id))
            context_menu.addAction(new_chat_here_action)

            regenerate_action = QAction(self.tr("Regenerate"), self)
            regenerate_action.triggered.connect(lambda event: self.turnRegenerate(message_bubble.turn_id))
            if not message_bubble.is_user: context_menu.addAction(regenerate_action)

            edit_message_action = QAction(self.tr("Edit message"), self)
            edit_message_action.triggered.connect(lambda event: self.editMessage(message_bubble.turn_id))
            context_menu.addAction(edit_message_action)

        context_menu.exec(message_bubble.mapToGlobal(pos))

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if self.cis_visible:
            global_click_pos = event.globalPosition().toPoint()
            sidebar_global_pos = self.character_info_sidebar.mapToGlobal(self.character_info_sidebar.rect().topLeft())
            sidebar_rect = QRect(sidebar_global_pos, self.character_info_sidebar.size())
            if not sidebar_rect.contains(global_click_pos):
                self.hideCharacterInfoSidebar2()

    def hideEvent(self, a0):
        super().hideEvent(a0)
        if hasattr(self, 'recent_card') and not self.scene_id:
            self.recent_card.setCheckable(False)

    def closeEvent(self, a0):
        if self._detach:
            a0.ignore()
            self._detach = False
            self.attach_signal.emit(True)
        else:
            super().closeEvent(a0)
            self.deleteLater()
