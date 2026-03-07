from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QWidget

from modules.style.Elements import VerticalScrollPage, ClickableFrame
from modules.style.Icons import Svg
from modules.pages.ScenePages.CreatePages import MainCharCreatePage

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