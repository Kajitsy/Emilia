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
import datetime
import sounddevice as sd
import google.generativeai as genai
import speech_recognition as sr
from gpytranslate import Translator
from characterai import aiocai
from num2words import num2words
from PySide6.QtWidgets import QHBoxLayout, QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtCore import QLocale, Qt
from win32mica import ApplyMica, MicaStyle, MicaTheme

## Изменить тему со светлой на тёмную либо наоборот
def micatheme(self):
    self.setAttribute(Qt.WA_TranslucentBackground)
    ApplyMica(self.winId(), MicaTheme.LIGHT, MicaStyle.DEFAULT) ##Светлая тема
    # ApplyMica(self.winId(), MicaTheme.DARK, MicaStyle.DEFAULT) ##Тёмная тема





locale = QLocale.system().name()

def load_translations(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Translation file not found: {filename}\nUsing en_US.json")
        with open("locales/en_US.json", "r", encoding="utf-8") as f:
            return json.load(f)

def tr(context, text):
    if context in translations and text in translations[context]:
        return translations[context][text]
    else:
        return text 

build = "243004"
version = f"exc{build}"
pre = "True"
local_file = 'voice.pt'
sample_rate = 48000
put_accent = True
put_yo = True
devmode = "false"

def writeconfig(config, value, pup):
        try:
            with open(config, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({value: pup})
        with open(config, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

if os.path.exists('config.json'):
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        aitype = config.get('aitype', '')
        if aitype == "gemini":
            aitype = "gemini"
        else:
            aitype = "charai"
        theme = config.get('theme', '')
        backcolor = config.get('backgroundcolor', "")
        buttoncolor = config.get('buttoncolor', "")
        buttontextcolor = config.get('buttontextcolor', "")
        labelcolor = config.get('labelcolor', "")
        lang = config.get('language', locale)
        deviceft = config.get('devicefortorch', '')
        if deviceft == "cpu":
            devicefortorch = deviceft
        else:
            devicefortorch = 'cuda'
else:
    guitheme = 'windowsvista'
    theme = "white"
    aitype = "charai"
    devicefortorch = 'cuda'
    backcolor = ""
    buttoncolor = ""
    buttontextcolor = ""
    labelcolor = ""
    lang = locale

translations = load_translations(f"locales/{lang}.json")
gendevice = torch.device(devicefortorch)
#Иконки
if pre == "True":
    emiliaicon = './images/premilia.png'
else:
    emiliaicon = './images/emilia.png'
googleicon = './images/google.png'
charaiicon = './images/charai.png'
githubicon = './images/github.png'

if not os.path.exists('voice.pt'):
    if lang == "ru_RU":
        print("Идёт загрузка модели SileroTTS RU")
        print("")
        try:
            torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', "voice.pt")
        except:
            torch.hub.download_url_to_file('https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/tts_models/v4_ru.pt', "voice.pt")
        print("_____________________________________________________")
        print("ГОТОВО, ПРОСТИТЕ")
    else:
        print("The SileroTTS EN model is being loaded")
        print("")
        try:
            torch.hub.download_url_to_file('https://models.silero.ai/models/tts/en/v3_en.pt', "voice.pt")
        except:
            torch.hub.download_url_to_file('https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/tts_models/v3_en.pt', "voice.pt")
        print("_____________________________________________________")
        print("DONE, SORRY")

def numbers_to_words(text):
    try:
        def _conv_num(match):
            if lang == "ru_RU":
                return num2words(int(match.group()), lang='ru')
            else:
                return num2words(int(match.group()), lang='en')
        return re.sub(r'\b\d+\b', _conv_num, text)
    except Exception as e:
        print(tr("MainWinow", 'noncriterror') + {e})
        return text

class EmiliaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emilia")
        micatheme(self)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        global tstart_button, user_aiinput, vstart_button, visibletextmode, visiblevoicemode, issues
        if aitype == "gemini":
            token_label = QLabel(tr("MainWindow", "geminitoken"))
            self.layout.addWidget(token_label)
            self.token_entry = QLineEdit()
            self.token_entry.setStyleSheet("background: transparent; border: transparent; padding: 5px;")
            self.token_entry.setPlaceholderText(tr("MainWindow", "token"))
            self.layout.addWidget(self.token_entry)
        elif aitype == "charai":
            hlayout = QHBoxLayout()
            char_label = QLabel(tr("MainWindow", "characterid"))
            char_label.setStyleSheet("background: transparent; border: transparent; padding: 5px;")
            char_label.setWordWrap(True)
            hlayout.addWidget(char_label)
            self.char_entry = QLineEdit()
            hlayout.addWidget(self.char_entry)
            self.char_entry.setPlaceholderText("ID...")
            self.char_entry.setStyleSheet("background: transparent; border: transparent; padding: 5px;")
            client_label = QLabel(tr("MainWindow", "charactertoken"))
            client_label.setWordWrap(True)
            hlayout.addWidget(client_label)
            self.client_entry = QLineEdit()
            hlayout.addWidget(self.client_entry)
            self.client_entry.setPlaceholderText(tr("MainWindow", "token"))
            self.client_entry.setStyleSheet("background: transparent; border: transparent; padding: 5px;")
            self.layout.addLayout(hlayout)
        speaker_label = QLabel(tr("MainWindow", "voice"))
        self.layout.addWidget(speaker_label)
        self.speaker_entry = QLineEdit()
        self.speaker_entry.setStyleSheet("background: transparent; border: transparent; padding: 5px;")
        self.layout.addWidget(self.speaker_entry)
        self.speaker_entry.setPlaceholderText(tr("MainWindow", "voices"))

        self.microphone = ""
        self.selected_device_index = ""

        self.load_config()

        save_button = QPushButton(tr("MainWindow", "save"))
        if aitype == "charai":
            save_button.clicked.connect(lambda: self.charsetupconfig(self.char_entry, self.client_entry, self.speaker_entry))
        elif aitype == "gemini": 
            save_button.clicked.connect(lambda: self.geminisetupconfig(self.token_entry, self.speaker_entry))
        save_button.setStyleSheet("background: transparent; border: transparent; padding: 5px;")
        self.layout.addWidget(save_button)

        vstart_button = QPushButton(tr("MainWindow", "start"))
        vstart_button.clicked.connect(lambda: self.start_main("voice"))
        vstart_button.setStyleSheet("background: transparent; border: transparent; padding: 5px;")
        self.layout.addWidget(vstart_button)

        self.user_input = QLabel("")
        self.user_input.setWordWrap(True)
        self.layout.addWidget(self.user_input)
        
        user_aiinput = QLineEdit()
        user_aiinput.setPlaceholderText(tr("MainWindow", "textmodeinput"))
        self.layout.addWidget(user_aiinput)
        user_aiinput.setVisible(False)

        tstart_button = QPushButton(tr("MainWindow", "starttext"))
        tstart_button.clicked.connect(lambda: self.start_main("text"))
        self.layout.addWidget(tstart_button)
        tstart_button.setVisible(False)

        self.ai_output = QLabel("")
        self.ai_output.setWordWrap(True)
        self.layout.addWidget(self.ai_output)

        self.central_widget.setLayout(self.layout)
        menubar = self.menuBar()
        emi_menu = menubar.addMenu('&Emilia')

        if aitype == "charai":
            getcharaitoken = QAction(QIcon(charaiicon), tr("MainWindow", 'gettoken'), self)
        elif aitype == "gemini":
            getcharaitoken = QAction(QIcon(googleicon), tr("MainWindow", 'gettoken'), self)
        getcharaitoken.triggered.connect(lambda: self.gettoken())

        visibletextmode = QAction(tr("MainWindow", 'usetextmode'), self)
        emi_menu.addAction(visibletextmode)

        visiblevoicemode = QAction(tr("MainWindow", 'usevoicemode'), self)
        emi_menu.addAction(visiblevoicemode)
        visiblevoicemode.setVisible(False)

        deviceselect = QMenu(tr("MainWindow", 'voicegendevice'), self)
        emi_menu.addMenu(deviceselect)

        usecpumode = QAction(tr("MainWindow", 'usecpu'), self)
        usecpumode.triggered.connect(lambda: self.devicechange('cpu'))
        deviceselect.addAction(usecpumode)

        usegpumode = QAction(tr("MainWindow", 'usegpu'), self)
        usegpumode.triggered.connect(lambda: self.devicechange('cuda'))
        deviceselect.addAction(usegpumode)

        self.recognizer = sr.Recognizer()
        self.mic_list = [
            mic_name for mic_name in sr.Microphone.list_microphone_names()
            if any(keyword in mic_name.lower() for keyword in ["microphone", "mic", "input"])
        ]

        mic_menu = emi_menu.addMenu(tr("MainWindow", 'inputdevice'))

        for index, mic_name in enumerate(self.mic_list):
            action = QAction(mic_name, self)
            action.triggered.connect(lambda checked, i=index: self.set_microphone(i))
            mic_menu.addAction(action)

        outputdeviceselect = QMenu(tr("MainWindow", 'outputdevice'), self)
        emi_menu.addMenu(outputdeviceselect)

        self.unique_devices = {}
        for dev in sd.query_devices():
            if dev["max_output_channels"] > 0 and dev["name"] not in self.unique_devices:
                self.unique_devices[dev["name"]] = dev

        for index, (name, device) in enumerate(self.unique_devices.items()):
            action = QAction(name, self)
            action.triggered.connect(lambda checked, i=index: self.set_output_device(i))
            outputdeviceselect.addAction(action)

        changelanguage = QAction(tr("MainWindow", 'changelanguage'), self)
        if lang == "en_US" or lang == "":
            changelanguage.triggered.connect(lambda: self.geminiuse(self.langchange("ru_RU")))
        elif lang == "ru_RU":
            changelanguage.triggered.connect(lambda: self.geminiuse(self.langchange("en_US")))
        emi_menu.addAction(changelanguage)

        serviceselect = QMenu(tr("MainWindow", 'changeai'), self)
        emi_menu.addMenu(serviceselect)

        usegemini = QAction(QIcon(googleicon), tr("MainWindow", 'usegemini'), self)
        usegemini.triggered.connect(lambda: self.geminiuse(self.speaker_entry))
        serviceselect.addAction(usegemini)

        usecharai = QAction(QIcon(charaiicon), tr("MainWindow", 'usecharacterai'), self)
        usecharai.triggered.connect(lambda: self.charaiuse(self.speaker_entry))
        serviceselect.addAction(usecharai)

        if aitype == "charai":
            emi_menu.addAction(getcharaitoken)
            usecharai.setEnabled(False)
            usegemini.setEnabled(True)
            charselect = menubar.addMenu(tr("MainWindow", 'charchoice'))
            chareditopen = QAction(tr("MainWindow", 'openchareditor'), self)
            chareditopen.triggered.connect(lambda: subprocess.call(["python", "charedit.py"]))
            charselect.addAction(chareditopen)
            if os.path.exists('config.json'):
                def create_action(key, value):
                    def action_func():
                        self.open_json(value['char'], value['voice'])
                    action = QAction(f'&{key}', self)
                    action.triggered.connect(action_func)
                    return action
                try:
                    with open('data.json', 'r', encoding='utf-8') as file:
                        data = json.load(file)
                except FileNotFoundError:
                    data = {}
                except json.JSONDecodeError:
                    data = {}
                for key, value in data.items():
                    action = create_action(key, value)
                    charselect.addAction(action)
        elif aitype == "gemini":
            usegemini.setEnabled(False)
            usecharai.setEnabled(True)

        if aitype == "charai":
            spacer = menubar.addMenu(tr("MainWindow", "spacerwincharai"))
        elif aitype == "gemini":
            spacer = menubar.addMenu(tr("MainWindow", "spacerwingemini"))
        spacer.setEnabled(False)

        ver_menu = menubar.addMenu(tr("MainWindow", 'version') + version)
        ver_menu.setEnabled(False)

        visibletextmode.triggered.connect(lambda: self.modehide("voice"))
        visiblevoicemode.triggered.connect(lambda: self.modehide("text"))

        issues = QAction(QIcon(githubicon), tr("MainWindow", 'BUUUG'), self)
        issues.triggered.connect(self.issuesopen)
        emi_menu.addAction(issues)

        aboutemi = QAction(QIcon(emiliaicon), tr("MainWindow", 'aboutemi'), self)
        aboutemi.triggered.connect(self.about)
        emi_menu.addAction(aboutemi)

    def set_microphone(self, index):
        self.microphone = sr.Microphone(device_index=index)
        print(f"Выбран микрофон: {self.mic_list[index]}")

    def set_output_device(self, index):
        device = list(self.unique_devices.values())[index]
        sd.default.device = device["index"]
        self.selected_device_index = index

    def open_json(self, value, pup):
        global char, speaker
        char = value
        speaker = pup
        self.char_entry.setText(char)
        self.speaker_entry.setText(speaker)
    
    def devicechange(self, device):
        global devicefortorch
        devicefortorch = device
        writeconfig('config.json', "devicefortorch", device)

    def langchange(self, lang):
        writeconfig('config.json', "language", lang)
        os.remove("voice.pt")
        os.execv(sys.executable, ['python'] + sys.argv)

    def gettoken(self):
        if aitype == "charai":
            subprocess.call(["python", "auth.py"])
        elif aitype == "gemini":
            webbrowser.open("https://aistudio.google.com/app/apikey")
        self.load_config()

    def issuesopen(self):
        webbrowser.open("https://github.com/Kajitsy/Emilia/issues")

    def modehide(self, mode):
        if mode == "text":
            visiblevoicemode.setVisible(False)
            visibletextmode.setVisible(True)
            tstart_button.setVisible(False)
            user_aiinput.setVisible(False)
            vstart_button.setVisible(True)
        elif mode == "voice":
            visibletextmode.setVisible(False)
            visiblevoicemode.setVisible(True)
            vstart_button.setVisible(False)
            tstart_button.setVisible(True)
            user_aiinput.setVisible(True)   

    def geminiuse(self, speaker_entry):
        global aitype
        aitype = "gemini"
        self.globalsetupconfig(speaker_entry)
        os.execv(sys.executable, ['python'] + sys.argv)

    def charaiuse(self, speaker_entry):
        global aitype
        aitype = "charai"
        self.globalsetupconfig(speaker_entry)
        os.execv(sys.executable, ['python'] + sys.argv)

    def about(self):
        msg = QMessageBox()
        micatheme(msg)
        if pre == "True":
            msg.setWindowTitle(tr("About", "aboutemi") + build)
        else:
            msg.setWindowTitle(tr("About", "aboutemi"))
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        language = tr("About", "languagefrom")
        whatsnew = tr("About", "newin") + version + tr("About", "whatsnew")
        otherversions = tr("About", "viewallreleases")
        text = tr("About", "emiopenproject") + version + tr("About", "usever") + language + whatsnew + otherversions
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
        dtime = "%m-%d %H:%M:%S"
        data.update({datetime.datetime.now().strftime(dtime): text})

        with open('chat_history.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def chating(self, textinchat):
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=[])
        chat.send_message(f"Here's our chat history: {self.reading_chat_history()}")
        for chunk in chat.send_message(textinchat):
            continue
        return chunk.text

    async def main(self):
        while True:
            recognizer = sr.Recognizer()
            self.user_input.setText(tr("Main", "speakup"))
            if self.microphone != "":
                with self.microphone as source:
                    audio = recognizer.listen(source)
            else: 
                with sr.Microphone() as source:
                    audio = recognizer.listen(source)
            try:
                if lang == "ru_RU":
                    msg1 = recognizer.recognize_google(audio, language="ru-RU")
                else:
                    msg1 = recognizer.recognize_google(audio, language="en-US")
            except sr.UnknownValueError:
                self.user_input.setText(tr("Main", "sayagain"))
                continue
            self.user_input.setText(tr("Main", "user") + msg1)
            self.ai_output.setText(tr("Main", "emigen"))
            if aitype == "charai":
                token = aiocai.Client(client)
                chatid = await token.get_chat(char)
                async with await token.connect() as chat:
                    messagenotext = await chat.send_message(char, chatid.chat_id, msg1)
                    message = messagenotext.text
            elif aitype == "gemini":
                try:
                    message = self.chating(msg1)
                    self.writing_chat_history(f"User: {msg1}")
                    self.writing_chat_history(f"AI: {message}")
                except Exception as e:
                    if e.code == 400 and "User location is not supported" in e.message:
                        self.ai_output.setText(tr("Errors", 'Gemini 400'))
            if lang == "ru_RU":
                translation = await Translator().translate(message, targetlang="ru")
                nums = numbers_to_words(translation.text)
            else:
                nums = numbers_to_words(message.text)
            model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
            model.to(gendevice)
            audio = model.apply_tts(text=nums,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo)
            self.ai_output.setText(tr("Main", "emimessage") + translation.text)
            if self.selected_device_index != "":
                device = list(self.unique_devices.values())[self.selected_device_index]
                sd.play(audio, sample_rate, device=device["index"])
            else: 
                sd.play(audio, sample_rate)
            time.sleep(len(audio - 5) / sample_rate)
            sd.stop()
        
    async def maintext(self):
        self.user_input.setText(tr("Main", "user"))
        msg1 = user_aiinput.text()
        self.ai_output.setText(tr("Main", "emigen"))
        if aitype == "charai":
            token = aiocai.Client(client)
            chatid = await token.get_chat(char)
            async with await token.connect() as chat:
                messagenotext = await chat.send_message(char, chatid.chat_id, msg1)
                message = messagenotext.text
        elif aitype == "gemini":
            try:
                message = self.chating(msg1)
                self.writing_chat_history(f"User: {msg1}")
                self.writing_chat_history(f"AI: {message}")
            except Exception as e:
                if e.code == 400 and "User location is not supported" in e.message:
                    self.ai_output.setText(tr("Errors", 'Gemini 400'))
        if lang == "ru_RU":
            translation = await Translator().translate(message, targetlang="ru")
            nums = numbers_to_words(translation.text)
        else:
            nums = numbers_to_words(message.text)
        nums = numbers_to_words(translation.text)
        model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        model.to(gendevice)
        audio = model.apply_tts(text=nums,
                                speaker=speaker,
                                sample_rate=sample_rate,
                                put_accent=put_accent,
                                put_yo=put_yo)
        self.ai_output.setText(tr("Main", "emimessage") + translation.text)
        if self.selected_device_index != "":
            device = list(self.unique_devices.values())[self.selected_device_index]
            sd.play(audio, sample_rate, device=device["index"])
        else: 
            sd.play(audio, sample_rate)
        time.sleep(len(audio - 5) / sample_rate)
        sd.stop()

    def start_main(self, mode):
        if self.speaker_entry == "":
            self.ai_output.setText(tr("Errors", "nonvoice"))
        else:
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
        global speaker, char, client, token, devicefortorch
        if aitype == "charai":
            if os.path.exists('charaiconfig.json'):
                with open('charaiconfig.json', 'r') as config_file:
                    config = json.load(config_file)
                    char = config.get('char', '')
                    client = config.get('client', '')
                    self.char_entry.setText(char)
                    self.client_entry.setText(client)
        elif aitype == "gemini":
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
                devicefortorch = config.get('devicefortorch', '')
                self.speaker_entry.setText(speaker)

    def charsetupconfig(self, char_entry, client_entry, speaker_entry):
        global char, client
        char = char_entry.text()
        client = client_entry.text()
        writeconfig('charaiconfig.json', "char", char)
        writeconfig('charaiconfig.json', "client", client)
        self.globalsetupconfig(speaker_entry)

    def geminisetupconfig(self, token_entry, speaker_entry):
        global token, aitype
        token = token_entry.text()
        writeconfig('geminiconfig.json', "token", token)
        self.globalsetupconfig(speaker_entry)
        genai.configure(api_key=token)

    def globalsetupconfig(self, speaker_entry):
        global speaker, aitype, devicefortorch
        speaker = speaker_entry.text()
        writeconfig('config.json', "speaker", speaker)
        writeconfig('config.json', "aitype", aitype)
        writeconfig('config.json', "theme", theme)
        writeconfig('config.json', "devicefortorch", devicefortorch)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = EmiliaGUI()
    window.setFixedWidth(300)
    window.setMinimumHeight(250)
    window.setWindowIcon(QIcon(emiliaicon))
    window.show()
    sys.exit(app.exec())