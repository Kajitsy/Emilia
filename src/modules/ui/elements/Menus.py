from PyQt6.QtWidgets import QMenu

from modules.ui.ThemeManager import TM


class Menu(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("Menu"))


class PushButtonMenu(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("PushButtonMenu"))
