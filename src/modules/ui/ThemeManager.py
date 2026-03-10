import json, os, sys

from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path

class ThemeManager(QObject):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
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
        self.current = ""
        self.theme_path = "themes"
        self.colors_file = {}
        self.styles_file = {}
        self.default_styles = {}

    def c(self, key):
        if key in self.colors_file:
            return self.colors_file.get(key, "")
        else:
            return  self.recovery_theme["colors"].get(key, "")

    def get_style(self, element):
        if element in self.styles_file:
            return self.styles_file.get(element, "")
        else:
            return self.default_styles.get(element, "")

    def set_theme(self, theme_name):
        themes = self.get_themes()
        if theme_name in themes and self.current != theme_name:
            self.styles_file.clear()
            self.colors_file.clear()

            self.current = theme_name
            file = self.get_theme(self.current)
            self.colors_file = file['colors']
            use_def_qss = file.get('use_default_elements', True)
            main_dir = Path(sys.argv[0]).resolve().parent
            if use_def_qss:
                self.load_default_qss()
                self.styles_file = self.default_styles
            else:
                self.load_default_qss()
                for element, path in file.get('elements', {}).items():
                    style = open(main_dir / "themes" / self.current / path, "r", encoding="utf-8").read()
                    for key, value in self.colors_file.items():
                        style = style.replace(f"@{key}", value)
                    self.styles_file[element] = style
            self.theme_changed.emit()

    def load_default_qss(self):
        self.default_styles = {}
        main_dir = Path(sys.argv[0]).resolve().parent
        default_qss_dir = main_dir / "data" / "default_qss"
        for qss_file in default_qss_dir.rglob("*.qss"):
            element = qss_file.stem
            style = qss_file.read_text(encoding="utf-8")
            for key, value in self.colors_file.items():
                style = style.replace(f"@{key}", value)
            self.default_styles[element] = style

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