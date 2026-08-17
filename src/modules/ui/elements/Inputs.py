import re

from PyQt6.QtCore import QStringListModel, Qt, QTimer
from PyQt6.QtGui import QIcon, QKeyEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QKeySequenceEdit,
    QLineEdit,
    QTextEdit,
)

from modules.ui.ThemeManager import TM


class LineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("LineEdit"))

    def setIcon(self, icon: QIcon):
        self.addAction(icon, QLineEdit.ActionPosition.LeadingPosition)


class CheckBox(QCheckBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("CheckBox"))


class KeySequenceEdit(QKeySequenceEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("KeySequenceEdit"))


class ComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("ComboBox"))


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
        if (
            event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}
            and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.keyPress()
        elif (
            event.key() == Qt.Key.Key_B
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.formatSelectedText("**", "**")
            return
        elif (
            event.key() == Qt.Key.Key_I
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.formatSelectedText("*", "*")
            return
        elif (
            event.key() == Qt.Key.Key_E
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
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
                cursor.movePosition(
                    cursor.MoveOperation.Left,
                    cursor.MoveMode.MoveAnchor,
                    len(end_marker),
                )
            else:
                cursor.insertText(start_marker + end_marker)
                cursor.movePosition(
                    cursor.MoveOperation.Left,
                    cursor.MoveMode.MoveAnchor,
                    len(end_marker),
                )
            self.setTextCursor(cursor)
            return

        selected_text = cursor.selectedText()
        selected_text = selected_text.replace("\u2029", "\n")

        if selected_text.startswith(start_marker.strip()) and selected_text.endswith(
            end_marker.strip()
        ):
            new_text = selected_text[
                len(start_marker.strip()) : -len(end_marker.strip())
            ]
        else:
            new_text = f"{start_marker}{selected_text}{end_marker}"

        cursor.insertText(new_text)

        cursor.movePosition(
            cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, len(new_text)
        )
        self.setTextCursor(cursor)
        self.format_timer.start(500)

    def startFormat(self):
        text = self.toPlainText()
        line_count = text.count("\n")
        line_count += text.count("<br>") + 1 if text else 1
        height = line_count * self.fontMetrics().lineSpacing() + 16
        self.setFixedHeight(height)
        self.format_timer.start(500)

    def formatUserMessage(self):
        self.blockSignals(True)
        text = self.toPlainText()
        cursor = self.textCursor()
        position = cursor.position()

        replacements = [
            (
                r"^(#{1,6})\s*(.+)$",
                lambda m: f'<span style="color: gray;">{m.group(1)}</span> <h{len(m.group(1))} style="display:inline; font-size: {20 - len(m.group(1)) * 2}px;">{m.group(2)}</h{len(m.group(1))}>',
                re.MULTILINE,
            ),
            (r"``````", r'<span style="color: gray;">``````</span>', re.DOTALL),
            (
                r"`(.*?)`",
                r'<span style="color: gray;">`</span><code style="padding: 2px;">\1</code><span style="color: gray;">`</span>',
            ),
            (
                r"\*\*\*(.*?)\*\*\*",
                r'<span style="color: gray;">***</span><b><i>\1</i></b><span style="color: gray;">***</span>',
            ),
            (
                r"\*\*(.*?)\*\*",
                r'<span style="color: gray;">**</span><b>\1</b><span style="color: gray;">**</span>',
            ),
            (
                r"\*(.*?)\*",
                r'<span style="color: gray;">*</span><i>\1</i><span style="color: gray;">*</span>',
            ),
            ("\n", "<br>"),
        ]

        for pattern, replacement, *flags in replacements:
            text = re.sub(pattern, replacement, text, flags=flags[0] if flags else 0)

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

        line_text = re.sub(r"^#{1,6}\s*", "", line_text)

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
        self.custom_completer.setCompletionMode(
            QCompleter.CompletionMode.UnfilteredPopupCompletion
        )
        self.custom_completer.activated.connect(self.simulateEnter)
        self.setCompleter(self.custom_completer)

        self.popup = self.custom_completer.popup()
        self.popup.setWindowFlag(
            self.windowFlags() | Qt.WindowType.NoDropShadowWindowHint
        )

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.popup.setStyleSheet(TM.get_style("SearchPopup"))
        self.setStyleSheet(TM.get_style("SearchLineEdit"))

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
