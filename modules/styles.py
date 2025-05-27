import re
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont, QPainterPath, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QRectF

def format_text(text, username="User"):
    replacements = [
        (r"^(#{1,6})\s*(.+)$", lambda m: f"<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>", re.MULTILINE),
        (r"```(.*?)```", r"<pre><code>\1</code></pre>", re.DOTALL),
        (r"`(.*?)`", r"<code>\1</code>"),
        (r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>"),
        (r"\*\*(.*?)\*\*", r"<b>\1</b>"),
        (r"\*(.*?)\*", r"<i>\1</i>"),
        ("\n", "<br>"),
        ("{{user}}", username)
    ]

    for pattern, replacement, *flags in replacements:
        text = re.sub(pattern, replacement, text, flags=flags[0] if flags else 0)

    return text

def format_number(num: float, decimals: int = 1):
    if num < 1000:
        return str(num)

    suffixes = ['k', 'm', 'b', 't']
    for i, suffix in enumerate(suffixes, start=1):
        unit = 1000 ** i
        if num < unit * 1000:
            return f"{num / unit:.{decimals}f}{suffix}"

    return f"{num / (1000 ** len(suffixes)):.{decimals}f}P"

def color_avatar(avatar_label, avatar_w, avatar_h, name, radius=100):
    pixmap = QPixmap(avatar_w, avatar_h)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    gradient = QLinearGradient(0, 0, avatar_w, avatar_h * 0.7)
    gradient.setColorAt(0, QColor("#f47c3b"))
    gradient.setColorAt(1, Qt.GlobalColor.transparent)

    painter.fillRect(pixmap.rect(), QBrush(gradient))

    font = QFont("Arial", int(avatar_h / 3))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))

    first_letter = name[0].upper() if name else ""
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, first_letter)
    painter.end()

    def round_pixmap(source_pixmap: QPixmap) -> QPixmap:
        rounded = QPixmap(avatar_w, avatar_h)
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, source_pixmap.width(), source_pixmap.height()), radius, radius)
        painter.setClipPath(path)

        painter.drawPixmap(0, 0, source_pixmap)
        painter.end()

        return rounded

    rounded_pixmap = round_pixmap(pixmap)
    avatar_label.setPixmap(rounded_pixmap)

def combobox_style():
    return """
        QComboBox {
            background-color: #494a4d;
            color: #e8eaed;
            border: 2px solid #5f6368;
            border-radius: 4px;
            padding: 5px 8px;
        }
        QComboBox:hover {
            border: 2px solid #a2a2ac;
        }
        QComboBox::drop-down {
            border: none;
            background: transparent;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: url(down_arrow_icon.png);
            width: 12px;
            height: 12px;
        }
        QComboBox::down-arrow:on {
            image: url(down_arrow_icon_hover.png);
        }
        QComboBox QAbstractItemView {
            background-color: #202024;
            border: 1px solid #5f6368;
            selection-background-color: #25262b;
            color: #e8eaed;
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox::item {
            background-color: #202024;
            padding: 5px 10px;
            border-radius: 4px;
        }
        QComboBox::item:selected {
            background-color: #25262b;
        }
        QComboBox:disabled {
            background-color: #3c3d3f;
            color: #a2a2ac;
            border: 2px solid #555;
        }
    """

def pushbutton_style():
    return """
        QPushButton {
            color: #e8eaed;
            padding: 8px;
            border-radius: 4px;
            background: #494a4d;
            border: 2px solid #5f6368;
        }
        QPushButton:hover {
            border: 2px solid #a2a2ac;
        }
        QPushButton:checked {
            background: #5f6368;
            border: 2px solid #e8eaed;
        }
        QPushButton:checked:hover {
            background: #777;
        }
        QPushButton:disabled {
            background: #3c3d3f;
            border: 2px solid #555;
        }
        QPushButton:checked:disabled {
            background: #555;
            border: 2px solid #a2a2ac;
        }
    """

def menu_style():
    return """
            QMenu {
                background-color: #202024;
                border-radius: 4px;
            }
            QMenu::item {
                background-color: #202024;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #25262b;
                border-radius: 4px;
            }
        """

def profile_menu_style():
    return """
            QMenu {
                background-color: #202024;
                border-radius: 4px;
            }
            QMenu::item {
                background-color: #202024;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #25262b;
                border-radius: 4px;
            }
        """

def button_style():
    return """
        QPushButton {
            background-color: #494a4d;
            color: #e8eaed;
            border: none;
            border-radius: 4px;
            padding: 8px 15px;
            text-align: left;
        }
        QPushButton:disabled {
            background-color: #3c3d3f;
            color: #a2a2ac;
        }
        QPushButton:hover {
            background-color: #5f6368;
        }
        QPushButton:pressed {
            background-color: #3c3d3f;
        }
        QPushButton:checked {
            background-color: #3c3d3f;
        }
    """

def tab_button_style():
    return """
        QPushButton {
            background-color: #494a4d;
            color: #e8eaed;
            border: none;
            border-radius: 4px;
            padding: 8px 15px;
            text-align: left;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #a2a2ac;
        }
        QPushButton:hover {
            background-color: #5f6368;
        }
        QPushButton:pressed, QPushButton:checked {
            background-color: #494a4d;
            border-bottom: 5px solid #555;
            padding-bottom: 3px;
        }
    """

def icon_button_style():
    return """
        QPushButton {
            background-color: #494a4d;
            color: #e8eaed;
            border: none;
            border-radius: 4px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #5f6368;
        }
        QPushButton:pressed {
            background-color: #3c3d3f;
        }
        QPushButton:checked {
            background-color: #3c3d3f;
        }
    """

def icon_pressbutton_style():
    return """
        QPushButton {
            background-color: #494a4d;
            color: #e8eaed;
            border: none;
            border-radius: 4px;
            padding: 2px;
        }
        QPushButton:checked {
            background-color: #fafafa;
        }
    """

def check_button_style():
    return """
        QPushButton {
            background-color: #494a4d;
            color: #e8eaed;
            border: none;
            border-radius: 4px;
            padding: 8px;
        }
        QPushButton:checked {
            background-color: #fafafa;
        }
    """

def scroll_bar_style():
    return """
        QScrollBar:horizontal {
            border: none;
            background-color: #303134;
            height: 8px;
            margin: 0px 0 0px 0;
        }
        QScrollBar::sub-control:horizontal {
            background: #f0f0f0;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal {
            background: #555;
            min-width: 20px;
            border-radius: 4px;
        }
        QScrollBar::add-line:horizontal {
            width: 0px;
            subcontrol-position: right;
            subcontrol-origin: margin;
        }
        QScrollBar::sub-line:horizontal {
            width: 0px;
            subcontrol-position: left;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        QScrollBar::handle:horizontal:hover {
            background: #777;
        }

        QScrollBar:vertical {
            border: none;
            background: #303134;
            width: 8px;
            margin: 0px 0 0px 0;
            border-radius: 4px;
        }
        QScrollBar::sub-control:vertical {
            background: #f0f0f0;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            min-height: 20px;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical {
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }
        QScrollBar::sub-line:vertical {
            height: 0px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QScrollBar::handle:vertical:hover {
            background: #777;
        }
    """

def scroll_style():
    return """
        QScrollArea {
            background-color: #303134;
            border: none;
            border-radius: 4px;
        }
        QScrollBar:horizontal {
            border: none;
            background: #303134;
            height: 8px;
            margin: 0px 0 0px 0;
            border-bottom-right-radius: 4px;
            border-bottom-left-radius: 4px; 
        }
        QScrollBar::sub-control:horizontal {
            background: #f0f0f0;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal {
            background: #555;
            min-width: 20px;
            border-radius: 4px;
        }
        QScrollBar::add-line:horizontal {
            width: 0px;
            subcontrol-position: right;
            subcontrol-origin: margin;
        }
        QScrollBar::sub-line:horizontal {
            width: 0px;
            subcontrol-position: left;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        QScrollBar::handle:horizontal:hover {
            background: #777;
        }

        QScrollBar:vertical {
            border: none;
            background: #303134;
            width: 8px;
            margin: 0px 0 0px 0;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px; 
        }
        QScrollBar::sub-control:vertical {
            background: #f0f0f0;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            min-height: 20px;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical {
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }
        QScrollBar::sub-line:vertical {
            height: 0px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QScrollBar::handle:vertical:hover {
            background: #777;
        }
    """

def lineedit_style():
    return """
        QLineEdit {
            background-color: #494a4d; 
            color: #e8eaed; 
            border-radius: 4px; 
            padding: 7px;
        }
        QLineEdit:disabled {
            background-color: #3c3d3f;
            color: #a2a2ac;
        }
        QTextEdit {
            background-color: #494a4d; 
            color: #e8eaed; 
            border-radius: 4px; 
            padding: 7px;
        }
        QTextEdit:disabled {
            background-color: #3c3d3f;
            color: #a2a2ac;
        }
    """

def lineedit_style2():
    return """
        QWidget {
            background-color: #494a4d; 
            color: #e8eaed; 
            border-radius: 4px;
        }
    """

def keysequenceedit_style():
    return """
        background-color: #494a4d; 
        color: #e8eaed; 
        border-radius: 4px; 
        padding: 6px;
        border: 1px solid #5a5b5e;
    """

def left_sidebar_style():
    return """
        #leftSidebar {
            background-color: #303134;
            border-radius: 4px;
            border: none;
        }
    """

def top_bar_style():
    return """
        QWidget {
            background-color: transparent;
        }
        QFrame {
            background-color: transparent;
        }
        #topBar {
            background-color: #303134;
            border: none;
            border-radius: 4px;
        }
    """

def character_info_sidebar_style():
    return """
        QFrame {
            background-color: #303134;
            border-radius: 4px;
            border: none;
        }
    """

def main_window_style():
    return """
        background-color: #202124;
        color: #e8eaed;
    """

def card_style():
    return """
        QFrame {
            border-radius: 4px;
        }
        QFrame:hover {
            background-color: #3c3d3f;
        }
    """

def card_pressed_style():
    return """
        QFrame {
            border-radius: 4px;
            background-color: #3c3d3f;
        }
    """

def recent_delete_button_style():
    return """
        QPushButton {
            background-color: transparent;
            border: none;
            margin-right: 10px;
        }
        QPushButton:hover {
            background-color: #5a5c60;
            border-radius: 4px;
        }
        QPushButton:pressed {
            background-color: #3e4043;
            border-radius: 4px;
        }
    """

class SvgIcons:
    def _svg_to_pixmap(self, svg):
        renderer = QSvgRenderer()
        renderer.load(svg.encode('utf-8'))

        pixmap = QPixmap(renderer.viewBox().size())
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap

    def new_chat(self, color = '#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24"><path d="M11 5a1 1 0 1 0 0-2zm10 8a1 1 0 1 0-2 0zM5.638 19.673l.454-.891zm-1.311-1.311-.891.454zm14.035 1.311-.454-.891zm1.311-1.311-.891-.454zM4.327 5.638l.891.454zm1.311-1.311.454.891zM9 15H8a1 1 0 0 0 1 1zm.293-3.293.707.707zM17.25 3.75l-.707-.707zm3 3-.707-.707zm-7.957 7.957.707.707zM20.25 3.75l-.707.707zM15.2 19H8.8v2h6.4zM5 15.2V8.8H3v6.4zM8.8 5H11V3H8.8zM19 13v2.2h2V13zM8.8 19c-.857 0-1.439 0-1.889-.038-.438-.035-.663-.1-.819-.18l-.908 1.782c.485.247 1.002.346 1.564.392C7.298 21 7.976 21 8.8 21zM3 15.2c0 .824 0 1.501.044 2.052.046.562.145 1.079.392 1.564l1.782-.908c-.08-.156-.145-.38-.18-.82C5 16.639 5 16.058 5 15.2zm3.092 3.582a2 2 0 0 1-.874-.874l-1.782.908a4 4 0 0 0 1.748 1.748zM15.2 21c.824 0 1.501 0 2.052-.044.562-.046 1.079-.145 1.564-.392l-.908-1.782c-.156.08-.38.145-.819.18-.45.037-1.032.038-1.889.038zm3.8-5.8c0 .857 0 1.439-.038 1.889-.035.438-.1.663-.18.819l1.782.908c.247-.485.346-1.002.392-1.564.045-.55.044-1.228.044-2.052zm-.184 5.364a4 4 0 0 0 1.748-1.748l-1.782-.908a2 2 0 0 1-.874.874zM5 8.8c0-.857 0-1.439.038-1.889.035-.438.1-.663.18-.819l-1.782-.908c-.247.485-.346 1.002-.392 1.564C3 7.298 3 7.976 3 8.8zM8.8 3c-.824 0-1.501 0-2.052.044-.562.046-1.079.145-1.564.392l.908 1.782c.156-.08.38-.145.819-.18C7.361 5 7.943 5 8.8 5zM5.218 6.092a2 2 0 0 1 .874-.874l-.908-1.782a4 4 0 0 0-1.748 1.748zM8 12.414V15h2v-2.586zM9 16h2.586v-2H9zm1-3.586 7.957-7.957-1.414-1.414L8.586 11zm9.543-6.371L11.586 14 13 15.414l7.957-7.957zm0-1.586a1.12 1.12 0 0 1 0 1.586l1.414 1.414a3.12 3.12 0 0 0 0-4.414zm-1.586 0a1.12 1.12 0 0 1 1.586 0l1.414-1.414a3.12 3.12 0 0 0-4.414 0zM11.586 16A2 2 0 0 0 13 15.414L11.586 14zM10 12.414 8.586 11A2 2 0 0 0 8 12.414z" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def no_voice(self, color='#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24"><path d="M8 3a1 1 0 0 1 1 1v7.105l2-1.473V8a1 1 0 1 1 2 0v.158l2-1.474V6a1 1 0 0 1 1.78-.627l2.415-1.78a1 1 0 0 1 1.186 1.61L2.991 18.018a1 1 0 0 1-1.186-1.61L3 15.527V10a1 1 0 1 1 2 0v4.053l2-1.474V4a1 1 0 0 1 1-1M7 20v-1.958l2-1.474V20a1 1 0 1 1-2 0m6-4v-2.379l-2 1.474V16a1 1 0 1 0 2 0m2 2v-5.853l2-1.473V18a1 1 0 1 1-2 0m5-9a1 1 0 0 1 1 1v4a1 1 0 1 1-2 0v-4a1 1 0 0 1 1-1"  fill="{color}" fill-role="evenodd"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def with_voice(self, color='#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24"><path d="M8 4v16M4 10v4m8-6v8m4-10v12m4-8v4" stroke="{color}" stroke-linecap="round" stroke-width="2"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def share(self, color='#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M20 12.75V17a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-4.25M12 4v11.25M12 4l4.5 4.5M12 4 7.5 8.5" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def like(self, color='#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M7 11H4a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h3m0-9v9m0-9 4-8h.616a2 2 0 0 1 1.976 2.308L13.016 9h5.047a3 3 0 0 1 2.973 3.405l-.682 5A3 3 0 0 1 17.38 20H7" stroke="{color}" stroke-linejoin="round" stroke-width="2"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def liked(self, color='#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path fill="{color}" fill-rule="evenodd" clip-rule="evenodd" d="M11 2C10.6212 2 10.275 2.214 10.1056 2.55279L6.38197 10H4C2.89543 10 2 10.8954 2 12V19C2 20.1046 2.89543 21 4 21H17.3813C19.3816 21 21.0744 19.5224 21.3446 17.5405L22.0265 12.5405C22.354 10.1387 20.4871 8 18.0631 8H14.1841L14.5798 5.46216C14.8634 3.64303 13.4567 2 11.6156 2H11ZM6 19V12H4V19H6Z"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def dislike(self, color='#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none" height="16px"><path d="M17 13H20C20.5523 13 21 12.5523 21 12L21 5C21 4.44772 20.5523 4 20 4H17M17 13L17 4M17 13L13.301 20.4505C13.1339 20.7871 12.7905 21 12.4147 21V21C11.1917 21 10.2572 19.9046 10.4456 18.6919L11.0192 15L5.98994 15C4.17839 15 2.78316 13.3959 3.02793 11.5947L3.70735 6.59466C3.90933 5.1082 5.17443 4 6.66936 4H17" stroke="{color}" stroke-linejoin="round" stroke-width="2"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def disliked(self, color='#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M14.1967 20.8952C13.8607 21.572 13.1703 22 12.4147 22C10.5741 22 9.17547 20.3533 9.45744 18.5384L9.85181 16H5.98994C3.56858 16 1.71124 13.8576 2.03703 11.46L2.71645 6.46001C2.98543 4.48052 4.67151 3 6.66936 3L20 3C21.1046 3 22 3.89543 22 5L22 12C22 13.1046 21.1046 14 20 14H17.62L14.1967 20.8952ZM18 12H20L20 5H18L18 12Z" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def history(self, color='#a2a2ac'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M15 4.582a8 8 0 0 0-6.5 14.614M9 15v5H4" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path><path d="M13 21a1 1 0 1 0 0-2 1 1 0 0 0 0 2M21 11a1 1 0 1 0-2 0 1 1 0 0 0 2 0M19.93 14.268a1 1 0 1 1-1 1.732 1 1 0 0 1 1-1.732M17.368 19.294a1 1 0 1 0-1-1.732 1 1 0 0 0 1 1.732M18.927 8a1 1 0 1 1-1-1.732 1 1 0 0 1 1 1.732" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def show_right_sidebar(self, color='#a2a2ac'):
        svg = f"""<svg stroke="{color}" fill="{color}" stroke-width="0" viewBox="0 0 16 16" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M3 9.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def hide_left_sidebar(self, color='#A2A2AC'):
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none"><g clip-path="url(#clip0_3610_3218)"><path d="M6.4 4.8002L3.2 8.0002L6.4 11.2002" stroke="{color}" stroke-width="1.28" stroke-linecap="round" stroke-linejoin="round"></path><path d="M12.4 4.8002L9.19999 8.0002L12.4 11.2002" stroke="{color}" stroke-width="1.28" stroke-linecap="round" stroke-linejoin="round"></path></g><defs><clipPath id="clip0_3610_3218"><rect width="16" height="16" fill="white" transform="matrix(-1 0 0 -1 16 16)"></rect></clipPath></defs></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def hide_right_sidebar(self, color='#A2A2AC'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="m9 4 8 8-8 8" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def colors(self, color='#A2A2AC'):
        svg = f"""<svg stroke="{color}" fill="{color}" stroke-width="0" viewBox="0 0 512 512" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M167.02 309.34c-40.12 2.58-76.53 17.86-97.19 72.3-2.35 6.21-8 9.98-14.59 9.98-11.11 0-45.46-27.67-55.25-34.35C0 439.62 37.93 512 128 512c75.86 0 128-43.77 128-120.19 0-3.11-.65-6.08-.97-9.13l-88.01-73.34zM457.89 0c-15.16 0-29.37 6.71-40.21 16.45C213.27 199.05 192 203.34 192 257.09c0 13.7 3.25 26.76 8.73 38.7l63.82 53.18c7.21 1.8 14.64 3.03 22.39 3.03 62.11 0 98.11-45.47 211.16-256.46 7.38-14.35 13.9-29.85 13.9-45.99C512 20.64 486 0 457.89 0z"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def send(self, color='#A2A2AC'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none" height="1.25em"><path d="M3.113 6.178C2.448 4.073 4.64 2.202 6.615 3.19l13.149 6.575c1.842.921 1.842 3.55 0 4.472l-13.15 6.575c-1.974.987-4.166-.884-3.501-2.99L4.635 13H9a1 1 0 1 0 0-2H4.635z" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def selected(self, color='#A2A2AC'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none" color="{color}" height="1.25em" width="1.25em"><path d="M3 15L9.29412 20L21 4" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="4"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return pixmap

    def play(self, color='#ffffff'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M9.576 2.534C7.578 1.299 5 2.737 5 5.086v13.828c0 2.35 2.578 3.787 4.576 2.552l11.194-6.914c1.899-1.172 1.899-3.932 0-5.104z" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def pause(self, color='#ffffff'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M16.839 3H7.16c-.527 0-.981 0-1.356.03-.395.033-.789.104-1.167.297a3 3 0 0 0-1.311 1.311c-.193.378-.264.772-.296 1.167C3 6.18 3 6.635 3 7.161v9.678c0 .527 0 .982.03 1.356.033.395.104.789.297 1.167a3 3 0 0 0 1.311 1.311c.378.193.772.264 1.167.296.375.031.83.031 1.356.031h9.678c.527 0 .982 0 1.356-.03.395-.033.789-.104 1.167-.297a3 3 0 0 0 1.311-1.311c.193-.378.264-.772.296-1.167.031-.375.031-.83.031-1.356V7.16c0-.527 0-.981-.03-1.356-.033-.395-.104-.789-.297-1.167a3 3 0 0 0-1.311-1.311c-.378-.193-.772-.264-1.167-.296A18 18 0 0 0 16.838 3" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def search(self, color='#A2A2AC'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none" height="16px"><path d="m20 20-3.95-3.95M18 11a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" stroke="{color}" stroke-linecap="round" stroke-width="2"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return pixmap

    def call(self, color='#A2A2AC'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M6.754 3C4.738 3 2.866 4.684 3.25 6.91c1.218 7.058 6.784 12.624 13.841 13.842 2.226.384 3.91-1.489 3.91-3.504a3.75 3.75 0 0 0-2.674-3.594l-.994-.299a2.83 2.83 0 0 0-2.81.709c-.266.266-.609.283-.826.149a12.1 12.1 0 0 1-3.908-3.908c-.135-.218-.118-.56.149-.827a2.83 2.83 0 0 0 .708-2.81l-.298-.994A3.75 3.75 0 0 0 6.754 3" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def end_call(self, color='#CE365C'):
        svg = f"""<svg width="29" height="1.5em" viewBox="0 0 29 28" fill="none" xmlns="http://www.w3.org/2000/svg"><g clip-path="url(#clip0_4103_8518)"><g clip-path="url(#clip1_4103_8518)"><path d="M26.6224 17.0963C28.2852 15.4335 28.4408 12.4995 26.2875 10.98C19.4604 6.16245 10.2769 6.16245 3.44984 10.98C1.29654 12.4995 1.45207 15.4335 3.11485 17.0963C4.48182 18.4633 6.58361 18.7718 8.28573 17.8552L9.35227 17.2809C10.4198 16.7061 11.0856 15.5915 11.0856 14.379C11.0856 13.9392 11.3544 13.6426 11.6448 13.5743C13.7626 13.0755 15.9747 13.0755 18.0925 13.5743C18.3828 13.6426 18.6517 13.9392 18.6517 14.379C18.6517 15.5915 19.3175 16.7061 20.385 17.2809L21.4516 17.8552C23.1537 18.7718 25.2555 18.4633 26.6224 17.0963Z" fill="{color}"></path></g></g><defs><clipPath id="clip0_4103_8518"><rect width="28" height="28" fill="white" transform="translate(0.25)"></rect></clipPath><clipPath id="clip1_4103_8518"><rect width="28" height="28" fill="white" transform="translate(34.668 14) rotate(135)"></rect></clipPath></defs></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def muted(self, color='#A2A2AC'):
        svg = f"""<svg width="29" height="1.5em" viewBox="0 0 29 28" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14.75 25.6666V23.3333M14.75 23.3333C10.4588 23.3333 7.9213 20.7026 6.60007 18.6666M14.75 23.3333C17.3496 23.3333 19.3056 22.3679 20.7375 21.1541M11.8554 5.67255C12.6509 5.0427 13.6566 4.66663 14.75 4.66663C17.3273 4.66663 19.4167 6.75596 19.4167 9.33329V13.2338M10.0833 10.5L4.25 4.66663L25.25 25.6666L20.7375 21.1541M10.0833 10.5V14C10.0833 16.5773 12.1727 18.6666 14.75 18.6666C15.7407 18.6666 16.6593 18.3579 17.4148 17.8315M10.0833 10.5L17.4148 17.8315M17.4148 17.8315L20.7375 21.1541" stroke-width="1.63333" stroke="{color}" stroke-linecap="round"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def mute(self, color='#A2A2AC'):
        svg = f"""<svg width="29" height="1.5em" viewBox="0 0 29 28" xmlns="http://www.w3.org/2000/svg" fill="none"><path d="M14.7515 23.3307V25.6641M14.7515 23.3307C10.4603 23.3307 7.92279 20.7 6.60156 18.6641M14.7515 23.3307C19.0428 23.3307 21.5802 20.7 22.9015 18.6641M19.4182 9.33073V13.9974C19.4182 16.5747 17.3288 18.6641 14.7515 18.6641C12.1742 18.6641 10.0848 16.5747 10.0848 13.9974V9.33073C10.0848 6.7534 12.1742 4.66406 14.7515 4.66406C17.3288 4.66406 19.4182 6.7534 19.4182 9.33073Z" stroke="{color}" stroke-width="1.63333" stroke-linecap="round"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def ellipsis(self, color='#A2A2AC'):
        svg = f"""<svg stroke="{color}" fill="{color}" stroke-width="0" viewBox="0 0 16 16" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M3 9.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def settings(self, color='#A2A2AC'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none" height="1.5em"><path d="m7.677 5.325-.372-.085A1.722 1.722 0 0 0 5.24 7.305l.085.372a2.41 2.41 0 0 1-1.011 2.547l-.565.377a1.682 1.682 0 0 0 0 2.798l.565.377a2.41 2.41 0 0 1 1.011 2.547l-.085.372a1.722 1.722 0 0 0 2.065 2.065l.372-.085a2.41 2.41 0 0 1 2.547 1.011l.377.565a1.682 1.682 0 0 0 2.798 0l.377-.565a2.41 2.41 0 0 1 2.547-1.011l.372.085a1.722 1.722 0 0 0 2.065-2.065l-.085-.372a2.41 2.41 0 0 1 1.011-2.547l.565-.377a1.682 1.682 0 0 0 0-2.798l-.565-.377a2.41 2.41 0 0 1-1.011-2.547l.085-.372a1.722 1.722 0 0 0-2.065-2.065l-.372.085a2.41 2.41 0 0 1-2.547-1.011l-.377-.565a1.682 1.682 0 0 0-2.798 0l-.377.565a2.41 2.41 0 0 1-2.547 1.011Z" stroke="{color}" stroke-linejoin="round" stroke-width="2"></path><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" stroke="{color}" stroke-linejoin="round" stroke-width="2"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def close(self, color='#A2A2AC'):
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def check(self, color='#A2A2AC'):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M3 15L9.29412 20L21 4" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="4"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def style(self, color='#A2A2AC'):
        svg = f"""<svg viewBox="0 0 21 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3.83333 4.16669C3.3731 4.16669 3 4.53978 3 5.00002C3 5.46026 3.3731 5.83335 3.83333 5.83335H17.1667C17.6269 5.83335 18 5.46026 18 5.00002C18 4.53978 17.6269 4.16669 17.1667 4.16669H3.83333Z" fill="{color}"></path><path d="M15.4326 8.00509C15.3013 7.69868 15 7.50002 14.6667 7.50002C14.3333 7.50002 14.032 7.69868 13.9007 8.00509L12.782 10.6154L10.1717 11.7341C9.86533 11.8654 9.66667 12.1667 9.66667 12.5C9.66667 12.8334 9.86533 13.1347 10.1717 13.266L12.782 14.3847L13.9007 16.995C14.032 17.3014 14.3333 17.5 14.6667 17.5C15 17.5 15.3013 17.3014 15.4326 16.995L16.5513 14.3847L19.1616 13.266C19.468 13.1347 19.6667 12.8334 19.6667 12.5C19.6667 12.1667 19.468 11.8654 19.1616 11.7341L16.5513 10.6154L15.4326 8.00509Z" fill="{color}"></path><path d="M3.83333 9.16669C3.3731 9.16669 3 9.53978 3 10C3 10.4603 3.3731 10.8334 3.83333 10.8334H8C8.46024 10.8334 8.83333 10.4603 8.83333 10C8.83333 9.53978 8.46024 9.16669 8 9.16669H3.83333Z" fill="{color}"></path><path d="M3.83333 14.1667C3.3731 14.1667 3 14.5398 3 15C3 15.4603 3.3731 15.8334 3.83333 15.8334H6.33333C6.79357 15.8334 7.16667 15.4603 7.16667 15C7.16667 14.5398 6.79357 14.1667 6.33333 14.1667H3.83333Z" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)
        return QIcon(pixmap)

    def beta(self, color='#A2A2AC', pixmap_ret=False):
        svg = f"""<svg viewBox="0 0 45 17" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet"><rect x="0.5" y="1" width="44" height="15" rx="3.5" stroke="{color}"></rect><path fill-rule="evenodd" clip-rule="evenodd" d="M7.5 5.875C7.5 5.66789 7.66789 5.5 7.875 5.5H12.125C12.3321 5.5 12.5 5.66789 12.5 5.875C12.5 6.08211 12.3321 6.25 12.125 6.25H12V7.86629C12.1194 8.00963 12.2527 8.1588 12.3958 8.31774C12.4112 8.33484 12.4267 8.35205 12.4423 8.36937C12.6035 8.54833 12.7748 8.73846 12.94 8.93544C13.3002 9.36505 13.657 9.85631 13.8547 10.4095C13.9448 10.662 14 10.9291 14 11.2081C14 12.4739 12.9739 13.5 11.7081 13.5H8.29188C7.02611 13.5 6 12.4739 6 11.2081C6 10.9291 6.05516 10.662 6.14535 10.4095C6.34301 9.85631 6.69982 9.36505 7.06005 8.93544C7.22521 8.73846 7.39649 8.54833 7.5577 8.36937C7.5733 8.35206 7.5888 8.33484 7.6042 8.31774C7.74728 8.1588 7.88058 8.00963 8 7.86629V6.25H7.875C7.66789 6.25 7.5 6.08211 7.5 5.875ZM8.75 6.25V8.13154L8.66783 8.23426C8.51305 8.42774 8.3371 8.62458 8.16162 8.81952C8.14641 8.83642 8.13119 8.85331 8.11598 8.8702C7.95335 9.05075 7.7909 9.23111 7.63475 9.41733C7.46273 9.62248 7.30478 9.82746 7.17085 10.0345C7.1871 10.0319 7.20351 10.0294 7.22008 10.0269C7.6673 9.95864 8.24651 9.88941 8.71536 9.90192C9.28335 9.91707 9.71495 10.0529 10.1021 10.1747L10.1126 10.178C10.502 10.3005 10.8469 10.4076 11.3046 10.4198C11.7032 10.4304 12.2275 10.3702 12.6668 10.3031C12.7726 10.287 12.8721 10.2707 12.962 10.2553C12.8054 9.97266 12.5982 9.69515 12.3652 9.41733C12.2091 9.23111 12.0467 9.05075 11.884 8.87021C11.8688 8.85331 11.8536 8.83642 11.8384 8.81952C11.6629 8.62458 11.487 8.42774 11.3322 8.23426L11.25 8.13154V6.25H8.75Z" fill="{color}"></path><path d="M9.5 4.5C9.5 4.77614 9.27614 5 9 5C8.72386 5 8.5 4.77614 8.5 4.5C8.5 4.22386 8.72386 4 9 4C9.27614 4 9.5 4.22386 9.5 4.5Z" fill="{color}"></path><path d="M11.5 3.75C11.5 4.16421 11.1642 4.5 10.75 4.5C10.3358 4.5 10 4.16421 10 3.75C10 3.33579 10.3358 3 10.75 3C11.1642 3 11.5 3.33579 11.5 3.75Z" fill="{color}"></path><path d="M18.702 11.5V5.137H21.312C21.606 5.137 21.876 5.164 22.122 5.218C22.374 5.266 22.59 5.353 22.77 5.479C22.956 5.605 23.1 5.773 23.202 5.983C23.304 6.193 23.355 6.454 23.355 6.766C23.355 7.054 23.289 7.318 23.157 7.558C23.025 7.792 22.83 7.969 22.572 8.089C22.92 8.179 23.187 8.353 23.373 8.611C23.559 8.863 23.652 9.193 23.652 9.601C23.652 9.967 23.583 10.273 23.445 10.519C23.313 10.759 23.127 10.951 22.887 11.095C22.653 11.239 22.38 11.344 22.068 11.41C21.756 11.47 21.423 11.5 21.069 11.5H18.702ZM19.827 10.474H21.168C21.336 10.474 21.501 10.462 21.663 10.438C21.825 10.414 21.972 10.372 22.104 10.312C22.236 10.252 22.338 10.165 22.41 10.051C22.488 9.931 22.527 9.778 22.527 9.592C22.527 9.424 22.497 9.286 22.437 9.178C22.377 9.07 22.293 8.986 22.185 8.926C22.083 8.86 21.96 8.815 21.816 8.791C21.672 8.761 21.522 8.746 21.366 8.746H19.827V10.474ZM19.827 7.801H21.015C21.201 7.801 21.369 7.783 21.519 7.747C21.669 7.711 21.798 7.657 21.906 7.585C22.014 7.507 22.098 7.414 22.158 7.306C22.218 7.192 22.248 7.054 22.248 6.892C22.248 6.682 22.2 6.526 22.104 6.424C22.008 6.316 21.876 6.247 21.708 6.217C21.546 6.181 21.363 6.163 21.159 6.163H19.827V7.801ZM24.7315 11.5V5.137H29.2225V6.163H25.8565V7.837H28.7815V8.845H25.8565V10.474H29.2225V11.5H24.7315ZM31.663 11.5V6.163H29.674V5.137H34.768V6.163H32.779V11.5H31.663ZM34.3749 11.5L36.8139 5.137H38.1549L40.5849 11.5H39.3699L38.9469 10.321H36.0129L35.5809 11.5H34.3749ZM36.3729 9.304H38.5779L37.4799 6.271L36.3729 9.304Z" fill="{color}"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)

        if pixmap_ret:
            return pixmap
        else:
            return QIcon(pixmap)

    def limited(self, color='#A2A2AC', pixmap_ret=False):
        svg = f"""<svg class="mr-2" viewBox="0 0 58 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="0.5" y="0.5" width="57" height="15" rx="3.5" stroke="#7C7C87"></rect><g clip-path="url(#clip0_536_4044)"><path d="M10 5.875V8L11.375 9.375M14.625 8C14.625 10.5543 12.5543 12.625 10 12.625C7.44568 12.625 5.375 10.5543 5.375 8C5.375 5.44568 7.44568 3.375 10 3.375C12.5543 3.375 14.625 5.44568 14.625 8Z" stroke="#7C7C87" stroke-linecap="round" stroke-linejoin="round"></path></g><path d="M18.711 11V4.637H19.836V9.974H23.148V11H18.711ZM23.9932 11V4.637H25.1182V11H23.9932ZM26.5421 11V4.637H28.0811L29.8451 7.85L31.5911 4.637H33.0851V11H31.9601V6.059L30.0611 9.497H29.5841L27.6671 6.059V11H26.5421ZM34.5049 11V4.637H35.6299V11H34.5049ZM38.4218 11V5.663H36.4328V4.637H41.5268V5.663H39.5378V11H38.4218ZM42.3272 11V4.637H46.8182V5.663H43.4522V7.337H46.3772V8.345H43.4522V9.974H46.8182V11H42.3272ZM47.8907 11V4.637H50.2397C50.9057 4.637 51.4697 4.766 51.9317 5.024C52.3937 5.276 52.7447 5.642 52.9847 6.122C53.2307 6.596 53.3537 7.166 53.3537 7.832C53.3537 8.486 53.2337 9.05 52.9937 9.524C52.7597 9.998 52.4117 10.364 51.9497 10.622C51.4877 10.874 50.9207 11 50.2487 11H47.8907ZM49.0157 9.974H50.2217C50.6957 9.974 51.0767 9.884 51.3647 9.704C51.6587 9.518 51.8717 9.266 52.0037 8.948C52.1417 8.624 52.2107 8.249 52.2107 7.823C52.2107 7.409 52.1447 7.04 52.0127 6.716C51.8807 6.392 51.6677 6.137 51.3737 5.951C51.0857 5.759 50.7047 5.663 50.2307 5.663H49.0157V9.974Z" fill="#7C7C87"></path><defs><clipPath id="clip0_536_4044"><rect width="12" height="12" fill="{color}" transform="translate(4 2)"></rect></clipPath></defs></svg>"""
        pixmap = self._svg_to_pixmap(svg)

        if pixmap_ret:
            return pixmap
        else:
            return QIcon(pixmap)

    def profile(self, color='#A2A2AC', pixmap_ret=False):
        svg = f"""<svg viewBox="0 0 24 24" fill="none"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10m3-12a3 3 0 1 1-6 0 3 3 0 0 1 6 0m-3 10a7.98 7.98 0 0 1-5.714-2.4C7.618 16.004 9.605 15 12 15s4.383 1.005 5.714 2.6A7.98 7.98 0 0 1 12 20" fill="{color}" fill-rule="evenodd"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)

        if pixmap_ret:
            return pixmap
        else:
            return QIcon(pixmap)

    def discover(self, color='#A2A2AC', pixmap_ret=False):
        svg = f"""<svg viewBox="0 0 24 24" fill="none" color="{color}"><path d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12m12.524-3.753a1 1 0 0 1 1.228 1.228l-1.12 4.105a1.5 1.5 0 0 1-1.052 1.052l-4.105 1.12a1 1 0 0 1-1.228-1.228l1.12-4.105a1.5 1.5 0 0 1 1.052-1.052z" fill="{color}" fill-rule="evenodd"></path></svg>"""
        pixmap = self._svg_to_pixmap(svg)

        if pixmap_ret:
            return pixmap
        else:
            return QIcon(pixmap)

    def model_type_icon(self, svg, color='#A2A2AC', pixmap_ret=False):
        svg = svg.replace("currentColor", color)
        pixmap = self._svg_to_pixmap(svg)

        if pixmap_ret:
            return pixmap
        else:
            return QIcon(pixmap)