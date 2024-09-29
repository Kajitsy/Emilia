import requests, os
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon
from modules.config import resource_path

emiliaicon = f'{resource_path('images')}/emilia.png'

def MessageBox(title = "Emilia", text = "Hm?", icon = emiliaicon, pixmap = None, self = None): 
    msg = QMessageBox()
    msg.setWindowTitle(title)
    if self: msg.setStyleSheet(self.styleSheet())
    if pixmap: msg.setIconPixmap(pixmap)
    msg.setWindowIcon(QIcon(icon))
    msg.setText(text)
    msg.exec()

def Emote_File():
    if not os.path.exists('Emotes.json'):
        emotesjson = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/Emotes.json")
        emotesjson.raise_for_status()
        with open("Emotes.json", "wb") as f:
            f.write(emotesjson.content)