import io, os, asyncio, winreg, threading, re, json, sys, webbrowser, ctypes, warnings
import requests, websockets
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import google.generativeai as genai
import modules.eec as EEC
import modules.CustomCharAI as CustomCharAI
from gpytranslate import Translator
from characterai import aiocai, sendCode, authUser
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings, play
from PyQt6.QtWidgets import (QColorDialog,
                             QComboBox, 
                             QCheckBox,
                             QHBoxLayout, 
                             QApplication, 
                             QMainWindow, 
                             QLabel, QLineEdit, 
                             QPushButton, 
                             QVBoxLayout, 
                             QWidget, 
                             QMenu, 
                             QListWidget, 
                             QListWidgetItem)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor
from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtMultimedia import QMediaDevices
from modules.config import getconfig, writeconfig, resource_path 
from modules.auto_update import AutoUpdate
from modules.character_search import CharacterSearch, CharacterWidget, NewCharacterEditor, ChatWithCharacter
from modules.translations import translations
from modules.other import MessageBox, Emote_File, ChatDataWorker

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('emilia.app')
except Exception as e:
    print(f"Ctypes error {e}")

warnings.filterwarnings("ignore", category=DeprecationWarning)

version = "2.2.4"
build = "20240823"
pre = True
sample_rate = 48000

# Global Variables
autoupdate_enable = getconfig('autoupdate_enable', False)
vtube_enable = getconfig('vtubeenable', False)
lang = getconfig('language', QLocale.system().name())
aitype = getconfig('aitype', 'charai')
tts = getconfig('tts', 'charai')
theme = getconfig('theme', 'windowsvista')
iconcolor = getconfig('iconcolor', 'black')
backcolor = getconfig('backgroundcolor')
buttoncolor = getconfig('buttoncolor')
buttontextcolor = getconfig('buttontextcolor')
labelcolor = getconfig('labelcolor')
imagesfolder = resource_path('images')
localesfolder = resource_path('locales')
trls = translations(lang, localesfolder)

# Icons
emiliaicon = f'{imagesfolder}/emilia.png'
googleicon = f'{imagesfolder}/google.png'
charaiicon = f'{imagesfolder}/charai.png'
refreshicon = f'{imagesfolder}/refresh.png'
if iconcolor == 'white':
    keyboardicon = f'{imagesfolder}/keyboard_white.png'
    inputicon = f'{imagesfolder}/input_white.png'
    charediticon = f'{imagesfolder}/open_char_editor_white.png'
else:
    keyboardicon = f'{imagesfolder}/keyboard.png'
    inputicon = f'{imagesfolder}/input.png'
    charediticon = f'{imagesfolder}/open_char_editor.png'

if tts == 'charai' and aitype != 'charai':
    tts = 'elevenlabs'
    writeconfig('tts', tts)

print("(｡･∀･)ﾉﾞ")

class FirstLaunch(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia")
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        # First Page

        self.first_launch_notification_label = QLabel(trls.tr('FirstLaunch', 'first_launch_notification_label'))
        self.first_launch_notification_label.setWordWrap(True)
        self.layout.addWidget(self.first_launch_notification_label)

        fphlayout = QHBoxLayout()
        self.layout.addLayout(fphlayout)
        self.first_launch_notification_button_yes = QPushButton(trls.tr('FirstLaunch', 'first_launch_notification_button_yes'))
        self.first_launch_notification_button_yes.clicked.connect(self.second_page)
        fphlayout.addWidget(self.first_launch_notification_button_yes)

        self.first_launch_notification_button_no = QPushButton(trls.tr('FirstLaunch', 'first_launch_notification_button_no'))
        self.first_launch_notification_button_no.clicked.connect(self.first_launch_button_no)
        fphlayout.addWidget(self.first_launch_notification_button_no)
        
        self.central_widget.setLayout(self.layout)

        # Second Page

        self.second_page_widget = QWidget()
        self.second_page_layout = QVBoxLayout()
        self.second_page_widget.setLayout(self.second_page_layout)

        self.autoupdate_layout = QHBoxLayout()
        self.autoupdate = QCheckBox()
        if autoupdate_enable:
            self.autoupdate.setChecked(True)
        self.autoupdate.stateChanged.connect(self.autoupdate_change)

        self.autoupdate_layout.addWidget(QLabel(trls.tr("OptionsWindow", 'automatic_updates')))
        self.autoupdate_layout.addWidget(self.autoupdate)
        self.second_page_layout.addLayout(self.autoupdate_layout)


        self.ttslayout = QHBoxLayout()
        self.ttsselect = QComboBox()
        self.ttsselect.addItems([trls.tr("OptionsWindow", 'character.ai_voices'), "ElevenLabs"])
        self.ttsselect.currentTextChanged.connect(self.ttschange)

        self.ttslabel = QLabel(trls.tr("OptionsWindow", 'select_tts'))
        self.ttslabel.setWordWrap(True)

        self.ttslayout.addWidget(self.ttslabel)
        self.ttslayout.addWidget(self.ttsselect)
        self.second_page_layout.addLayout(self.ttslayout)


        self.vtubelayout = QHBoxLayout()
        self.vtubecheck = QCheckBox()
        if vtube_enable:
            self.vtubecheck.setChecked(True)
        self.vtubecheck.stateChanged.connect(self.vtubechange)
        self.vtubewiki = QPushButton("Wiki")
        self.vtubewiki.clicked.connect(lambda: webbrowser.open("https://github.com/Kajitsy/Emilia/wiki/%D0%98%D1%81%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-VTube-%D0%9C%D0%BE%D0%B4%D0%B5%D0%BB%D1%8C%D0%BA%D0%B8"))

        self.vtubelayout.addWidget(QLabel("VTube Model"))
        self.vtubelayout.addWidget(self.vtubecheck)
        self.vtubelayout.addWidget(self.vtubewiki)
        self.second_page_layout.addLayout(self.vtubelayout)


        try:
            build_number, _ = winreg.QueryValueEx(
                winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"),
                "CurrentBuildNumber")
        except Exception:
            build_number = "0"
        self.theme_layout = QHBoxLayout()
        self.themechange = QComboBox()
        self.themechange.addItems(["Fusion", "Windows Old"])
        if int(build_number) > 22000:
            self.themechange.addItem("Windows 11")
        theme = getconfig('theme', 'windowsvista')
        if theme == 'windowsvista':
            self.themechange.setCurrentIndex(1)
        elif theme == 'windows11':
            self.themechange.setCurrentIndex(2)
        elif theme == 'Fuison':
            self.themechange.setCurrentIndex(0)
        self.themechange.currentTextChanged.connect(self.change_theme)

        self.theme_layout.addWidget(QLabel(trls.tr("OptionsWindow", "select_theme")))
        self.theme_layout.addWidget(self.themechange)
        self.second_page_layout.addLayout(self.theme_layout)


        self.iconcolorlayout = QHBoxLayout()
        self.iconcolorchange = QComboBox()
        self.iconcolorchange.addItems([trls.tr("OptionsWindow", 'white'), trls.tr("OptionsWindow", 'black')])
        iconcolor = getconfig('iconcolor', 'white')
        if iconcolor == 'black':
            self.iconcolorchange.setCurrentIndex(1)
        self.iconcolorchange.currentTextChanged.connect(self.changeiconcolor)

        self.iconcolorlayout.addWidget(QLabel(trls.tr("OptionsWindow", "pick_icon_color")))
        self.iconcolorlayout.addWidget(self.iconcolorchange)
        self.second_page_layout.addLayout(self.iconcolorlayout)

        self.second_page_continue_button = QPushButton("Continue")
        self.second_page_continue_button.clicked.connect(self.second_page_continue)
        self.second_page_layout.addWidget(self.second_page_continue_button)
        
        # Third Page

        self.third_page_widget = QWidget()
        self.third_page_layout = QVBoxLayout()
        self.third_page_widget.setLayout(self.third_page_layout)

        email_layout = QHBoxLayout()
        self.email_label = QLabel(trls.tr("GetToken","your_email"))
        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("example@example.com")

        email_layout.addWidget(self.email_label)
        email_layout.addWidget(self.email_entry)
        self.third_page_layout.addLayout(email_layout)

        self.getlink_button = QPushButton(trls.tr("GetToken", "send_email"))
        self.getlink_button.clicked.connect(lambda: self.getlink())
        self.third_page_layout.addWidget(self.getlink_button)

        self.getlink_button = QPushButton(trls.tr("GetToken", "send_email"))
        self.getlink_button.clicked.connect(self.getlink)

        self.link_layout = QHBoxLayout()
        self.link_label = QLabel(trls.tr("GetToken", "link_from_email"))
        self.link_entry = QLineEdit()
        self.link_entry.setPlaceholderText("https...")

        self.link_layout.addWidget(self.link_label)
        self.link_layout.addWidget(self.link_entry)

        self.gettoken_button = QPushButton(trls.tr("GetToken", "get_token"))
        self.gettoken_button.clicked.connect(self.gettoken)

        # Fourth Page

        self.fourth_page_widget = QWidget()
        self.fourth_page_layout = QVBoxLayout()
        self.fourth_page_widget.setLayout(self.fourth_page_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(trls.tr("CharEditor", 'network_search_input'))
        self.search_input.returnPressed.connect(self.search_and_load)
        self.fourth_page_layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.fourth_page_layout.addWidget(self.list_widget)

        self.add_another_charcter_button = QPushButton(trls.tr("CharEditor", 'add_another_charcter_button'))
        self.add_another_charcter_button.clicked.connect(self.open_NewCharacherEditor)

        self.network_buttons_layout = QVBoxLayout()
        self.network_buttons_layout.addWidget(self.add_another_charcter_button)

        self.central_widget.setLayout(self.layout)

    def closeEvent(self, event):
        Emilia().show()
        super().closeEvent(event)

    def search_and_load(self):
        search_query = self.search_input.text().strip()
        if not search_query:
            return
        try:
            response = requests.get(f'https://character.ai/api/trpc/search.search?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{search_query}%22%7D%7D%7D')
            if response.status_code == 200:
                self.network_data = response.json()
                self.populate_network_list()
                self.setGeometry(300, 300, 800, 400)
            else:
                MessageBox(trls.tr('Errors', 'Label'), f"Error receiving data: {response.status_code}")
        except Exception as e:
            MessageBox(trls.tr('Errors', 'Label'), f"Error when executing the request: {e}")

    def populate_network_list(self):
        self.list_widget.clear()
        if not self.network_data or not isinstance(self.network_data, list):
            return

        for data in self.network_data[0].get("result", {}).get("data", {}).get("json", []):
            self.populate_list(data, "firstlaunch")

        self.add_another_charcter_button.setVisible(False)

    def populate_list(self, data, mode):
        item = QListWidgetItem()
        custom_widget = CharacterWidget(self, data, mode)
        
        item.setSizeHint(custom_widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, custom_widget)

    def open_NewCharacherEditor(self):
        window = NewCharacterEditor()
        window.show()

    def gettoken(self):
        try:
            token = authUser(self.link_entry.text(), self.email_entry.text())
            self.third_page_widget.hide()
            MessageBox(text=trls.tr('FirstLaunch', 'token_saves'))
            writeconfig('client', token, 'charaiconfig.json')
            self.first_launch_notification_label.setText(trls.tr('FirstLaunch', 'third_page'))
            self.layout.addWidget(self.fourth_page_widget)
        except Exception as e:
            MessageBox(trls.tr("Errors", "Label"), trls.tr("Errors", "other") + str(e))

    def getlink(self):
        try:
            sendCode(self.email_entry.text())
            self.email_entry.setEnabled(False)
            self.getlink_button.setEnabled(False)
            self.third_page_layout.addLayout(self.link_layout)
            self.third_page_layout.addWidget(self.gettoken_button)
        except Exception as e:
            MessageBox(trls.tr("Errors", "Label"), trls.tr("Errors", "other") + str(e))

    def second_page_continue(self):
        self.first_launch_notification_label.setText(trls.tr('FirstLaunch', 'use_characterai'))
        self.second_page_widget.setVisible(False)
        self.layout.addWidget(self.third_page_widget)

    def vtubechange(self, state):
        global vtube_enable
        if state == 2:
            vtube_enable = True
        else:
            vtube_enable = False
        writeconfig('vtubeenable', vtube_enable)

    def ttschange(self):
        value = self.ttsselect.currentIndex()
        global tts
        if value == 0:
            tts = 'charai'
        elif value == 1:
            tts = 'elevenlabs'
        writeconfig('tts', tts)

    def change_theme(self):
        value = self.themechange.currentIndex()
        global theme
        if value == 0:
            theme = 'fusion'
        elif value == 1:
            theme = 'windowsvista'
        elif value == 2:
            theme = 'windows11'
        app = QApplication.instance()
        app.setStyle(theme)
        writeconfig('theme', theme)

    def changeiconcolor(self):
        value = self.iconcolorchange.currentIndex()
        global iconcolor, keyboardicon, inputicon, charediticon
        if value == 0:
            keyboardicon =f'{imagesfolder}/keyboard_white.png'
            inputicon = f'{imagesfolder}/input_white.png'
            charediticon = f'{imagesfolder}/open_char_editor_white.png'
            iconcolor = 'white'
        elif value == 1:
            keyboardicon = f'{imagesfolder}/keyboard.png'
            inputicon = f'{imagesfolder}/input.png'
            charediticon = f'{imagesfolder}/open_char_editor.png'
            iconcolor = 'black'
        writeconfig('iconcolor', iconcolor)

    def autoupdate_change(self, state):
        global autoupdate_enable
        if state == 2:
            autoupdate_enable = True
        else:
            autoupdate_enable = False
        writeconfig('autoupdate_enable', autoupdate_enable)

    def second_page(self):
        self.first_launch_notification_label.setText(trls.tr('FirstLaunch', 'second_page'))
        self.first_launch_notification_button_yes.setVisible(False)
        self.first_launch_notification_button_no.setVisible(False)
        self.layout.addWidget(self.second_page_widget)
        self.setMinimumHeight(185)

    def first_launch_button_no(self):
        writeconfig('aitype', 'charai')
        self.close()

class OptionsWindow(QWidget):
    def __init__(self, mainwindow):
        super().__init__()
        self.setWindowTitle("Emilia: Options")
        self.setWindowIcon(QIcon(emiliaicon))
        self.setFixedWidth(450)
        self.setMinimumHeight(150)
        self.trl = "OptionsWindow"

        self.mainwindow = mainwindow
        layout = QHBoxLayout()

        firsthalf = QVBoxLayout()
        self.firsthalf = firsthalf
        secondhalf = QVBoxLayout()

        autoupdatelayout = QHBoxLayout()
        self.autoupdate = QCheckBox()
        if autoupdate_enable:
            self.autoupdate.setChecked(True)
        self.autoupdate.stateChanged.connect(self.autoupdatechange)


        autoupdatelayout.addWidget(QLabel(trls.tr(self.trl, 'automatic_updates')))
        autoupdatelayout.addWidget(self.autoupdate)
        firsthalf.addLayout(autoupdatelayout)


        langlayout = QHBoxLayout()
        self.languagechange = QComboBox()
        self.languagechange.addItems([trls.tr(self.trl, 'english'), trls.tr(self.trl, 'russian')])
        if lang == "ru_RU":
            self.languagechange.setCurrentIndex(1)
        self.languagechange.currentTextChanged.connect(self.langchange)

        langlayout.addWidget(QLabel(trls.tr(self.trl, 'select_language')))
        langlayout.addWidget(self.languagechange)
        firsthalf.addLayout(langlayout)


        self.aitypelayout = QHBoxLayout()
        self.aitypechange = QComboBox()
        self.aitypechange.addItems(["Character.AI", "Google Gemini"])
        if aitype == "gemini":
            self.aitypechange.setCurrentIndex(1)
        self.aitypechange.currentTextChanged.connect(self.aichange)

        self.aitypelayout.addWidget(QLabel(trls.tr("OptionsWindow", 'select_ai')))
        self.aitypelayout.addWidget(self.aitypechange)
        firsthalf.addLayout(self.aitypelayout)


        ttslayout = QHBoxLayout()
        self.ttsselect = QComboBox()
        self.ttsselect.addItems([trls.tr(self.trl, 'character.ai_voices'), "ElevenLabs"])
        if getconfig("tts", "silerotts") == "elevenlabs":
            self.ttsselect.setCurrentIndex(1)
        self.ttsselect.currentTextChanged.connect(lambda: self.ttschange())

        self.ttslabel = QLabel(trls.tr(self.trl, 'select_tts'))
        self.ttslabel.setWordWrap(True)

        ttslayout.addWidget(self.ttslabel)
        ttslayout.addWidget(self.ttsselect)
        firsthalf.addLayout(ttslayout)


        vtubelayout = QHBoxLayout()
        self.vtubecheck = QCheckBox()
        if vtube_enable:
            self.vtubecheck.setChecked(True)
        self.vtubecheck.stateChanged.connect(self.vtubechange)
        self.vtubewiki = QPushButton("Wiki")
        self.vtubewiki.clicked.connect(lambda: webbrowser.open("https://github.com/Kajitsy/Emilia/wiki/%D0%98%D1%81%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-VTube-%D0%9C%D0%BE%D0%B4%D0%B5%D0%BB%D1%8C%D0%BA%D0%B8"))

        vtubelayout.addWidget(QLabel("VTube Model"))
        vtubelayout.addWidget(self.vtubecheck)
        vtubelayout.addWidget(self.vtubewiki)
        firsthalf.addLayout(vtubelayout)


        try:
            build_number, _ = winreg.QueryValueEx(
                winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"),
                "CurrentBuildNumber")
        except Exception:
            build_number = "0"
        themelayout = QHBoxLayout()
        self.themechange = QComboBox()
        self.themechange.addItems(["Fusion", "Windows Old"])
        if int(build_number) > 22000:
            self.themechange.addItem("Windows 11")
        theme = getconfig('theme', 'windowsvista')
        if theme == 'windowsvista':
            self.themechange.setCurrentIndex(1)
        elif theme == 'windows11':
            self.themechange.setCurrentIndex(2)
        elif theme == 'Fuison':
            self.themechange.setCurrentIndex(0)
        self.themechange.currentTextChanged.connect(lambda: self.changetheme())

        themelayout.addWidget(QLabel(trls.tr(self.trl, "select_theme")))
        themelayout.addWidget(self.themechange)
        secondhalf.addLayout(themelayout)


        iconcolorlayout = QHBoxLayout()
        self.iconcolorchange = QComboBox()
        self.iconcolorchange.addItems([trls.tr(self.trl, 'white'), trls.tr(self.trl, 'black')])
        iconcolor = getconfig('iconcolor', 'white')
        if iconcolor == 'black':
            self.iconcolorchange.setCurrentIndex(1)
        self.iconcolorchange.currentTextChanged.connect(lambda: self.changeiconcolor())

        iconcolorlayout.addWidget(QLabel(trls.tr(self.trl, "pick_icon_color")))
        iconcolorlayout.addWidget(self.iconcolorchange)
        secondhalf.addLayout(iconcolorlayout)


        backgroundlayout = QHBoxLayout()
        self.pickbackground_button = QPushButton(trls.tr(self.trl, "pick_background_color"))
        self.pickbackground_button.clicked.connect(self.pick_background_color)

        backgroundlayout.addWidget(self.pickbackground_button)
        secondhalf.addLayout(backgroundlayout)


        textcolor = QHBoxLayout()
        self.picktext_button = QPushButton(trls.tr(self.trl, "pick_text_color"))
        self.picktext_button.clicked.connect(self.pick_text_color)

        textcolor.addWidget(self.picktext_button)
        secondhalf.addLayout(textcolor)


        fullbuttoncolorslayout = QVBoxLayout()
        buttoncolorslayout = QHBoxLayout()
        self.button_label = QLabel(trls.tr(self.trl, "button_colors"))
        self.pickbutton_button = QPushButton(trls.tr(self.trl, "pick_background_color"))
        self.pickbutton_button.clicked.connect(self.pick_button_color)
        self.pickbuttontext_button = QPushButton(trls.tr(self.trl, "pick_text_color"))
        self.pickbuttontext_button.clicked.connect(self.pick_button_text_color)

        fullbuttoncolorslayout.addWidget(self.button_label, alignment=Qt.AlignmentFlag.AlignCenter)
        buttoncolorslayout.addWidget(self.pickbutton_button)
        buttoncolorslayout.addWidget(self.pickbuttontext_button)
        fullbuttoncolorslayout.addLayout(buttoncolorslayout)
        secondhalf.addLayout(fullbuttoncolorslayout)


        self.reset_button = QPushButton(trls.tr(self.trl, "reset"))
        self.reset_button.clicked.connect(self.allreset)
        secondhalf.addWidget(self.reset_button)

        layout.addLayout(firsthalf)
        layout.addLayout(secondhalf)
        self.setLayout(layout)

        self.current_color = QColor("#ffffff")
        self.current_button_color = QColor("#ffffff") 
        self.current_label_color = QColor("#000000")

        if backcolor:
            self.set_background_color(QColor(backcolor))
        if buttoncolor:
            self.set_button_color(QColor(buttoncolor))
        if labelcolor:
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor:
            self.set_button_text_color(QColor(buttontextcolor))

    def vtubechange(self, state):
        global vtube_enable
        if state == 2:
            MessageBox(text="Attention, using Emilia together with the VTube model can greatly slow down the generation of responses")
            vtube_enable = True
        else:
            vtube_enable = False
        writeconfig('vtubeenable', vtube_enable)

    def autoupdatechange(self, state):
        global autoupdate_enable
        if state == 2:
            autoupdate_enable = True
        else:
            autoupdate_enable = False
        writeconfig('autoupdate_enable', autoupdate_enable)

    def aichange(self):
        value = self.aitypechange.currentIndex()
        global aitype
        if value == 0:
            aitype = 'charai'
            self.ttsselect.addItem(trls.tr("OptionsWindow", 'character.ai_voices'))
        elif value == 1:
            aitype = 'gemini'
            self.ttsselect.removeItem(2)
            self.ttsselect.setCurrentIndex(0)
        writeconfig('aitype', aitype)
        print('Restart Request')
        sys.exit()

    def ttschange(self):
        value = self.ttsselect.currentIndex()
        global tts
        if value == 0:
            tts = 'charai'
            self.mainwindow.tts_token_label.setVisible(False)
            self.mainwindow.tts_token_entry.setVisible(False)
            self.mainwindow.voice_label.setText(trls.tr("MainWindow", "voice_id"))
            self.mainwindow.voice_entry.setToolTip("")
            self.mainwindow.voice_entry.setPlaceholderText("")
            self.mainwindow.voice_entry.textChanged.disconnect()
            self.mainwindow.voice_entry.textChanged.connect(lambda: writeconfig("voiceid", self.mainwindow.voice_entry.text().replace("https://character.ai/?voiceId=", ""), "charaiconfig.json"))
            self.mainwindow.voice_entry.setText(getconfig('voiceid', configfile="charaiconfig.json"))
        elif value == 1:
            tts = 'elevenlabs'
            self.mainwindow.tts_token_label.setVisible(True)
            self.mainwindow.tts_token_entry.setVisible(True)
            self.mainwindow.voice_label.setText(trls.tr("MainWindow", "voice"))
            self.mainwindow.tts_token_label.setText(trls.tr("MainWindow", "elevenlabs_api_key"))
            self.mainwindow.tts_token_entry.setText(getconfig("elevenlabs_api_key"))
            self.mainwindow.voice_entry.setPlaceholderText("")
            self.mainwindow.voice_entry.textChanged.disconnect()
            self.mainwindow.voice_entry.textChanged.connect(lambda: writeconfig("elevenlabs_voice", self.mainwindow.voice_entry.text(), "charaiconfig.json"))
            self.mainwindow.voice_entry.setText(getconfig('elevenlabs_voice', configfile="charaiconfig.json"))
            self.mainwindow.voice_layout.addWidget(self.mainwindow.tts_token_label)
            self.mainwindow.voice_layout.addWidget(self.mainwindow.tts_token_entry)
        writeconfig('tts', tts)

    def changetheme(self):
        value = self.themechange.currentIndex()
        global theme
        if value == 0:
            theme = 'fusion'
        elif value == 1:
            theme = 'windowsvista'
        elif value == 2:
            theme = 'windows11'
        app = QApplication.instance()
        app.setStyle(theme)
        writeconfig('theme', theme)

    def changeiconcolor(self):
        value = self.iconcolorchange.currentIndex()
        global iconcolor
        if value == 0:
            keyboardicon =f'{imagesfolder}/keyboard_white.png'
            inputicon = f'{imagesfolder}/input_white.png'
            charediticon = f'{imagesfolder}/open_char_editor_white.png'
            iconcolor = 'white'
        elif value == 1:
            keyboardicon = f'{imagesfolder}/keyboard.png'
            inputicon = f'{imagesfolder}/input.png'
            charediticon = f'{imagesfolder}/open_char_editor.png'
            iconcolor = 'black'
        writeconfig('iconcolor', iconcolor)
        self.mainwindow.visibletextmode.setIcon(QIcon(keyboardicon))
        self.mainwindow.visiblevoicemode.setIcon(QIcon(inputicon))
        self.mainwindow.CharacterSearchopen.setIcon(QIcon(charediticon))

    def langchange(self):
        value = self.languagechange.currentIndex()
        if value == 0:
            writeconfig('language', "en_US")
        elif value == 1:
            writeconfig('language', "ru_RU")
        print("Restart required")
        if imagesfolder == "images":
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)

    def pick_background_color(self):
        globals['backcolor'] = QColorDialog.getColor(self.current_color, self)
        self.mainwindow.set_background_color(backcolor) 
        self.set_background_color(backcolor)
        writeconfig('backgroundcolor', backcolor.name())

    def pick_button_color(self):
        globals['buttoncolor'] = QColorDialog.getColor(self.current_button_color, self)
        self.mainwindow.set_button_color(buttoncolor)
        self.set_button_color(buttoncolor)
        writeconfig('buttoncolor', buttoncolor.name())

    def pick_button_text_color(self):
        globals()['buttontextcolor'] = QColorDialog.getColor(self.current_button_color, self)
        self.mainwindow.set_button_text_color(buttontextcolor)
        self.set_button_text_color(buttontextcolor)
        writeconfig('buttontextcolor', buttontextcolor.name())

    def pick_text_color(self):
        globals()['labelcolor'] = QColorDialog.getColor(self.current_label_color, self)
        self.mainwindow.set_label_color(labelcolor)
        self.set_label_color(labelcolor)
        writeconfig('labelcolor', labelcolor.name())

    def allreset(self):
        global iconcolor, backcolor, buttoncolor, buttontextcolor, labelcolor, keyboardicon, inputicon, charediticon
        globals().update({
            'backcolor': '',
            'buttoncolor': '',
            'buttontextcolor': '',
            'labelcolor': ''
        })
        self.mainwindow.styles_reset()
        self.styles_reset()
        writeconfig("backgroundcolor", backcolor)
        writeconfig("labelcolor", buttoncolor)
        writeconfig("buttontextcolor", buttontextcolor)
        writeconfig("buttoncolor", labelcolor)

    def set_background_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QWidget {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_text_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_label_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QWidget {{
                color: {color.name()};
            }}
        """
        new_style_sheet2 = f"""
            QLineEdit {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet + new_style_sheet2)

    def styles_reset(self):
        self.setStyleSheet("")

class EmiliaAuth(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Getting Token")
        self.setFixedWidth(300)
        self.setMinimumHeight(100)

        self.layout = QVBoxLayout()

        email_layout = QHBoxLayout()
        self.email_label = QLabel(trls.tr("GetToken","your_email"))
        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("example@example.com")

        email_layout.addWidget(self.email_label)
        email_layout.addWidget(self.email_entry)
        self.layout.addLayout(email_layout)


        self.getlink_button = QPushButton(trls.tr("GetToken", "send_email"))
        self.getlink_button.clicked.connect(self.getlink)
        self.layout.addWidget(self.getlink_button)


        self.link_layout = QHBoxLayout()
        self.link_label = QLabel(trls.tr("GetToken", "link_from_email"))
        self.link_entry = QLineEdit()
        self.link_entry.setPlaceholderText("https...")

        self.link_layout.addWidget(self.link_label)
        self.link_layout.addWidget(self.link_entry)
        

        self.gettoken_button = QPushButton(trls.tr("GetToken", "get_token"))
        self.gettoken_button.clicked.connect(self.gettoken)
        
        self.setLayout(self.layout)

        if backcolor:
            self.set_background_color(QColor(backcolor))
        if buttoncolor:
            self.set_button_color(QColor(buttoncolor))
        if labelcolor:
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor:
            self.set_button_text_color(QColor(buttontextcolor))

    def getlink(self):
        sendCode(self.email_entry.text())
        self.layout.addLayout(self.link_layout)
        self.layout.addWidget(self.gettoken_button)

    def gettoken(self):
        try:
            token = authUser(self.link_entry.text(), self.email_entry.text())
            self.link_label.setVisible(False)
            self.link_entry.setVisible(False)
            self.gettoken_button.setVisible(False)
            self.email_entry.setVisible(False)
            self.getlink_button.setVisible(False)
            self.email_label.setText(trls.tr("GetToken", "your_token") + token + trls.tr("GetToken", "save_in_charaiconfig"))
            writeconfig('client', token, 'charaiconfig.json')
        except Exception as e:
            MessageBox(title=trls.tr("Errors", "Label"), text=trls.tr("Errors", "other") + str(e))

    def set_background_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QWidget {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_text_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_label_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QWidget {{
                color: {color.name()};
            }}
        """
        new_style_sheet2 = f"""
            QLineEdit {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet + new_style_sheet2)

    def styles_reset(self):
        self.setStyleSheet("")

class Emilia(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia")
        self.setFixedWidth(320)
        self.setMinimumHeight(160)

        self.characters_list = []
        self.connect = None
        self.microphone_muted = False
        self.ev_close = False

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        hlayout = QHBoxLayout()

        if aitype == "gemini":
            hlayout = QHBoxLayout()

            self.token_label = QLabel(trls.tr("MainWindow", "gemini_token"))
            self.token_label.setWordWrap(True)

            self.token_entry = QLineEdit()
            self.token_entry.setPlaceholderText(trls.tr("MainWindow", "token"))
            self.token_entry.textChanged.connect(lambda: writeconfig("token", self.token_entry.text(), "geminiconfig.json"))
            self.token_entry.setText(getconfig('token', configfile='geminiconfig.json'))

            hlayout.addWidget(self.token_label)
            hlayout.addWidget(self.token_entry)

        elif aitype == "charai":
            hlayout = QHBoxLayout()

            self.char_label = QLabel(trls.tr("MainWindow", "character_id"))
            self.char_label.setWordWrap(True)

            self.char_entry = QLineEdit()
            self.char_entry.setPlaceholderText("ID...")
            self.char_entry.textChanged.connect(lambda: writeconfig("char", self.char_entry.text().replace("https://character.ai/chat/", ""), "charaiconfig.json"))
            self.char_entry.setText(getconfig('char', configfile='charaiconfig.json'))

            self.client_label = QLabel(trls.tr("MainWindow", "character_token"))
            self.client_label.setWordWrap(True)

            self.client_entry = QLineEdit()
            self.client_entry.setPlaceholderText(trls.tr("MainWindow", "token"))
            self.client_entry.textChanged.connect(lambda: writeconfig("client", self.client_entry.text(), "charaiconfig.json"))
            self.client_entry.setText(getconfig('client', configfile='charaiconfig.json'))

            hlayout.addWidget(self.char_label)
            hlayout.addWidget(self.char_entry)
            hlayout.addWidget(self.client_label)
            hlayout.addWidget(self.client_entry)
        
        self.layout.addLayout(hlayout)
            
        self.voice_layout = QHBoxLayout()
        self.tts_token_label = QLabel()
        self.tts_token_label.setWordWrap(True)
        self.tts_token_entry = QLineEdit()
        self.voice_label = QLabel()
        self.voice_entry = QLineEdit()
        if tts == "charai":
            self.voice_label.setText(trls.tr("MainWindow", "voice_id"))
            self.voice_entry.setToolTip(trls.tr("MainWindow", "voice_id_tooltip"))
            self.voice_entry.textChanged.connect(lambda: writeconfig("voiceid", self.voice_entry.text().replace("https://character.ai/?voiceId=", ""), "charaiconfig.json"))
            self.voice_entry.setText(getconfig('voiceid', configfile="charaiconfig.json"))
        elif tts == "elevenlabs":
            self.voice_label.setText(trls.tr("MainWindow", "voice"))
            self.voice_entry.textChanged.connect(lambda: writeconfig("elevenlabs_voice", self.voice_entry.text(), "charaiconfig.json"))
            self.voice_entry.setText(getconfig('elevenlabs_voice', configfile="charaiconfig.json"))
            self.tts_token_label.setText(trls.tr("MainWindow", "elevenlabs_api_key"))
            self.tts_token_entry.setText(getconfig("elevenlabs_api_key"))
            self.tts_token_entry.textChanged.connect(lambda: writeconfig("elevenlabs_api_key", self.tts_token_entry.text()))
            self.voice_layout.addWidget(self.tts_token_label)
            self.voice_layout.addWidget(self.tts_token_entry)
        self.voice_layout.addWidget(self.voice_label)
        self.voice_layout.addWidget(self.voice_entry)

        self.microphone = ""
        self.selected_device_index = ""

        if backcolor:
            self.set_background_color(QColor(backcolor))
        if buttoncolor:
            self.set_button_color(QColor(buttoncolor))
        if labelcolor:
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor:
            self.set_button_text_color(QColor(buttontextcolor))

        self.vstart_button = QPushButton(trls.tr("MainWindow", "start"))
        self.vstart_button.clicked.connect(lambda: self.start_main("voice"))

        self.user_input = QLabel("")
        self.user_input.setWordWrap(True)

        self.user_aiinput = QLineEdit()
        self.user_aiinput.setPlaceholderText(trls.tr("MainWindow", "before_pressing"))

        self.tstart_button = QPushButton(trls.tr("MainWindow", "start_text_mode"))
        self.tstart_button.clicked.connect(lambda: self.start_main("text"))

        self.ai_output = QLabel("")
        self.ai_output.setWordWrap(True)

        self.layout.addLayout(self.voice_layout)
        self.layout.addWidget(self.vstart_button)
        self.layout.addWidget(self.user_aiinput)
        self.layout.addWidget(self.tstart_button)
        self.user_aiinput.setVisible(False)
        self.tstart_button.setVisible(False)
        self.central_widget.setLayout(self.layout)

        # MenuBar
        self.menubar = self.menuBar()
        self.emi_menu = self.menubar.addMenu(f"&Emilia {version}")

        if aitype == "charai":
            self.gettokenaction = QAction(QIcon(charaiicon), trls.tr("MainWindow", 'get_token'), self)
        elif aitype == "gemini":
            self.gettokenaction = QAction(QIcon(googleicon), trls.tr("MainWindow", 'get_token'), self)
        self.gettokenaction.triggered.connect(self.gettoken)

        self.show_chat = QAction(trls.tr('MainWindow', 'show_chat'), self)
        self.show_chat.triggered.connect(self.open_chat)

        self.optionsopenaction = QAction(trls.tr("MainWindow", "options"))
        self.optionsopenaction.triggered.connect(self.optionsopen)

        self.visibletextmode = QAction(QIcon(keyboardicon), trls.tr("MainWindow", 'use_text_mode'), self)
        self.visibletextmode.triggered.connect(lambda: self.modehide("text"))

        self.visiblevoicemode = QAction(QIcon(inputicon), trls.tr("MainWindow", 'use_voice_mode'), self)
        self.visiblevoicemode.triggered.connect(lambda: self.modehide("voice"))
        self.visiblevoicemode.setVisible(False)

        self.mute_microphone_action = QAction(trls.tr("MainWindow", 'mute_microphone'), self)
        self.mute_microphone_action.setCheckable(True)
        self.mute_microphone_action.triggered.connect(self.toggle_microphone_mute)

        self.inputdeviceselect = QMenu(trls.tr("MainWindow", 'input_device'), self)
        
        input_devices = QMediaDevices.audioInputs()
        
        for index, device in enumerate(input_devices):
            device_name = device.description()
            action = QAction(device_name, self)
            action.triggered.connect(lambda checked, i=index: self.set_microphone(i))
            self.inputdeviceselect.addAction(action)

        self.outputdeviceselect = QMenu(trls.tr("MainWindow", 'output_device'), self)
        
        output_devices = QMediaDevices.audioOutputs()
        
        self.unique_devices = {}
        for device in output_devices:
            device_name = device.description()
            if device_name not in self.unique_devices:
                self.unique_devices[device_name] = device

        for index, (name, device) in enumerate(self.unique_devices.items()):
            action = QAction(name, self)
            action.triggered.connect(lambda checked, i=index: self.set_output_device(i))
            self.outputdeviceselect.addAction(action)
        if aitype == "charai":
            self.charselect = self.menubar.addMenu(trls.tr("MainWindow", 'character_choice'))

            self.CharacterSearchopen = QAction(QIcon(charediticon), trls.tr('MainWindow', 'open_character_search'), self)
            self.CharacterSearchopen.triggered.connect(self.charsopen)

            self.charrefreshlist = QAction(QIcon(refreshicon), trls.tr("MainWindow", "refresh_list"))
            self.charrefreshlist.triggered.connect(self.refreshcharsinmenubar)

        
            self.charselect.addAction(self.CharacterSearchopen)
            self.charselect.addAction(self.charrefreshlist)
            
            self.start_fetching_data()
            self.addcharsinmenubar()

        self.aboutemi = QAction(QIcon(emiliaicon), trls.tr("MainWindow", 'about_emilia'), self)
        self.aboutemi.triggered.connect(self.about)

        self.emi_menu.addAction(self.gettokenaction)
        if aitype == "charai":
            self.emi_menu.addAction(self.show_chat)
        self.emi_menu.addAction(self.visibletextmode)
        self.emi_menu.addAction(self.visiblevoicemode)
        self.emi_menu.addAction(self.optionsopenaction)
        self.emi_menu.addAction(self.aboutemi)
        self.emi_menu.addMenu(self.inputdeviceselect)
        self.emi_menu.addMenu(self.outputdeviceselect)


    def start_fetching_data(self):
        try:
            if self.client_entry.text() != "":
                self.CharacterSearchopen.setEnabled(False)
                self.custom_char_ai = CustomCharAI
                self.chat_data_worker = ChatDataWorker(self.custom_char_ai)
                self.chat_data_worker.recommend_chats_signal.connect(self.handle_recommend_chats)
                self.chat_data_worker.recent_chats_signal.connect(self.handle_recent_chats)
                self.chat_data_worker.error_signal.connect(self.handle_error)
                self.chat_data_worker.start()
            else:
                self.CharacterSearchopen.setEnabled(True)
                self.recommend_chats = None
                self.recent_chats = None
        except:
                self.CharacterSearchopen.setEnabled(True)
                self.recommend_chats = None
                self.recent_chats = None

    def handle_recommend_chats(self, chats):
        self.recommend_chats = chats

    def handle_recent_chats(self, chats):
        self.recent_chats = chats
        self.CharacterSearchopen.setEnabled(True)

    def handle_error(self, error_message):
        self.recommend_chats = None
        self.recent_chats = None
        MessageBox(trls.tr("Errors", "Label"), f"An error occurred: {error_message}")

    def toggle_microphone_mute(self, checked):
        self.microphone_muted = checked

    def open_chat(self):
        window = ChatWithCharacter()
        window.show()

    def optionsopen(self):
        window = OptionsWindow(self)
        window.show()

    def charsopen(self):
        window = CharacterSearch(self)
        window.show()

    def addcharsinmenubar(self):
        if os.path.exists('data.json'):
            def open_json(char, speaker):
                self.char_entry.setText(char)
                self.voice_entry.setText(speaker)
            def create_action(key, value):
                def action_func():
                    open_json(value['char'], value.get('voice', ''))
                action = QAction(value['name'], self)
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
                self.characters_list.append(action)
                self.charselect.addAction(action)

    def refreshcharsinmenubar(self):
        for action in self.characters_list:
            self.charselect.removeAction(action)
        self.characters_list.clear()
        self.addcharsinmenubar()

    def set_microphone(self, index):
        self.microphone = sr.Microphone(device_index=index)

    def set_output_device(self, index):
        device = list(self.unique_devices.values())[index]
        device_name = device.description()
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['name'] == device_name and dev['max_output_channels'] > 0:
                sd.default.device = (sd.default.device[0], i)
                self.selected_device_index = index
                break

    def set_background_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QMainWindow {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_text_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_label_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QLabel {{
                color: {color.name()};
            }}
        """
        new_style_sheet2 = f"""
            QLineEdit {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet + new_style_sheet2)

    def styles_reset(self):
        self.setStyleSheet("")

    def gettoken(self):
        if aitype == "charai":
            self.auth_window = EmiliaAuth()
            self.auth_window.show()
        elif aitype == "gemini":
            webbrowser.open("https://aistudio.google.com/app/apikey")

    def modehide(self, mode):
        if mode == "text":
            self.setMinimumHeight(200)
            self.visiblevoicemode.setVisible(True)
            self.visibletextmode.setVisible(False)
            self.tstart_button.setVisible(True)
            self.user_aiinput.setVisible(True)
            self.vstart_button.setVisible(False)
        elif mode == "voice":
            self.setMinimumHeight(150)
            self.visiblevoicemode.setVisible(False)
            self.visibletextmode.setVisible(True)
            self.tstart_button.setVisible(False)
            self.user_aiinput.setVisible(False)
            self.vstart_button.setVisible(True)

    def about(self):
        if pre == True:
            title = trls.tr("About", "about_emilia") + build
        else:
            title = trls.tr("About", "about_emilia")
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        language = trls.tr("About", "language_from")
        whatsnew = trls.tr("About", "new_in") + version + trls.tr("About", "whats_new")
        otherversions = trls.tr("About", "show_all_releases")
        text = trls.tr("About", "emilia_is_open_source") + version + trls.tr("About", "use_version") + language + whatsnew + otherversions
        MessageBox(title, text, pixmap=pixmap, self=self)

    async def charai_tts(self):
        message = self.messagenotext
        voiceid = self.voice_entry.text()
        if voiceid == "":
            data = {
                'candidateId': re.search(r"candidate_id='([^']*)'", (str(message.candidates))).group(1),
                'roomId': message.turn_key.chat_id,
                'turnId': message.turn_key.turn_id,
                'voiceId': voiceid,
                'voiceQuery': message.name
            }
        else:
            data = {
                'candidateId': re.search(r"candidate_id='([^']*)'", (str(message.candidates))).group(1),
                'roomId': message.turn_key.chat_id,
                'turnId': message.turn_key.turn_id,
                'voiceId': voiceid
            }
        response = await CustomCharAI.tts(data)
        link = response["replayUrl"]
        download = requests.get(link, stream=True)
        if download.status_code == 200: 
            audio_bytes = io.BytesIO(download.content)
            audio_array, samplerate = sf.read(audio_bytes)
            return audio_array, samplerate

    def load_characters_data(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                self.characters_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.characters_data = {}

    async def main(self):
        try:
            self.layout.addWidget(self.user_input)
            self.layout.addWidget(self.ai_output)
            if aitype == 'charai':
                self.username, self.ai_name, self.chat, self.character, self.token, self.connect = await self.setup_ai()
            elif aitype == 'gemini':
                self.username, self.ai_name, self.chat, self.character, self.token, self.connect = await self.setup_ai()
            while True:
                if self.ev_close:
                    break
                await self.process_user_input()
        except Exception as e:
            print(e)
            MessageBox(trls.tr('Errors', 'Label'), str(e), self=self)

    async def setup_ai(self):
        if tts == "elevenlabs":
            self.elevenlabs = ElevenLabs(api_key=getconfig('elevenlabs_api_key'))
            
        if aitype == 'charai':
            token = aiocai.Client(self.client_entry.text())
            self.load_characters_data()
            character = self.char_entry.text().replace("https://character.ai/chat/", "")
            connect = await token.connect()
            account = await token.get_me()
            try:
                chatid = await token.get_chat(character)
            except:
                chatid = await connect.new_chat(character, account.id)
            persona = self.characters_data.get(character, CustomCharAI.get_character(character))
            try:
                username = f"{account.name}: "
            except Exception as e:
                username = trls.tr("MainWindow", "user")
                print(e)
            ai_name = f"{persona['name']}: "
            return username, ai_name, chatid, character, token, connect
        elif aitype == 'gemini':
            genai.configure(api_key=self.token_entry.text())
            model = genai.GenerativeModel('gemini-1.5-pro')
            chat = model.start_chat(history=[])
            username = trls.tr("Main", "user")
            ai_name = "Gemini: "
            return username, ai_name, chat, None, None, None

    async def process_user_input(self):
        if vtube_enable:
            await EEC.UseEmote("Listening")

        recognizer = sr.Recognizer()
        self.user_input.setText(self.username + trls.tr("Main", "speak"))
        msg1 = await self.recognize_speech(recognizer)

        self.user_input.setText(self.username + msg1)
        self.ai_output.setText(self.ai_name + trls.tr("Main", "generation"))
        
        if vtube_enable:
            await EEC.UseEmote("Thinks")

        message = await self.generate_ai_response(msg1)

        if tts != "charai" and lang == "ru_RU":
            self.translation = await Translator().translate(message, targetlang="ru")
            message = self.translation.text

        if vtube_enable:
            await EEC.UseEmote("VoiceGen")

        self.ai_output.setText(self.ai_name + message)

        if vtube_enable:
            await EEC.UseEmote("Says")

        await self.play_audio_response(message)

        if vtube_enable:
            await EEC.UseEmote("AfterSays")

    async def recognize_speech(self, recognizer):
        while True:
            if not self.microphone_muted:
                try:
                    audio = await self.listen_to_microphone(recognizer)
                    result = recognizer.recognize_google(audio, language="ru-RU" if lang == "ru_RU" else "en-US")
                    if not self.microphone_muted:
                        return result
                    else:
                        await asyncio.sleep(0.5)
                except sr.UnknownValueError:
                    self.user_input.setText(self.username + trls.tr("Main", "say_again"))
            else:
                await asyncio.sleep(0.5)

    async def listen_to_microphone(self, recognizer):
        if self.microphone:
            with self.microphone as source:
                return recognizer.listen(source)
        else:
            with sr.Microphone() as source:
                return recognizer.listen(source)

    async def generate_ai_response(self, text):
        if aitype == 'charai':
            while True:
                try:
                    self.messagenotext = await self.connect.send_message(self.character, self.chat.chat_id, text)
                    return self.messagenotext.text
                except websockets.exceptions.ConnectionClosedError:
                    self.connect = await self.token.connect()
        elif aitype == 'gemini':
            try:
                chunk = self.chat.send_message(text)
                return chunk.text
            except Exception as e:
                if e.code == 400 and "User location is not supported" in e.message:
                    MessageBox(trls.tr('Errors', 'Label') + trls.tr('Errors', 'Gemini 400'))
                else:
                    MessageBox(trls.tr('Errors', 'Label') + str(e))
                return ""

    async def play_audio_response(self, text):
        try:
            if tts == 'charai' and aitype == 'charai':
                audio, sample_rate = await self.charai_tts()
            elif tts == 'elevenlabs':
                audio = self.elevenlabs.generate(
                    voice=getconfig('elevenlabs_voice', configfile='charaiconfig.json'),
                    output_format='mp3_22050_32',
                    text=text,
                    model='eleven_multilingual_v2',
                    voice_settings=VoiceSettings(
                        stability=0.2,
                        similarity_boost=0.8,
                        style=0.4,
                        use_speaker_boost=True,
                    )
                )
                play(audio, use_ffmpeg=False)
                return
            sd.play(audio, sample_rate)
            await asyncio.sleep(len(audio) / sample_rate)
            sd.stop()
        except Exception as e:
            print(e)
            MessageBox(trls.tr('Errors', 'Label'), str(e))

    async def maintext(self):
        if self.user_aiinput.text() == "" or self.user_aiinput.text() == trls.tr("MainWindow", "but_it_is_empty"):
            self.user_aiinput.setText(trls.tr("MainWindow", "but_it_is_empty"))
        else:
            self.layout.addWidget(self.ai_output)
            self.username, self.ai_name, self.chat, self.character, self.token, self.connect = await self.setup_ai()
                
            msg1 = self.user_aiinput.text()

            self.ai_output.setText(self.ai_name + trls.tr("Main", "generation"))

            if vtube_enable:
                await EEC.UseEmote("Thinks")

            message = await self.generate_ai_response(msg1)

            if vtube_enable:
                await EEC.UseEmote("VoiceGen")
                
            self.ai_output.setText(self.ai_name + message)

            if vtube_enable:
                await EEC.UseEmote("Says")

            await self.play_audio_response(message)

            if vtube_enable:
                await EEC.UseEmote("Listening")

    def start_main(self, mode):
        if mode == "voice":
            threading.Thread(target=lambda: asyncio.run(self.main())).start()
            for actions in self.emi_menu.actions():
                actions.setVisible(False)
            self.emi_menu.addAction(self.mute_microphone_action)
            if aitype == 'charai':
                self.charselect.setEnabled(False)
                self.char_label.setVisible(False)
                self.char_entry.setVisible(False)
                self.client_label.setVisible(False)
                self.client_entry.setVisible(False)
            elif aitype == 'gemini':
                self.token_entry.setVisible(False)
                self.token_label.setVisible(False)
            self.tts_token_label.setVisible(False)
            self.tts_token_entry.setVisible(False)
            self.voice_label.setVisible(False)
            self.voice_entry.setVisible(False)
            self.vstart_button.setVisible(False)
            self.tstart_button.setVisible(False)
            self.user_aiinput.setVisible(False)
            self.user_input.setVisible(True)
        elif mode == "text":
            threading.Thread(target=lambda: asyncio.run(self.maintext())).start()

    def closeEvent(self, event):
        self.ev_close = True
        super().closeEvent(event)

if __name__ == "__main__":
    if autoupdate_enable:
        AutoUpdate(build, 'charai', True).check_for_updates()
    app = QApplication(sys.argv)
    app.setStyle(theme)
    if not os.path.exists('config.json'):
        window = FirstLaunch()
    else:
        window = Emilia()
    if vtube_enable:
        Emote_File()
        asyncio.run(EEC.VTubeConnect())
    window.show()
    sys.exit(app.exec())