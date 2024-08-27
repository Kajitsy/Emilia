import requests, os
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QLocale
from modules.config import resource_path, getconfig

emiliaicon = f'{resource_path('images')}/emilia.png'
lang = getconfig('language', QLocale.system().name())

def MessageBox(title = "Emilia", text = "Hm?", icon = emiliaicon, pixmap = None,self = None): 
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

def Voice_File():
    if not os.path.exists('voice.pt'):
        if lang == 'ru_RU':
            voicefile = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/tts_models/v4_ru.pt")
        elif lang == 'en_US':
            voicefile = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/tts_models/v3_en.pt")
        voicefile.raise_for_status()
        with open("voice.pt", "wb") as f:
            f.write(voicefile.content)