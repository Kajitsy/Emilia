import ctypes, json, os, platform

from PyQt6.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current = "Dark"
        self.theme_path = "themes"

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
        for root, _, files in os.walk(self.theme_path):
            for file in files:
                if file.endswith(".json"):
                    theme = json.load(open(os.path.join(root, file)))
                    if theme.get('name') == theme_name:
                        return theme