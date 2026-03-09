import json, os

from PyQt6.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current = "Dark"
        self.theme_path = "themes"
        self.recovery_theme = {
            "name": "Dark",
            "titlebar": "dark",
            "colors": {
                "element_bg": "#494a4d",
                "text": "#e8eaed",
                "hover_bg": "#5f6368",
                "pressed_bg": "#3c3d3f",
                "disabled_text": "#a2a2ac",
                "menu_bg": "#202024",
                "menu_item_select": "#25262b",
                "primary_bg": "#303134",
                "scroll_sub": "#f0f0f0",
                "scroll_handle": "#555",
                "scroll_hover": "#777",
                "mw_back": "#202124",
                "mw_color": "#e8eaed"
            }
        }

    def c(self, key):
        return self.get_theme(self.current)['colors'][key]

    def set_theme(self, theme_name):
        themes = self.get_themes()
        if theme_name in themes and self.current != theme_name:
            self.current = theme_name
            self.theme_changed.emit()

    def get_themes_count(self):
        count = 0
        for root, _, files in os.walk(self.theme_path):
            for file in files:
                if file.endswith(".json"):
                    theme = json.load(open(os.path.join(root, file)))
                    if theme.get('name'):
                        count += 1
        return count

    def get_themes_name(self):
        names = []
        for root, _, files in os.walk(self.theme_path):
            for file in files:
                if file.endswith(".json"):
                    theme = json.load(open(os.path.join(root, file)))
                    if theme.get('name'):
                        names.append(theme['name'])
        return names

    def get_themes(self):
        themes = {}
        for root, _, files in os.walk(self.theme_path):
            for file in files:
                if file.endswith(".json"):
                    theme = json.load(open(os.path.join(root, file)))
                    if theme.get('name'):
                        themes[theme.get('name')] = theme
        return themes

    def get_theme(self, theme_name):
        if theme_name not in self.get_themes():
            return self.recovery_theme
        for root, _, files in os.walk(self.theme_path):
            for file in files:
                if file.endswith(".json"):
                    theme = json.load(open(os.path.join(root, file)))
                    if theme.get('name') == theme_name:
                        return theme
        return {}