import os
import asyncio
import threading
import torch
import time
import re
import json
import sys
import webbrowser
import sounddevice as sd
from gpytranslate import Translator
from characterai import PyAsyncCAI
import speech_recognition as sr
from num2words import num2words
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtGui import QIcon, QAction, QPixmap

version = "2.0"
local_file = 'russian.pt'
device = torch.device('cuda')
sample_rate = 48000
put_accent = True
put_yo = True
debugmode = False

def numbers_to_words(text):
    def _conv_num(match):
        return num2words(int(match.group()), lang='ru')
    return re.sub(r'\b\d+\b', _conv_num, text)

class EmiliaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emilia")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        global tstart_button, user_aiinput, vstart_button, visibletextmode, visiblevoicemode, issues

        char_label = QLabel("ID персонажа:")
        self.layout.addWidget(char_label)
        self.char_entry = QLineEdit()
        self.layout.addWidget(self.char_entry)
        self.char_entry.setPlaceholderText("ID...")

        client_label = QLabel("Токен клиента:")
        self.layout.addWidget(client_label)
        self.client_entry = QLineEdit()
        self.layout.addWidget(self.client_entry)
        self.client_entry.setPlaceholderText("Токен...")

        speaker_label = QLabel("Голос:")
        self.layout.addWidget(speaker_label)
        self.speaker_entry = QLineEdit()
        self.layout.addWidget(self.speaker_entry)
        self.speaker_entry.setPlaceholderText("aidar, baya, kseniya, xenia, eugene или же random")

        self.load_config()

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.setup_config(self.char_entry, self.client_entry, self.speaker_entry))
        self.layout.addWidget(save_button)

        vstart_button = QPushButton("Запустить")
        vstart_button.clicked.connect(lambda: self.start_main("voice"))
        self.layout.addWidget(vstart_button)

        self.user_input = QLabel("")
        self.user_input.setWordWrap(True)
        self.layout.addWidget(self.user_input)
        
        user_aiinput = QLineEdit()
        user_aiinput.setPlaceholderText("Прежде чем жать кнопку ниже...")
        self.layout.addWidget(user_aiinput)
        user_aiinput.setVisible(False)

        tstart_button = QPushButton("Запустить в текстовом режиме")
        tstart_button.clicked.connect(lambda: self.start_main("text"))
        self.layout.addWidget(tstart_button)
        tstart_button.setVisible(False)
        

        self.ai_output = QLabel("")
        self.ai_output.setWordWrap(True)
        self.layout.addWidget(self.ai_output)

        self.central_widget.setLayout(self.layout)
        menubar = self.menuBar()
        emi_menu = menubar.addMenu('&Emilia')
        menubar.addMenu('                                                     ')
        ver_menu = menubar.addMenu('&Версия: ' + version)

        issues = QAction(QIcon('github.png'), '&Сообщить об ошибке', self)
        issues.triggered.connect(self.issuesopen)
        emi_menu.addAction(issues)

        debug = QAction(QIcon('github.png'), '&Debug', self)
        debug.triggered.connect(self.debugfun)
        ver_menu.addAction(debug)

        visibletextmode = QAction('&Активировать текстовый режим', self)
        emi_menu.addAction(visibletextmode)

        visiblevoicemode = QAction('&Активировать голосовой режим', self)
        visiblevoicemode.setEnabled(False)
        emi_menu.addAction(visiblevoicemode)

        visibletextmode.triggered.connect(self.hidetext)
        visiblevoicemode.triggered.connect(self.hidevoice)
        aboutemi = QAction(QIcon('emilia.png'), '&Об Emilia', self)
        aboutemi.triggered.connect(self.about)
        emi_menu.addAction(aboutemi)

    def issuesopen(self):
        webbrowser.open("https://github.com/Kajitsy/Soul-of-Waifu-Fork/issues")

    def hidevoice(self):
        tstart_button.setVisible(False)
        user_aiinput.setVisible(False)
        visiblevoicemode.setEnabled(False)
        vstart_button.setVisible(True)
        visibletextmode.setEnabled(True)

    def hidetext(self):
        vstart_button.setVisible(False)
        visibletextmode.setEnabled(False)
        tstart_button.setVisible(True)
        user_aiinput.setVisible(True)
        visiblevoicemode.setEnabled(True)

    def about(self):
        msg = QMessageBox()
        msg.setWindowTitle("Об Emilia")
        msg.setWindowIcon(QIcon('emilia.png'))
        pixmap = QPixmap('emilia.png').scaled(64, 64)
        msg.setIconPixmap(pixmap)
        text = "Emilia - проект с открытым исходным кодом, являющийся графическим интерфейсом для <a href='https://github.com/jofizcd/Soul-of-Waifu'>Soul of Waifu</a>. На данный момент вы используете версию " + version + ", и она полностью бесплатно распространяется на <a href='https://github.com/Kajitsy/Soul-of-Waifu-Fork'>GitHub</a>"
        msg.setText(text)
        msg.exec()
        self.central_widget.setLayout(self.layout)

    async def main(self):
        while True:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.user_input.setText("Пользователь: Говорите...")
                audio = recognizer.listen(source)
            try:
                msg1 = recognizer.recognize_google(audio, language="ru-RU")
            except sr.UnknownValueError:
                self.user_input.setText("Скажите ещё раз...")
                continue
            self.ai_output.setText("Ответ: генерация...")
            chat = await PyAsyncCAI(client).chat2.get_chat(char)
            author = {'author_id': chat['chats'][0]['creator_id']}
            self.user_input.setText("Пользователь: " + msg1)
            async with PyAsyncCAI(client).connect() as chat2:
                data = await chat2.send_message(
                    char, chat['chats'][0]['chat_id'],
                    msg1, author
                )
            textil = data['turn']['candidates'][0]['raw_content']
            translation = await Translator().translate(textil, targetlang="ru")
            nums = numbers_to_words(translation.text)
            model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
            model.to(device)
            audio = model.apply_tts(text=nums,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo)
            self.ai_output.setText("Ответ: " + translation.text)
            sd.play(audio, sample_rate)
            time.sleep(len(audio - 5) / sample_rate)
            sd.stop()
        
    async def maintext(self):
        self.user_input.setText("Пользователь: ")
        msg1 = user_aiinput.text()
        chat = await PyAsyncCAI(client).chat2.get_chat(char)
        author = {'author_id': chat['chats'][0]['creator_id']}
        self.ai_output.setText("Ответ: генерация...")
        async with PyAsyncCAI(client).connect() as chat2:
            data = await chat2.send_message(
                char, chat['chats'][0]['chat_id'],
                msg1, author
            )
        textil = data['turn']['candidates'][0]['raw_content']
        translation = await Translator().translate(textil, targetlang="ru")
        nums = numbers_to_words(translation.text)
        model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        model.to(device)
        audio = model.apply_tts(text=nums,
                                speaker=speaker,
                                sample_rate=sample_rate,
                                put_accent=put_accent,
                                put_yo=put_yo)
        self.ai_output.setText("Ответ: " + translation.text)
        sd.play(audio, sample_rate)
        time.sleep(len(audio - 5) / sample_rate)
        sd.stop()

    def start_main(self, mode):
        if mode == "voice":
            threading.Thread(target=lambda: asyncio.run(self.main())).start()
            for i in range(self.layout.count()):
                widget = self.layout.itemAt(i).widget()
                widget.setVisible(False)
                self.user_input.setVisible(True)
                self.ai_output.setVisible(True)
        elif mode == "text":
            threading.Thread(target=lambda: asyncio.run(self.maintext())).start()

    def load_config(self):
        if debugmode:
            print("Настройки загружены")
        if os.path.exists('config.json'):
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
                self.char_entry.setText(config.get('char', ''))
                self.client_entry.setText(config.get('client', ''))
                self.speaker_entry.setText(config.get('speaker', ''))
                global char, client, speaker
                char = config.get('char', '')
                client = config.get('client', '')
                speaker = config.get('speaker', '')

    def setup_config(self, char_entry, client_entry, speaker_entry):
        if debugmode:
            print("Настройки сохранены")
        global char, client, speaker
        char = char_entry.text()
        client = client_entry.text()
        speaker = speaker_entry.text()
        config = {
            "char": char,
            "client": client,
            "speaker": speaker
        }

        with open('config.json', 'w') as config_file:
            json.dump(config, config_file)

    def debugfun(self):
        global version
        version = "Debug"
        self.setWindowTitle("Emilia Debug")
        msg = QMessageBox()
        msg.setStyleSheet("QMessageBox {background-color: red;}")
        msg.setWindowTitle("Emilia Error")
        msg.setWindowIcon(QIcon('emilia.png'))
        pixmap = QPixmap('emilia.png').scaled(64, 64)
        msg.setIconPixmap(pixmap)
        text = "Зачем ты здесь что-то ищешь?\nПонимаешь что здесь ничего нет?\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nНет?"
        msg.setText(text)
        msg.exec()
        self.central_widget.setLayout(self.layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle('Fusion') #если нужна тёмная тема
    window = EmiliaGUI()
    window.setFixedWidth(300)
    window.setWindowIcon(QIcon("emilia.png"))
    window.show()
    sys.exit(app.exec())