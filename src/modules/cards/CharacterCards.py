import base64, uuid

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QSpacerItem,
    QSizePolicy, QWidget, QFileDialog)

from modules.style.Elements import (CustomTextEdit, PushButton, LineEdit, CheckBox, ComboBox, VerticalScrollPage,
    CardFrame)
from modules.style.Icons import Svg
from modules.style.Utils import format_text, format_number, color_avatar
from modules.QThreads import ImageLoaderThread

class MainCard(CardFrame):
    def __init__(self, main_window, name="", avatar_url="", description="", author="", character_id="", chats=0,
                 voted=0, avatar_label_w=90, avatar_label_h=114):
        super().__init__()
        self.mw = main_window
        self.name = name
        self.avatar_url = avatar_url
        self.description = description
        self.author = author
        self.character_id = character_id
        self.chats = chats
        self.voted = voted
        self.avatar_label_w = avatar_label_w
        self.avatar_label_h = avatar_label_h

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()
        self.setLayout(card_layout)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.avatar_label)

        if self.avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.avatar_url + '?webp=true&anim=0',
                self.avatar_label_w,
                self.avatar_label_h)
            load_avatar_thread.image_loaded.connect(self.avatar_label.setPixmap)
            load_avatar_thread.error_loading.connect(
                lambda _: color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name, 4))
            load_avatar_thread.radius = 4
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name, 4)

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(text_layout, 1)

        title_label = QLabel(self.name)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

        if self.author:
            author_label = QLabel(self.tr("Author: @") + self.author)
            font = author_label.font()
            font.setPointSize(8)
            author_label.setStyleSheet("color: #a2a2ac;")
            author_label.setFont(font)
            text_layout.addWidget(author_label)

        if self.description:
            description_label = QLabel(format_text(self.description, self.name))
            description_label.setWordWrap(True)
            font = description_label.font()
            font.setPointSize(10)
            description_label.setFont(font)
            fm = QFontMetrics(font)
            description_label.setMaximumHeight(fm.lineSpacing() * 4)
            text_layout.addWidget(description_label)
            self.setToolTip(format_text(self.description))

        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        text_layout.addItem(spacer)

        add_info = QLabel()
        add_info.setStyleSheet("color: #a2a2ac;")
        font = add_info.font()
        font.setPointSize(10)
        add_info.setFont(font)
        if self.chats:
            add_info.setText(add_info.text() + str(format_number(self.chats)) + self.tr(" chats"))
        if self.voted:
            add_info.setText(add_info.text() + " • " + str(format_number(self.voted)) + self.tr(" likes"))

        if add_info.text():
            text_layout.addWidget(add_info)

        self.edit_button = PushButton(self.tr("Edit"))
        self.edit_button.clicked.connect(lambda: self.mw.openCreateCharacterPage(self.character_id))

        if self.author == self.mw.username:
            card_layout.addWidget(self.edit_button, alignment=Qt.AlignmentFlag.AlignRight)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openChat(self.character_id, self.name)

class MiniCard(CardFrame):
    def __init__(self, main_window, character_name, character_id, avatar_url, chat_id=None):
        super().__init__()
        self.mw = main_window
        self.name = character_name
        self.character_id = character_id
        self.avatar_url = avatar_url
        self.chat_id = chat_id

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()
        self.setLayout(card_layout)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(54, 54)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.avatar_label)

        if self.avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.avatar_url + '?webp=true&anim=0', 54, 54)
            load_avatar_thread.image_loaded.connect(self.avatar_label.setPixmap)
            load_avatar_thread.radius = 4
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.avatar_label, 54, 54, self.name, 4)

        title_label = QLabel(self.name)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(16)
        title_label.setFont(font)
        card_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openChat(self.character_id, self.name, self.chat_id)

class EditPage(QWidget):
    def __init__(self, main_window, character_id=None):
        super().__init__(main_window)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.svg_icons = Svg()
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.initUI()
        if character_id is None:
            self.loadData({'character': {
                'allow_dynamic_greeting': True,
                'avatar_rel_path': "",
                'base_img_prompt': "",
                'categories': [],
                'copyable': False,
                'default_voice_id': "",
                'definition': "",
                'description': "",
                'dynamic_greeting_enabled': "",
                'greeting': "",
                'identifier': f"id:{uuid.uuid4()}",
                'img_gen_enabled': False,
                'name': "",
                'strip_img_prompt_from_msg': False,
                'tags': [],
                'title': "",
                'visibility': "",
                'voice_id': "",
                'external_id': ""
            }})
        else:
            self.mw.chat_thread.get_char_signal.connect(self.loadData)
            self.mw.chat_thread.get_character(character_id)

    def initUI(self):
        main_layout = QVBoxLayout()

        scroll_page = VerticalScrollPage()
        scroll_page.setFixedWidth(800)
        scroll_page.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        self.display_avatar = QLabel()
        self.display_avatar.mousePressEvent = lambda _: self.selectAvatar()
        self.display_avatar.setFixedSize(60, 60)
        self.display_avatar.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.mw.me_has_avatar:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.mw.me_avatar + '?webp=true&anim=0',
                60, 60)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.mw.me_avatar, 60, 60, self.mw.name))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.display_avatar, 60, 60, self.mw.name)
        scroll_layout.addWidget(self.display_avatar)

        self.character_name_label = QLabel(self.tr("Character Name"))
        font = self.character_name_label.font()
        font.setBold(True)
        font.setPointSize(12)
        self.character_name_label.setFont(font)
        scroll_layout.addWidget(self.character_name_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.character_name_edit = LineEdit()
        self.character_name_edit.setPlaceholderText(self.tr("e.g. Albert Einstein"))
        self.character_name_edit.setMaxLength(20)
        scroll_layout.addWidget(self.character_name_edit)

        self.tagline_label = QLabel(self.tr("Tagline"))
        self.tagline_label.setFont(font)
        scroll_layout.addWidget(self.tagline_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.tagline_edit = LineEdit()
        self.tagline_edit.setMaxLength(50)
        self.tagline_edit.setPlaceholderText(self.tr("Add a short tagline of your Character"))
        scroll_layout.addWidget(self.tagline_edit)

        self.description_label = QLabel(self.tr("Description"))
        self.description_label.setFont(font)
        scroll_layout.addWidget(self.description_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.description_edit = CustomTextEdit()
        self.description_edit.setPlaceholderText(self.tr("How would your Character describe themselves?"))
        self.description_edit.textChanged.connect(lambda: self.textChanged(self.description_edit, 500))
        self.description_edit.setFixedHeight(48)
        self.description_edit.horizontalScrollBar().setVisible(False)
        self.description_edit.verticalScrollBar().setVisible(False)
        scroll_layout.addWidget(self.description_edit)

        self.greeting_label = QLabel(self.tr("Greeting"))
        self.greeting_label.setFont(font)
        scroll_layout.addWidget(self.greeting_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.greeting_edit = CustomTextEdit()
        self.greeting_edit.setPlaceholderText(self.tr("e.g. Hello, I am Albert. Ask me anything about my scientific contributions."))
        self.greeting_edit.textChanged.connect(lambda: self.textChanged(self.greeting_edit, 4096))
        self.greeting_edit.setFixedHeight(48)
        self.greeting_edit.horizontalScrollBar().setVisible(False)
        self.greeting_edit.verticalScrollBar().setVisible(False)
        scroll_layout.addWidget(self.greeting_edit)

        dg_layout = QHBoxLayout()
        dg_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.dg_checkbox = CheckBox()
        dg_layout.addWidget(self.dg_checkbox)
        self.dg_label = QLabel(self.tr('Allow dynamic greetings'))
        dg_layout.addWidget(self.dg_label)
        scroll_layout.addLayout(dg_layout)

        self.definition_label = QLabel(self.tr("Definition"))
        self.definition_label.setFont(font)
        scroll_layout.addWidget(self.definition_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.definition_edit = CustomTextEdit()
        self.definition_edit.setPlaceholderText(self.tr("What's your Character's backstory? How do you want it to talk or act?"))
        self.definition_edit.textChanged.connect(lambda: self.textChanged(self.definition_edit, 32000))
        self.definition_edit.setFixedHeight(48)
        self.definition_edit.horizontalScrollBar().setVisible(False)
        self.definition_edit.verticalScrollBar().setVisible(False)
        scroll_layout.addWidget(self.definition_edit)

        def_layout = QHBoxLayout()
        def_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.add_user_message_button = PushButton(self.tr("User message"))
        self.add_user_message_button.clicked.connect(lambda: self.addText('\n{{user}}: '))
        def_layout.addWidget(self.add_user_message_button)
        self.add_char_message_button = PushButton(self.tr("Character message"))
        self.add_char_message_button.clicked.connect(lambda: self.addText('\n{{char}}: '))
        def_layout.addWidget(self.add_char_message_button)
        self.add_end_button = PushButton(self.tr("End of dialog"))
        self.add_end_button.clicked.connect(lambda: self.addText('\nEND_OF_DIALOG'))
        def_layout.addWidget(self.add_end_button)
        scroll_layout.addLayout(def_layout)

        kcdp_layout = QHBoxLayout()
        kcdp_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.kcdp_checkbox = CheckBox()
        self.kcdp_checkbox.setChecked(True)
        kcdp_layout.addWidget(self.kcdp_checkbox)
        self.kcdp_label = QLabel(self.tr('Keep Character definition private'))
        kcdp_layout.addWidget(self.kcdp_label)
        scroll_layout.addLayout(kcdp_layout)

        self.visibility_label = QLabel(self.tr("Visibility"))
        self.visibility_label.setFont(font)
        scroll_layout.addWidget(self.visibility_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.visible_combobox = ComboBox()
        self.visible_combobox.addItems([self.tr("Public"), self.tr("Unlisted"), self.tr("Private")])
        scroll_layout.addWidget(self.visible_combobox, alignment=Qt.AlignmentFlag.AlignLeft)

        final_buttons_layout = QHBoxLayout()
        final_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.create_button = PushButton(self.tr("Create Character"))
        self.create_button.clicked.connect(self.createCharacter)
        final_buttons_layout.addWidget(self.create_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.save_button = PushButton(self.tr("Save Changes"))
        self.save_button.clicked.connect(self.saveCharacter)
        final_buttons_layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.save_chat_button = PushButton(self.tr("Save and Chat"))
        self.save_chat_button.clicked.connect(self.saveCharacterChat)
        final_buttons_layout.addWidget(self.save_chat_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.create_button.setVisible(False)
        self.save_button.setVisible(False)
        self.save_chat_button.setVisible(False)
        scroll_layout.addLayout(final_buttons_layout)

        main_layout.addWidget(scroll_page, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)

    def saveCharacterChat(self):
        self.saveData()

        self.mw.chat_thread.update_character_signal.connect(self._saveCharacterChat)
        self.mw.chat_thread.update_character(self.data)

    def _saveCharacterChat(self, data):
        if data.get('status') == "OK":
            self.mw.showNotification(self.tr("The character has been saved successfully!"))
            char = data.get('character')
            self.mw.openChat(char['external_id'], char['name'])
        else:
            self.mw.showNotification(data)

    def saveCharacter(self):
        self.saveData()

        self.mw.chat_thread.update_character_signal.connect(self._saveCharacter)
        self.mw.chat_thread.update_character(self.data)

    def _saveCharacter(self, data):
        if data.get('status') == "OK":
            self.mw.showNotification(self.tr("The character has been saved successfully!"))
        else:
            self.mw.showNotification(str(data))

    def createCharacter(self):
        self.saveData()

        self.mw.chat_thread.create_character_signal.connect(self._createCharacter)
        self.mw.chat_thread.create_character(self.data)

    def _createCharacter(self, data):
        if data.get('status') == "OK":
            self.mw.showNotification(self.tr("The character has been successfully created!"))
            char = data.get('character')
            self.mw.openChat(char['external_id'], char['name'])
        else:
            self.mw.showNotification(data)

    def saveData(self):
        if len(self.character_name_edit.text()) <= 2:
            self.mw.showNotification(self.tr("The character's name must be longer than three characters."))
            return
        if len(self.greeting_edit.toPlainText()) <= 2:
            self.mw.showNotification(self.tr("The character's greeting must be longer than three characters."))
            return
        self.data['name'] = self.character_name_edit.text()
        self.data['title'] = self.tagline_edit.text()
        self.data['description'] = self.description_edit.toPlainText()
        self.data['greeting'] = self.greeting_edit.toPlainText()
        self.data['dynamic_greeting_enabled'] = self.dg_checkbox.isChecked()
        self.data['definition'] = self.definition_edit.toPlainText()
        self.data['copyable'] = self.kcdp_checkbox.isChecked()

        if self.visible_combobox.currentText() == self.tr('Public'):
            self.data['visibility'] = "PUBLIC"
        elif self.visible_combobox.currentText() == self.tr('Unlisted'):
            self.data['visibility'] = "UNLISTED"
        elif self.visible_combobox.currentText() == self.tr('Private'):
            self.data['visibility'] = "PRIVATE"

    def loadData(self, data):
        data = data['character']
        self.data = data
        if self.data['external_id']:
            self.create_button.setVisible(False)
            self.save_button.setVisible(True)
            self.save_chat_button.setVisible(True)
            self.data['avatar_rel_path'] = self.data['avatar_file_name']
            if self.data.get('avatar_rel_path'):
                load_avatar_thread = ImageLoaderThread(
                    "https://characterai.io/i/80/static/avatars/" + self.data['avatar_rel_path'] + '?webp=true&anim=0',
                    60, 60)
                load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
                load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.display_avatar, 60, 60, data['name']))
                load_avatar_thread.start()
                self.mw.threads.append(load_avatar_thread)
            else:
                color_avatar(self.display_avatar, 60, 60, data['name'])
            self.character_name_edit.setText(self.data['name'])
            self.tagline_edit.setText(self.data['title'])
            self.description_edit.setText(self.data['description'])
            self.greeting_edit.setText(self.data['greeting'])
            self.dg_checkbox.setChecked(self.data['dynamic_greeting_enabled'])
            self.definition_edit.setText(self.data['definition'])
            self.kcdp_checkbox.setChecked(self.data['copyable'])
            if self.data['visibility'] == "PUBLIC":
                self.visible_combobox.setCurrentText(self.tr('Public'))
            elif self.data['visibility'] == "UNLISTED":
                self.visible_combobox.setCurrentText(self.tr('Unlisted'))
            elif self.data['visibility'] == "PRIVATE":
                self.visible_combobox.setCurrentText(self.tr('Private'))
        else:
            self.create_button.setVisible(True)
            self.save_button.setVisible(False)
            self.save_chat_button.setVisible(False)

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(0)
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def addText(self, text):
        original_text = self.definition_edit.toPlainText()
        original_text += text
        self.definition_edit.setText(original_text)

    def textChanged(self, text_edit, max_len):
        text = text_edit.toPlainText()
        line_count = text.count('\n')
        line_count += text.count('<br>') + 1 if text else 1
        height = line_count * text_edit.fontMetrics().lineSpacing() + 32
        text_edit.setFixedHeight(height)
        if len(text) > max_len:
            text_edit.setPlainText(text[:max_len])
            cursor = text_edit.textCursor()
            cursor.setPosition(max_len)
            text_edit.setTextCursor(cursor)

    def selectAvatar(self):
        def uploaded(link):
            setattr(self, 'temp_link', link)
            self.data['avatar_rel_path'] = link
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + link + '?webp=true&anim=0',
                60, 60)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)

        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if file_path.endswith(".png"):
                file_type = "png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                file_type = "jpeg"
            elif file_path.endswith(".bmp"):
                file_type = "bmp"

            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            self.mw.chat_thread.upload_avatar_signal.connect(uploaded)
            self.mw.chat_thread.upload_avatar(file_type, encoded)

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.left_sidebar.create_character_button.setChecked(True)
        self.mw.left_sidebar.create_character_button_2.setChecked(True)
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.mw.left_sidebar.create_character_button.setChecked(False)
        self.mw.left_sidebar.create_character_button_2.setChecked(False)
        self.deleteLater()