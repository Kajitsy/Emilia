from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent, QKeyEvent, QIcon
from PyQt6.QtWidgets import (QPushButton, QLineEdit, QScrollArea, QTextEdit, QFrame, QVBoxLayout,
    QHBoxLayout, QWidget,QCheckBox, QKeySequenceEdit, QMenu, QComboBox)

from modules.QThreads import ImageLoaderThread


class PushButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QPushButton {
                background-color: #494a4d;
                color: #e8eaed;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                text-align: left;
            }
            QPushButton:disabled {
                background-color: #3c3d3f;
                color: #a2a2ac;
            }
            QPushButton:hover {
                background-color: #5f6368;
            }
            QPushButton:pressed, QPushButton:checked {
                background-color: #3c3d3f;
            }
        """)

    def setIcon(self, icon):
        super().setIcon(icon)
        self.setStyleSheet("""
            QPushButton {
                background-color: #494a4d;
                color: #e8eaed;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:disabled {
                background-color: #3c3d3f;
                color: #a2a2ac;
            }
            QPushButton:hover {
                background-color: #5f6368;
            }
            QPushButton:pressed, QPushButton:checked {
                background-color: #3c3d3f;
            }
        """)

class TabButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QPushButton {
                background-color: #494a4d;
                color: #e8eaed;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                text-align: left;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #a2a2ac;
            }
            QPushButton:hover {
                background-color: #5f6368;
            }
            QPushButton:pressed, QPushButton:checked {
                background-color: #494a4d;
                border-bottom: 5px solid #555;
                padding-bottom: 3px;
            }
        """)

    def setIcon(self, icon):
        super().setIcon(icon)
        self.setStyleSheet("""
            QPushButton {
                background-color: #494a4d;
                color: #e8eaed;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #a2a2ac;
            }
            QPushButton:hover {
                background-color: #5f6368;
            }
            QPushButton:pressed, QPushButton:checked {
                background-color: #494a4d;
                border-bottom: 5px solid #555;
                padding-bottom: 3px;
            }
        """)

class LineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #494a4d; 
                color: #e8eaed; 
                border-radius: 4px; 
                padding: 7px;
            }
            QLineEdit:disabled {
                background-color: #3c3d3f;
                color: #a2a2ac;
            }
        """)

    def setIcon(self, icon: QIcon):
        self.addAction(icon, QLineEdit.ActionPosition.LeadingPosition)

class CheckBox(QCheckBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QCheckBox {
                color: #e8eaed;
                padding: 4px;
                border: none;
                border-radius: 4px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #494a4d;
                background-color: #494a4d;
            }
            QCheckBox::indicator:checked {
                background-color: #fafafa;
            }
        """)

class KeySequenceEdit(QKeySequenceEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            background-color: #494a4d; 
            color: #e8eaed; 
            border-radius: 4px; 
            padding: 6px;
            border: 1px solid #5a5b5e;
        """)

class Menu(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QMenu {
                background-color: #202024;
                border-radius: 4px;
            }
            QMenu::item {
                color: white;
                background-color: #202024;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                color: white;
                background-color: #25262b;
                border-radius: 4px;
            }
        """)

class ComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QComboBox {
                background-color: #494a4d;
                color: #e8eaed;
                border: 2px solid #5f6368;
                border-radius: 4px;
                padding: 5px 8px;
            }
            QComboBox:hover {
                border: 2px solid #a2a2ac;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #202024;
                border: 1px solid #5f6368;
                selection-background-color: #25262b;
                color: #e8eaed;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox::item {
                background-color: #202024;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QComboBox::item:selected {
                background-color: #25262b;
            }
            QComboBox:disabled {
                background-color: #3c3d3f;
                color: #a2a2ac;
                border: 2px solid #555;
            }
        """)

class CardFrame(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QFrame {
                border-radius: 4px;
            }
            QFrame:hover {
                background-color: #3c3d3f;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class HorizontalScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QScrollArea {
                background-color: #303134;
                border: none;
                border-radius: 4px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #303134;
                height: 8px;
                margin: 0px 0 0px 0;
                border-bottom-right-radius: 4px;
                border-bottom-left-radius: 4px; 
            }
            QScrollBar::sub-control:horizontal {
                background: #f0f0f0;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #555;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:horizontal {
                width: 0px;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:horizontal {
                width: 0px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QScrollBar::handle:horizontal:hover {
                background: #777;
            }
        """)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

    def wheelEvent(self, event: QWheelEvent):
        hbar = self.horizontalScrollBar()
        delta = event.angleDelta().y()
        hbar.setValue(hbar.value() - delta)
        event.accept()

class VerticalScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QScrollArea {
                background-color: #303134;
                border: none;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #303134;
                width: 8px;
                margin: 0px 0 0px 0;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px; 
            }
            QScrollBar::sub-control:vertical {
                background: #f0f0f0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
        """)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

    def wheelEvent(self, event: QWheelEvent):
        hbar = self.verticalScrollBar()
        delta = event.angleDelta().y()
        hbar.setValue(hbar.value() - delta)
        event.accept()

class HorizontalScrollPage(HorizontalScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport = QWidget()
        self.layout = QHBoxLayout(self.viewport)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.viewport.setLayout(self.layout)
        self.setWidget(self.viewport)

class VerticalScrollPage(VerticalScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport = QWidget()
        self.layout = QVBoxLayout(self.viewport)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.viewport.setLayout(self.layout)
        self.setWidget(self.viewport)

class CustomTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
        QTextEdit {
            background-color: #494a4d; 
            color: #e8eaed; 
            border-radius: 4px; 
            padding: 7px;
        }
        QTextEdit:disabled {
            background-color: #3c3d3f;
            color: #a2a2ac;
        }
    """)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.keyPress()
        else:
            super().keyPressEvent(event)

    def keyPress(self, *args, **kwargs):
        pass


class ClickableFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_style = """
        QFrame {
            border-radius: 4px;
        }
        QFrame:hover {
            background-color: #3c3d3f;
        }
    """
        self.press_style = """
        QFrame {
            border-radius: 4px;
            background-color: #3c3d3f;
        }
    """
        self.checkable = False
        self.setStyleSheet(self.default_style)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.checkable = not self.checkable
        if self.checkable:
            self.setStyleSheet(self.press_style)
        else:
            self.setStyleSheet(self.default_style)
        self.mousePress(event)

    def setCheckable(self, check):
        self.checkable = check
        if self.checkable:
            self.setStyleSheet(self.press_style)
        else:
            self.setStyleSheet(self.default_style)

    def mousePress(self, *args, **kwargs):
        pass


class LeftSidebar(QFrame):
    def __init__(self, mw):
        super().__init__(mw)
        self.setStyleSheet("""
            #leftSidebar {
                background-color: #303134;
                border-radius: 4px;
                border: none;
            }
        """)
        self.setMouseTracking(True)
        self.setObjectName("leftSidebar")
        self.resizing = False
        self.startPos = None
        self.mw = mw
        self.setFixedWidth(int(self.mw.settings.value("left_sidebar_width", 255)))

        self.initUI()
        self.resizeCards()
        if self.width() <= 100:
            self.profile_button.setVisible(False)
            self.to_main_page_button.setVisible(False)
            self.create_character_button.setVisible(False)
            self.profile_button_2.setVisible(True)
            self.to_main_page_button_2.setVisible(True)
            self.create_character_button_2.setVisible(True)
        else:
            self.profile_button.setVisible(True)
            self.to_main_page_button.setVisible(True)
            self.create_character_button.setVisible(True)
            self.profile_button_2.setVisible(False)
            self.to_main_page_button_2.setVisible(False)
            self.create_character_button_2.setVisible(False)

    def initUI(self):
        self.left_sidebar_layout = QVBoxLayout()
        self.left_sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.left_sidebar_layout)

        self.buttons_layout = QHBoxLayout()
        self.left_sidebar_layout.addLayout(self.buttons_layout)

        self.to_main_page_button = PushButton(self.tr("To Main Page"))
        self.to_main_page_button.clicked.connect(self.mw.showMainPage)
        self.buttons_layout.addWidget(self.to_main_page_button, 1)

        self.to_main_page_button_2 = PushButton()
        self.to_main_page_button_2.setIcon(self.mw.svg_icons.discover('white'))
        self.to_main_page_button_2.clicked.connect(self.mw.showMainPage)
        self.buttons_layout.addWidget(self.to_main_page_button_2, 1)
        self.to_main_page_button_2.setVisible(False)

        self.sidebar_collapse_button = PushButton()
        self.sidebar_collapse_button.setIcon(self.mw.svg_icons.hide_left_sidebar('white'))
        self.sidebar_collapse_button.clicked.connect(self.mw.toggleLeftSidebar)
        self.sidebar_collapse_button.setVisible(self.mw.left_sidebar_visible)
        self.buttons_layout.addWidget(self.sidebar_collapse_button, 0)

        self.create_character_button = PushButton(self.tr('Create Character'))
        self.create_character_button.setCheckable(True)
        self.create_character_button.clicked.connect(self.openCreateCharacterPage)
        self.left_sidebar_layout.addWidget(self.create_character_button)

        self.create_character_button_2 = PushButton()
        self.create_character_button_2.setIcon(self.mw.svg_icons.create_character('white'))
        self.create_character_button_2.setCheckable(True)
        self.create_character_button_2.clicked.connect(self.openCreateCharacterPage)
        self.left_sidebar_layout.addWidget(self.create_character_button_2)
        self.create_character_button_2.setVisible(False)

        self.recent_chat_scroll_page = VerticalScrollPage()
        self.recent_chat_scroll_page.setFixedWidth(int(self.mw.settings.value("left_sidebar_width", 250)) - 20)
        self.recent_chat_scroll_viewport = self.recent_chat_scroll_page.viewport
        self.recent_chat_scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
        self.recent_chat_scroll_layout = self.recent_chat_scroll_page.layout
        self.recent_chat_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_chat_scroll_layout.setSpacing(5)

        self.left_sidebar_layout.addWidget(self.recent_chat_scroll_page)

        self.bottom_button_layout = QHBoxLayout()
        self.left_sidebar_layout.addLayout(self.bottom_button_layout)

        self.profile_button = PushButton(self.tr("Profile"))
        self.profile_button.clicked.connect(self.openUserPage)
        self.profile_button.setCheckable(True)
        self.bottom_button_layout.addWidget(self.profile_button, 1)

        self.profile_button_2 = PushButton()
        if self.mw.me_has_avatar:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.mw.me_avatar + '?webp=true&anim=0',
                45, 45)
            load_avatar_thread.image_loaded.connect(lambda pixmap:self.profile_button_2.setIcon(QIcon(pixmap)))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            self.profile_button_2.setIcon(self.mw.svg_icons.profile('white'))
        self.profile_button_2.clicked.connect(self.openUserPage)
        self.profile_button_2.setCheckable(True)
        self.bottom_button_layout.addWidget(self.profile_button_2, 1)
        self.profile_button_2.setVisible(False)

        self.settings_button = PushButton()
        self.settings_button.setIcon(self.mw.svg_icons.settings('white'))
        self.settings_button.clicked.connect(self.mw.openSettings)
        self.settings_button.setCheckable(True)
        self.bottom_button_layout.addWidget(self.settings_button)

    def avatarUpdate(self):
        if self.mw.me_has_avatar:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.mw.me_avatar + '?webp=true&anim=0',
                45, 45)
            load_avatar_thread.image_loaded.connect(lambda pixmap:self.profile_button_2.setIcon(QIcon(pixmap)))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            self.profile_button_2.setIcon(self.mw.svg_icons.profile('white'))

    def openUserPage(self):
        self.mw.openUserPage(self.mw.username)
        self.profile_button.setChecked(True)
        self.profile_button_2.setChecked(True)

    def openCreateCharacterPage(self):
        self.mw.openCreateCharacterPage()
        self.create_character_button.setChecked(True)
        self.create_character_button_2.setChecked(True)

    def resizeCards(self):
        for i in range(self.recent_chat_scroll_layout.count()):
            card = self.recent_chat_scroll_layout.itemAt(i)
            card_widget = card.widget()
            self.resizeCard(card_widget)

    def resizeCard(self, card_widget):
        card_widget.setFixedWidth(self.width() - 30)
        if card_widget.width() <= 66:
            card_widget.avatar_label.setVisible(False)
            card_widget.name_label.setVisible(False)
            card_widget.menu_button.visibility = False
            card_widget.avatar_label_2.setVisible(True)
        else:
            card_widget.avatar_label.setVisible(True)
            card_widget.name_label.setVisible(True)
            card_widget.menu_button.visibility = True
            card_widget.avatar_label_2.setVisible(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.cursor().shape() == Qt.CursorShape.SizeHorCursor:
                self.resizing = True
                self.startPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        edge_size = 5
        frame_rect = self.rect()

        if self.resizing:
            diff_x = event.globalPosition().toPoint().x() - self.startPos.x()
            new_width = min(max(96, self.width() + diff_x), 255)
            self.startPos = event.globalPosition().toPoint()

            self.setFixedWidth(new_width)
            self.recent_chat_scroll_page.setFixedWidth(new_width - 20)
            self.mw.settings.setValue("left_sidebar_width", new_width)
            self.resizeCards()
            if self.width() <= 100:
                self.profile_button.setVisible(False)
                self.to_main_page_button.setVisible(False)
                self.create_character_button.setVisible(False)
                self.profile_button_2.setVisible(True)
                self.to_main_page_button_2.setVisible(True)
                self.create_character_button_2.setVisible(True)
            else:
                self.profile_button.setVisible(True)
                self.to_main_page_button.setVisible(True)
                self.create_character_button.setVisible(True)
                self.profile_button_2.setVisible(False)
                self.to_main_page_button_2.setVisible(False)
                self.create_character_button_2.setVisible(False)

        else:
            if frame_rect.right() - edge_size < event.pos().x() < frame_rect.right():
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.resizing = False
