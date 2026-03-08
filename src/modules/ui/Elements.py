import re

from PyQt6.QtCore import Qt, QTimer, QPoint, QStringListModel
from PyQt6.QtGui import QWheelEvent, QKeyEvent, QIcon, QAction
from PyQt6.QtWidgets import (QPushButton, QLineEdit, QScrollArea, QTextEdit, QFrame, QVBoxLayout,
                             QHBoxLayout, QWidget, QCheckBox, QKeySequenceEdit, QMenu, QComboBox, QCompleter)

from . import TM

class PushButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._has_icon = False

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        padding = "8px" if self._has_icon else "8px 15px"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {TM.c('element_bg')};
                color: {TM.c('text')};
                border: none;
                border-radius: 4px;
                padding: {padding};
                text-align: left;
            }}
            QPushButton:disabled {{
                background-color: {TM.c('pressed_bg')};
                color: {TM.c('disabled_text')};
            }}
            QPushButton:hover {{
                background-color: {TM.c('hover_bg')};
            }}
            QPushButton:pressed, QPushButton:checked {{
                background-color: {TM.c('pressed_bg')};
            }}
        """)

    def setIcon(self, icon):
        super().setIcon(icon)
        self._has_icon = True
        self.update_theme()

class TabButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self._has_icon = False

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        padding = "8px" if self._has_icon else "8px 15px"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {TM.c('element_bg')};
                color: {TM.c('text')};
                border: none;
                border-radius: 4px;
                padding: {padding};
                text-align: left;
            }}
            QPushButton:disabled {{
                background-color: {TM.c('pressed_bg')};
                color: {TM.c('disabled_text')};
            }}
            QPushButton:hover {{
                background-color: {TM.c('hover_bg')};
            }}
            QPushButton:pressed, QPushButton:checked {{
                background-color: {TM.c('pressed_bg')};
                border-bottom: 5px solid #555;
                padding-bottom: 3px;
            }}
        """)

    def setIcon(self, icon):
        super().setIcon(icon)
        self._has_icon = True
        self.update_theme()

class LineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {TM.c('element_bg')};
                color: {TM.c('text')};
                border-radius: 4px;
                padding: 7px;
            }}
            QPushButton:disabled {{
                background-color: {TM.c('pressed_bg')};
                color: {TM.c('disabled_text')};
            }}
        """)

    def setIcon(self, icon: QIcon):
        self.addAction(icon, QLineEdit.ActionPosition.LeadingPosition)

class CheckBox(QCheckBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QCheckBox {{
                color: {TM.c('text')};
                padding: 4px;
                border: none;
                border-radius: 4px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                background-color: {TM.c('element_bg')};
                border: 1px solid {TM.c('element_bg')};
            }}
            QCheckBox::indicator:checked {{
                background-color: #fafafa;
            }}
        """)

class KeySequenceEdit(QKeySequenceEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            background-color: {TM.c('element_bg')};
            color: {TM.c('text')};
            border: 1px solid #5a5b5e;
            border-radius: 4px;
            padding: 6px;
        """)

class Menu(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QMenu {{
                background-color: {TM.c('menu_bg')};
                border-radius: 4px;
            }}
            QMenu::item {{
                background-color: {TM.c('menu_bg')};
                color: {TM.c('text')};
                padding: 8px 15px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {TM.c('menu_item_select')};
                color: {TM.c('text')};
                padding: 8px 15px;
                border-radius: 4px;
            }}
        """)

class PushButtonMenu(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlag(
            self.windowFlags() |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QMenu {{
                background-color: {TM.c('hover_bg')};
                border-radius: 4px;
            }}
            QMenu::item {{
                background-color: {TM.c('hover_bg')};
                color: {TM.c('text')};
                padding: 8px 15px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {TM.c('element_bg')};
                color: {TM.c('text')};
            }}
        """)

class ComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {TM.c('element_bg')};
                color: {TM.c('text')};
                border: 2px solid {TM.c('hover_bg')};
                border-radius: 4px;
                padding: 5px 8px;
            }}
            QComboBox:hover {{
                border: 2px solid {TM.c('disabled_text')};
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {TM.c('menu_bg')};
                border: 1px solid {TM.c('hover_bg')};
                selection-background-color: {TM.c('menu_item_select')};
                color: {TM.c('text')};
                border-radius: 4px;
                padding: 4px;
            }}
            QComboBox::item {{
                background-color: {TM.c('menu_bg')};
                padding: 5px 10px;
                border-radius: 4px;
            }}
            QComboBox::item:selected {{
                background-color: {TM.c('menu_item_select')};
            }}
            QComboBox:disabled {{
                background-color: {TM.c('pressed_bg')};
                color: {TM.c('disabled_text')};
                border: 2px solid {TM.c('pressed_bg')};
            }}
        """)

class CardFrame(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()


    def update_theme(self):
        self.setStyleSheet(f"""
            QFrame {{
                border-radius: 4px;
                color: {TM.c('text')};
            }}
            QFrame:hover {{
                background-color: {TM.c('pressed_bg')};
            }}
        """)

class HorizontalScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {TM.c('primary_bg')};
                border: none;
                border-radius: 4px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {TM.c('primary_bg')};
                height: 8px;
                margin: 0px 0 0px 0;
                border-bottom-right-radius: 4px;
                border-bottom-left-radius: 4px; 
            }}
            QScrollBar::sub-control:horizontal {{
                background: {TM.c('scroll_sub')};
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {TM.c('scroll_handle')};
                min-width: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:horizontal {{
                width: 0px;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }}
            QScrollBar::sub-line:horizontal {{
                width: 0px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {TM.c('scroll_hover')};
            }}
        """)

    def wheelEvent(self, event: QWheelEvent):
        hbar = self.horizontalScrollBar()
        delta = event.angleDelta().y()
        hbar.setValue(hbar.value() - delta)
        event.accept()

class VerticalScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {TM.c('primary_bg')};
                border: none;
                border-radius: 4px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {TM.c('primary_bg')};
                height: 8px;
                margin: 0px 0 0px 0;
                border-bottom-right-radius: 4px;
                border-bottom-left-radius: 4px; 
            }}
            QScrollBar::sub-control:vertical {{
                background: {TM.c('scroll_sub')};
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {TM.c('scroll_handle')};
                min-width: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical {{
                width: 0px;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }}
            QScrollBar::sub-line:vertical {{
                width: 0px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {TM.c('scroll_hover')};
            }}
        """)

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
        self.format_timer = QTimer()
        self.format_timer.setSingleShot(True)
        self.format_timer.timeout.connect(self.formatUserMessage)
        self.textChanged.connect(self.startFormat)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {TM.c('element_bg')};
                color: {TM.c('text')};
                border-radius: 4px;
                padding: 7px;
            }}
            QTextEdit:disabled {{
                background-color: {TM.c('pressed_bg')};
                color: {TM.c('disabled_text')};
            }}
        """)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.keyPress()
        elif event.key() == Qt.Key.Key_B and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.formatSelectedText("**", "**")
            return
        elif event.key() == Qt.Key.Key_I and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.formatSelectedText("*", "*")
            return
        elif event.key() == Qt.Key.Key_E and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.formatSelectedText("`", "`")
            return
        else:
            super().keyPressEvent(event)

    def keyPress(self, *args, **kwargs):
        pass

    def formatSelectedText(self, start_marker, end_marker, block=False):
        cursor = self.textCursor()

        if not cursor.hasSelection():
            if block:
                cursor.insertText(start_marker + end_marker)
                cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.MoveAnchor, len(end_marker))
            else:
                cursor.insertText(start_marker + end_marker)
                cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.MoveAnchor, len(end_marker))
            self.setTextCursor(cursor)
            return

        selected_text = cursor.selectedText()
        selected_text = selected_text.replace('\u2029', '\n')

        if selected_text.startswith(start_marker.strip()) and selected_text.endswith(end_marker.strip()):
            new_text = selected_text[len(start_marker.strip()):-len(end_marker.strip())]
        else:
            new_text = f"{start_marker}{selected_text}{end_marker}"

        cursor.insertText(new_text)

        cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, len(new_text))
        self.setTextCursor(cursor)
        self.format_timer.start(500)

    def startFormat(self):
        text = self.toPlainText()
        line_count = text.count('\n')
        line_count += text.count('<br>') + 1 if text else 1
        height = line_count * self.fontMetrics().lineSpacing() + 16
        self.setFixedHeight(height)
        self.format_timer.start(500)

    def formatUserMessage(self):
        self.blockSignals(True)
        text = self.toPlainText()
        cursor = self.textCursor()
        position = cursor.position()

        replacements = [
            (r"^(#{1,6})\s*(.+)$", lambda
                m: f'<span style="color: gray;">{m.group(1)}</span> <h{len(m.group(1))} style="display:inline; font-size: {20 - len(m.group(1)) * 2}px;">{m.group(2)}</h{len(m.group(1))}>',
             re.MULTILINE),
            (r"``````", r'<span style="color: gray;">``````</span>', re.DOTALL),
            (r"`(.*?)`", r'<span style="color: gray;">`</span><code style="padding: 2px;">\1</code><span style="color: gray;">`</span>'),
            (r"\*\*\*(.*?)\*\*\*", r'<span style="color: gray;">***</span><b><i>\1</i></b><span style="color: gray;">***</span>'),
            (r"\*\*(.*?)\*\*", r'<span style="color: gray;">**</span><b>\1</b><span style="color: gray;">**</span>'),
            (r"\*(.*?)\*", r'<span style="color: gray;">*</span><i>\1</i><span style="color: gray;">*</span>'),
            ("\n", "<br>"),
        ]

        for pattern, replacement, *flags in replacements:
            text = re.sub(pattern, replacement, text, flags=flags[0] if flags else 0)

        #line_count = text.count('<br>') + 1 if text else 1
        #height = line_count * self.fontMetrics().lineSpacing() + 16

        if text != self.toHtml():
            self.setHtml(text)
            cursor.setPosition(min(position, len(self.toPlainText())))
            self.setTextCursor(cursor)

        self.blockSignals(False)


    def applyHeading(self, combo):
        heading_marker = combo.currentData()

        if not heading_marker:
            combo.setCurrentIndex(0)
            return

        cursor = self.textCursor()

        cursor.movePosition(cursor.MoveOperation.StartOfLine)
        cursor.movePosition(cursor.MoveOperation.EndOfLine, cursor.MoveMode.KeepAnchor)

        line_text = cursor.selectedText()

        line_text = re.sub(r'^#{1,6}\s*', '', line_text)

        new_text = f"{heading_marker} {line_text}"

        cursor.insertText(new_text)

        combo.blockSignals(True)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)

        self.format_timer.start(500)


class SearchLineEdit(QLineEdit):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_thread = main_window.chat_thread
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.showAutoCompleteMenu)
        self.textChanged.connect(self.startAutoComplete)

        self.setPlaceholderText(self.tr("Character Search"))

        self.completer_model = QStringListModel()
        self.custom_completer = QCompleter()
        self.custom_completer.setModel(self.completer_model)
        self.custom_completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.custom_completer.activated.connect(self.simulateEnter)
        self.setCompleter(self.custom_completer)

        self.popup = self.custom_completer.popup()
        self.popup.setWindowFlag(
            self.windowFlags() |
            Qt.WindowType.NoDropShadowWindowHint
        )

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.popup.setStyleSheet(f"""
            QListView {{
                background-color: {TM.c('element_bg')};
                border-radius: 4px;
            }}
            QListView::item {{
                color: {TM.c('text')};
                background-color: {TM.c('element_bg')};
                padding: 4px 15px;
                border-radius: 4px;
            }}
            QListView::item:selected {{
                background-color: {TM.c('hover_bg')};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {TM.c('element_bg')};
                width: 8px;
                margin: 0px 0 0px 0;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px; 
            }}
            QScrollBar::sub-control:vertical {{
                background: {TM.c('scroll_sub')};
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {TM.c('scroll_handle')};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical {{
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }}
            QScrollBar::sub-line:vertical {{
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {TM.c('scroll_hover')};
            }}
        """)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {TM.c('element_bg')};
                color: {TM.c('text')};
                border-radius: 4px;
                padding: 7px;
            }}
            QPushButton:disabled {{
                background-color: {TM.c('pressed_bg')};
                color: {TM.c('disabled_text')};
            }}
        """)

    def setIcon(self, icon: QIcon):
        self.addAction(icon, QLineEdit.ActionPosition.LeadingPosition)

    def startAutoComplete(self):
        self.timer.start(500)

    def showAutoCompleteMenu(self):
        self.blockSignals(True)
        self.chat_thread.query_autocomplete_signal.connect(self._showAutoCompleteMenu)
        self.chat_thread.query_autocomplete(self.text())
        self.blockSignals(False)

    def _showAutoCompleteMenu(self, data):
        self.chat_thread.query_autocomplete_signal.disconnect()

        if not data:
            self.completer_model.setStringList([])
            return
        self.completer_model.setStringList(data)
        self.custom_completer.complete()

    def simulateEnter(self, text):
        self.returnPressed.emit()


class ClickableFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkable = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.default_style = f"""
            QFrame {{
                border-radius: 4px;
            }}
            QFrame:hover {{
                background-color: {TM.c('pressed_bg')};
            }}
        """
        self.press_style = f"""
            QFrame {{
                border-radius: 4px;
                background-color: {TM.c('pressed_bg')};
            }}
        """

        if self.checkable:
            self.setStyleSheet(self.press_style)
        else:
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
            self.create_button.setVisible(False)
            self.profile_button_2.setVisible(True)
            self.to_main_page_button_2.setVisible(True)
            self.create_button_2.setVisible(True)
        else:
            self.profile_button.setVisible(True)
            self.to_main_page_button.setVisible(True)
            self.create_button.setVisible(True)
            self.profile_button_2.setVisible(False)
            self.to_main_page_button_2.setVisible(False)
            self.create_button_2.setVisible(False)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
        #leftSidebar {{
            background-color: {TM.c('primary_bg')};
            border-radius: 4px;
            border: none;
        }}""")

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

        self.create_button = PushButton(self.tr('Create'))
        self.create_button.clicked.connect(lambda: self.showCreateContextMenu(self.create_button))
        self.left_sidebar_layout.addWidget(self.create_button)

        self.create_button_2 = PushButton()
        self.create_button_2.setIcon(self.mw.svg_icons.create('white'))
        self.create_button_2.clicked.connect(lambda: self.showCreateContextMenu(self.create_button_2))
        self.left_sidebar_layout.addWidget(self.create_button_2)
        self.create_button_2.setVisible(False)

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
        self.profile_button.clicked.connect(lambda: self.showProfileContextMenu(self.profile_button))
        self.bottom_button_layout.addWidget(self.profile_button, 1)

        self.profile_button_2 = PushButton()
        if self.mw.me_has_avatar:
            self.mw.image_loader.load(f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0",
                                   45, 45, 100, callback=lambda pixmap:self.profile_button_2.setIcon(QIcon(pixmap)),
                                   error_cb=lambda _: self.profile_button_2.setIcon(self.mw.svg_icons.profile('white')))
        else:
            self.profile_button_2.setIcon(self.mw.svg_icons.profile('white'))
        self.profile_button_2.clicked.connect(lambda: self.showProfileContextMenu(self.profile_button_2))
        self.bottom_button_layout.addWidget(self.profile_button_2, 1)
        self.profile_button_2.setVisible(False)

    def showCreateContextMenu(self, button: PushButton):
        from . import TM
        TM.set_theme("light")
        context_menu = PushButtonMenu(self)
        context_menu.setFixedWidth(int(self.mw.settings.value("left_sidebar_width", 250)) - 20)

        character_action = QAction(self.tr("Character"))
        character_action.triggered.connect(self.mw.openCreateCharacterPage)
        context_menu.addAction(character_action)

        scene_action = QAction(self.tr("Scene"))
        scene_action.triggered.connect(self.mw.openCreateScenePage)
        context_menu.addAction(scene_action)

        #voice_action = QAction(self.tr("Voice"))
        #settings_action.triggered.connect(self.mw.openSettings)
        #voice_action.setEnabled(False)
        #context_menu.addAction(voice_action)

        context_menu.exec(button.mapToGlobal(QPoint(0, context_menu.height())))

    def showProfileContextMenu(self, button: PushButton):
        context_menu = PushButtonMenu(self)
        context_menu.setFixedWidth(int(self.mw.settings.value("left_sidebar_width", 250)) - 20)

        profile_action = QAction(self.tr("Profile"))
        profile_action.triggered.connect(self.openUserPage)
        context_menu.addAction(profile_action)

        settings_action = QAction(self.tr("Settings"))
        settings_action.triggered.connect(self.mw.openSettings)
        context_menu.addAction(settings_action)

        context_menu.exec(button.mapToGlobal(QPoint(0, -2*context_menu.height())))

    def avatarUpdate(self):
        if self.mw.me_has_avatar:
            self.mw.image_loader.load(f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0",
                                      45, 45, 100,
                                      callback=lambda pixmap:self.profile_button_2.setIcon(QIcon(pixmap)),
                                      error_cb=lambda _: self.profile_button_2.setIcon(self.mw.svg_icons.profile('white')))
        else:
            self.profile_button_2.setIcon(self.mw.svg_icons.profile('white'))

    def openUserPage(self):
        self.mw.openUserPage(self.mw.username)

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
                self.create_button.setVisible(False)
                self.profile_button_2.setVisible(True)
                self.to_main_page_button_2.setVisible(True)
                self.create_button_2.setVisible(True)
            else:
                self.profile_button.setVisible(True)
                self.to_main_page_button.setVisible(True)
                self.create_button.setVisible(True)
                self.profile_button_2.setVisible(False)
                self.to_main_page_button_2.setVisible(False)
                self.create_button_2.setVisible(False)

        else:
            if frame_rect.right() - edge_size < event.pos().x() < frame_rect.right():
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.resizing = False
