import requests, os
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon

def message_box(title ="Emilia", text ="Hm?", icon = "images/emilia.png", pixmap = None, self = None):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    if self: msg.setStyleSheet(self.styleSheet())
    if pixmap: msg.setIconPixmap(pixmap)
    msg.setWindowIcon(QIcon(icon))
    msg.setText(text)
    msg.exec()

def emote_file():
    if not os.path.exists("Emotes.json"):
        emotes_json = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/Emotes.json")
        if emotes_json.status_code == 200:
            with open("Emotes.json", "wb") as f:
                f.write(emotes_json.content)