from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from modules.ui.Elements import ClickableFrame, VerticalScrollPage
from modules.ui.Icons import Svg
from modules.ui.pages.ScenePages.CreatePages import AnyCharCreatePage


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

        first_line = [
            {
                "title": "",
                "description": self.tr("Create my own"),
                "style": self.tr(
                    "You write the story, your audience pick the Character"
                ),
                "data": {},
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("The Mysteriously Vanishing Fortune"),
                "style": self.tr("Mystery"),
                "data": {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "Mystery",
                        "goal": "Get {{char}} to explain how they came into possession of the gold.",
                        "location": "First-class passenger car of a train at a remote station",
                        "timeframe": "Late 1800s",
                        "tone": "Mysterious",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                },
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("The Shapeshifter’s Genome: A Sci-Fi Scene"),
                "style": self.tr("Sci-Fi"),
                "data": {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "Sci-Fi",
                        "goal": "Get {{char}} to reveal what they truly are. ",
                        "location": "School",
                        "timeframe": "2020s",
                        "tone": "Dramatic",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                },
            },
        ]
        second_line = [
            {
                "title": self.tr("Template"),
                "description": self.tr("Ride the Dragon"),
                "style": self.tr("Fantasy"),
                "data": {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "Fantasy",
                        "goal": "Make the dragon agree to let {{user}} ride on them ",
                        "location": "Forest",
                        "timeframe": "1800s",
                        "tone": "Dramatic",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                },
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("The Romantic Ball: Ask Them To Dance"),
                "style": self.tr("Romance"),
                "data": {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "Romance",
                        "goal": "Reassure {{char}} about their worries and invite them to dance. Have them accept your hand.",
                        "location": "Ballroom",
                        "timeframe": "Late 1800s",
                        "tone": "Romantic",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                },
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("They Cheated on Me"),
                "style": self.tr("Drama"),
                "data": {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "Drama",
                        "goal": "Confront {{char}} about their betrayal and decide whether to forgive or walk away for good.",
                        "location": "Apartment",
                        "timeframe": "Present Day",
                        "tone": "Dramatic",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                },
            },
        ]
        third_line = [
            {
                "title": self.tr("Template"),
                "description": self.tr("Plane Crashed: Stranded on an Island"),
                "style": self.tr("Survival/Adventure"),
                "data": {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "Survival",
                        "goal": "Explore the environment with {{char}} and create a signal strong enough to draw rescue before it’s too late.",
                        "location": "Island",
                        "timeframe": "2000s",
                        "tone": "Tense",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                },
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("The Freshman College Party"),
                "style": self.tr("Coming-of-age"),
                "data": {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "Coming-of-Age",
                        "goal": "Choose what to wear to the party and leave the dorm with {{char}}. ",
                        "location": "College Dorms",
                        "timeframe": "2010s",
                        "tone": "Dramatic",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                },
            },
            {
                "title": self.tr("Template"),
                "description": self.tr("Coffee Shop AU: Latte Hearts"),
                "style": self.tr("Slice-of-life"),
                "data": {
                    "background_image_url": "",
                    "character_id": "",
                    "color_scheme_id": "",
                    "definition": {
                        "backstory": "",
                        "genre": "Slice-of-life",
                        "goal": "Get {{char}} to agree to go on a date with you",
                        "location": "Coffee Shop",
                        "timeframe": "Present Day",
                        "tone": "Heartwarming",
                    },
                    "description": "",
                    "greeting_override": "",
                    "tags": [],
                    "title": "",
                    "visibility": "",
                },
            },
        ]

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
        title = data.get("title")
        description = data.get("description")
        style = data.get("style")
        sdata = data.get("data", {})

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
