import hashlib
import os
import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QWidget,
                             QFileDialog, QFrame, QStackedWidget)
from curl_cffi import CurlMime

from modules.cards.CharacterCards import ListCard
from modules.style.Elements import (CustomTextEdit, PushButton, LineEdit, ComboBox, VerticalScrollPage,
                                    ClickableFrame, TabButton)
from modules.style.Icons import Svg

class ChoiceStep(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.svg_icons = Svg()
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        scroll_page = VerticalScrollPage()
        scroll_page.setFixedWidth(800)
        scroll_page.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        setup_label = QLabel(self.tr("Scenes are instant roleplay setups you create, where anyone can drop into a specific setting with their favorite Character. They are like side stories branching from the core chat, perfect for anyone to start roleplaying right away. Create a Scene to bring your story to life."))
        font = setup_label.font()
        font.setBold(True)
        font.setPointSize(12)
        setup_label.setFont(font)
        setup_label.setWordWrap(True)
        scroll_layout.addWidget(setup_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        best_practices_button = PushButton(self.tr("Tips and best practices"))
        best_practices_button.clicked.connect(lambda: webbrowser.open_new_tab("https://support.character.ai/hc/en-us/articles/41918454359451-Scene-Creation-Quickstart-Guide"))
        scroll_layout.addWidget(best_practices_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        choice_widget = QWidget()
        choice_layout = QHBoxLayout()
        choice_widget.setLayout(choice_layout)

        any_char_frame = ClickableFrame()
        any_char_frame.mousePressEvent = self.openAnyCharFirstPage
        acf_layout = QVBoxLayout()
        any_char_frame.setLayout(acf_layout)
        acf_title_label = QLabel(self.tr("Any Character Scene"))
        font = acf_title_label.font()
        font.setBold(True)
        font.setPointSize(14)
        acf_title_label.setFont(font)
        acf_layout.addWidget(acf_title_label, alignment=Qt.AlignmentFlag.AlignLeft)
        acf_description_label = QLabel(self.tr("A Scene that works with any Character. Perfect for general scenarios where any Character can jump in and interact."))
        font = acf_description_label.font()
        font.setPointSize(12)
        acf_description_label.setFont(font)
        acf_description_label.setWordWrap(True)
        acf_layout.addWidget(acf_description_label, alignment=Qt.AlignmentFlag.AlignLeft)
        choice_layout.addWidget(any_char_frame)

        main_char_frame = ClickableFrame()
        main_char_frame.mousePressEvent = self.openMainCharFirstPage
        mcf_layout = QVBoxLayout()
        main_char_frame.setLayout(mcf_layout)
        mcf_title_label = QLabel(self.tr("Main Character Scene"))
        font = mcf_title_label.font()
        font.setBold(True)
        font.setPointSize(14)
        mcf_title_label.setFont(font)
        mcf_layout.addWidget(mcf_title_label, alignment=Qt.AlignmentFlag.AlignLeft)
        mcf_description_label = QLabel(self.tr("A Scene designed for a specific Character you have in mind, tailored to their personality and backstory."))
        font = mcf_description_label.font()
        font.setPointSize(12)
        mcf_description_label.setFont(font)
        mcf_description_label.setWordWrap(True)
        mcf_layout.addWidget(mcf_description_label, alignment=Qt.AlignmentFlag.AlignLeft)
        choice_layout.addWidget(main_char_frame)

        scroll_layout.addWidget(choice_widget, alignment=Qt.AlignmentFlag.AlignHCenter)

        main_layout.addWidget(scroll_page, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)

    def createTopBar(self):
        top_bar = QWidget()
        #top_bar.setFixedHeight(0)
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        welcome_label = QLabel(self.tr("Welcome to Scenes. Ready to create?"))
        font = welcome_label.font()
        font.setBold(True)
        font.setPointSize(16)
        welcome_label.setFont(font)
        top_bar_layout.addWidget(welcome_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        return top_bar, top_bar_layout

    def openAnyCharFirstPage(self, i):
        page = AnyCharFirstPage(self.mw)
        self.mw.main_content_area.addWidget(page)
        self.mw.main_content_area.setCurrentWidget(page)
        self.deleteLater()

    def openMainCharFirstPage(self, i):
        page = MainCharFirstPage(self.mw)
        self.mw.main_content_area.addWidget(page)
        self.mw.main_content_area.setCurrentWidget(page)
        self.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.deleteLater()

class AnyCharFirstPage(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.svg_icons = Svg()
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        scroll_page = VerticalScrollPage()
        scroll_page.setFixedWidth(800)
        scroll_page.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        first_line = [{
            "title": "",
            "description": self.tr("Create my own"),
            "style": self.tr("You write the story, your audience pick the Character"),
            "data": {}
        },
        {
            "title": self.tr("Template"),
            "description": self.tr("The Mysteriously Vanishing Fortune"),
            "style": self.tr("Mystery"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Mystery",
                    'goal': "Get {{char}} to explain how they came into possession of the gold.",
                    'location': "First-class passenger car of a train at a remote station",
                    'timeframe': "Late 1800s",
                    'tone': "Mysterious"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        },
        {
            "title": self.tr("Template"),
            "description": self.tr("The Shapeshifter’s Genome: A Sci-Fi Scene"),
            "style": self.tr("Sci-Fi"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Sci-Fi",
                    'goal': "Get {{char}} to reveal what they truly are. ",
                    'location': "School",
                    'timeframe': "2020s",
                    'tone': "Dramatic"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        }]
        second_line = [{
            "title": self.tr("Template"),
            "description": self.tr("Ride the Dragon"),
            "style": self.tr("Fantasy"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Fantasy",
                    'goal': "Make the dragon agree to let {{user}} ride on them ",
                    'location': "Forest",
                    'timeframe': "1800s",
                    'tone': "Dramatic"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        },
        {
            "title": self.tr("Template"),
            "description": self.tr("The Romantic Ball: Ask Them To Dance"),
            "style": self.tr("Romance"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Romance",
                    'goal': "Reassure {{char}} about their worries and invite them to dance. Have them accept your hand.",
                    'location': "Ballroom",
                    'timeframe': "Late 1800s",
                    'tone': "Romantic"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        },
        {
            "title": self.tr("Template"),
            "description": self.tr("They Cheated on Me"),
            "style": self.tr("Drama"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Drama",
                    'goal': "Confront {{char}} about their betrayal and decide whether to forgive or walk away for good.",
                    'location': "Apartment",
                    'timeframe': "Present Day",
                    'tone': "Dramatic"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        }]
        third_line = [{
            "title": self.tr("Template"),
            "description": self.tr("Plane Crashed: Stranded on an Island"),
            "style": self.tr("Survival/Adventure"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Survival",
                    'goal': "Explore the environment with {{char}} and create a signal strong enough to draw rescue before it’s too late.",
                    'location': "Island",
                    'timeframe': "2000s",
                    'tone': "Tense"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        },
        {
            "title": self.tr("Template"),
            "description": self.tr("The Freshman College Party"),
            "style": self.tr("Coming-of-age"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Coming-of-Age",
                    'goal': "Choose what to wear to the party and leave the dorm with {{char}}. ",
                    'location': "College Dorms",
                    'timeframe': "2010s",
                    'tone': "Dramatic"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        },
        {
            "title": self.tr("Template"),
            "description": self.tr("Coffee Shop AU: Latte Hearts"),
            "style": self.tr("Slice-of-life"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Slice-of-life",
                    'goal': "Get {{char}} to agree to go on a date with you",
                    'location': "Coffee Shop",
                    'timeframe': "Present Day",
                    'tone': "Heartwarming"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        }]

        first_line_widget = QWidget()
        first_line_layout = QHBoxLayout()
        first_line_layout.setContentsMargins(0,0,0,0)
        first_line_widget.setLayout(first_line_layout)
        second_line_widget = QWidget()
        second_line_layout = QHBoxLayout()
        second_line_layout.setContentsMargins(0, 0, 0, 0)
        second_line_widget.setLayout(second_line_layout)
        third_line_widget = QWidget()
        third_line_layout = QHBoxLayout()
        third_line_layout.setContentsMargins(0, 0, 0, 0)
        third_line_widget.setLayout(third_line_layout)

        for i in first_line:
            frame = self.createVariantFrame(i)
            first_line_layout.addWidget(frame)
        for i in second_line:
            frame = self.createVariantFrame(i)
            second_line_layout.addWidget(frame)
        for i in third_line:
            frame = self.createVariantFrame(i)
            third_line_layout.addWidget(frame)

        scroll_layout.addWidget(first_line_widget)
        scroll_layout.addWidget(second_line_widget)
        scroll_layout.addWidget(third_line_widget)
        main_layout.addWidget(scroll_page, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)

    def createTopBar(self):
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        welcome_label = QLabel(self.tr("Welcome to Scenes. Ready to create?"))
        font = welcome_label.font()
        font.setBold(True)
        font.setPointSize(16)
        welcome_label.setFont(font)
        top_bar_layout.addWidget(welcome_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        return top_bar, top_bar_layout

    def createVariantFrame(self, data):
        title = data.get('title')
        description = data.get('description')
        style = data.get('style')
        sdata = data.get('data', {})

        frame = ClickableFrame()
        frame.setFixedSize(260, 180)
        def _open(_):
            page = AnyCharCreatePage(self.mw, sdata, True)
            self.mw.main_content_area.addWidget(page)
            self.mw.main_content_area.setCurrentWidget(page)
            self.deleteLater()
        frame.mousePress = _open
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        frame.setLayout(layout)
        title_label = QLabel(title)
        font = title_label.font()
        font.setPointSize(10)
        title_label.setFont(font)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignLeft)
        description_label = QLabel(description)
        font = description_label.font()
        font.setPointSize(14)
        description_label.setFont(font)
        description_label.setWordWrap(True)
        layout.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignLeft)
        style_label = QLabel(style)
        font = style_label.font()
        font.setPointSize(12)
        style_label.setFont(font)
        style_label.setWordWrap(True)
        layout.addWidget(style_label, alignment=Qt.AlignmentFlag.AlignLeft)

        return frame

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.deleteLater()

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
            self.loadData({
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "",
                    'goal': "",
                    'location': "",
                    'timeframe': "",
                    'tone': ""
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            })
        else:
            self.data = {
                'background_image_url': data.get("background_image_url"),
                'character_id': data.get("character_id", ""),
                'color_scheme_id': data.get("color_scheme_id", ""),
                'definition': {
                    'backstory': data.get("definition", {}).get("backstory"),
                    'genre': data.get("definition", {}).get("genre"),
                    'goal': data.get("definition", {}).get("goal"),
                    'location': data.get("definition", {}).get("location"),
                    'timeframe': data.get("definition", {}).get("timeframe"),
                    'tone': data.get("definition", {}).get("tone"),
                },
                'description': data.get("description"),
                'greeting_override': data.get("greeting_override"),
                'scene_id': data.get("scene_id"),
                'tags': data.get("tags", []),
                'title': data.get("title"),
                'visibility': data.get("visibility"),
            }
            if data['background_image_url'] != "":
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
        self.scene_genre_label.setToolTip(self.tr("Select the genre. This guides the Character's style and tone."))
        scroll_layout.addWidget(self.scene_genre_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.scene_genre_edit = LineEdit()
        self.scene_genre_edit.setPlaceholderText(self.tr("Select the genre. This guides the Character’s style and tone."))
        self.scene_genre_edit.setMaxLength(60)
        scroll_layout.addWidget(self.scene_genre_edit)

        self.when_scene_label = QLabel(self.tr("When is this Scene set?"))
        self.when_scene_label.setFont(font)
        self.when_scene_label.setToolTip(self.tr("Set the time. This guides the Character contextually when the Scene is taking place."))
        scroll_layout.addWidget(self.when_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.when_scene_edit = LineEdit()
        self.when_scene_edit.setMaxLength(60)
        self.when_scene_edit.setPlaceholderText(self.tr("Set the time. This guides the Character contextually when the Scene is taking place."))
        scroll_layout.addWidget(self.when_scene_edit)

        self.where_scene_label = QLabel(self.tr("Where does this Scene happen?"))
        self.where_scene_label.setFont(font)
        self.where_scene_label.setToolTip(self.tr("Set the location. This grounds the Character where the Scene is taking place."))
        scroll_layout.addWidget(self.where_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.where_scene_edit = LineEdit()
        self.where_scene_edit.setMaxLength(60)
        self.where_scene_edit.setPlaceholderText(self.tr("Set the location. This grounds the Character where the Scene is taking place."))
        scroll_layout.addWidget(self.where_scene_edit)

        self.tone_scene_label = QLabel(self.tr("Tone of this Scene"))
        self.tone_scene_label.setFont(font)
        self.tone_scene_label.setToolTip(self.tr("What's the mood of the Scene? The defines the atmosphere and emotional tone to help your audience immerse."))
        scroll_layout.addWidget(self.tone_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.tone_scene_edit = LineEdit()
        self.tone_scene_edit.setMaxLength(60)
        self.tone_scene_edit.setPlaceholderText(self.tr("What’s the mood of the Scene? This defines the atmosphere and emotional tone to help your audience immerse."))
        scroll_layout.addWidget(self.tone_scene_edit)

        self.what_scene_label = QLabel(self.tr("What’s the backstory of this Scene?"))
        self.what_scene_label.setFont(font)
        self.what_scene_label.setToolTip(self.tr("Describe what is happening in this Scene. Include relevant details about the situation and backstory. This will help shape how the Scene unfolds and how the Character responds. Use {{user}} for the user. Use {{char}} for the Character. If you are building an Any-Character Scene we recommend that you avoid the following pronouns: he, she, his, her, so your Scene can work for any character."))
        scroll_layout.addWidget(self.what_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.what_scene_edit = LineEdit()
        self.what_scene_edit.setMaxLength(500)
        self.what_scene_edit.setPlaceholderText(self.tr("""Describe what is happening in this Scene. Include relevant details about the situation and backstory. This will help shape how the Scene unfolds and how the Character responds.
        
Use {{user}} for the user.
Use {{char}} for the Character.

If you are building an Any-Character Scene we recommend that you avoid the following pronouns: he, she, his, her, so your Scene can work for any character.
"""))
        scroll_layout.addWidget(self.what_scene_edit)

        self.goal_scene_label = QLabel(self.tr("What's the player's goal in this Scene?"))
        self.goal_scene_label.setFont(font)
        self.goal_scene_label.setToolTip(self.tr("Define a goal that is the next logical story beat, tells the player what to try, and make the goal achievable with a clear, detectable moment of success.Keep it specific and concrete. A good goal = verb that implies effort + challenges or constraints. E.g. Unmask the stranger before the final waltz ends."))
        scroll_layout.addWidget(self.goal_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.goal_scene_edit = LineEdit()
        self.goal_scene_edit.setMaxLength(120)
        self.goal_scene_edit.setPlaceholderText(self.tr("""Define a goal that is the next logical story beat, tells the player what to try, and make the goal achievable with a clear, detectable moment of success.Keep it specific and concrete.

A good goal = verb that implies effort + challenges or constraints
E.g. Unmask the stranger before the final waltz ends.
"""))
        scroll_layout.addWidget(self.goal_scene_edit)

        self.audience_scene_label = QLabel(self.tr("Introduce this Scene to your audience"))
        self.audience_scene_label.setFont(font)
        self.audience_scene_label.setToolTip(self.tr("This is the starting screen of your Scene. Your audience will see this intro before entering the Scene. Help them understand what’s happening and get excited to start playing the Scene. Use {{user}} for the user. Use {{char}} for the Character."))
        scroll_layout.addWidget(self.audience_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.audience_scene_edit = LineEdit()
        self.audience_scene_edit.setMaxLength(650)
        self.audience_scene_edit.setPlaceholderText(self.tr("This is the starting screen of your Scene. Your audience will see this intro before entering the Scene. Help them understand what’s happening and get excited to start playing the Scene. Use {{user}} for the user. Use {{char}} for the Character."))
        scroll_layout.addWidget(self.audience_scene_edit)

        greeting_layout = QHBoxLayout()
        scroll_layout.addLayout(greeting_layout)
        self.greeting_label = QLabel(self.tr("Character greeting"))
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
        self.greeting_edit.setPlaceholderText(self.tr("This is the first Character message your audience will see after entering the Scene. Make it your hook with what they will see, hear, and feel."))
        self.greeting_edit.textChanged.connect(lambda: self.textChanged(self.greeting_edit, 1200))
        self.greeting_edit.setFixedHeight(48)
        self.greeting_edit.horizontalScrollBar().setVisible(False)
        self.greeting_edit.verticalScrollBar().setVisible(False)
        scroll_layout.addWidget(self.greeting_edit)

        self.name_scene_label = QLabel(self.tr("Name"))
        self.name_scene_label.setFont(font)
        scroll_layout.addWidget(self.name_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.name_scene_edit = LineEdit()
        self.name_scene_edit.setMaxLength(40)
        self.name_scene_edit.setPlaceholderText(self.tr('Give your Scene a memorable name. e.g. "Her Last Secret"'))
        scroll_layout.addWidget(self.name_scene_edit)

        self.image_scene_label = QLabel(self.tr("Cover Image"))
        self.image_scene_label.setFont(font)
        scroll_layout.addWidget(self.image_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.cover_widget = QWidget()
        self.cover_widget.setObjectName("chatScrollArea")
        self.cover_widget.setFixedSize(750, 296)
        cover_layout = QVBoxLayout()
        self.cover_widget.setLayout(cover_layout)

        upload_button = PushButton(self.tr("Upload"))
        upload_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        upload_button.clicked.connect(self.selectImage)
        cover_layout.addWidget(upload_button, alignment=Qt.AlignmentFlag.AlignCenter)

        scroll_layout.addWidget(self.cover_widget, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.visibility_label = QLabel(self.tr("Visibility"))
        self.visibility_label.setFont(font)
        scroll_layout.addWidget(self.visibility_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.visible_combobox = ComboBox()
        self.visible_combobox.addItems([self.tr("Public"), self.tr("Unlisted"), self.tr("Private")])
        scroll_layout.addWidget(self.visible_combobox, alignment=Qt.AlignmentFlag.AlignLeft)

        final_buttons_layout = QHBoxLayout()
        final_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.create_button = PushButton(self.tr("Create Scene"))
        self.create_button.clicked.connect(self.createScene)
        final_buttons_layout.addWidget(self.create_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.save_button = PushButton(self.tr("Save Changes"))
        self.save_button.clicked.connect(self.saveScene)
        final_buttons_layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.save_chat_button = PushButton(self.tr("Save and Chat"))
        self.save_chat_button.clicked.connect(self.saveSceneChat)
        final_buttons_layout.addWidget(self.save_chat_button, alignment=Qt.AlignmentFlag.AlignRight)
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
        if len(self.scene_genre_edit.text()) <= 1 or len(self.when_scene_edit.text()) <= 1 or len(self.where_scene_edit.text()) <= 1 or len(self.tone_scene_edit.text()) <= 1 or len(self.what_scene_edit.text()) <= 1 or len(self.goal_scene_edit.text()) <= 1 or len(self.audience_scene_edit.text()) <= 1 or len(self.greeting_edit.toPlainText()) <= 1 or len(self.name_scene_edit.text()) <= 1 or not self.image_selected:
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.saveData()

        self.mw.chat_thread.update_scene_signal.connect(self._saveSceneChat)
        self.mw.chat_thread.update_scene(self.data, self.scene_id)

    def _saveSceneChat(self, data):
        if data.get('scene_id'):
            self.mw.showNotification(self.tr("The scene has been saved successfully!"))
            self.mw.openScene(scene_id=self.scene_id)
        else:
            self.mw.showNotification(str(data))

    def saveScene(self):
        if len(self.scene_genre_edit.text()) <= 1 or len(self.when_scene_edit.text()) <= 1 or len(self.where_scene_edit.text()) <= 1 or len(self.tone_scene_edit.text()) <= 1 or len(self.what_scene_edit.text()) <= 1 or len(self.goal_scene_edit.text()) <= 1 or len(self.audience_scene_edit.text()) <= 1 or len(self.greeting_edit.toPlainText()) <= 1 or len(self.name_scene_edit.text()) <= 1 or not self.image_selected:
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.saveData()

        self.mw.chat_thread.update_scene_signal.connect(self._saveScene)
        self.mw.chat_thread.update_scene(self.data, self.scene_id)

    def _saveScene(self, data):
        if data.get('scene_id'):
            self.mw.showNotification(self.tr("The scene has been saved successfully!"))
        else:
            self.mw.showNotification(str(data))

    def createScene(self):
        self.saveData()

        self.mw.chat_thread.create_scene_signal.connect(self._createScene)
        self.mw.chat_thread.create_scene(self.data)

    def _createScene(self, data):
        if data.get('scene_id'):
            self.mw.showNotification(self.tr("The scene has been successfully created!"))
            self.mw.openScene(data, data.get('scene_id'))
        else:
            self.mw.showNotification(str(data))

    def saveData(self):
        if len(self.scene_genre_edit.text()) <= 1 or len(self.when_scene_edit.text()) <= 1 or len(self.where_scene_edit.text()) <= 1 or len(self.tone_scene_edit.text()) <= 1 or len(self.what_scene_edit.text()) <= 1 or len(self.goal_scene_edit.text()) <= 1 or len(self.audience_scene_edit.text()) <= 1 or len(self.greeting_edit.toPlainText()) <= 1 or len(self.name_scene_edit.text()) <= 1 or not self.image_selected:
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.data['definition']['genre'] = self.scene_genre_edit.text()
        self.data['definition']['timeframe'] = self.when_scene_edit.text()
        self.data['definition']['location'] = self.where_scene_edit.text()
        self.data['definition']['tone'] = self.tone_scene_edit.text()
        self.data['definition']['backstory'] = self.what_scene_edit.text()
        self.data['definition']['goal'] = self.goal_scene_edit.text()
        self.data['description'] = self.audience_scene_edit.text()
        self.data['greeting_override'] = self.greeting_edit.toPlainText()
        self.data['title'] = self.name_scene_edit.text()

        if self.visible_combobox.currentText() == self.tr('Public'):
            self.data['visibility'] = "VISIBILITY_PUBLIC"
        elif self.visible_combobox.currentText() == self.tr('Unlisted'):
            self.data['visibility'] = "VISIBILITY_UNLISTED"
        elif self.visible_combobox.currentText() == self.tr('Private'):
            self.data['visibility'] = "VISIBILITY_PRIVATE"

    def loadData(self, data):
        self.data = data
        if len(self.data) != 0:
            if self.data.get('background_image_url'):
                link = self.data.get('background_image_url')
                self.mw.image_loader.load(
                    link, 854, 480, 0,
                    callback=lambda _: self._onBackgroundDownloaded(
                        os.path.join("cache/background", hashlib.md5(link.encode()).hexdigest() + ".png")),
                    error_cb=lambda _: self.mw.showNotification(self.tr("Error downloading image")),
                    cache_dir="cache/background")
                self.image_selected = True
            self.scene_genre_edit.setText(self.data.get('definition', {}).get('genre'))
            self.when_scene_edit.setText(self.data.get('definition', {}).get('timeframe'))
            self.where_scene_edit.setText(self.data.get('definition', {}).get('location'))
            self.tone_scene_edit.setText(self.data.get('definition', {}).get('tone'))
            self.what_scene_edit.setText(self.data.get('definition', {}).get('backstory'))
            self.goal_scene_edit.setText(self.data.get('definition', {}).get('goal'))
            self.audience_scene_edit.setText(self.data.get('description'))
            self.greeting_edit.setText(self.data.get('greeting_override'))
            self.name_scene_edit.setText(self.data.get('title'))
            if self.data['visibility'] == "VISIBILITY_PUBLIC":
                self.visible_combobox.setCurrentText(self.tr('Public'))
            elif self.data['visibility'] == "VISIBILITY_UNLISTED":
                self.visible_combobox.setCurrentText(self.tr('Unlisted'))
            elif self.data['visibility'] == "VISIBILITY_PRIVATE":
                self.visible_combobox.setCurrentText(self.tr('Private'))

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
        line_count = text.count('\n')
        line_count += text.count('<br>') + 1 if text else 1
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
                link = response['value']
                self.mw.image_loader.load(
                    link, 1280, 720, 0,
                    callback=lambda _: self._onBackgroundDownloaded(
                        os.path.join("cache/background", hashlib.md5(link.encode()).hexdigest() + ".png")),
                    error_cb=lambda _: self.mw.showNotification(self.tr("Error downloading image")),
                    cache_dir="cache/background")
                self.data['background_image_url'] = link
                self.image_selected = True
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

    def _onBackgroundDownloaded(self, file_path):
        self.background_image = file_path
        self.applyBackground(file_path)

    def applyBackground(self, path):
        if path and os.path.exists(path):
            path = path.replace('\\', '/')
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


class MainCharFirstPage(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.svg_icons = Svg()
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        scroll_page = VerticalScrollPage()
        scroll_page.setFixedWidth(800)
        scroll_page.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        first_line = [{
            "title": "",
            "description": self.tr("Create my own"),
            "style": self.tr("You write the story, your audience pick the Character"),
            "data": {}
        },
            {
                "title": self.tr("Template"),
                "description": self.tr("The Vanishing Headstone"),
                "style": self.tr("Mystery"),
                "data": {
                    'background_image_url': "",
                    'character_id': "",
                    'color_scheme_id': "",
                    'definition': {
                        'backstory': "",
                        'genre': "Mystery",
                        'goal': "Investigate the disturbed gravesite with Jasper and uncover a concrete clue about who took the headstone.",
                        'location': "Graveyard",
                        'timeframe': "Future",
                        'tone': "Mysterious"
                    },
                    'description': "",
                    'greeting_override': "",
                    'tags': [],
                    'title': "",
                    'visibility': ""
                }
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("The Jungle on Pluto"),
                "style": self.tr("Sci-Fi"),
                "data": {
                    'background_image_url': "",
                    'character_id': "",
                    'color_scheme_id': "",
                    'definition': {
                        'backstory': "",
                        'genre': "Sci-Fi",
                        'goal': "Travel with Ele to a new part of the jungle and identify a unique lifeform or phenomenon.",
                        'location': "Jungle",
                        'timeframe': "Future",
                        'tone': "Dramatic"
                    },
                    'description': "",
                    'greeting_override': "",
                    'tags': [],
                    'title': "",
                    'visibility': ""
                }
            }]
        second_line = [{
            "title": self.tr("Template"),
            "description": self.tr("Zixie’s Path to the Elven Village"),
            "style": self.tr("Fantasy"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Fantasy",
                    'goal': "Navigate the first shift in the vine-path by choosing the correct way forward and have Zixie acknowledge your success. ",
                    'location': "Forest",
                    'timeframe': "Present Day",
                    'tone': "Dramatic"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        },
            {
                "title": self.tr("Template"),
                "description": self.tr("A Date at the Garlic Coffee Shop"),
                "style": self.tr("Romance"),
                "data": {
                    'background_image_url': "",
                    'character_id': "",
                    'color_scheme_id': "",
                    'definition': {
                        'backstory': "",
                        'genre': "Romance",
                        'goal': "Flirt with {{char}} and get her to acknowledge that she feels it too.",
                        'location': "Coffee Shop",
                        'timeframe': "Present day",
                        'tone': "Romantic"
                    },
                    'description': "",
                    'greeting_override': "",
                    'tags': [],
                    'title': "",
                    'visibility': ""
                }
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("They Cheated on Me"),
                "style": self.tr("Drama"),
                "data": {
                    'background_image_url': "",
                    'character_id': "",
                    'color_scheme_id': "",
                    'definition': {
                        'backstory': "",
                        'genre': "Drama",
                        'goal': "Choose a defense plan with Isabel and carry out the first step of it.",
                        'location': "Ocean",
                        'timeframe': "1700s",
                        'tone': "Dramatic"
                    },
                    'description': "",
                    'greeting_override': "",
                    'tags': [],
                    'title': "",
                    'visibility': ""
                }
            }]
        third_line = [{
            "title": self.tr("Template"),
            "description": self.tr("Brown Butter Cookies Vlog"),
            "style": self.tr("Slice-of-life"),
            "data": {
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "Slice-of-life",
                    'goal': "Create the brown butter cookie vlog with {{char}}, capturing not just the recipe but the memory that makes it matter.",
                    'location': "Kitchen",
                    'timeframe': "Present day",
                    'tone': "Gen Z"
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            }
        },
            {
                "title": self.tr("Template"),
                "description": self.tr("The Secrets of the Moonveil Sea"),
                "style": self.tr("Adventure"),
                "data": {
                    'background_image_url': "",
                    'character_id': "",
                    'color_scheme_id': "",
                    'definition': {
                        'backstory': "",
                        'genre': "Adventure",
                        'goal': "Explore the Moonveil Sea, follow {{char}} into the depths and discover the hidden creature or phenomenon he reveals.",
                        'location': "Ocean",
                        'timeframe': "1800s",
                        'tone': "Adventurous"
                    },
                    'description': "",
                    'greeting_override': "",
                    'tags': [],
                    'title': "",
                    'visibility': ""
                }
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("Candlelight and Silverware"),
                "style": self.tr("Slice-of-life"),
                "data": {
                    'background_image_url': "",
                    'character_id': "",
                    'color_scheme_id': "",
                    'definition': {
                        'backstory': "",
                        'genre': "Slice-of-life",
                        'goal': "Navigate small talk, tension, and formality to reach a moment where Ollie lets something personal slip.",
                        'location': "Restaurant",
                        'timeframe': "Present Day",
                        'tone': "Heartwarming"
                    },
                    'description': "",
                    'greeting_override': "",
                    'tags': [],
                    'title': "",
                    'visibility': ""
                }
            }]

        first_line_widget = QWidget()
        first_line_layout = QHBoxLayout()
        first_line_layout.setContentsMargins(0, 0, 0, 0)
        first_line_widget.setLayout(first_line_layout)
        second_line_widget = QWidget()
        second_line_layout = QHBoxLayout()
        second_line_layout.setContentsMargins(0, 0, 0, 0)
        second_line_widget.setLayout(second_line_layout)
        third_line_widget = QWidget()
        third_line_layout = QHBoxLayout()
        third_line_layout.setContentsMargins(0, 0, 0, 0)
        third_line_widget.setLayout(third_line_layout)

        for i in first_line:
            frame = self.createVariantFrame(i)
            first_line_layout.addWidget(frame)
        for i in second_line:
            frame = self.createVariantFrame(i)
            second_line_layout.addWidget(frame)
        for i in third_line:
            frame = self.createVariantFrame(i)
            third_line_layout.addWidget(frame)

        scroll_layout.addWidget(first_line_widget)
        scroll_layout.addWidget(second_line_widget)
        scroll_layout.addWidget(third_line_widget)
        main_layout.addWidget(scroll_page, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)

    def createTopBar(self):
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        welcome_label = QLabel(self.tr("Welcome to Scenes. Ready to create?"))
        font = welcome_label.font()
        font.setBold(True)
        font.setPointSize(16)
        welcome_label.setFont(font)
        top_bar_layout.addWidget(welcome_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        return top_bar, top_bar_layout

    def createVariantFrame(self, data):
        title = data.get('title')
        description = data.get('description')
        style = data.get('style')
        sdata = data.get('data', {})

        frame = ClickableFrame()
        frame.setFixedSize(260, 180)

        def _open(_):
            page = MainCharCreatePage(self.mw, sdata, True)
            self.mw.main_content_area.addWidget(page)
            self.mw.main_content_area.setCurrentWidget(page)
            self.deleteLater()

        frame.mousePress = _open
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        frame.setLayout(layout)
        title_label = QLabel(title)
        font = title_label.font()
        font.setPointSize(10)
        title_label.setFont(font)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignLeft)
        description_label = QLabel(description)
        font = description_label.font()
        font.setPointSize(14)
        description_label.setFont(font)
        description_label.setWordWrap(True)
        layout.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignLeft)
        style_label = QLabel(style)
        font = style_label.font()
        font.setPointSize(12)
        style_label.setFont(font)
        style_label.setWordWrap(True)
        layout.addWidget(style_label, alignment=Qt.AlignmentFlag.AlignLeft)

        return frame

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.deleteLater()

class MainCharCreatePage(QWidget):
    def __init__(self, main_window, data=None, create=False, scene_id=None):
        super().__init__(main_window)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.data = data
        self.create = create
        self.scene_id = scene_id
        self.current_character_id = ""
        self.image_loader = main_window.image_loader
        self.svg_icons = Svg()
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.image_selected = False
        self.initUI()
        if len(self.data) == 0:
            self.loadData({
                'background_image_url': "",
                'character_id': "",
                'color_scheme_id': "",
                'definition': {
                    'backstory': "",
                    'genre': "",
                    'goal': "",
                    'location': "",
                    'timeframe': "",
                    'tone': ""
                },
                'description': "",
                'greeting_override': "",
                'tags': [],
                'title': "",
                'visibility': ""
            })
        else:
            self.data = {
                'background_image_url': data.get("background_image_url"),
                'character_id': data.get("character_id", ""),
                'color_scheme_id': data.get("color_scheme_id", ""),
                'definition': {
                    'backstory': data.get("definition", {}).get("backstory"),
                    'genre': data.get("definition", {}).get("genre"),
                    'goal': data.get("definition", {}).get("goal"),
                    'location': data.get("definition", {}).get("location"),
                    'timeframe': data.get("definition", {}).get("timeframe"),
                    'tone': data.get("definition", {}).get("tone"),
                },
                'description': data.get("description"),
                'greeting_override': data.get("greeting_override"),
                'scene_id': data.get("scene_id"),
                'tags': data.get("tags", []),
                'title': data.get("title"),
                'visibility': data.get("visibility"),
            }
            if data['background_image_url'] != "":
                self.image_selected = True
            self.loadData(self.data)

        self.mw.chat_thread.get_user(self.mw.username)
        self.mw.chat_thread.get_user_signal.connect(self.getYourChars)

    def initUI(self):
        main_layout = QVBoxLayout()

        scroll_page = VerticalScrollPage()
        scroll_page.setFixedWidth(800)
        scroll_page.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        self.char_scene_label = QLabel(self.tr("Main Character of the Scene"))
        font = self.char_scene_label.font()
        font.setBold(True)
        font.setPointSize(12)
        self.char_scene_label.setFont(font)
        scroll_layout.addWidget(self.char_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.char_scene_widget = QStackedWidget()
        card = ListCard(self.mw, {})
        card.chat_button.setVisible(False)
        card.mousePressEvent = self.selectCharacter
        self.char_scene_widget.addWidget(card)
        self.char_scene_widget.setCurrentWidget(card)
        self.char_scene_widget.mousePressEvent = self.selectCharacter
        scroll_layout.addWidget(self.char_scene_widget, 1)

        self.scene_genre_label = QLabel(self.tr("Scene genre"))
        self.scene_genre_label.setFont(font)
        self.scene_genre_label.setToolTip(self.tr("Select the genre. This guides the Character's style and tone."))
        scroll_layout.addWidget(self.scene_genre_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.scene_genre_edit = LineEdit()
        self.scene_genre_edit.setPlaceholderText(self.tr("Select the genre. This guides the Character’s style and tone."))
        self.scene_genre_edit.setMaxLength(60)
        scroll_layout.addWidget(self.scene_genre_edit)

        self.when_scene_label = QLabel(self.tr("When is this Scene set?"))
        self.when_scene_label.setFont(font)
        self.when_scene_label.setToolTip(self.tr("Set the time. This guides the Character contextually when the Scene is taking place."))
        scroll_layout.addWidget(self.when_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.when_scene_edit = LineEdit()
        self.when_scene_edit.setMaxLength(60)
        self.when_scene_edit.setPlaceholderText(self.tr("Set the time. This guides the Character contextually when the Scene is taking place."))
        scroll_layout.addWidget(self.when_scene_edit)

        self.where_scene_label = QLabel(self.tr("Where does this Scene happen?"))
        self.where_scene_label.setFont(font)
        self.where_scene_label.setToolTip(self.tr("Set the location. This grounds the Character where the Scene is taking place."))
        scroll_layout.addWidget(self.where_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.where_scene_edit = LineEdit()
        self.where_scene_edit.setMaxLength(60)
        self.where_scene_edit.setPlaceholderText(self.tr("Set the location. This grounds the Character where the Scene is taking place."))
        scroll_layout.addWidget(self.where_scene_edit)

        self.tone_scene_label = QLabel(self.tr("Tone of this Scene"))
        self.tone_scene_label.setFont(font)
        self.tone_scene_label.setToolTip(self.tr("What's the mood of the Scene? The defines the atmosphere and emotional tone to help your audience immerse."))
        scroll_layout.addWidget(self.tone_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.tone_scene_edit = LineEdit()
        self.tone_scene_edit.setMaxLength(60)
        self.tone_scene_edit.setPlaceholderText(self.tr("What’s the mood of the Scene? This defines the atmosphere and emotional tone to help your audience immerse."))
        scroll_layout.addWidget(self.tone_scene_edit)

        self.what_scene_label = QLabel(self.tr("What’s the backstory of this Scene?"))
        self.what_scene_label.setFont(font)
        self.what_scene_label.setToolTip(self.tr("Describe what is happening in this Scene. Include relevant details about the situation and backstory. This will help shape how the Scene unfolds and how the Character responds. Use {{user}} for the user. Use {{char}} for the Character. If you are building an Any-Character Scene we recommend that you avoid the following pronouns: he, she, his, her, so your Scene can work for any character."))
        scroll_layout.addWidget(self.what_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.what_scene_edit = LineEdit()
        self.what_scene_edit.setMaxLength(500)
        self.what_scene_edit.setPlaceholderText(self.tr("""Describe what is happening in this Scene. Include relevant details about the situation and backstory. This will help shape how the Scene unfolds and how the Character responds.

Use {{user}} for the user.
Use {{char}} for the Character.

If you are building an Any-Character Scene we recommend that you avoid the following pronouns: he, she, his, her, so your Scene can work for any character.
"""))
        scroll_layout.addWidget(self.what_scene_edit)

        self.goal_scene_label = QLabel(self.tr("What's the player's goal in this Scene?"))
        self.goal_scene_label.setFont(font)
        self.goal_scene_label.setToolTip(self.tr("Define a goal that is the next logical story beat, tells the player what to try, and make the goal achievable with a clear, detectable moment of success.Keep it specific and concrete. A good goal = verb that implies effort + challenges or constraints. E.g. Unmask the stranger before the final waltz ends."))
        scroll_layout.addWidget(self.goal_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.goal_scene_edit = LineEdit()
        self.goal_scene_edit.setMaxLength(120)
        self.goal_scene_edit.setPlaceholderText(self.tr("""Define a goal that is the next logical story beat, tells the player what to try, and make the goal achievable with a clear, detectable moment of success.Keep it specific and concrete.

A good goal = verb that implies effort + challenges or constraints
E.g. Unmask the stranger before the final waltz ends.
"""))
        scroll_layout.addWidget(self.goal_scene_edit)

        self.audience_scene_label = QLabel(self.tr("Introduce this Scene to your audience"))
        self.audience_scene_label.setFont(font)
        self.audience_scene_label.setToolTip(self.tr("This is the starting screen of your Scene. Your audience will see this intro before entering the Scene. Help them understand what’s happening and get excited to start playing the Scene. Use {{user}} for the user. Use {{char}} for the Character."))
        scroll_layout.addWidget(self.audience_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.audience_scene_edit = LineEdit()
        self.audience_scene_edit.setMaxLength(650)
        self.audience_scene_edit.setPlaceholderText(self.tr("This is the starting screen of your Scene. Your audience will see this intro before entering the Scene. Help them understand what’s happening and get excited to start playing the Scene. Use {{user}} for the user. Use {{char}} for the Character."))
        scroll_layout.addWidget(self.audience_scene_edit)

        greeting_layout = QHBoxLayout()
        scroll_layout.addLayout(greeting_layout)
        self.greeting_label = QLabel(self.tr("Character greeting"))
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
        self.greeting_edit.setPlaceholderText(self.tr("This is the first Character message your audience will see after entering the Scene. Make it your hook with what they will see, hear, and feel."))
        self.greeting_edit.textChanged.connect(lambda: self.textChanged(self.greeting_edit, 1200))
        self.greeting_edit.setFixedHeight(48)
        self.greeting_edit.horizontalScrollBar().setVisible(False)
        self.greeting_edit.verticalScrollBar().setVisible(False)
        scroll_layout.addWidget(self.greeting_edit)

        self.name_scene_label = QLabel(self.tr("Name"))
        self.name_scene_label.setFont(font)
        scroll_layout.addWidget(self.name_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.name_scene_edit = LineEdit()
        self.name_scene_edit.setMaxLength(40)
        self.name_scene_edit.setPlaceholderText(self.tr('Give your Scene a memorable name. e.g. "Her Last Secret"'))
        scroll_layout.addWidget(self.name_scene_edit)

        self.image_scene_label = QLabel(self.tr("Cover Image"))
        self.image_scene_label.setFont(font)
        scroll_layout.addWidget(self.image_scene_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.cover_widget = QWidget()
        self.cover_widget.setObjectName("chatScrollArea")
        self.cover_widget.setFixedSize(750, 296)
        cover_layout = QVBoxLayout()
        self.cover_widget.setLayout(cover_layout)

        upload_button = PushButton(self.tr("Upload"))
        upload_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        upload_button.clicked.connect(self.selectImage)
        cover_layout.addWidget(upload_button, alignment=Qt.AlignmentFlag.AlignCenter)

        scroll_layout.addWidget(self.cover_widget, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.visibility_label = QLabel(self.tr("Visibility"))
        self.visibility_label.setFont(font)
        scroll_layout.addWidget(self.visibility_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.visible_combobox = ComboBox()
        self.visible_combobox.addItems([self.tr("Public"), self.tr("Unlisted"), self.tr("Private")])
        scroll_layout.addWidget(self.visible_combobox, alignment=Qt.AlignmentFlag.AlignLeft)

        final_buttons_layout = QHBoxLayout()
        final_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.create_button = PushButton(self.tr("Create Scene"))
        self.create_button.clicked.connect(self.createScene)
        final_buttons_layout.addWidget(self.create_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.save_button = PushButton(self.tr("Save Changes"))
        self.save_button.clicked.connect(self.saveScene)
        final_buttons_layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.save_chat_button = PushButton(self.tr("Save and Chat"))
        self.save_chat_button.clicked.connect(self.saveSceneChat)
        final_buttons_layout.addWidget(self.save_chat_button, alignment=Qt.AlignmentFlag.AlignRight)
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
        if len(self.scene_genre_edit.text()) <= 1 or len(self.when_scene_edit.text()) <= 1 or len(
                self.where_scene_edit.text()) <= 1 or len(self.tone_scene_edit.text()) <= 1 or len(
                self.what_scene_edit.text()) <= 1 or len(self.goal_scene_edit.text()) <= 1 or len(
                self.audience_scene_edit.text()) <= 1 or len(self.greeting_edit.toPlainText()) <= 1 or len(
                self.name_scene_edit.text()) <= 1 or not self.image_selected or not self.current_character_id:
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.saveData()

        self.mw.chat_thread.update_scene_signal.connect(self._saveSceneChat)
        self.mw.chat_thread.update_scene(self.data, self.scene_id)

    def selectCharacter(self, mouseclick=None):
        def getYourChars(data):
            self.mw.chat_thread.get_user_signal.disconnect(getYourChars)
            for chat in data.get('characters', []):
                cdata = {
                    'avatar_file_name': chat.get('avatar_file_name'),
                    'name': chat.get('participant__name'),
                    'external_id': chat.get('external_id')
                }
                card = ListCard(self.mw, cdata)
                card.chat_button.setVisible(False)
                card.mousePressEvent = lambda event, c=card: select(event, c)
                your_layout.addWidget(card)

        def select(event, widget):
            self.mw.hideOverlay()
            self.current_character_id = widget.character_id
            widget.mousePressEvent = self.selectCharacter
            self.char_scene_widget.addWidget(widget)
            self.char_scene_widget.setCurrentWidget(widget)

        widget = QWidget()
        widget.setFixedSize(500, 750)
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)

        buttons_frame = QFrame(widget)
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        buttons_frame.setLayout(buttons_layout)

        your_button = TabButton(self.tr("Your Characters"))
        your_button.clicked.connect(lambda: pages_widget.setCurrentWidget(your_page))
        your_button.clicked.connect(lambda: recent_button.setChecked(False))
        buttons_layout.addWidget(your_button)

        recent_button = TabButton(self.tr("Recent"))
        recent_button.clicked.connect(lambda: pages_widget.setCurrentWidget(recent_page))
        recent_button.clicked.connect(lambda: your_button.setChecked(False))
        buttons_layout.addWidget(recent_button)

        your_page, your_layout = self.scroll_page()
        recent_page, recent_layout = self.scroll_page()

        pages_widget = QStackedWidget()
        pages_widget.addWidget(your_page)
        pages_widget.addWidget(recent_page)

        pages_widget.setCurrentWidget(your_page)
        your_button.setChecked(True)

        layout.addWidget(buttons_frame)
        layout.addWidget(pages_widget, 1)
        self.mw.showOverlay(widget)

        self.mw.chat_thread.get_user(self.mw.username)
        self.mw.chat_thread.get_user_signal.connect(getYourChars)
        for chat in self.mw.recent_chats:
            cdata = {
                'avatar_file_name': chat.get('character_avatar_uri'),
                'name': chat.get('character_name'),
                'external_id': chat.get('character_id')
            }
            card = ListCard(self.mw, cdata)
            card.chat_button.setVisible(False)
            card.mousePressEvent = lambda event, c=card: select(event, c)
            recent_layout.addWidget(card)

    def getYourChars(self, data):
        self.mw.chat_thread.get_user_signal.disconnect(self.getYourChars)
        cdata = {
            'avatar_file_name': data.get('characters', [])[0].get('avatar_file_name'),
            'name': data.get('characters', [])[0].get('participant__name'),
            'external_id': data.get('characters', [])[0].get('external_id')
        }
        card = ListCard(self.mw, cdata)
        card.chat_button.setVisible(False)
        card.mousePressEvent = self.selectCharacter

        self.char_scene_widget.addWidget(card)
        self.char_scene_widget.setCurrentWidget(card)

    def scroll_page(self):
        f_page = QWidget()
        f_page_layout = QVBoxLayout(f_page)
        f_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        f_page.setLayout(f_page_layout)

        scroll_page = VerticalScrollPage()
        scroll_page.viewport.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        f_page_layout.addWidget(scroll_page)
        return f_page, scroll_layout

    def _saveSceneChat(self, data):
        if data.get('scene_id'):
            self.mw.showNotification(self.tr("The scene has been saved successfully!"))
            self.mw.openScene(scene_id=self.scene_id)
        else:
            self.mw.showNotification(str(data))

    def saveScene(self):
        if len(self.scene_genre_edit.text()) <= 1 or len(self.when_scene_edit.text()) <= 1 or len(
                self.where_scene_edit.text()) <= 1 or len(self.tone_scene_edit.text()) <= 1 or len(
                self.what_scene_edit.text()) <= 1 or len(self.goal_scene_edit.text()) <= 1 or len(
                self.audience_scene_edit.text()) <= 1 or len(self.greeting_edit.toPlainText()) <= 1 or len(
                self.name_scene_edit.text()) <= 1 or not self.image_selected or not self.current_character_id:
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.saveData()

        self.mw.chat_thread.update_scene_signal.connect(self._saveScene)
        self.mw.chat_thread.update_scene(self.data, self.scene_id)

    def _saveScene(self, data):
        if data.get('scene_id'):
            self.mw.showNotification(self.tr("The scene has been saved successfully!"))
        else:
            self.mw.showNotification(str(data))

    def createScene(self):
        self.saveData()

        self.mw.chat_thread.create_scene_signal.connect(self._createScene)
        self.mw.chat_thread.create_scene(self.data)

    def _createScene(self, data):
        if data.get('scene_id'):
            self.mw.showNotification(self.tr("The scene has been successfully created!"))
            self.mw.openScene(data, data.get('scene_id'))
        else:
            self.mw.showNotification(str(data))

    def saveData(self):
        if len(self.scene_genre_edit.text()) <= 1 or len(self.when_scene_edit.text()) <= 1 or len(
                self.where_scene_edit.text()) <= 1 or len(self.tone_scene_edit.text()) <= 1 or len(
                self.what_scene_edit.text()) <= 1 or len(self.goal_scene_edit.text()) <= 1 or len(
                self.audience_scene_edit.text()) <= 1 or len(self.greeting_edit.toPlainText()) <= 1 or len(
                self.name_scene_edit.text()) <= 1 or not self.image_selected or not self.current_character_id:
            self.mw.showNotification(self.tr("You haven't filled out everything."))
            return
        self.data['definition']['genre'] = self.scene_genre_edit.text()
        self.data['definition']['timeframe'] = self.when_scene_edit.text()
        self.data['definition']['location'] = self.where_scene_edit.text()
        self.data['definition']['tone'] = self.tone_scene_edit.text()
        self.data['definition']['backstory'] = self.what_scene_edit.text()
        self.data['definition']['goal'] = self.goal_scene_edit.text()
        self.data['description'] = self.audience_scene_edit.text()
        self.data['greeting_override'] = self.greeting_edit.toPlainText()
        self.data['title'] = self.name_scene_edit.text()
        self.data['character_id'] = self.current_character_id

        if self.visible_combobox.currentText() == self.tr('Public'):
            self.data['visibility'] = "VISIBILITY_PUBLIC"
        elif self.visible_combobox.currentText() == self.tr('Unlisted'):
            self.data['visibility'] = "VISIBILITY_UNLISTED"
        elif self.visible_combobox.currentText() == self.tr('Private'):
            self.data['visibility'] = "VISIBILITY_PRIVATE"

    def loadData(self, data):
        self.data = data
        if len(self.data) != 0:
            if self.data.get('background_image_url'):
                link = self.data.get('background_image_url')
                self.mw.image_loader.load(
                    link, 854, 480, 0,
                    callback=lambda _: self._onBackgroundDownloaded(
                        os.path.join("cache/background", hashlib.md5(link.encode()).hexdigest() + ".png")),
                    error_cb=lambda _: self.mw.showNotification(self.tr("Error downloading image")),
                    cache_dir="cache/background")
                self.image_selected = True
            self.scene_genre_edit.setText(self.data.get('definition', {}).get('genre'))
            self.when_scene_edit.setText(self.data.get('definition', {}).get('timeframe'))
            self.where_scene_edit.setText(self.data.get('definition', {}).get('location'))
            self.tone_scene_edit.setText(self.data.get('definition', {}).get('tone'))
            self.what_scene_edit.setText(self.data.get('definition', {}).get('backstory'))
            self.goal_scene_edit.setText(self.data.get('definition', {}).get('goal'))
            self.audience_scene_edit.setText(self.data.get('description'))
            self.greeting_edit.setText(self.data.get('greeting_override'))
            self.name_scene_edit.setText(self.data.get('title'))
            if self.data['visibility'] == "VISIBILITY_PUBLIC":
                self.visible_combobox.setCurrentText(self.tr('Public'))
            elif self.data['visibility'] == "VISIBILITY_UNLISTED":
                self.visible_combobox.setCurrentText(self.tr('Unlisted'))
            elif self.data['visibility'] == "VISIBILITY_PRIVATE":
                self.visible_combobox.setCurrentText(self.tr('Private'))

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
        line_count = text.count('\n')
        line_count += text.count('<br>') + 1 if text else 1
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
                link = response['value']
                self.mw.image_loader.load(
                    link, 1280, 720, 0,
                    callback=lambda _: self._onBackgroundDownloaded(
                        os.path.join("cache/background", hashlib.md5(link.encode()).hexdigest() + ".png")),
                    error_cb=lambda _: self.mw.showNotification(self.tr("Error downloading image")),
                    cache_dir="cache/background")
                self.data['background_image_url'] = link
                self.image_selected = True
            else:
                self.mw.showNotification(response.get("error"))

        file_dialog = QFileDialog()
        file_dialog.setNameFilter(
            "Images (*.xbm *.tif *.jfif *.pjp *.apng *.svgz *.jpg *.heif *.ico *.tiff *.webp *.jpeg *.heic *.gif *.svg *.png *.bmp *.pjpeg *.avif)")

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

    def _onBackgroundDownloaded(self, file_path):
        self.background_image = file_path
        self.applyBackground(file_path)

    def applyBackground(self, path):
        if path and os.path.exists(path):
            path = path.replace('\\', '/')
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