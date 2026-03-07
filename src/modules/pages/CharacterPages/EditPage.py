import base64
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QSpacerItem,
                             QSizePolicy, QWidget, QFileDialog)

from modules.style.Elements import CustomTextEdit, PushButton, LineEdit, CheckBox, ComboBox, VerticalScrollPage
from modules.style.Icons import Svg
from modules.style.Utils import color_avatar

class EditPage(QWidget):
    def __init__(self, main_window, character_id=None):
        super().__init__(main_window)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.svg_icons = Svg()
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.initUI()
        self.has_data = False
        if character_id:
            self.has_data = True
            self.mw.chat_thread.get_char_signal.connect(self.loadData)
            self.mw.chat_thread.get_character(character_id)
        else:
            self.create_button.setVisible(True)

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
        data = data.get('character', {})
        self.data = data
        if self.data and self.has_data:
            self.create_button.setVisible(False)
            self.save_button.setVisible(True)
            self.save_chat_button.setVisible(True)
            self.data['avatar_rel_path'] = self.data.get('avatar_file_name', '')
            if self.data.get('avatar_rel_path'):
                self.image_loader.load(
                    f"https://characterai.io/i/80/static/avatars/{self.data['avatar_rel_path']}?webp=true&anim=0", 60, 60, 100,
                    label=self.display_avatar,
                    error_cb=lambda _: color_avatar(self.display_avatar, 60, 60, data['name']))
            else:
                color_avatar(self.display_avatar, 60, 60, data['name'])
            self.character_name_edit.setText(self.data.get('name'))
            self.tagline_edit.setText(self.data.get('title'))
            self.description_edit.setText(self.data.get('description'))
            self.greeting_edit.setText(self.data.get('greeting'))
            self.dg_checkbox.setChecked(self.data.get('dynamic_greeting_enabled', False))
            self.definition_edit.setText(self.data.get('definition'))
            self.kcdp_checkbox.setChecked(self.data.get('copyable', False))
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