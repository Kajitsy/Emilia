import base64, uuid
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QSpacerItem,
                             QSizePolicy, QWidget, QFileDialog, QApplication)

from modules.style.Elements import (CustomTextEdit, PushButton, LineEdit, CheckBox, ComboBox, VerticalScrollPage,
                                    CardFrame, ClickableFrame)
from modules.style.Icons import Svg
from modules.style.Utils import format_text, format_number, color_avatar

class MainCard(CardFrame):
    def __init__(self, main_window, name="", avatar_url="", description="", author="", character_id="", chats=0,
                 voted=0, avatar_label_w=90, avatar_label_h=114):
        super().__init__()
        self.mw = main_window
        self.image_loader = self.mw.image_loader
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
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0", self.avatar_label_w, self.avatar_label_h, 4,
                label=self.avatar_label, error_cb=lambda _: color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name))
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

class ListCard(CardFrame):
    def __init__(self, main_window, data, avatar_label_w=70, avatar_label_h=70):
        super().__init__()
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.data = data
        self.avatar_url = self.data.get('avatar_file_name')
        self.name = self.data.get('name')
        self.character_id = self.data.get('external_id')
        self.avatar_label_w = avatar_label_w
        self.avatar_label_h = avatar_label_h

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()
        self.setLayout(card_layout)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
        card_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        if self.avatar_url:
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0", self.avatar_label_w, self.avatar_label_h, 4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name))
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

        if self.data.get('title'):
            description_label = QLabel(format_text(self.data.get('title'), self.name))
            description_label.setWordWrap(True)
            description_label.setStyleSheet("color: #a2a2ac;")
            font = description_label.font()
            font.setPointSize(9)
            description_label.setFont(font)
            fm = QFontMetrics(font)
            description_label.setMaximumHeight(fm.lineSpacing())
            text_layout.addWidget(description_label)
            self.setToolTip(format_text(self.data.get('title')))

        add_info = QLabel()
        add_info.setStyleSheet("color: #a2a2ac;")
        font = add_info.font()
        font.setPointSize(10)
        add_info.setFont(font)
        if self.data.get('participant__num_interactions'):
            add_info.setText(add_info.text() + str(format_number(self.data.get('participant__num_interactions'))) + self.tr(" chats"))

        if add_info.text():
            text_layout.addWidget(add_info)

        self.chat_button = PushButton(self.tr("Chat"))
        self.chat_button.clicked.connect(lambda: self.mw.openChat(self.character_id, self.name))
        card_layout.addWidget(self.chat_button, alignment=Qt.AlignmentFlag.AlignRight)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        self.mw.openCharacter(character_id=self.data["external_id"])

class MiniCard(CardFrame):
    def __init__(self, main_window, character_name, character_id, avatar_url, chat_id=None):
        super().__init__()
        self.mw = main_window
        self.image_loader = main_window.image_loader
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
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0", 54, 54, 4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, 54, 54, self.name))
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

class ClickableMiniCard(ClickableFrame):
    def __init__(self, main_window, character_name, character_id, avatar_url, chat_id=None):
        super().__init__()
        self.mw = main_window
        self.image_loader = main_window.image_loader
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
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0", 54, 54, 4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, 54, 54, self.name))
        else:
            color_avatar(self.avatar_label, 54, 54, self.name, 4)

        title_label = QLabel(self.name)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(16)
        title_label.setFont(font)
        card_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

class EditPage(QWidget):
    def __init__(self, main_window, character_id=None):
        super().__init__(main_window)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.image_loader = main_window.image_loader
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
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0", 60, 60, 100,
                label=self.display_avatar,
                error_cb=lambda _: color_avatar(self.display_avatar, 60, 60, self.mw.name))
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

        scroll_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))

        description_layout = QHBoxLayout()
        scroll_layout.addLayout(description_layout)
        self.description_label = QLabel(self.tr("Description"))
        self.description_label.setFont(font)
        description_layout.addWidget(self.description_label, alignment=Qt.AlignmentFlag.AlignLeft)
        description_layout.addStretch()
        heading_combo = ComboBox()
        heading_combo.addItem(self.tr("Plain text"), "")
        heading_combo.addItem(self.tr("# Title 1"), "#")
        heading_combo.addItem(self.tr("## Title 2"), "##")
        heading_combo.addItem(self.tr("### Title 3"), "###")
        heading_combo.addItem(self.tr("#### Title 4"), "####")
        heading_combo.addItem(self.tr("##### Title 5"), "#####")
        heading_combo.addItem(self.tr("###### Title 6"), "######")
        heading_combo.currentIndexChanged.connect(lambda: self.description_edit.applyHeading(heading_combo))
        description_layout.addWidget(heading_combo)
        bold_button = PushButton(self.tr("Bold"))
        bold_button.clicked.connect(lambda: self.description_edit.formatSelectedText("**", "**"))
        description_layout.addWidget(bold_button)
        italic_button = PushButton(self.tr("Italic"))
        italic_button.clicked.connect(lambda: self.description_edit.formatSelectedText("*", "*"))
        description_layout.addWidget(italic_button)
        code_button = PushButton(self.tr("Code"))
        code_button.clicked.connect(lambda: self.description_edit.formatSelectedText("`", "`"))
        description_layout.addWidget(code_button)

        self.description_edit = CustomTextEdit()
        self.description_edit.setPlaceholderText(self.tr("How would your Character describe themselves?"))
        self.description_edit.textChanged.connect(lambda: self.textChanged(self.description_edit, 500))
        self.description_edit.setFixedHeight(48)
        self.description_edit.horizontalScrollBar().setVisible(False)
        self.description_edit.verticalScrollBar().setVisible(False)
        scroll_layout.addWidget(self.description_edit)

        scroll_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))

        greeting_layout = QHBoxLayout()
        scroll_layout.addLayout(greeting_layout)
        self.greeting_label = QLabel(self.tr("Greeting"))
        self.greeting_label.setFont(font)
        greeting_layout.addWidget(self.greeting_label, alignment=Qt.AlignmentFlag.AlignLeft)
        greeting_layout.addStretch()
        heading_combo = ComboBox()
        heading_combo.addItem(self.tr("Plain text"), "")
        heading_combo.addItem(self.tr("# Title 1"), "#")
        heading_combo.addItem(self.tr("## Title 2"), "##")
        heading_combo.addItem(self.tr("### Title 3"), "###")
        heading_combo.addItem(self.tr("#### Title 4"), "####")
        heading_combo.addItem(self.tr("##### Title 5"), "#####")
        heading_combo.addItem(self.tr("###### Title 6"), "######")
        heading_combo.currentIndexChanged.connect(lambda: self.greeting_edit.applyHeading(heading_combo))
        greeting_layout.addWidget(heading_combo)
        bold_button = PushButton(self.tr("Bold"))
        bold_button.clicked.connect(lambda: self.greeting_edit.formatSelectedText("**", "**"))
        greeting_layout.addWidget(bold_button)
        italic_button = PushButton(self.tr("Italic"))
        italic_button.clicked.connect(lambda: self.greeting_edit.formatSelectedText("*", "*"))
        greeting_layout.addWidget(italic_button)
        code_button = PushButton(self.tr("Code"))
        code_button.clicked.connect(lambda: self.greeting_edit.formatSelectedText("`", "`"))
        greeting_layout.addWidget(code_button)

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

        scroll_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))

        definition_layout = QHBoxLayout()
        scroll_layout.addLayout(definition_layout)
        self.definition_label = QLabel(self.tr("Definition"))
        self.definition_label.setFont(font)
        definition_layout.addWidget(self.definition_label, alignment=Qt.AlignmentFlag.AlignLeft)
        definition_layout.addStretch()
        heading_combo = ComboBox()
        heading_combo.addItem(self.tr("Plain text"), "")
        heading_combo.addItem(self.tr("# Title 1"), "#")
        heading_combo.addItem(self.tr("## Title 2"), "##")
        heading_combo.addItem(self.tr("### Title 3"), "###")
        heading_combo.addItem(self.tr("#### Title 4"), "####")
        heading_combo.addItem(self.tr("##### Title 5"), "#####")
        heading_combo.addItem(self.tr("###### Title 6"), "######")
        heading_combo.currentIndexChanged.connect(lambda: self.definition_edit.applyHeading(heading_combo))
        definition_layout.addWidget(heading_combo)
        bold_button = PushButton(self.tr("Bold"))
        bold_button.clicked.connect(lambda: self.definition_edit.formatSelectedText("**", "**"))
        definition_layout.addWidget(bold_button)
        italic_button = PushButton(self.tr("Italic"))
        italic_button.clicked.connect(lambda: self.definition_edit.formatSelectedText("*", "*"))
        definition_layout.addWidget(italic_button)
        code_button = PushButton(self.tr("Code"))
        code_button.clicked.connect(lambda: self.definition_edit.formatSelectedText("`", "`"))
        definition_layout.addWidget(code_button)

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
        if self.data:
            self.create_button.setVisible(False)
            self.save_button.setVisible(True)
            self.save_chat_button.setVisible(True)
            self.data['avatar_rel_path'] = self.data['avatar_file_name']
            if self.data.get('avatar_rel_path'):
                self.image_loader.load(
                    f"https://characterai.io/i/80/static/avatars/{self.data['avatar_rel_path']}?webp=true&anim=0", 60, 60, 100,
                    label=self.display_avatar,
                    error_cb=lambda _: color_avatar(self.display_avatar, 60, 60, data['name']))
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
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{link}?webp=true&anim=0", 60, 60, 100,
                label=self.display_avatar)

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
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.deleteLater()

class MainPage(QWidget):
    def __init__(self, main_window, short_id=None, character_id=None):
        super().__init__()
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.chat_thread = self.mw.chat_thread
        self.short_id = short_id
        self.character_id = character_id
        self.character_name = None
        self.data = {}

        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.initUI()

        self.chat_thread.get_char_signal.connect(self._getCharacter)
        self.chat_thread.get_character(self.character_id, self.short_id)

    def initUI(self):
        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        fhs_page = VerticalScrollPage()
        fhs_page.setStyleSheet("background-color: transparent; border: none;")
        fhs_page.setFixedWidth(400)
        fhs_layout = fhs_page.layout

        self.display_avatar = QLabel()
        self.display_avatar.setFixedSize(120, 120)
        fhs_layout.addWidget(self.display_avatar)

        self.character_name_label = QLabel()
        hg_font = self.character_name_label.font()
        hg_font.setBold(True)
        hg_font.setPointSize(14)
        self.character_name_label.setFont(hg_font)
        self.character_name_label.setWordWrap(True)
        fhs_layout.addWidget(self.character_name_label)

        self.author_label = QLabel()
        self.author_label.setStyleSheet("color: #a2a2ac;")
        font = self.author_label.font()
        font.setBold(True)
        font.setPointSize(10)
        self.author_label.setFont(font)
        self.author_label.setWordWrap(True)
        fhs_layout.addWidget(self.author_label)
        self.author_label.setVisible(False)

        but_layout = QHBoxLayout()
        fhs_layout.addLayout(but_layout)

        self.chat_button = PushButton(self.tr("Chat"))
        self.chat_button.clicked.connect(lambda: self.mw.openChat(self.character_id, self.character_name))
        but_layout.addWidget(self.chat_button, 1)

        self.like_button = PushButton()
        self.like_button.setIcon(self.mw.svg_icons.like())
        self.like_button.clicked.connect(self.likeCharacter)
        but_layout.addWidget(self.like_button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.dislike_button = PushButton()
        self.dislike_button.setIcon(self.mw.svg_icons.dislike())
        self.dislike_button.clicked.connect(self.dislikeCharacter)
        but_layout.addWidget(self.dislike_button, 0, Qt.AlignmentFlag.AlignHCenter)

        self.share_button = PushButton()
        self.share_button.setIcon(self.mw.svg_icons.share())
        self.share_button.clicked.connect(self.shareCharacter)
        but_layout.addWidget(self.share_button, 0, Qt.AlignmentFlag.AlignRight)

        cl_layout = QHBoxLayout()
        cl_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fhs_layout.addLayout(cl_layout)
        self.chats_label = QLabel(self.tr("0 chats"))
        sc_font = self.chats_label.font()
        sc_font.setBold(True)
        sc_font.setPointSize(10)
        self.chats_label.setFont(sc_font)
        cl_layout.addWidget(self.chats_label)
        self.span_label = QLabel("|")
        self.span_label.setFont(sc_font)
        cl_layout.addWidget(self.span_label)
        self.likes_label = QLabel(self.tr("0 likes"))
        self.likes_label.setFont(sc_font)
        cl_layout.addWidget(self.likes_label)

        self.description_label = QLabel("")
        self.description_label.setStyleSheet("color: #a2a2ac;")
        self.description_label.setFont(hg_font)
        self.description_label.setWordWrap(True)
        fhs_layout.addWidget(self.description_label, 1, alignment=Qt.AlignmentFlag.AlignTop)

        shs_page = VerticalScrollPage()
        shs_page.setStyleSheet("background-color: transparent; border: none;")
        shs_page.setFixedWidth(400)
        shs_layout = shs_page.layout

        self.simchars_label = QLabel(self.tr("Similar characters"))
        self.simchars_label.setFont(hg_font)
        shs_layout.addWidget(self.simchars_label)

        simchars_page = VerticalScrollPage()
        self.simchars_layout = simchars_page.layout
        shs_layout.addWidget(simchars_page)

        main_layout.addWidget(fhs_page)
        main_layout.addWidget(shs_page)

        self.setLayout(main_layout)

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(0)
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def _getSimChars(self, data):
        self.chat_thread.get_recommend_chars_by_id_signal.disconnect()
        for char in data:
            card = ListCard(self.mw, char)
            card.setFixedHeight(80)
            self.simchars_layout.addWidget(card)

    def _getCharacter(self, data):
        self.chat_thread.get_char_signal.disconnect()
        self.data = data['character']
        self.character_id = self.data.get('external_id')
        self.short_id = self.data.get('short_hash')
        self.character_name = self.data['name']
        self.chat_thread.get_recommend_chars_by_id_signal.connect(self._getSimChars)
        self.chat_thread.get_recommend_chars_by_id(self.character_id)
        self.voted = data.get('voted', {}).get('voted', False)
        self.vote = data.get('voted', {}).get('vote', None)
        self.character_name_label.setText(self.character_name)
        if self.data.get('avatar_file_name'):
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.data.get('avatar_file_name')}?webp=true&anim=0", 120, 120, 100,
                label=self.display_avatar,
                error_cb=lambda _: color_avatar(self.display_avatar, 120, 120, self.mw.name))
        else:
            color_avatar(self.display_avatar, 120, 120, self.character_name)
        if self.data.get('user__username'):
            self.author_label.setText(self.tr("Author: @") + self.data.get('user__username'))
            self.author_label.setVisible(True)
            self.author_label.mousePressEvent = lambda x: self.mw.openUserPage(self.data.get('user__username'))
            self.author_label.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.data.get('participant__num_interactions'):
            self.chats_label.setText(format_number(self.data.get('participant__num_interactions', 0)) + self.tr(" chats"))
            self.chats_label.setVisible(True)
        if self.data.get('upvotes'):
            self.likes_label.setText(format_number(self.data.get('upvotes', '0')) + self.tr(" likes"))
            self.likes_label.setVisible(True)
        if self.data.get('description'):
            self.description_label.setText(self.data.get('description'))
        if self.voted:
            if self.vote == True:
                self.like_button.setIcon(self.mw.svg_icons.liked())
            elif self.vote == False:
                self.dislike_button.setIcon(self.mw.svg_icons.disliked())

    def shareCharacter(self):
        QApplication.clipboard().setText(f'https://character.ai/character/{self.short_id}')
        self.mw.showNotification(self.tr("Link copied to clipboard"))

    def dislikeCharacter(self):
        self.like_button.setIcon(self.mw.svg_icons.like())
        if self.vote == False:
            self.vote = None
            self.chat_thread.character_vote(self.character_id, None)
            self.dislike_button.setIcon(self.mw.svg_icons.dislike())
        else:
            self.vote = False
            self.chat_thread.character_vote(self.character_id, False)
            self.dislike_button.setIcon(self.mw.svg_icons.disliked())

    def likeCharacter(self):
        self.dislike_button.setIcon(self.mw.svg_icons.dislike())
        if self.vote:
            self.vote = None
            self.chat_thread.character_vote(self.character_id, None)
            self.like_button.setIcon(self.mw.svg_icons.like())
        else:
            self.vote = True
            self.chat_thread.character_vote(self.character_id, True)
            self.like_button.setIcon(self.mw.svg_icons.liked())

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.deleteLater()