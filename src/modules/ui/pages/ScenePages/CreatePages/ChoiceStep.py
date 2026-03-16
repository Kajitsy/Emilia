import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QWidget

from modules.ui.Elements import PushButton, VerticalScrollPage, ClickableFrame
from modules.ui.Icons import Svg
from modules.ui.pages.ScenePages.CreatePages import AnyCharFirstPage, MainCharFirstPage

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