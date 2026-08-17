from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton

from modules.ui.ThemeManager import TM


class PushButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        theme = TM.get_style("PushButton")
        if self._icon:
            self.setStyleSheet(theme.replace("text-align: left", "text-align: center"))
        else:
            self.setStyleSheet(theme)

    def setIcon(self, icon):
        super().setIcon(icon)
        self._icon = True
        self.update_theme()


class TabButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        theme = TM.get_style("TabButton")
        if self._icon:
            self.setStyleSheet(theme.replace("text-align: left", "text-align: center"))
        else:
            self.setStyleSheet(theme)

    def setIcon(self, icon):
        super().setIcon(icon)
        self._icon = True
        self.update_theme()
