from PyQt6.QtWidgets import QFrame

from modules.ui.ThemeManager import TM


class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("CardFrame"))


class ClickableFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkable = False

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    @property
    def default_style(self):
        return TM.get_style("ClickableFrame")

    @property
    def press_style(self):
        return TM.get_style("PressedFrame")

    def update_theme(self):
        if self.checkable:
            self.setStyleSheet(self.press_style)
        else:
            self.setStyleSheet(self.default_style)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.checkable = not self.checkable
        self.update_theme()
        self.mousePress(event)

    def setCheckable(self, check):
        self.checkable = check
        self.update_theme()

    def mousePress(self, *args, **kwargs):
        pass
