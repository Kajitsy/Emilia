from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from modules.ui.ThemeManager import TM


class HorizontalScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("HorizontalScrollArea"))

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        self.horizontalScrollBar().setValue(
            self.horizontalScrollBar().value() - delta // 2
        )


class VerticalScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("VerticalScrollArea"))

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta // 2)


class HorizontalScrollPage(HorizontalScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport = QWidget()
        self.viewport.setStyleSheet("background: transparent; border: none;")
        self.layout = QHBoxLayout(self.viewport)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.viewport.setLayout(self.layout)
        self.setWidget(self.viewport)


class VerticalScrollPage(VerticalScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport = QWidget()
        self.viewport.setStyleSheet("background: transparent; border: none;")
        self.layout = QVBoxLayout(self.viewport)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.viewport.setLayout(self.layout)
        self.setWidget(self.viewport)
