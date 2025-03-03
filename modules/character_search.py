import io, asyncio, threading, json, re, os, time
import requests

import sounddevice as sd
import soundfile as sf
import translators as ts

from characterai import aiocai
from PyQt6.QtWidgets import (QTabWidget,
                             QHBoxLayout, 
                             QLabel, QLineEdit, 
                             QPushButton, 
                             QVBoxLayout, 
                             QWidget, QMessageBox,
                             QListWidget, 
                             QListWidgetItem,
                             QGraphicsOpacityEffect,
                             QGridLayout, QScrollArea)
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QMouseEvent, QLinearGradient, QPainterPath, QFont
from PyQt6.QtCore import QLocale, Qt, QPropertyAnimation, QTimer, QRectF

from modules.config import getconfig
from modules.CustomCharAI import Sync as ccas
from modules.CustomCharAI import Async as ccaa
from modules.ets import translations
from modules.other import message_box
from modules.QCustom import ResizableButton, ResizableLineEdit
from modules.QThreads import ImageLoaderThread, LoadChatThread, SearchLoaderThread, FileLoaderThread, AudioPlayerThread

lang = getconfig("language", QLocale.system().name())
backcolor = getconfig("backgroundcolor")
buttoncolor = getconfig("buttoncolor")
buttontextcolor = getconfig("buttontextcolor")
labelcolor = getconfig("labelcolor")
emiliaicon = "images/emilia.png"
trls = translations(lang)

def color_avatar(avatar_label, avatar_w, avatar_h, name, radius=100, label=True):
    pixmap = QPixmap(avatar_w, avatar_h)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    gradient = QLinearGradient(0, 0, avatar_w, avatar_h * 0.7)
    gradient.setColorAt(0, QColor("#f47c3b"))
    gradient.setColorAt(1, Qt.GlobalColor.transparent)

    painter.fillRect(pixmap.rect(), QBrush(gradient))

    font = QFont("Arial", int(avatar_h / 3))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))

    first_letter = name[0].upper() if name else ""
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, first_letter)
    painter.end()

    def round_pixmap(source_pixmap: QPixmap) -> QPixmap:
        rounded = QPixmap(avatar_w, avatar_h)
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, source_pixmap.width(), source_pixmap.height()), radius, radius)
        painter.setClipPath(path)

        painter.drawPixmap(0, 0, source_pixmap)
        painter.end()

        return rounded

    rounded_pixmap = round_pixmap(pixmap)
    if label: avatar_label.setPixmap(rounded_pixmap)
    return rounded_pixmap

class MessageWidget(QWidget):
    def __init__(self, chat, data = None, message_type = None):
        super().__init__()
        self.threads = []
        self.data = data
        self.chat = chat
        self.message_type = message_type
        self.character_id = None
        self.message_id = None
        self.translated = False; self.formatted_tr_text = ""
        if self.message_type is None:
            self.character_id = data['author']['author_id']
            self.message_id = data['turn_key']

        self.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #333;
            }
        """)

        layout = QHBoxLayout()

        self.author_name = data['author']['name']
        self.raw_content = data['candidates'][0]['raw_content']

        self.formatted_text = self.format_text(self.raw_content)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(50, 50)

        self.name_label = QLabel(f"{self.author_name}")
        self.name_label.setFixedSize(50, 50)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 13px; background-color: #fff; border-radius: 10px;")

        self.avatar_name_layout = QVBoxLayout()
        self.avatar_name_layout.addWidget(self.avatar_label)
        self.avatar_name_layout.addWidget(self.name_label)

        text_layout = QVBoxLayout()
        if self.message_type:
            self.text_label = QLabel(f"{self.formatted_text}")
            self.text_label.setStyleSheet("font-size: 16px; background-color: #e1f5fe; border-radius: 10px; padding: 5px;")
            text_layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignHCenter)
        else:
            self.text_label = QLabel(f"{self.formatted_text}")
            self.text_label.setStyleSheet("font-size: 16px; background-color: #fff; border-radius: 10px; padding: 5px;")
            text_layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignHCenter)
        self.text_label.setWordWrap(True)

        if self.message_type:
            layout.addLayout(text_layout)
        else:
            if len(self.text_label.text()) > 80:
                layout.addLayout(self.avatar_name_layout)
            else: 
                layout.addWidget(self.avatar_label)
            layout.addLayout(text_layout)
        self.setLayout(layout)
        self.load_image_async()

    def load_image_async(self):
        self.avatar_url = self.chat.character.get("avatar_file_name")
        if self.avatar_url:
            url = f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0"
            thread = ImageLoaderThread(url, 50, 50)
            thread.radius = 25
            thread.image_loaded.connect(self.avatar_label.setPixmap)
            self.threads.append(thread)
            thread.start()
        else:
            color_avatar(self.avatar_label, 50, 50, self.author_name)

    def round_corners(self, pixmap, radius):
        size = pixmap.size()
        mask = QPixmap(size)
        mask.fill(Qt.GlobalColor.transparent)

        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawRoundedRect(0, 0, size.width(), size.height(), radius, radius)
        painter.end()

        pixmap.setMask(mask.mask())
        return pixmap

    def format_text(self, text):
        pattern = re.compile(r"\*(.*?)\*")
        html_text = pattern.sub(r"<i>\1</i>", text)
        html_text = html_text.replace("\n", "<br>")
        return html_text

    def adjust_size(self):
        item = self.chat.list_widget.itemAt(self.pos())
        if item:
            item.setSizeHint(self.sizeHint())

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.translated:
                if not self.formatted_tr_text:
                    tr_text = ts.translate_text(self.raw_content, to_language=trls.slang, translator="google")
                    self.formatted_tr_text = self.format_text(tr_text)
                self.text_label.setText(self.formatted_tr_text)
                self.translated = True
            else:
                self.text_label.setText(self.formatted_text)
                self.translated = False
            self.adjust_size()

class ChatWithCharacter(QWidget):
    def __init__(self, character_id=getconfig("char", configfile="charaiconfig.json")):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle(f"Emilia: Chat With...")
        self.character_id = character_id
        self.account_id = None
        self.trl = "ChatWithCharacter"
        self.client = aiocai.Client(getconfig("client", configfile="charaiconfig.json"))
        self.ccaa = ccaa()

        self.setGeometry(300, 300, 800, 400)

        self.list_widget = QListWidget()
        self.new_chat_button = QPushButton(trls.tr("MainWindow", "reset_chat"))
        self.new_chat_button.clicked.connect(self.new_chat)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.list_widget)
        self.main_layout.addWidget(self.new_chat_button)

        self.setLayout(self.main_layout)

        self.load_chat()

    def load_chat(self):
        self.load_chat_thread = LoadChatThread(self, self.client, self.character_id)
        self.load_chat_thread.chatLoaded.connect(self.populate_list)
        self.load_chat_thread.chatLoaded.connect(lambda data: self.list_widget.setEnabled(True))
        self.load_chat_thread.errorOccurred.connect(lambda error: self.new_chat())
        self.load_chat_thread.start()

    def populate_list(self, data):
        self.list_widget.clear()

        if data == []:
            QMessageBox.information(self, "Problem", "The chat history is empty")
            self.close()
            return

        for turn in data:
            if turn['author'].get('is_human', False):
                self.account_id = turn['author']['author_id']
                custom_widget = MessageWidget(self, turn, True)
            else:
                custom_widget = MessageWidget(self, turn, None)
            item = QListWidgetItem()
            item.setSizeHint(custom_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, custom_widget)
        self.list_widget.scrollToBottom()

    def on_chat_load_finish(self):
        self.list_widget.setEnabled(True)

    def new_chat(self):
        self.list_widget.setEnabled(False)
        self.new_chat_button.setEnabled(False)
        threading.Thread(target=lambda: asyncio.run(self.start_new_chat())).start()

    async def start_new_chat(self):
            if self.account_id is None:
                self.account = await self.ccaa.get_me()
                self.account_id = self.account["id"]
            async with await self.client.connect() as chat:
                await chat.new_chat(self.character_id, self.account_id)
            self.on_new_chat_finish()

    def on_new_chat_finish(self):
        self.list_widget.clear()
        self.list_widget.setEnabled(True)
        self.new_chat_button.setEnabled(True)

class MainMessageWidget(QWidget):
    def __init__(self, parent, mode, text, audio_len, new, translated = False):
        super().__init__()
        self.mode = mode
        self.text = text
        self.parent = parent
        self.audio_len = audio_len
        self.new = new
        self.translated = translated

        self.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #333;
            }
        """)

        layout = QHBoxLayout()

        self.formatted_text = self.format_text(self.text)
        self.index = 0
        self.total_duration = audio_len
        self.interval = self.total_duration // len(self.formatted_text) // 28

        text_layout = QVBoxLayout()
        self.text_label = QLabel()
        if mode == "human":
            self.interval = self.interval * 50
            self.text_label.setStyleSheet("font-size: 16px; background-color: #e1f5fe; border-radius: 10px; padding: 5px;")
            text_layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignHCenter)
            if new:
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.show_next_char)
                self.timer.start(self.interval)
            else:
                self.text_label.setText(self.formatted_text)
        elif mode == "sys":
            self.text_label.setStyleSheet("color: gray; font-style: italic; font-size: 12px; background-color: white; border-radius: 10px; padding: 5px;")
            text_layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
            self.text_label.setText(self.formatted_text)
        elif mode == "ai":
            self.text_label.setStyleSheet("font-size: 16px; background-color: #fff; border-radius: 10px; padding: 5px;")
            text_layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignHCenter)
            if new:
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.show_next_char)
                self.timer.start(self.interval)
            else:
                self.text_label.setText(self.formatted_text)
        self.text_label.setWordWrap(True)

        layout.addLayout(text_layout)
        self.setLayout(layout)

    def show_next_char(self):
        item = self.parent.chat_widget
        if self.index < len(self.formatted_text):
            self.text_label.setText(self.text_label.text() + self.formatted_text[self.index])
            self.index += 1
            self.adjust_size()
            item.scrollToBottom()
        else:
            self.timer.stop()
            item.scrollToBottom()

    def adjust_size(self):
        item = self.parent.chat_widget.itemAt(self.pos())
        if item:
            item.setSizeHint(self.sizeHint()) 

    def format_text(self, text):
        pattern = re.compile(r"\*(.*?)\*")
        html_text = pattern.sub(r"<i>\1</i>", text)
        html_text = html_text.replace("\n", "<br>")
        return html_text

class NewCharacterEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.ccas = ccas()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Character Editor")
        self.setFixedWidth(300)

        self.addchar_button = QPushButton(trls.tr("CharEditor", "add_character"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        layout = QVBoxLayout()


        id_layout = QHBoxLayout()
        self.id_entry = QLineEdit()
        self.id_entry.setPlaceholderText("ID...")

        id_layout.addWidget(QLabel(trls.tr("MainWindow", "character_id")))
        id_layout.addWidget(self.id_entry)
        layout.addLayout(id_layout)


        buttons_layout = QHBoxLayout()
        self.add_character_button = QPushButton(trls.tr("CharEditor", "add_character"))
        self.add_character_button.clicked.connect(self.add_character)

        buttons_layout.addWidget(self.add_character_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
    
        if backcolor:
            self.set_background_color(QColor(backcolor))
        if buttoncolor:
            self.set_button_color(QColor(buttoncolor))
        if labelcolor:
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor:
            self.set_button_text_color(QColor(buttontextcolor))
    
    def add_character(self):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        charid = self.id_entry.text().replace("https://character.ai/chat/", "") 
        character = self.ccas.get_character(charid)
        data.update({charid: {"name": character["name"], "char": charid, "avatar_url": character["avatar_file_name"], "description": character["description"], "author": character["user__username"]}})
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        pixmap = QPixmap()
        text = trls.tr("CharEditor", "yourchar") + character["name"] + trls.tr("CharEditor", "withid") + charid + trls.tr("CharEditor", "added")

        if character.get('avatar_file_name'):
            thread = ImageLoaderThread(f"https://characterai.io/i/80/static/avatars/{character['avatar_file_name']}?webp=true&anim=0", 80, 80)
            thread.image_loaded.connect(lambda image: message_box(trls.tr("CharEditor", "character_added"), text, image, image, self))
            thread.error.connect(lambda error: QMessageBox.critical(self, "Error", error))
            thread.start()
        else:
            avatar = color_avatar(QMessageBox, 80, 80, character["name"], False)
            message_box(trls.tr("CharEditor", "character_added"), text, avatar, avatar, self)

        self.close()

    def set_background_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QWidget {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_text_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_label_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QWidget {{
                color: {color.name()};
            }}
        """
        new_style_sheet2 = f"""
            QLineEdit {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet + new_style_sheet2)

    def styles_reset(self):
        self.setStyleSheet("")

class CharacterWidget(QWidget):
    def __init__(self, parent, data, mode):
        super().__init__()
        self.threads = []
        self.data = data
        self.local_data = None
        if mode != "firstlaunch":
            self.local_data = parent.local_data
        self.parent = parent
        self.mode = mode
        self.tts = getconfig("tts", "charai")
        self.trl = "CharEditor"
        self.ccas = ccas()

        layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setFixedSize(80, 80)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        text_buttons_layout = QHBoxLayout()
        local_text_buttons_layout = QVBoxLayout()

        self.text_label = QLabel()
        self.text_label.setWordWrap(True)

        buttons_layout = QVBoxLayout()
        self.add_without_voice_button = ResizableButton(trls.tr(self.trl, "add_without_voice"))
        self.add_without_voice_button.setFixedWidth(200)
        self.add_without_voice_button.clicked.connect(self.add_without_voice)

        self.search_voice_button = ResizableButton(trls.tr(self.trl, "search_voice"))
        self.search_voice_button.setFixedWidth(200)
        self.search_voice_button.clicked.connect(self.add_with_voice)

        self.voice_entry_button = ResizableLineEdit()
        self.voice_entry_button.setFixedWidth(200)
        self.voice_entry_button.setText(self.data.get("elevenlabs_voice", ""))
        self.voice_entry_button.textChanged.connect(self.speaker_entry)
        self.voice_entry_button.setPlaceholderText("Enter the name of the voice")

        self.set_voice_button = ResizableButton(trls.tr(self.trl, "set_voice"))
        self.set_voice_button.setFixedWidth(200)
        self.set_voice_button.setEnabled(False)
        self.set_voice_button.clicked.connect(self.add_with_elevenlabs_voice)

        local_seldel_buttons = QHBoxLayout()

        if mode != "local":
            self.select_char_button = ResizableButton(trls.tr(self.trl,"select"))
        else:
            self.select_char_button = QPushButton(trls.tr(self.trl,"select"))
        self.select_char_button.clicked.connect(self.select_char)
        local_seldel_buttons.addWidget(self.select_char_button)

        self.show_chat_button = QPushButton(trls.tr("MainWindow", "show_chat"))
        self.show_chat_button.clicked.connect(self.open_chat)
        local_seldel_buttons.addWidget(self.show_chat_button)

        self.delete_char_button = QPushButton(trls.tr(self.trl,"delete"))
        self.delete_char_button.clicked.connect(self.local_delete_character)
        local_seldel_buttons.addWidget(self.delete_char_button)

        self.edit_voice_button = ResizableButton(trls.tr(self.trl,"edit_voice"))
        self.edit_voice_button.clicked.connect(self.local_add_char_voice)
        self.edit_voice_button.setFixedWidth(200)

        self.add_voice_button = ResizableButton(trls.tr(self.trl,"add_voice"))
        self.add_voice_button.setFixedWidth(200)
        self.add_voice_button.clicked.connect(self.local_add_char_voice)

        self.delete_voice_button = ResizableButton(trls.tr(self.trl,"delete_voice"))
        self.delete_voice_button.setFixedWidth(200)
        self.delete_voice_button.clicked.connect(self.local_delete_voice)
        if self.data.get("voiceid", "") == "":
            self.delete_voice_button.setEnabled(False)

        local_text_buttons_layout.addWidget(self.text_label)
        if mode == "local":
            text_buttons_layout.addLayout(local_text_buttons_layout)
        else:
            text_buttons_layout.addWidget(self.text_label)
        local_text_buttons_layout.addLayout(local_seldel_buttons)
        
        if mode == "network":
            self.author_label = trls.tr(self.trl, "author_label")
            self.char = data.get("external_id")
            self.name = data.get("participant__name", "No Name")
            self.title = data.get("title", "None")
            self.chats = data.get("score", "0")
            self.author = data.get("user__username", "Unknown")
            self.description = data.get("description", "None")
            self.avatar_url = data.get("avatar_file_name", "")

            self.full_description = self.description
            self.local_chars = self.local_data.keys()
            if f"{self.description}" != "None" and len(f"{self.description}") > 220:
                self.description = self.description[:220] + "..."
            if self.char in self.local_chars:
                buttons_layout.addWidget(self.select_char_button)
                self.select_char_button.setFixedWidth(200)
            else:
                if self.tts == "charai":
                    buttons_layout.addWidget(self.search_voice_button)
                    buttons_layout.addWidget(self.add_without_voice_button)
                elif self.tts == "elevenlabs":
                    buttons_layout.addWidget(self.voice_entry_button)
                    buttons_layout.addWidget(self.set_voice_button)

            if f"{self.title}" == "None" or f"{self.title}" == "":
                if f"{self.description}" == "None" or f"{self.description}" == "":
                    text = f"<b>{self.name}</b><br>{self.chats} {trls.tr(self.trl, 'chats_label')} • {self.author_label}: {self.author}"
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f"<b>{self.name}</b><br>{self.description}<br>{self.chats} {trls.tr(self.trl, 'chats_label')} • {self.author_label}: {self.author}"
            else:
                if f"{self.description}" == "None" or f"{self.description}" == "":
                    text = f"<b>{self.name}</b> - {self.title}<br>{self.chats} {trls.tr(self.trl, 'chats_label')} • {self.author_label}: {self.author}"
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f"<b>{self.name}</b> - {self.title}<br>{self.description}<br>{self.chats} {trls.tr(self.trl, 'chats_label')} • {self.author_label}: {self.author}"
        elif mode == "recent":
            self.char = data.get("character_id")
            self.name = data.get("character_name", "No Name")
            self.avatar_url = data.get("character_avatar_uri", "")
            self.local_chars = self.local_data.keys()

            if self.tts == "charai":
                self.select_char_button.setFixedWidth(200)
                self.show_chat_button.setFixedWidth(200)
            elif self.tts == "elevenlabs":
                self.select_char_button.setFixedWidth(200)
                self.show_chat_button.setFixedWidth(200)

            if self.char in self.local_chars:
                buttons_layout.addWidget(self.select_char_button)
            else:
                if self.tts == "charai":
                    buttons_layout.addWidget(self.search_voice_button)
                    buttons_layout.addWidget(self.add_without_voice_button)
                elif self.tts == "elevenlabs":
                    buttons_layout.addWidget(self.voice_entry_button)
                    buttons_layout.addWidget(self.set_voice_button)
            buttons_layout.addWidget(self.show_chat_button)

            text = f"<b>{self.name}</b>"
        elif mode == "recommend":
            self.char = data.get("external_id")
            self.name = data.get("participant__name", "No Name")
            self.avatar_url = data.get("avatar_file_name", "")

            if self.tts == "charai":
                buttons_layout.addWidget(self.search_voice_button)
                buttons_layout.addWidget(self.add_without_voice_button)
            elif self.tts == "elevenlabs":
                buttons_layout.addWidget(self.voice_entry_button)
                buttons_layout.addWidget(self.set_voice_button)

            text = f"<b>{self.name}</b>"
        elif mode == "local":
            self.author_label = trls.tr(self.trl, "author_label")
            self.name = data.get("name", "No Name")
            self.char = data.get("char", "")
            self.title = data.get("title", "None")
            self.author = data.get("author", "Unknown")
            self.description = data.get("description", "None")
            self.avatar_url = data.get("avatar_url", "")
            self.voiceid = data.get("voiceid", "")
            self.image_label.setFixedSize(80, 80)

            self.full_description = self.description
            if self.tts == "charai":
                if f"{self.description}" != "None" and len(f"{self.description}") > 220:
                    self.description = self.description[:220] + "..."
                if self.voiceid == "":
                    buttons_layout.addWidget(self.add_voice_button)
                else:
                    buttons_layout.addWidget(self.edit_voice_button)
                buttons_layout.addWidget(self.delete_voice_button)
            elif self.tts == "elevenlabs":
                if f"{self.description}" != "None" and len(f"{self.description}") > 220:
                    self.description = self.description[:220] + "..."
                buttons_layout.addWidget(self.voice_entry_button)
                buttons_layout.addWidget(self.set_voice_button)

            if f"{self.title}" == "None" or f"{self.title}" == "":
                if f"{self.description}" == "None" or f"{self.description}" == "":
                    text = f"<b>{self.name}</b><br>• {self.author_label}: {self.author}"
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f"<b>{self.name}</b><br>{self.description}<br> • {self.author_label}: {self.author}"
            else:
                if f"{self.description}" == "None" or f"{self.description}" == "":
                    text = f"<b>{self.name}</b> - {self.title}<br> • {self.author_label}: {self.author}"
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f"<b>{self.name}</b> - {self.title}<br>{self.description}<br>• {self.author_label}: {self.author}"
        elif mode == "firstlaunch":
            self.author_label = trls.tr(self.trl, "author_label")
            self.char = data.get("external_id")
            self.name = data.get("participant__name", "No Name")
            self.title = data.get("title", "None")
            self.chats = data.get("score", "0")
            self.author = data.get("user__username", "Unknown")
            self.description = data.get("description", "None")
            self.avatar_url = data.get("avatar_file_name", "")

            self.image_label.setFixedSize(80, 80)

            self.full_description = self.description
            if f"{self.description}" != "None" and len(f"{self.description}") > 220:
                self.description = self.description[:220] + "..."
            buttons_layout.addWidget(self.search_voice_button)
            buttons_layout.addWidget(self.add_without_voice_button)

            if f"{self.title}" == "None" or f"{self.title}" == "":
                if f"{self.description}" == "None" or f"{self.description}" == "":
                    text = f"<b>{self.name}</b><br>{self.chats} {trls.tr(self.trl, 'chats_label')} • {self.author_label}: {self.author}"
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f"<b>{self.name}</b><br>{self.description}<br>{self.chats} {trls.tr(self.trl, 'chats_label')} • {self.author_label}: {self.author}"
            else:
                if f"{self.description}" == "None" or f"{self.description}" == "":
                    text = f"<b>{self.name}</b> - {self.title}<br>{self.chats} {trls.tr(self.trl, 'chats_label')} • {self.author_label}: {self.author}"
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f"<b>{self.name}</b> - {self.title}<br>{self.description}<br>{self.chats} {trls.tr(self.trl, 'chats_label')} • {self.author_label}: {self.author}"

        self.threads = []
        if f"{self.avatar_url}" != "None" and f"{self.avatar_url}" != "" :
            thread = ImageLoaderThread(f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0", 80, 80)
            thread.image_loaded.connect(self.image_label.setPixmap)
            self.threads.append(thread)
            thread.start()
        else:
            color_avatar(self.image_label, 80, 80, self.name)
        self.text_label.setText(text)

        text_buttons_layout.addLayout(buttons_layout)
        layout.addLayout(text_buttons_layout)
        self.setLayout(layout)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode == "local":
                self.select_char()
                return
            self.add_without_voice()
        elif event.button() == Qt.MouseButton.RightButton:
            self.open_chat()

    def open_chat(self):
        window = ChatWithCharacter(self.char)
        window.show()

    def load_image_async(self, url):
        if url:
            thread = ImageLoaderThread(url, 80, 80)
            thread.image_loaded.connect(self.image_label.setPixmap)
            self.threads.append(thread)
            thread.start()
        else:
            color_avatar(self.image_label, 80, 80, self.name)

    def round_corners(self, pixmap, radius):
        size = pixmap.size()
        mask = QPixmap(size)
        mask.fill(Qt.GlobalColor.transparent)

        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawRoundedRect(0, 0, size.width(), size.height(), radius, radius)
        painter.end()

        pixmap.setMask(mask.mask())
        return pixmap

    def speaker_entry(self):
        if self.voice_entry_button.text() == "":
            self.set_voice_button.setEnabled(False)
        elif self.voice_entry_button.text() != "":
            self.set_voice_button.setEnabled(True)

    def add_with_voice(self):
        self.load_data()
        if self.mode == "recent" or self.mode == "recommend":
            self.get_recent_data()

        self.datafile.update({self.char: {"name": self.name, "char": self.char, "avatar_url": self.avatar_url, "description": self.description, "title": self.title, "author": self.author}})
        self.save_data()

        if self.mode != "firstlaunch":
            self.parent.close()
        VoiceSearch(self.char, self.name).show()

    def add_with_elevenlabs_voice(self):
        self.load_data()
        if self.mode == "recent" or self.mode == "recommend":
            self.get_recent_data()

        self.datafile.update({self.char: {"name": self.name, "char": self.char, "avatar_url": self.avatar_url, "description": self.description, "title": self.title, "author": self.author, "elevenlabs_voice": self.voice_entry_button.text()}})
        self.save_data()

        if self.mode != "firstlaunch":
            self.parent.close()

    def add_without_voice(self):
        self.load_data()
        if self.mode == "recent" or self.mode == "recommend":
            self.get_recent_data()

        self.datafile.update({self.char: {"name": self.name, "char": self.char, "avatar_url": self.avatar_url, "description": self.description, "title": self.title, "author": self.author}})
        self.save_data()

        QMessageBox.information(self, trls.tr(self.trl, "character_added"), trls.tr(self.trl, "character_added_text"))

        self.select_char()

    def load_data(self):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                self.datafile = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.datafile = {}

    def save_data(self):
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(self.datafile, f, ensure_ascii=False, indent=4)

    def get_recent_data(self):
        char = self.ccas.get_character(self.char)
        self.name = char.get("participant__name", "No Name")
        self.author = char.get("user__username", "Unknown")
        self.avatar_url = char.get("avatar_file_name", "")
        self.description = char.get("description", "")
        self.title = char.get("title", "")

    def local_add_char_voice(self):
        if self.mode != "firstlaunch":
            self.parent.close()
        VoiceSearch(self.char, self.name).show()

    def local_delete_character(self):
        self.load_data()
        del self.datafile[self.char]
        self.save_data()
        self.parent.parent.refreshcharsinmenubar()
        self.parent.load_local_data()
        self.parent.populate_local_list()

    def local_delete_voice(self):
        self.load_data()
        if self.char in self.datafile:
            if "voiceid" in self.datafile[self.char]:
                del self.datafile[self.char]["voiceid"]
        self.save_data()
        self.parent.parent.refreshcharsinmenubar()
        self.parent.load_local_data()
        self.parent.populate_local_list()

    def select_char(self):
        if self.mode == "network" or self.mode == "recent" or self.mode == "recommend":
            self.load_data()
            if self.tts == "charai":
                self.voiceid = self.datafile[self.char].get("voiceid", "")
            elif self.tts == "elevenlabs":
                self.voiceid = self.datafile[self.char].get("elevenlabs_voice", "")
        elif self.mode == "local":
            if self.tts == "charai":
                self.voiceid = self.data.get("voiceid", "")
            elif self.tts == "elevenlabs":
                self.voiceid = self.data.get("elevenlabs_voice", "")
        self.parent.parent.charai_char_entry.setText(self.char)
        self.parent.parent.charaitts_voice_entry.setText(self.voiceid)
        self.parent.close()

    def closeEvent(self, event):
        for thread in self.threads:
            thread.quit()
        super().closeEvent(event)

class CharacterSearch(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Character Search")
        self.setMinimumHeight(700)
        self.setMinimumWidth(1200)

        self.addchar_button = QPushButton(trls.tr("CharEditor", "add_character"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.trl = "CharEditor"
        self.threads = []

        main_layout = QVBoxLayout(self)
        self.parent = parent

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)


        self.network_tab = QWidget()
        self.network_layout = QVBoxLayout(self.network_tab)
        self.network_search_input = QLineEdit()
        self.network_search_input.setPlaceholderText(trls.tr(self.trl, "network_search_input"))
        self.network_search_input.returnPressed.connect(self.search_and_load)
        self.network_layout.addWidget(self.network_search_input)
        self.network_scroll_area = QScrollArea()
        self.network_scroll_area.setWidgetResizable(True)
        self.network_content_widget = QWidget()
        self.network_list_layout = QVBoxLayout(self.network_content_widget)
        self.network_scroll_area.setWidget(self.network_content_widget)
        self.network_layout.addWidget(self.network_scroll_area)

        self.add_another_charcter_button = QPushButton(trls.tr(self.trl, "add_another_charcter_button"))
        self.add_another_charcter_button.clicked.connect(self.open_NewCharacherEditor)
        self.network_layout.addWidget(self.add_another_charcter_button)

        self.local_tab = QWidget()
        self.local_layout = QVBoxLayout(self.local_tab)
        self.local_scroll_area = QScrollArea()
        self.local_scroll_area.setWidgetResizable(True)
        self.local_content_widget = QWidget()
        self.local_list_widget = QGridLayout(self.local_content_widget)
        self.local_scroll_area.setWidget(self.local_content_widget)
        self.local_layout.addWidget(self.local_scroll_area)

        self.tab_widget.addTab(self.network_tab, trls.tr(self.trl, "network_tab"))
        self.tab_widget.addTab(self.local_tab, trls.tr(self.trl, "local_tab"))

        main_layout.addWidget(self.tab_widget)

        self.setLayout(main_layout)

        if backcolor:
            self.set_background_color(QColor(backcolor))
        if buttoncolor:
            self.set_button_color(QColor(buttoncolor))
        if labelcolor:
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor:
            self.set_button_text_color(QColor(buttontextcolor))

        self.recommend_recent_items = []

        self.load_local_data()
        self.populate_recent_list()
        self.populate_recommend_list()

    def open_NewCharacherEditor(self):
        window = NewCharacterEditor()
        window.show()
        self.close()

    def populate_list(self, data_list, mode, grid_layout):
        while grid_layout.count():
            item = grid_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        if isinstance(data_list, list):
            for data in data_list:
                character_widget = CharacterWidget(self, data, mode)
                grid_layout.addWidget(character_widget)
        else:
            if data_list.get('characters'):
                for data in data_list.get('characters', {}):
                    character_widget = CharacterWidget(self, data, mode)
                    grid_layout.addWidget(character_widget)
            else:
                for key, data in data_list.items():
                    character_widget = CharacterWidget(self, data, mode)
                    grid_layout.addWidget(character_widget)

    def populate_category_header(self, category_name):
        header_item = QListWidgetItem()
        header_widget = QLabel(f"<b>{category_name}</b>")
        header_widget.setStyleSheet("font-size: 15px; font-weight: bold;")
        header_widget.setFixedHeight(30)
        header_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_item.setSizeHint(header_widget.sizeHint())

    def populate_network_list(self, data):
        self.network_data = data
        if not self.network_data or not isinstance(self.network_data, list):
            return

        self.populate_list(self.network_data[0].get("result", {}).get("data", {}).get("json", []).get('characters', []), "network", self.network_list_layout)

        self.network_list_layout.setEnabled(True)
        self.network_search_input.returnPressed.connect(self.search_and_load)

    def populate_recent_list(self):
        self.populate_category_header(trls.tr(self.trl, "recent_chats"))
        if self.parent.recent_chats:
            self.populate_list(self.parent.recent_chats, "recent", self.network_list_layout)
        else:
            self.populate_category_header(f"{trls.tr(self.trl, 'empty_chats')}... <(＿　＿)>")

    def populate_recommend_list(self):
        self.populate_category_header(trls.tr(self.trl, "recommend_chats"))
        if self.parent.recommend_chats:
            self.populate_list(self.parent.recommend_chats, "recommend", self.network_list_layout)
        else:
            self.populate_category_header(f"{trls.tr(self.trl, 'empty_chats')}... <(＿　＿)>")

    def populate_local_list(self):
        if not self.local_data:
            return
        self.populate_list(self.local_data, "local", self.local_list_widget)

    def on_tab_changed(self, index):
        if index == 1:
            self.populate_local_list()

    def search_and_load(self):
        search_query = self.network_search_input.text().strip()
        if not search_query:
            return
        
        self.add_another_charcter_button.setVisible(False)

        self.network_list_layout.setEnabled(False)
        self.network_search_input.returnPressed.disconnect()

        try:
            url = f"https://character.ai/api/trpc/search.search?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{search_query}%22%7D%7D%7D"

            search_thread = SearchLoaderThread(url, query=search_query, cache_dir="cache/search_character")
            search_thread.data.connect(lambda data: self.populate_network_list(data))
            search_thread.error.connect(lambda error: QMessageBox.critical(self, trls.tr("Errors", "Label"), error))
            self.threads.append(search_thread)
            search_thread.start()

        except Exception as e:
            QMessageBox.critical(self, trls.tr("Errors", "Label"), f"Error when executing the request: {e}")

    def load_local_data(self):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                self.local_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.local_data = {}

    def save_local_data(self):
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(self.local_data, f, ensure_ascii=False, indent=4)

    def set_background_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QWidget {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_text_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_label_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QWidget {{
                color: {color.name()};
            }}
        """
        new_style_sheet2 = f"""
            QLineEdit {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet + new_style_sheet2)

    def closeEvent(self, event):
        if self.parent:
            self.parent.refreshcharsinmenubar()
        super().closeEvent(event)

    def styles_reset(self):
        self.setStyleSheet("")

class VoiceSearch(QWidget):
    cache_dir = "cache/search_voice"
    save_cache_status = getconfig("save_cache", True)

    def __init__(self, character_id, character_name="", main_window=False, parent=None):
        super().__init__()
        self.character_id = character_id
        self.character_name = character_name
        self.main_window = main_window
        self.parent = parent
        self.data = None
        self.played = False
        self.audio_thread = None
        self.trl = "CharEditor"
        self.threads = []

        self.CACHE_TTL = 86400 # in seconds

        os.makedirs(self.cache_dir, exist_ok=True)

        self.setWindowTitle("Emilia: Voice Search")
        self.setWindowIcon(QIcon(emiliaicon))
        self.setGeometry(300, 300, 800, 400)

        self.addchar_button = QPushButton(trls.tr("CharEditor", "add_character"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.search_and_load)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.display_details)

        self.details_label = QLabel()
        self.details_label.setWordWrap(True)

        self.preview_text_label = QLabel()

        self.play_button = QPushButton(trls.tr(self.trl, "play_an_example"))
        self.play_button.clicked.connect(self.play_audio)
        self.play_button.setEnabled(False)

        self.select_button = QPushButton(trls.tr(self.trl, "select"))
        self.select_button.clicked.connect(self.addcharvoice)
        self.select_button.setEnabled(False)

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.select_button)


        main_layout = QVBoxLayout()
        main_layout.addWidget(self.search_input)
        main_layout.addWidget(self.list_widget)
        main_layout.addWidget(self.details_label)
        main_layout.addWidget(self.preview_text_label)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)
        self.search_and_load()

    def get_cache_path(self, query):
        safe_query = query.replace(" ", "_")
        return os.path.join(self.cache_dir, f"{safe_query}.json")

    def get_audio_cache_path(self, audio_uri):
        filename = os.path.basename(audio_uri).split("?")[0]
        safe_filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
        return os.path.join(self.cache_dir, safe_filename)

    def populate_list(self, data):
        self.list_widget.clear()
        self.data = data
        for item in self.data["voices"]:
            description = item["description"]
            if description == "":
                list_item = QListWidgetItem(f"{item['name']} • {trls.tr(self.trl, 'author_label')}: {item['creatorInfo']['username']}")
            else:
                list_item = QListWidgetItem(f"{item['name']} - {description}\n• {trls.tr(self.trl, 'author_label')}: {item['creatorInfo']['username']}")
            list_item.setData(1, item)
            self.list_widget.addItem(list_item)

    def display_details(self, item):
        data = item.data(1)
        self.current_data = data
        self.details_label.setText(f"<b>{data['name']}</b> • {trls.tr(self.trl, 'author_label')}: {data['creatorInfo']['username']}<br>{data['description']}")
        self.preview_text_label.setText(f"{trls.tr(self.trl, 'example_phrase')}: {data['previewText']}")
        self.current_audio_uri = data["previewAudioURI"]
        self.play_button.setEnabled(not self.played)
        self.select_button.setEnabled(True)

    def save_and_play_audio(self, file, audio_cache_path):
        try:
            with open(audio_cache_path, "wb") as audio_file:
                audio_file.write(file)

            audio_bytes = sf.SoundFile(audio_cache_path, "rb")
            audio_array = audio_bytes.read()
            samplerate = audio_bytes.samplerate
            self.audio_thread = AudioPlayerThread(self, audio_array, samplerate)
            self.audio_thread.played.connect(lambda played: setattr(self, "played", played))
            self.audio_thread.played.connect(lambda played: self.play_button.setEnabled(not played))
            self.audio_thread.error.connect(lambda error: QMessageBox.critical(self, trls.tr("Errors", "Label"), error))
            self.audio_thread.start()
        except Exception as e:
            QMessageBox.critical(self, trls.tr("Errors", "Label"), f"Audio playback error: {e}")

    def play_audio(self):
        if hasattr(self, "current_audio_uri"):
            audio_cache_path = self.get_audio_cache_path(self.current_audio_uri)
            if os.path.exists(audio_cache_path):
                try:
                    with sf.SoundFile(audio_cache_path, "rb") as audio_file:
                        audio_array = audio_file.read()
                        samplerate = audio_file.samplerate
                    self.audio_thread = AudioPlayerThread(self, audio_array, samplerate)
                    self.audio_thread.played.connect(lambda played: setattr(self, "played", played))
                    self.audio_thread.played.connect(lambda played: self.play_button.setEnabled(not played))
                    self.audio_thread.error.connect(lambda error: QMessageBox.critical(self, trls.tr("Errors", "Label"), error))
                    self.audio_thread.start()
                except Exception as e:
                    QMessageBox.critical(self, trls.tr("Errors", "Label"), f"Audio playback error: {e}")

            else:
                file_thread = FileLoaderThread(self.current_audio_uri, {
                "Authorization": f"Token {getconfig('client', configfile='charaiconfig.json')}"
            })
                file_thread.file.connect(lambda file: self.save_and_play_audio(file, audio_cache_path))
                file_thread.error.connect(lambda error: QMessageBox.critical(self, trls.tr("Errors", "Label"), error))
                file_thread.start()

    def search_and_load(self):
        self.search_input.returnPressed.disconnect()
        self.list_widget.setEnabled(False)
        search_query = self.search_input.text().strip()
        if not search_query:
            search_query = self.character_name
            if not search_query:
                ccas().get_character(self.character_id)
                search_query = ccas().get_character(self.character_id).get("participant__name", "")
        self.search_input.setText(search_query)

        try:
            url = f"https://neo.character.ai/multimodal/api/v1/voices/search?query={search_query}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {getconfig('client', configfile='charaiconfig.json')}"
            }

            search_thread = SearchLoaderThread(url, headers, search_query, self.cache_dir)
            search_thread.data.connect(lambda data: self.populate_list(data))
            search_thread.data.connect(lambda data: self.list_widget.setEnabled(True))
            search_thread.data.connect(lambda data: self.search_input.returnPressed.connect(self.search_and_load))
            search_thread.error.connect(lambda error: QMessageBox.critical(self, trls.tr("Errors", "Label"), error))
            self.threads.append(search_thread)
            search_thread.start()

        except Exception as e:
            QMessageBox.critical(self, trls.tr("Errors", "Label"), f"Error when executing the request: {e}")

    def addcharvoice(self):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}

        data[self.character_id]["voiceid"] = self.current_data["id"]

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        if self.main_window and self.parent:
            self.parent.charaitts_voice_entry.setText(self.current_data["id"])
            self.close()
            return

        QMessageBox.information(self, "Ez", trls.tr(self.trl, "character_voice_changed"))
        self.close()