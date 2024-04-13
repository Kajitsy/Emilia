import os
import asyncio
import threading
import torch
import time
import re
import json
import sys
import subprocess
import webbrowser
import sounddevice as sd
import google.generativeai as genai
import speech_recognition as sr
from gpytranslate import Translator
from characterai import aiocai
from num2words import num2words
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap

ver = "2.1"
build = "241304.1"
pre = "True"
if pre == "True":
    version = "pre" + ver
else:
    version = ver
local_file = 'russian.pt'
device = torch.device('cuda')
sample_rate = 48000
put_accent = True
put_yo = True
devmode = "false"

def numbers_to_words(text):
    def _conv_num(match):
        return num2words(int(match.group()), lang='ru')
    return re.sub(r'\b\d+\b', _conv_num, text)


if os.path.exists('config.json'):
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        aitype = config.get('aitype', '')
        if aitype == "gemini":
            aitype = "gemini"
        else:
            aitype = "charai"
        theme = config.get('theme', '')
        if theme == "dark":
            guitheme = 'Fusion'
        else:
            guitheme = 'windowsvista'
else:
    guitheme = 'windowsvista'
    aitype = "charai"
#Иконки
if pre == "True":
    emiliaicon = './images/premilia.png'
else:
    emiliaicon = './images/emilia.png'
googleicon = './images/google.png'
charaiicon = './images/charai.png'
if guitheme == 'Fusion':
    themeicon = './images/sun.png'
    githubicon = './images/github_white.png'
else:
    themeicon = './images/moon.png'
    githubicon = './images/github.png'

class EmiliaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emilia")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        global tstart_button, user_aiinput, vstart_button, visibletextmode, visiblevoicemode, issues
        if aitype == "gemini":
            token_label = QLabel("Gemini Token:")
            self.layout.addWidget(token_label)
            self.token_entry = QLineEdit()
            self.layout.addWidget(self.token_entry)
            self.token_entry.setPlaceholderText("Ваш Gemini токен...")
        else:
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
        if aitype == "charai":
            save_button.clicked.connect(lambda: self.charsetupconfig(self.char_entry, self.client_entry, self.speaker_entry))
        else: 
            save_button.clicked.connect(lambda: self.geminisetupconfig(self.token_entry, self.speaker_entry))
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
        if guitheme == 'windowsvista':
            spacer = menubar.addMenu('                                               ')
        else:
            spacer = menubar.addMenu('                                                 ')
        spacer.setEnabled(False)
        ver_menu = menubar.addMenu('&Версия: ' + version)

        debug = QAction(QIcon('./images/emilia.png'), '&Debug', self)
        debug.triggered.connect(self.debugfun)
        ver_menu.addAction(debug)

        getcharaitoken = QAction(QIcon(charaiicon), '&Получить Char.AI токен', self)
        getcharaitoken.triggered.connect(lambda: self.gettoken())

        changethemeaction = QAction(QIcon(themeicon), '&Сменить тему', self)
        if guitheme == 'Fusion':
            changethemeaction.triggered.connect(lambda: self.change_theme("white"))
        else:
            changethemeaction.triggered.connect(lambda: self.change_theme("dark"))
        emi_menu.addAction(changethemeaction)

        visibletextmode = QAction('&Активировать текстовый режим', self)
        emi_menu.addAction(visibletextmode)

        visiblevoicemode = QAction('&Активировать голосовой режим', self)
        visiblevoicemode.setEnabled(False)
        emi_menu.addAction(visiblevoicemode)

        serviceselect = QMenu('&Смена ИИ-сервиса', self)
        emi_menu.addMenu(serviceselect)

        usegemini = QAction(QIcon(googleicon), '&Использовать Gemini', self)
        usegemini.triggered.connect(lambda: self.geminiuse(self.speaker_entry))
        serviceselect.addAction(usegemini)

        usecharai = QAction(QIcon(charaiicon), '&Использовать Character.AI', self)
        usecharai.triggered.connect(lambda: self.charaiuse(self.speaker_entry))
        serviceselect.addAction(usecharai)

        if aitype == "charai":
            emi_menu.addAction(getcharaitoken)
            usecharai.setEnabled(False)
            usegemini.setEnabled(True)
        else:
            usegemini.setEnabled(False)
            usecharai.setEnabled(True)
        
        visibletextmode.triggered.connect(self.hidetext)
        visiblevoicemode.triggered.connect(self.hidevoice)

        issues = QAction(QIcon(githubicon), '&Сообщить об ошибке', self)
        issues.triggered.connect(self.issuesopen)
        emi_menu.addAction(issues)

        aboutemi = QAction(QIcon(emiliaicon), '&Об Emilia', self)
        aboutemi.triggered.connect(self.about)
        emi_menu.addAction(aboutemi)

    def gettoken(self):
        subprocess.call(["python", "auth.py"])
        self.load_config()

    def issuesopen(self):
        webbrowser.open("https://github.com/Kajitsy/Emilia/issues")

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

    def geminiuse(self, speaker_entry):
        global aitype
        aitype = "gemini"
        config = {
            "speaker": speaker_entry.text(),
            "theme": theme,
            "aitype": aitype
        }
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file)
        os.execv(sys.executable, ['python'] + sys.argv)

    def charaiuse(self, speaker_entry):
        global aitype
        aitype = "charai"
        config = {
            "speaker": speaker_entry.text(),
            "theme": theme,
            "aitype": aitype
        }
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file)
        os.execv(sys.executable, ['python'] + sys.argv)

    def change_theme(self, theme):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({"theme": theme})
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.execv(sys.executable, ['python'] + sys.argv)

    def about(self):
        msg = QMessageBox()
        if pre == "True":
            msg.setWindowTitle("Об Emilia " + build)
        else:
            msg.setWindowTitle("Об Emilia")
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        whatsnew = "Что нового в " + version + ": <br>• Проект на GitHub переименован с Soul-Of-Waifu-Work на Emilia <br>• Добавлена возможность общения с Google Gemini 1.5 Pro<br>• Добавлена тёмная тема<br>• Добавлена возможность получения токена без необходимости искать его в DevTools"
        otherversions = "<br><br><a href='https://github.com/Kajitsy/Emilia/releases'>Чтобы посмотреть все прошлые релизы кликай сюда</a>"
        text = "Emilia - проект с открытым исходным кодом, являющийся графическим интерфейсом для <a href='https://github.com/jofizcd/Soul-of-Waifu'>Soul of Waifu</a>.<br> На данный момент вы используете версию " + version + ", и она полностью бесплатно распространяется на <a href='https://github.com/Kajitsy/Emilia'>GitHub</a><br><br>" + whatsnew + otherversions
        msg.setText(text)
        msg.exec()
        self.central_widget.setLayout(self.layout)

    def reading_chat_history(self):
      with open('chat_history.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
      return data

    def writing_chat_history(self, text):
        try:
            with open('chat_history.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}

        data.update(text)

        with open('chat_history.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def chating(self, textinchat):
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=[])
        # chat.send_message(first_message) #Это функция из будущего.
        if devmode == "True":
            chat.send_message("Вот наша с тобой история чата: " + self.reading_chat_history())
        for chunk in chat.send_message(textinchat):
            continue
        return chunk.text

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
            self.user_input.setText("Пользователь: " + msg1)
            if devmode == "true":
                self.writing_chat_history({"Пользователь: ": msg1})
            self.ai_output.setText("Ответ: генерация...")
            if aitype == "charai":
                token = aiocai.Client(client)
                chatid = await token.get_chat(char)
                async with await token.connect() as chat:
                    messagenotext = await chat.send_message(char, chatid.chat_id, msg1)
                    message = messagenotext.text
            else:
                message = self.chating(msg1)
            if devmode == "true":
                self.writing_chat_history({"AI: ": message})
            translation = await Translator().translate(message, targetlang="ru")
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
        if devmode == "true":
            self.writing_chat_history({"Пользователь: ": msg1})
        self.ai_output.setText("Ответ: генерация...")
        if aitype == "charai":
            token = aiocai.Client(client)
            chatid = await token.get_chat(char)
            async with await token.connect() as chat:
                messagenotext = await chat.send_message(char, chatid.chat_id, msg1)
                message = messagenotext.text
        else:
            message = self.chating(msg1)
        if devmode == "true":
            self.writing_chat_history({"AI: ": message})
        translation = await Translator().translate(message, targetlang="ru")
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
        global speaker, char, client, token
        if aitype == "charai":
            if os.path.exists('charaiconfig.json'):
                with open('charaiconfig.json', 'r') as config_file:
                    config = json.load(config_file)
                    char = config.get('char', '')
                    client = config.get('client', '')
                    self.char_entry.setText(char)
                    self.client_entry.setText(client)
        else:
            if os.path.exists('geminiconfig.json'):
                with open('geminiconfig.json', 'r') as config_file:
                    config = json.load(config_file)
                    token = config.get('token', '')
                    self.token_entry.setText(token)
                    genai.configure(api_key=token)
        if os.path.exists('config.json'):
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
                speaker = config.get('speaker', '')
                self.speaker_entry.setText(speaker)

    def charsetupconfig(self, char_entry, client_entry, speaker_entry):
        global char, client
        char = char_entry.text()
        client = client_entry.text()
        config = {
            "char": char,
            "client": client
        }

        with open('charaiconfig.json', 'w') as config_file:
            json.dump(config, config_file)
        self.globalsetupconfig(speaker_entry)

    def geminisetupconfig(self, token_entry, speaker_entry):
        global token, aitype
        token = token_entry.text()
        config = {
            "token": token
        }
        with open('geminiconfig.json', 'w') as config_file:
            json.dump(config, config_file)
        self.globalsetupconfig(speaker_entry)
        genai.configure(api_key=token)

    def globalsetupconfig(self, speaker_entry):
        global speaker, aitype
        speaker = speaker_entry.text()
        config = {
            "speaker": speaker,
            "aitype": aitype,
            "theme": theme
        }

        with open('config.json', 'w') as config_file:
            json.dump(config, config_file)
    
    def debugfun(self):
        global version, devmode
        devmode = "true"
        version = "Debug"
        self.setWindowTitle("Emilia Debug")
        msg = QMessageBox()
        msg.setStyleSheet("QMessageBox {background-color: red; text-color}")
        msg.setWindowTitle("Emilia Error")
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        text = "Зачем ты здесь что-то ищешь?\nПонимаешь что здесь ничего нет?\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nНет?"
        msg.setText(text)
        msg.exec()
        self.central_widget.setLayout(self.layout)
        self.writing_chat_history({"Пользователь: " : "Да"})

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(guitheme)
    window = EmiliaGUI()
    window.setFixedWidth(300)
    window.setWindowIcon(QIcon(emiliaicon))
    window.show()
    sys.exit(app.exec())