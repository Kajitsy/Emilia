import hashlib
import os

from curl_cffi import CurlMime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from modules.ui.Elements import (
    ComboBox,
    CustomTextEdit,
    LineEdit,
    PushButton,
    VerticalScrollPage,
)
from modules.ui.Icons import Svg


class AnyCharCreatePage(QWidget):
    def __init__(self, main_window, data=None, create=False, scene_id=None):
        super().__init__(main_window)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.data = data
        self.create = create
        self.scene_id = scene_id
        self.image_loader = main_window.image_loader
        self.svg_icons = Svg()
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.image_selected = False
        self.initUI()
        if len(self.data) == 0:
            self.loadData(
                {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "",
                        "goal": "",
                        "location": "",
                        "timeframe": "",
                        "tone": "",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                }
            )
        else:
            self.data = {
                "background_image_url": data.get("background_image_url"),
                "character_id": data.get("character_id", ""),
                "color_scheme_id": data.get("color_scheme_id", ""),
                "definition": {
                    "backstory": data.get("definition", {}).get("backstory"),
                    "genre": data.get("definition", {}).get("genre"),
                    "goal": data.get("definition", {}).get("goal"),
                    "location": data.get("definition", {}).get("location"),
                    "timeframe": data.get("definition", {}).get("timeframe"),
                    "tone": data.get("definition", {}).get("tone"),
                },
                "description": data.get("description"),
                "greeting_override": data.get("greeting_override"),
                "scene_id": data.get("scene_id"),
                "tags": data.get("tags", []),
                "title": data.get("title"),
                "visibility": data.get("visibility"),
            }
            if data["background_image_url"] != "":
                self.image_selected = True
            self.loadData(self.data)

    def initUI(self):
        main_layout = QVBoxLayout()

        scroll_page = VerticalScrollPage()
        scroll_page.setFixedWidth(800)
        scroll_page.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        self.scene_genre_label = QLabel(self.tr("Scene genre"))
        font = self.scene_genre_label.font()
        font.setBold(True)
        font.setPointSize(12)
        self.scene_genre_label.setFont(font)
        self.scene_genre_label.setToolTip(
            self.tr("Select the genre. This guides the Character's style and tone.")
        )
        scroll_layout.addWidget(
            self.scene_genre_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.scene_genre_edit = LineEdit()
        self.scene_genre_edit.setPlaceholderText(
            self.tr("Select the genre. This guides the Character’s style and tone.")
        )
        self.scene_genre_edit.setMaxLength(60)
        scroll_layout.addWidget(self.scene_genre_edit)

        self.when_scene_label = QLabel(self.tr("When is this Scene set?"))
        self.when_scene_label.setFont(font)
        self.when_scene_label.setToolTip(
            self.tr(
                "Set the time. This guides the Character contextually when the Scene is taking place."
            )
        )
        scroll_layout.addWidget(
            self.when_scene_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.when_scene_edit = LineEdit()
        self.when_scene_edit.setMaxLength(60)
        self.when_scene_edit.setPlaceholderText(
            self.tr(
                "Set the time. This guides the Character contextually when the Scene is taking place."
            )
        )
        scroll_layout.addWidget(self.when_scene_edit)

        self.where_scene_label = QLabel(self.tr("Where does this Scene happen?"))
        self.where_scene_label.setFont(font)
        self.where_scene_label.setToolTip(
            self.tr(
                "Set the location. This grounds the Character where the Scene is taking place."
            )
        )
        scroll_layout.addWidget(
            self.where_scene_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.where_scene_edit = LineEdit()
        self.where_scene_edit.setMaxLength(60)
        self.where_scene_edit.setPlaceholderText(
            self.tr(
                "Set the location. This grounds the Character where the Scene is taking place."
            )
        )
        scroll_layout.addWidget(self.where_scene_edit)

        self.tone_scene_label = QLabel(self.tr("Tone of this Scene"))
        self.tone_scene_label.setFont(font)
        self.tone_scene_label.setToolTip(
            self.tr(
                "What's the mood of the Scene? The defines the atmosphere and emotional tone to help your audience immerse."
            )
        )
        scroll_layout.addWidget(
            self.tone_scene_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.tone_scene_edit = LineEdit()
        self.tone_scene_edit.setMaxLength(60)
        self.tone_scene_edit.setPlaceholderText(
            self.tr(
                "What’s the mood of the Scene? This defines the atmosphere and emotional tone to help your audience immerse."
            )
        )
        scroll_layout.addWidget(self.tone_scene_edit)

        self.what_scene_label = QLabel(self.tr("What’s the backstory of this Scene?"))
        self.what_scene_label.setFont(font)
        self.what_scene_label.setToolTip(
            self.tr(
                "Describe what is happening in this Scene. Include relevant details about the situation and backstory. This will help shape how the Scene unfolds and how the Character responds. Use {{user}} for the user. Use {{char}} for the Character. If you are building an Any-Character Scene we recommend that you avoid the following pronouns: he, she, his, her, so your Scene can work for any character."
            )
        )
        scroll_layout.addWidget(
            self.what_scene_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.what_scene_edit = LineEdit()
        self.what_scene_edit.setMaxLength(500)
        self.what_scene_edit.setPlaceholderText(
            self.tr(
                """Describe what is happening in this Scene. Include relevant details about the situation and backstory. This will help shape how the Scene unfolds and how the Character responds.

Use {{user}} for the user.
Use {{char}} for the Character.

If you are building an Any-Character Scene we recommend that you avoid the following pronouns: he, she, his, her, so your Scene can work for any character.
"""
            )
        )
        scroll_layout.addWidget(self.what_scene_edit)

        self.goal_scene_label = QLabel(
            self.tr("What's the player's goal in this Scene?")
        )
        self.goal_scene_label.setFont(font)
        self.goal_scene_label.setToolTip(
            self.tr(
                "Define a goal that is the next logical story beat, tells the player what to try, and make the goal achievable with a clear, detectable moment of success.Keep it specific and concrete. A good goal = verb that implies effort + challenges or constraints. E.g. Unmask the stranger before the final waltz ends."
            )
        )
        scroll_layout.addWidget(
            self.goal_scene_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.goal_scene_edit = LineEdit()
        self.goal_scene_edit.setMaxLength(120)
        self.goal_scene_edit.setPlaceholderText(
            self.tr(
                """Define a goal that is the next logical story beat, tells the player what to try, and make the goal achievable with a clear, detectable moment of success.Keep it specific and concrete.

A good goal = verb that implies effort + challenges or constraints
E.g. Unmask the stranger before the final waltz ends.
"""
            )
        )
        scroll_layout.addWidget(self.goal_scene_edit)

        self.audience_scene_label = QLabel(
            self.tr("Introduce this Scene to your audience")
        )
        self.audience_scene_label.setFont(font)
        self.audience_scene_label.setToolTip(
            self.tr(
                "This is the starting screen of your Scene. Your audience will see this intro before entering the Scene. Help them understand what’s happening and get excited to start playing the Scene. Use {{user}} for the user. Use {{char}} for the Character."
            )
        )
        scroll_layout.addWidget(
            self.audience_scene_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.audience_scene_edit = LineEdit()
        self.audience_scene_edit.setMaxLength(650)
        self.audience_scene_edit.setPlaceholderText(
            self.tr(
                "This is the starting screen of your Scene. Your audience will see this intro before entering the Scene. Help them understand what’s happening and get excited to start playing the Scene. Use {{user}} for the user. Use {{char}} for the Character."
            )
        )
        scroll_layout.addWidget(self.audience_scene_edit)

        greeting_layout = QHBoxLayout()
        scroll_layout.addLayout(greeting_layout)
        self.greeting_label = QLabel(self.tr("Character greeting"))
        self.greeting_label.setFont(font)
        greeting_layout.addWidget(
            self.greeting_label, alignment=Qt.AlignmentFlag.AlignLeft
        )
        greeting_layout.addStretch()
        heading_combo = ComboBox()
        heading_combo.addItem(self.tr("Plain text"), "")
        heading_combo.addItem(self.tr("# Title 1"), "#")
        heading_combo.addItem(self.tr("## Title 2"), "##")
        heading_combo.addItem(self.tr("### Title 3"), "###")
        heading_combo.addItem(self.tr("#### Title 4"), "####")
        heading_combo.addItem(self.tr("##### Title 5"), "#####")
        heading_combo.addItem(self.tr("###### Title 6"), "######")
        heading_combo.currentIndexChanged.connect(
            lambda: self.greeting_edit.applyHeading(heading_combo)
        )
        greeting_layout.addWidget(heading_combo)
        bold_button = PushButton(self.tr("Bold"))
        bold_button.clicked.connect(
            lambda: self.greeting_edit.formatSelectedText("**", "**")
        )
        greeting_layout.addWidget(bold_button)
        italic_button = PushButton(self.tr("Italic"))
        italic_button.clicked.connect(
            lambda: self.greeting_edit.formatSelectedText("*", "*")
        )
        greeting_layout.addWidget(italic_button)
        code_button = PushButton(self.tr("Code"))
        code_button.clicked.connect(
            lambda: self.greeting_edit.formatSelectedText("`", "`")
        )
        greeting_layout.addWidget(code_button)

        self.greeting_edit = CustomTextEdit()
        self.greeting_edit.setPlaceholderText(
            self.tr(
                "This is the first Character message your audience will see after entering the Scene. Make it your hook with what they will see, hear, and feel."
            )
        )
        self.greeting_edit.textChanged.connect(
            lambda: self.textChanged(self.greeting_edit, 1200)
        )
        self.greeting_edit.setFixedHeight(48)
        self.greeting_edit.horizontalScrollBar().setVisible(False)
        self.greeting_edit.verticalScrollBar().setVisible(False)
        scroll_layout.addWidget(self.greeting_edit)

        self.name_scene_label = QLabel(self.tr("Name"))
        self.name_scene_label.setFont(font)
        scroll_layout.addWidget(
            self.name_scene_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.name_scene_edit = LineEdit()
        self.name_scene_edit.setMaxLength(40)
        self.name_scene_edit.setPlaceholderText(
            self.tr('Give your Scene a memorable name. e.g. "Her Last Secret"')
        )
        scroll_layout.addWidget(self.name_scene_edit)

        self.image_scene_label = QLabel(self.tr("Cover Image"))
        self.image_scene_label.setFont(font)
        scroll_layout.addWidget(
            self.image_scene_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.cover_widget = QWidget()
        self.cover_widget.setObjectName("chatScrollArea")
        self.cover_widget.setFixedSize(750, 296)
        cover_layout = QVBoxLayout()
        self.cover_widget.setLayout(cover_layout)

        upload_button = PushButton(self.tr("Upload"))
        upload_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        upload_button.clicked.connect(self.selectImage)
        cover_layout.addWidget(upload_button, alignment=Qt.AlignmentFlag.AlignCenter)

        scroll_layout.addWidget(
            self.cover_widget, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.visibility_label = QLabel(self.tr("Visibility"))
        self.visibility_label.setFont(font)
        scroll_layout.addWidget(
            self.visibility_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.visible_combobox = ComboBox()
        self.visible_combobox.addItems(
            [self.tr("Public"), self.tr("Unlisted"), self.tr("Private")]
        )
        scroll_layout.addWidget(
            self.visible_combobox, alignment=Qt.AlignmentFlag.AlignLeft
        )

        final_buttons_layout = QHBoxLayout()
        final_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.create_button = PushButton(self.tr("Create Scene"))
        self.create_button.clicked.connect(self.createScene)
        final_buttons_layout.addWidget(
            self.create_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.save_button = PushButton(self.tr("Save Changes"))
        self.save_button.clicked.connect(self.saveScene)
        final_buttons_layout.addWidget(
            self.save_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.save_chat_button = PushButton(self.tr("Save and Chat"))
        self.save_chat_button.clicked.connect(self.saveSceneChat)
        final_buttons_layout.addWidget(
            self.save_chat_button, alignment=Qt.AlignmentFlag.AlignRight
        )
        if self.create:
            self.create_button.setVisible(True)
            self.save_button.setVisible(False)
            self.save_chat_button.setVisible(False)
        else:
            self.create_button.setVisible(False)
            self.save_button.setVisible(True)
            self.save_chat_button.setVisible(True)
        scroll_layout.addLayout(final_buttons_layout)

        main_layout.addWidget(scroll_page, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)

    def saveSceneChat(self):
        if (
            len(self.scene_genre_edit.text()) <= 1
            or len(self.when_scene_edit.text()) <= 1
            or len(self.where_scene_edit.text()) <= 1
            or len(self.tone_scene_edit.text()) <= 1
            or len(self.what_scene_edit.text()) <= 1
            or len(self.goal_scene_edit.text()) <= 1
            or len(self.audience_scene_edit.text()) <= 1
            or len(self.greeting_edit.toPlainText()) <= 1
            or len(self.name_scene_edit.text()) <= 1
            or not self.image_selected
        ):
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.saveData()

        self.mw.chat_thread.update_scene_signal.connect(self._saveSceneChat)
        self.mw.chat_thread.update_scene(self.data, self.scene_id)

    def _saveSceneChat(self, data):
        if data.get("scene_id"):
            self.mw.showNotification(self.tr("The scene has been saved successfully!"))
            self.mw.openScene(scene_id=self.scene_id)
        else:
            self.mw.showNotification(str(data))

    def saveScene(self):
        if (
            len(self.scene_genre_edit.text()) <= 1
            or len(self.when_scene_edit.text()) <= 1
            or len(self.where_scene_edit.text()) <= 1
            or len(self.tone_scene_edit.text()) <= 1
            or len(self.what_scene_edit.text()) <= 1
            or len(self.goal_scene_edit.text()) <= 1
            or len(self.audience_scene_edit.text()) <= 1
            or len(self.greeting_edit.toPlainText()) <= 1
            or len(self.name_scene_edit.text()) <= 1
            or not self.image_selected
        ):
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.saveData()

        self.mw.chat_thread.update_scene_signal.connect(self._saveScene)
        self.mw.chat_thread.update_scene(self.data, self.scene_id)

    def _saveScene(self, data):
        if data.get("scene_id"):
            self.mw.showNotification(self.tr("The scene has been saved successfully!"))
        else:
            self.mw.showNotification(str(data))

    def createScene(self):
        self.saveData()

        self.mw.chat_thread.create_scene_signal.connect(self._createScene)
        self.mw.chat_thread.create_scene(self.data)

    def _createScene(self, data):
        if data.get("scene_id"):
            self.mw.showNotification(
                self.tr("The scene has been successfully created!")
            )
            self.mw.openScene(data, data.get("scene_id"))
        else:
            self.mw.showNotification(str(data))

    def saveData(self):
        if (
            len(self.scene_genre_edit.text()) <= 1
            or len(self.when_scene_edit.text()) <= 1
            or len(self.where_scene_edit.text()) <= 1
            or len(self.tone_scene_edit.text()) <= 1
            or len(self.what_scene_edit.text()) <= 1
            or len(self.goal_scene_edit.text()) <= 1
            or len(self.audience_scene_edit.text()) <= 1
            or len(self.greeting_edit.toPlainText()) <= 1
            or len(self.name_scene_edit.text()) <= 1
            or not self.image_selected
        ):
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.data["definition"]["genre"] = self.scene_genre_edit.text()
        self.data["definition"]["timeframe"] = self.when_scene_edit.text()
        self.data["definition"]["location"] = self.where_scene_edit.text()
        self.data["definition"]["tone"] = self.tone_scene_edit.text()
        self.data["definition"]["backstory"] = self.what_scene_edit.text()
        self.data["definition"]["goal"] = self.goal_scene_edit.text()
        self.data["description"] = self.audience_scene_edit.text()
        self.data["greeting_override"] = self.greeting_edit.toPlainText()
        self.data["title"] = self.name_scene_edit.text()

        if self.visible_combobox.currentText() == self.tr("Public"):
            self.data["visibility"] = "VISIBILITY_PUBLIC"
        elif self.visible_combobox.currentText() == self.tr("Unlisted"):
            self.data["visibility"] = "VISIBILITY_UNLISTED"
        elif self.visible_combobox.currentText() == self.tr("Private"):
            self.data["visibility"] = "VISIBILITY_PRIVATE"

    def loadData(self, data):
        self.data = data
        if len(self.data) != 0:
            if self.data.get("background_image_url"):
                link = self.data.get("background_image_url")
                self.mw.image_loader.load(
                    link,
                    854,
                    480,
                    0,
                    callback=lambda _: self._onBackgroundDownloaded(
                        os.path.join(
                            "cache/background",
                            hashlib.md5(link.encode()).hexdigest() + ".png",
                        )
                    ),
                    error_cb=lambda _: self.mw.showNotification(
                        self.tr("Error downloading image")
                    ),
                    cache_dir="cache/background",
                )
                self.image_selected = True
            self.scene_genre_edit.setText(self.data.get("definition", {}).get("genre"))
            self.when_scene_edit.setText(
                self.data.get("definition", {}).get("timeframe")
            )
            self.where_scene_edit.setText(
                self.data.get("definition", {}).get("location")
            )
            self.tone_scene_edit.setText(self.data.get("definition", {}).get("tone"))
            self.what_scene_edit.setText(
                self.data.get("definition", {}).get("backstory")
            )
            self.goal_scene_edit.setText(self.data.get("definition", {}).get("goal"))
            self.audience_scene_edit.setText(self.data.get("description"))
            self.greeting_edit.setText(self.data.get("greeting_override"))
            self.name_scene_edit.setText(self.data.get("title"))
            if self.data["visibility"] == "VISIBILITY_PUBLIC":
                self.visible_combobox.setCurrentText(self.tr("Public"))
            elif self.data["visibility"] == "VISIBILITY_UNLISTED":
                self.visible_combobox.setCurrentText(self.tr("Unlisted"))
            elif self.data["visibility"] == "VISIBILITY_PRIVATE":
                self.visible_combobox.setCurrentText(self.tr("Private"))

    def createTopBar(self):
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def addText(self, text):
        original_text = self.definition_edit.toPlainText()
        original_text += text
        self.definition_edit.setText(original_text)

    def textChanged(self, text_edit, max_len):
        text = text_edit.toPlainText()
        line_count = text.count("\n")
        line_count += text.count("<br>") + 1 if text else 1
        height = line_count * text_edit.fontMetrics().lineSpacing() + 32
        text_edit.setFixedHeight(height)
        if len(text) > max_len:
            text_edit.setPlainText(text[:max_len])
            cursor = text_edit.textCursor()
            cursor.setPosition(max_len)
            text_edit.setTextCursor(cursor)

    def selectImage(self):
        def uploaded(response):
            if response.get("status") == "OK":
                link = response["value"]
                self.mw.image_loader.load(
                    link,
                    1280,
                    720,
                    0,
                    callback=lambda _: self._onBackgroundDownloaded(
                        os.path.join(
                            "cache/background",
                            hashlib.md5(link.encode()).hexdigest() + ".png",
                        )
                    ),
                    error_cb=lambda _: self.mw.showNotification(
                        self.tr("Error downloading image")
                    ),
                    cache_dir="cache/background",
                )
                self.data["background_image_url"] = link
                self.image_selected = True
            else:
                self.mw.showNotification(response.get("error"))

        file_dialog = QFileDialog()
        file_dialog.setNameFilter(
            "Images (*.xbm *.tif *.jfif *.pjp *.apng *.svgz *.jpg *.heif *.ico *.tiff *.webp *.jpeg *.heic *.gif *.svg *.png *.bmp *.pjpeg *.avif)"
        )

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            mp = CurlMime()

            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".bmp": "image/bmp",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
                ".tiff": "image/tiff",
                ".tif": "image/tiff",
            }
            content_type = mime_types.get(ext, "application/octet-stream")

            mp.addpart(
                name="image",
                content_type=content_type,
                filename=os.path.basename(file_path),
                local_path=file_path,
            )

            self.mw.chat_thread.upload_image_signal.connect(uploaded)
            self.mw.chat_thread.upload_image(mp)

            self.mw.showNotification(self.tr("Uploading..."))

    def _onBackgroundDownloaded(self, file_path):
        self.background_image = file_path
        self.applyBackground(file_path)

    def applyBackground(self, path):
        if path and os.path.exists(path):
            path = path.replace("\\", "/")
            self.cover_widget.setStyleSheet(f"""
                #chatScrollArea {{
                    border-image: url("{path}") 0 0 0 0 stretch stretch;
                }}
            """)

        else:
            self.cover_widget.setStyleSheet("#chatScrollArea {}")

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.deleteLater()
