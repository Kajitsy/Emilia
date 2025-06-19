from PyQt6.QtWidgets import (
    QScrollArea, QPushButton,
    QFrame, QTextEdit, QVBoxLayout,
    QHBoxLayout, QWidget, QSizePolicy)
from PyQt6.QtGui import QWheelEvent, QKeyEvent
from PyQt6.QtCore import Qt
from modules.styles import (
    SvgIcons, check_button_style,
    left_sidebar_style, button_style,
    icon_button_style, scroll_style)

class CustomTextEdit(QTextEdit):
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.keyPress()
        else:
            super().keyPressEvent(event)

    def keyPress(self, *args, **kwargs):
        pass

class HorizontalScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def wheelEvent(self, event: QWheelEvent):
        hbar = self.horizontalScrollBar()
        delta = event.angleDelta().y()
        hbar.setValue(hbar.value() - delta)
        event.accept()

class CheckablePushButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setStyleSheet(check_button_style())
        self.svg = SvgIcons()

    def checkStateSet(self):
        if self.isChecked():
            self.setIcon(self.svg.check("#494a4d"))
        else:
            self.setIcon(self.svg.check("#4d4d4f"))

class ClickableFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_style = ""
        self.press_style = ""
        self.checkable = False

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
        self.setStyleSheet(left_sidebar_style())
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
            self.create_button.setVisible(False)
            self.profile_button_2.setVisible(True)
            self.create_button_2.setVisible(True)
        else:
            self.profile_button.setVisible(True)
            self.create_button.setVisible(True)
            self.profile_button_2.setVisible(False)
            self.create_button_2.setVisible(False)

    def initUI(self):
        self.left_sidebar_layout = QVBoxLayout()
        self.left_sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.left_sidebar_layout)

        self.buttons_layout = QHBoxLayout()
        self.left_sidebar_layout.addLayout(self.buttons_layout)

        self.create_button = QPushButton(self.tr("To Main Page"))
        self.create_button.clicked.connect(self.mw.showMainPage)
        self.create_button.setStyleSheet(button_style())
        self.buttons_layout.addWidget(self.create_button, 1)

        self.create_button_2 = QPushButton()
        self.create_button_2.setIcon(self.mw.svg_icons.discover('white'))
        self.create_button_2.clicked.connect(self.mw.showMainPage)
        self.create_button_2.setStyleSheet(icon_button_style())
        self.buttons_layout.addWidget(self.create_button_2, 1)
        self.create_button_2.setVisible(False)

        self.sidebar_collapse_button = QPushButton()
        self.sidebar_collapse_button.setIcon(self.mw.svg_icons.hide_left_sidebar('white'))
        self.sidebar_collapse_button.setStyleSheet(icon_button_style())
        self.sidebar_collapse_button.clicked.connect(self.mw.toggleLeftSidebar)
        self.sidebar_collapse_button.setVisible(self.mw.left_sidebar_visible)
        self.buttons_layout.addWidget(self.sidebar_collapse_button, 0)

        self.recent_chat_scroll_area = QScrollArea()
        self.recent_chat_scroll_area.setFixedWidth(int(self.mw.settings.value("left_sidebar_width", 250)) - 20)
        self.recent_chat_scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.recent_chat_scroll_area.verticalScrollBar().setStyleSheet(scroll_style())
        self.recent_chat_scroll_area.setWidgetResizable(True)

        self.recent_chat_container = QWidget()
        self.recent_chat_layout = QVBoxLayout()
        self.recent_chat_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_chat_layout.setSpacing(5)
        self.recent_chat_container.setLayout(self.recent_chat_layout)

        self.recent_chat_scroll_area.setWidget(self.recent_chat_container)
        self.left_sidebar_layout.addWidget(self.recent_chat_scroll_area)

        self.bottom_button_layout = QHBoxLayout()
        self.left_sidebar_layout.addLayout(self.bottom_button_layout)

        self.profile_button = QPushButton(self.tr("Profile"))
        self.profile_button.setStyleSheet(button_style())
        self.profile_button.clicked.connect(self.openUserPage)
        self.profile_button.setCheckable(True)
        self.bottom_button_layout.addWidget(self.profile_button, 1)

        self.profile_button_2 = QPushButton()
        self.profile_button_2.setIcon(self.mw.svg_icons.profile('white'))
        self.profile_button_2.setStyleSheet(icon_button_style())
        self.profile_button_2.clicked.connect(self.openUserPage)
        self.profile_button_2.setCheckable(True)
        self.bottom_button_layout.addWidget(self.profile_button_2, 1)
        self.profile_button_2.setVisible(False)

        self.settings_button = QPushButton()
        self.settings_button.setIcon(self.mw.svg_icons.settings('white'))
        self.settings_button.setStyleSheet(icon_button_style())
        self.settings_button.clicked.connect(self.mw.openSettings)
        self.settings_button.setCheckable(True)
        self.bottom_button_layout.addWidget(self.settings_button)

    def openUserPage(self):
        self.mw.openUserPage(self.mw.username)
        self.profile_button.setChecked(True)
        self.profile_button_2.setChecked(True)

    def resizeCards(self):
        for i in range(self.recent_chat_layout.count()):
            card = self.recent_chat_layout.itemAt(i)
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
            self.recent_chat_scroll_area.setFixedWidth(new_width - 20)
            self.mw.settings.setValue("left_sidebar_width", new_width)
            self.resizeCards()
            if self.width() <= 100:
                self.profile_button.setVisible(False)
                self.create_button.setVisible(False)
                self.profile_button_2.setVisible(True)
                self.create_button_2.setVisible(True)
            else:
                self.profile_button.setVisible(True)
                self.create_button.setVisible(True)
                self.profile_button_2.setVisible(False)
                self.create_button_2.setVisible(False)

        else:
            if frame_rect.right() - edge_size < event.pos().x() < frame_rect.right():
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.resizing = False