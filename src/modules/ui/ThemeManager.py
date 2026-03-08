from PyQt6.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current = "dark"
        self.palettes = {
            "dark": {
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
            },
            "light": {
                "element_bg": "#dee1e5",
                "text": "#202124",
                "hover_bg": "#e8eaed",
                "pressed_bg": "#bdc1c6",
                "disabled_text": "#80868b",
                "menu_bg": "#ffffff",
                "menu_item_select": "#f1f3f4",
                "primary_bg": "#f8f9fa",
                "scroll_sub": "#eeeeee",
                "scroll_handle": "#c1c1c1",
                "scroll_hover": "#a8a8a8",
                "mw_back": "#ffffff",
                "mw_color": "#202124"
            }
        }

    def c(self, key):
        return self.palettes[self.current][key]

    def set_theme(self, theme_name):
        if theme_name in self.palettes and self.current != theme_name:
            self.current = theme_name
            self.theme_changed.emit()