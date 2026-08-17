from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup
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


class SortTabButton(TabButton):
    sort_changed = pyqtSignal(str)

    def __init__(
        self,
        text: str = "",
        parent=None,
        include_likes: bool = True,
        default_sort: str = "default",
        show_arrow: bool = True,
    ):
        self._base_text = text
        self._show_arrow = show_arrow
        display_text = f"{text} ▾" if show_arrow and text else text
        super().__init__(display_text, parent)
        self.include_likes = include_likes
        self._current_sort = default_sort
        self._menu = None
        self._actions = {}
        self._init_menu()

    def _init_menu(self):
        from modules.ui.elements.Menus import Menu

        self._menu = Menu(self)
        self._action_group = QActionGroup(self)
        self._action_group.setExclusive(True)

        options = [
            (self.tr("Default"), "default"),
            (self.tr("Chats (High to Low)"), "chats_desc"),
            (self.tr("Chats (Low to High)"), "chats_asc"),
            (self.tr("Name (A-Z)"), "name_asc"),
            (self.tr("Name (Z-A)"), "name_desc"),
        ]
        if self.include_likes:
            options.append((self.tr("Likes (High to Low)"), "likes_desc"))

        for label, mode in options:
            action = QAction(label, self)
            action.setCheckable(True)
            if mode == self._current_sort:
                action.setChecked(True)
            action.setData(mode)
            action.triggered.connect(lambda checked, m=mode: self.set_sort_mode(m))
            self._action_group.addAction(action)
            self._menu.addAction(action)
            self._actions[mode] = action

    def set_sort_mode(self, mode: str):
        self._current_sort = mode
        if mode in self._actions:
            self._actions[mode].setChecked(True)
        self.sort_changed.emit(mode)

    def get_sort_mode(self) -> str:
        return self._current_sort

    def mousePressEvent(self, event):
        was_checked = self.isChecked()
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and was_checked:
            self.show_sort_menu()

    def contextMenuEvent(self, event):
        self.show_sort_menu()

    def show_sort_menu(self):
        if self._menu:
            pos = self.mapToGlobal(self.rect().bottomLeft())
            self._menu.exec(pos)

