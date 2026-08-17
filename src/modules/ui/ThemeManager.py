import json
import os
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal


from modules.logic.SystemAccent import (
    adjust_color_brightness,
    get_contrasting_text_color,
    get_system_accent_color,
)


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
                "icon": "#a2a2ac",
                "menu_bg": "#202024",
                "menu_item_select": "#25262b",
                "primary_bg": "#303134",
                "scroll_sub": "#f0f0f0",
                "scroll_handle": "#555",
                "scroll_hover": "#777",
                "mw_back": "#202124",
                "mw_color": "#e8eaed",
                "avatar_back": "#f47c3b",
                "avatar_color": "#ffffff",
                "accent": "#308cc6",
                "accent_hover": "#439cd6",
                "accent_pressed": "#207cb6",
                "accent_text": "#ffffff",
            },
        }
        self.current = ""
        self.use_system_accent = False
        src_dir = Path(__file__).resolve().parent.parent.parent
        self.theme_path = (
            str(src_dir / "themes") if (src_dir / "themes").exists() else "themes"
        )
        self.colors_file = {}
        self.styles_file = {}
        self.default_styles = {}

    def _apply_accent_colors(self):
        if self.use_system_accent:
            accent = get_system_accent_color()
        else:
            accent = self.colors_file.get("accent", "#308cc6")

        accent_hover = adjust_color_brightness(accent, 1.15)
        accent_pressed = adjust_color_brightness(accent, 0.85)
        accent_text = get_contrasting_text_color(accent)

        self.colors_file["accent"] = accent
        self.colors_file["accent_hover"] = accent_hover
        self.colors_file["accent_pressed"] = accent_pressed
        self.colors_file["accent_text"] = accent_text

    def set_use_system_accent(self, enable: bool):
        if self.use_system_accent != enable:
            self.use_system_accent = enable
            self.reload_theme()

    def reload_theme(self):
        current_theme = self.current or "Dark"
        self.current = ""
        self.set_theme(current_theme, force=True)

    def c(self, key):
        if key in self.colors_file:
            return self.colors_file.get(key, "")
        else:
            return self.recovery_theme["colors"].get(key, "")

    def get_style(self, element):
        if element in self.styles_file:
            return self.styles_file.get(element, "")
        else:
            return self.default_styles.get(element, "")

    def set_theme(self, theme_name, force=False):
        themes = self.get_themes()
        if (theme_name in themes and self.current != theme_name) or force:
            self.styles_file.clear()
            self.colors_file.clear()

            self.current = theme_name
            file = self.get_theme(self.current)
            self.colors_file = dict(file.get("colors", {}))
            self._apply_accent_colors()

            use_def_qss = file.get("use_default_elements", True)
            if use_def_qss:
                self.load_default_qss()
                self.styles_file = self.default_styles
            else:
                self.load_default_qss()
                for element, path in file.get("elements", {}).items():
                    theme_file = Path(self.theme_path) / self.current / path
                    if theme_file.exists():
                        style = theme_file.read_text(encoding="utf-8")
                        for key, value in self.colors_file.items():
                            style = style.replace(f"@{key}", value)
                        self.styles_file[element] = style
            self.theme_changed.emit()

    def load_default_qss(self):
        self.default_styles = {}
        src_dir = Path(__file__).resolve().parent.parent.parent
        default_qss_dir = src_dir / "data" / "default_qss"
        if default_qss_dir.exists():
            for qss_file in default_qss_dir.rglob("*.qss"):
                element = qss_file.stem
                style = qss_file.read_text(encoding="utf-8")
                for key, value in self.colors_file.items():
                    style = style.replace(f"@{key}", value)
                self.default_styles[element] = style

    def check_theme(self, theme_id):
        for root, _, files in os.walk(self.theme_path):
            if "theme.json" in files:
                file_path = os.path.join(root, "theme.json")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        theme = json.load(f)
                        if theme.get("theme_id") == theme_id:
                            return True
                except (json.JSONDecodeError, OSError):
                    continue
        return False

    def get_themes_name(self):
        names = []
        for root, _, files in os.walk(self.theme_path):
            if "theme.json" in files:
                file_path = os.path.join(root, "theme.json")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        theme = json.load(f)
                        name = theme.get("name")
                        if name:
                            names.append(theme["name"])
                except (json.JSONDecodeError, OSError):
                    continue
        return names

    def get_themes(self):
        themes = {}
        for root, _, files in os.walk(self.theme_path):
            if "theme.json" in files:
                file_path = os.path.join(root, "theme.json")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        theme = json.load(f)
                        name = theme.get("name")
                        if name:
                            themes[name] = theme
                except (json.JSONDecodeError, OSError):
                    continue
        return themes

    def get_theme(self, theme_name):
        if theme_name not in self.get_themes():
            return self.recovery_theme
        path = Path(self.theme_path, theme_name, "theme.json")
        if os.path.isfile(path):
            return json.load(open(path, "r", encoding="utf-8"))
        else:
            return self.recovery_theme


TM = ThemeManager()
