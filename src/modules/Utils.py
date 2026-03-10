import re
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QFont
from PyQt6.sip import isdeleted

from modules.ui import TM

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

    text = str(text)

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
    gradient.setColorAt(0, QColor(TM.c('avatar_back')))
    gradient.setColorAt(1, Qt.GlobalColor.transparent)

    painter.fillRect(pixmap.rect(), QBrush(gradient))

    font = QFont()
    font.setBold(True)
    font.setPointSize(int(avatar_h / 3))
    painter.setFont(font)
    painter.setPen(QColor(TM.c('avatar_color')))

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
    if not isdeleted(avatar_label):
        avatar_label.setPixmap(rounded_pixmap)
