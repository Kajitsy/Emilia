import requests, os, asyncio
import modules.CustomCharAI as CustomCharAI
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal, QThread, QLocale
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

class ChatDataWorker(QThread):
    recommend_chats_signal = pyqtSignal(object)
    recent_chats_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, custom_char_ai):
        super().__init__()
        self.custom_char_ai = custom_char_ai

    async def fetch_data(self):
        try:
            recommend_chats = await CustomCharAI.get_recommend_chats()
            recent_chats = await CustomCharAI.get_recent_chats()
            self.recommend_chats_signal.emit(recommend_chats)
            self.recent_chats_signal.emit(recent_chats)
        except Exception as e:
            self.error_signal.emit(str(e))

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetch_data())