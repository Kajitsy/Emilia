# pyinstaller --noconfirm --onefile --windowed --icon "Emilia\images\premilia.ico" --add-data "Emilia\images;images/" --add-data "Emilia\locales;locales/"  "Emilia\emilia_charai.py"

import io
import os
import asyncio
import winreg
import threading
import time
import zipfile
import requests
import re
import json
import sys
import webbrowser
import ctypes
import pyvts
import random
import warnings
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from characterai import aiocai, sendCode, authUser
from PyQt6.QtWidgets import QTabWidget, QColorDialog, QComboBox, QCheckBox, QHBoxLayout, QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QMenu, QListWidget, QListWidgetItem, QSizePolicy
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor
from PyQt6.QtCore import QLocale, Qt, pyqtSignal, Qt, QThread

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('emilia.charai.app')
except Exception as e:
    print(f"Ctypes error {e}")

warnings.filterwarnings("ignore", category=DeprecationWarning)

version = "2.2.1"
build = "20240725"
pre = True
local_file = 'voice.pt'
sample_rate = 48000
put_accent = True
put_yo = True

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def writeconfig(variable, value, configfile = 'config.json'):
    try:
        with open(configfile, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError:
         data = {}
    data.update({variable: value})
    with open(configfile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def getconfig(value, def_value = "", configfile = 'config.json'):
    if os.path.exists(configfile):
        with open(configfile, 'r') as configfile:
            config = json.load(configfile)
            return config.get(value, def_value)
    else:
        return def_value

# Global Variables
autoupdate_enable = getconfig('autoupdate_enable', 'False')
lang = getconfig('language', QLocale.system().name())
theme = getconfig('theme', 'windowsvista')
iconcolor = getconfig('iconcolor', 'black')
backcolor = getconfig('backgroundcolor')
buttoncolor = getconfig('buttoncolor')
buttontextcolor = getconfig('buttontextcolor')
labelcolor = getconfig('labelcolor')
imagesfolder = resource_path('images')
localesfolder = resource_path('locales')

# Icons
if pre == True:
    emiliaicon = f'{imagesfolder}/premilia.png'
else:
    emiliaicon = f'{imagesfolder}/emilia.png'
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
print("(｡･∀･)ﾉﾞ")

def load_translations(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(f"{localesfolder}/en_US.json", "r", encoding="utf-8") as f:
            return json.load(f)

def tr(context, text):
    if context in translations and text in translations[context]:
        return translations[context][text]
    else:
        return text

translations = load_translations(f"{localesfolder}/{lang}.json")

if not os.path.exists('Emotes.json'):
    emotesjson = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/autoupdate.json")
    emotesjson.raise_for_status()
    with open("Emotes.json", "wb") as f:
            f.write(emotesjson.content)

class EEC():
    """
    EMC - Emilia Emotes Core
    """

    plugin_info = {
        "plugin_name": "Emilia VTube",
        "developer": "kajitsy",
        "authentication_token_path": "./token.txt"
    }

    myvts = pyvts.vts(plugin_info)

    async def VTubeConnect(self):
        """
        Подключение к Vtube Studio
        """
        try:
            await self.myvts.connect()
            try:
                await self.myvts.read_token()
                await self.myvts.request_authenticate()
            except:
                await self.myvts.request_authenticate_token()
                await self.myvts.write_token()
                await self.myvts.request_authenticate()
            self.myvts.load_icon(emiliaicon)
        except:
            writeconfig('vtubeenable', 'False')

    async def SetCustomParameter(self, name, value=50, min=-100, max=100):
        """
        Лучше всего использовать для создания параметров плагина

        CustomParameter("EmiEyeX", -100, 100, 0)
        """

        try:
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(name, min, max, value)
            )
        except:
            await self.VTubeConnect()
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(name, min, max, value)
            )
        await self.myvts.close()

    async def DelCustomParameter(self, name):
        """
        Лучше всего использовать для создания параметров плагина

        CustomParameter("EmiEyeX", -100, 100, 0)
        """

        try:
            await self.myvts.request(
                self.myvts.vts_request.requestDeleteCustomParameter(name)
            )
        except:
            await self.VTubeConnect()
            await self.myvts.request(
                self.myvts.vts_request.requestDeleteCustomParameter(name)
            )
        await self.myvts.close()

    def RandomBetween(self, a, b):
        """
        Просто случайное число, не более.

        RandomBetween(-90, -75)
        """
        return random.randint(a, b)

    async def AddVariables(self):
        """
        Создаёт все нужные переменные
        """

        parameters = ["EmiFaceAngleX", "EmiFaceAngleY", "EmiFaceAngleZ",
                      "EmiEyeOpenLeft", "EmiEyeOpenRight",
                      "EmiEyeX", "EmiEyeY", "EmiMountSmile", "EmiMountX"]
        for param in parameters:
            await self.SetCustomParameter(param)

    async def DelVariables(self):
        """
        Удаляет все нужные переменные
        """

        parameters = ["EmiFaceAngleX", "EmiFaceAngleY", "EmiFaceAngleZ",
                      "EmiEyeOpenLeft", "EmiEyeOpenRight",
                      "EmiEyeX", "EmiEyeY", "EmiMountSmile", "EmiMountX"]
        for param in parameters:
            await self.DelCustomParameter(param)

    async def UseEmote(self, emote):
        """
        Управляет значениями переменных, беря их и их значение из Emotes.json
        """

        def getemotes(emote):
            with open("Emotes.json", "r") as f:
                emotes_data = json.load(f)
            emote_data = emotes_data[emote]
            return emote_data

        emote_data = getemotes(emote)
        rndm = EEC().RandomBetween
        names = []
        values = []
        for parameter_name, parameter_value in emote_data.items():
            if parameter_name == "EyesOpen":
                eyesopen_value = eval(parameter_value)
                values.append(eyesopen_value)
                values.append(eyesopen_value)
                names.append("EmiEyeOpenRight")
                names.append("EmiEyeOpenLeft")
            else:
                names.append(parameter_name)
                value = eval(parameter_value)
                values.append(value)

        await self.VTubeConnect()
        for i, name in enumerate(names):
            value = values[i]
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(
                    parameter=name,
                    min=0,
                    max=100,
                    default_value=value
                )
            )
        await self.myvts.close()

class AutoUpdate():
    def check_for_updates(self):
        response = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/autoupdate.json")
        response.raise_for_status()
        updates = response.json()
        try:
            if pre == True:
                if "charai_latest_prerealease" in updates:
                    latest_prerealease = updates["charai_latest_prerealease"]
                    if int(latest_prerealease["build"]) > int(build):
                        if resource_path("autoupdate") != "autoupdate":
                            if latest_prerealease.get('exe', '') != '':
                                self.download_and_update_script(latest_prerealease["exe"], latest_prerealease["build"])
                            return
                        self.download_and_update_script(latest_prerealease["url"], latest_prerealease["build"])
                        return
            else:
                if "charai_latest_release" in updates:
                    latest_release = updates["charai_latest_release"]
                    if int(latest_release["build"]) > int(build):
                        if resource_path("autoupdate") != "autoupdate":
                            if latest_release.get('exe', '') != '':
                                self.download_and_update_script(latest_release["exe"], latest_release["build"])
                            return
                        self.download_and_update_script(latest_release["url"], latest_release["build"])
                        return
        except Exception as e:
            print(f"{tr('Errors', 'UpdateCheckError')} {e}")
            writeconfig('autoupdate_enable', 'False')

    def download_and_update_script(self, url, build):
        print(f"{tr('AutoUpdate', 'upgradeto')} {build}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"{tr('Errors', 'UpdateDownloadError')} {e}")
            writeconfig('autoupdate_enable', 'False')
            return
        if resource_path("autoupdate") == "autoupdate":
            with open(f"Emilia_{build}.zip", "wb") as f:
                f.write(response.content)

            with zipfile.ZipFile(f"Emilia_{build}.zip", "r") as zip_ref:
                zip_ref.extractall(".")

            os.remove(f"Emilia_{build}.zip")

            print(f"{tr('AutoUpdate', 'emiliaupdated')} {build}!")
            os.system("install_charai.bat")
        elif resource_path("autoupdate") != "autoupdate":
            with open(f"Emilia_CharacterAI.exe", "wb") as f:
                f.write(response.content)

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
        if getconfig('autoupdate_enable', 'False') == "True":
            self.autoupdate.setChecked(True)
        self.autoupdate.stateChanged.connect(self.autoupdatechange)
        if resource_path("autoupdate") != "autoupdate":
            self.autoupdate.setEnabled(False)


        autoupdatelayout.addWidget(QLabel(tr(self.trl, 'autoupdate')))
        autoupdatelayout.addWidget(self.autoupdate)
        firsthalf.addLayout(autoupdatelayout)


        langlayout = QHBoxLayout()
        self.languagechange = QComboBox()
        self.languagechange.addItems([tr(self.trl, 'langselEN'), tr(self.trl, 'langselRU')])
        if lang == "ru_RU":
            self.languagechange.setCurrentIndex(1)
        self.languagechange.currentTextChanged.connect(lambda: self.langchange())

        langlayout.addWidget(QLabel(tr(self.trl, 'languagechange')))
        langlayout.addWidget(self.languagechange)
        firsthalf.addLayout(langlayout)


        vtubelayout = QHBoxLayout()
        self.vtubecheck = QCheckBox()
        if getconfig('vtubeenable', 'False') == "True":
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

        themelayout.addWidget(QLabel(tr(self.trl, "selecttheme")))
        themelayout.addWidget(self.themechange)
        firsthalf.addLayout(themelayout)


        iconcolorlayout = QHBoxLayout()
        self.iconcolorchange = QComboBox()
        self.iconcolorchange.addItems([tr(self.trl, 'whitecolor'), tr(self.trl, 'blackcolor')])
        iconcolor = getconfig('iconcolor', 'white')
        if iconcolor == 'black':
            self.iconcolorchange.setCurrentIndex(1)
        self.iconcolorchange.currentTextChanged.connect(lambda: self.changeiconcolor())

        iconcolorlayout.addWidget(QLabel(tr(self.trl, "selecticoncolor")))
        iconcolorlayout.addWidget(self.iconcolorchange)
        firsthalf.addLayout(iconcolorlayout)


        backgroundlayout = QHBoxLayout()
        self.pickbackground_button = QPushButton(tr(self.trl, "pickbackgroundcolor"))
        self.pickbackground_button.clicked.connect(self.pick_background_color)

        backgroundlayout.addWidget(self.pickbackground_button)
        secondhalf.addLayout(backgroundlayout)


        textcolor = QHBoxLayout()
        self.picktext_button = QPushButton(tr(self.trl, "picktextcolor"))
        self.picktext_button.clicked.connect(self.pick_text_color)

        textcolor.addWidget(self.picktext_button)
        secondhalf.addLayout(textcolor)


        fullbuttoncolorslayout = QVBoxLayout()
        buttoncolorslayout = QHBoxLayout()
        self.button_label = QLabel(tr(self.trl, "button"))
        self.pickbutton_button = QPushButton(tr(self.trl, "pickbackgroundcolor"))
        self.pickbutton_button.clicked.connect(self.pick_button_color)
        self.pickbuttontext_button = QPushButton(tr(self.trl, "picktextcolor"))
        self.pickbuttontext_button.clicked.connect(self.pick_button_text_color)

        fullbuttoncolorslayout.addWidget(self.button_label, alignment=Qt.AlignmentFlag.AlignCenter)
        buttoncolorslayout.addWidget(self.pickbutton_button)
        buttoncolorslayout.addWidget(self.pickbuttontext_button)
        fullbuttoncolorslayout.addLayout(buttoncolorslayout)
        secondhalf.addLayout(fullbuttoncolorslayout)


        self.reset_button = QPushButton(tr(self.trl, "reset"))
        self.reset_button.clicked.connect(self.allreset)
        secondhalf.addWidget(self.reset_button)

        layout.addLayout(firsthalf)
        layout.addLayout(secondhalf)
        self.setLayout(layout)

        self.current_color = QColor("#ffffff")
        self.current_button_color = QColor("#ffffff") 
        self.current_label_color = QColor("#000000")

        self.backcolor = getconfig('backgroundcolor')
        self.buttoncolor = getconfig('buttoncolor')
        self.buttontextcolor = getconfig('buttontextcolor')
        self.labelcolor = getconfig('labelcolor')
        if self.backcolor != "":
            self.set_background_color(QColor(self.backcolor))
        if self.buttoncolor != "":
            self.set_button_color(QColor(self.buttoncolor))
        if self.labelcolor != "":
            self.set_label_color(QColor(self.labelcolor))
        if self.buttontextcolor != "":
            self.set_button_text_color(QColor(self.buttontextcolor))

    def vtubechange(self, state):
        if state == 2:
            writeconfig('vtubeenable', "True")
            msg = QMessageBox()
            msg.setStyleSheet(self.styleSheet())
            msg.setWindowTitle("Emilia")
            msg.setWindowIcon(QIcon(emiliaicon))
            text = "Attention, using Emilia together with the VTube model can greatly slow down the generation of responses"
            msg.setText(text)
            msg.exec()
        else:
            writeconfig('vtubeenable', "False")

    def autoupdatechange(self, state):
        if state == 2:
            writeconfig('autoupdate_enable', "True")
        else:
            writeconfig('autoupdate_enable', "False")

    def torchdevicechange(self):
        value = self.torchdeviceselect.currentIndex()
        if value == 0:
            writeconfig('devicefortorch', "cuda")
        elif value == 1:
            writeconfig('devicefortorch', "cpu")

    def changetheme(self):
        value = self.themechange.currentIndex()
        if value == 0:
            ltheme = "fusion"
        elif value == 1:
            ltheme = "windowsvista"
        elif value == 2:
            ltheme = "windows11"
        app = QApplication.instance()
        app.setStyle(ltheme)
        writeconfig('theme', ltheme)

    def changeiconcolor(self):
        value = self.iconcolorchange.currentIndex()
        if value == 0:
            keyboardicon =f'{imagesfolder}/keyboard_white.png'
            inputicon = f'{imagesfolder}/input_white.png'
            charediticon = f'{imagesfolder}/open_char_editor_white.png'
            writeconfig('iconcolor', 'white')
        elif value == 1:
            keyboardicon = f'{imagesfolder}/keyboard.png'
            inputicon = f'{imagesfolder}/input.png'
            charediticon = f'{imagesfolder}/open_char_editor.png'
            writeconfig('iconcolor', 'black')
        self.mainwindow.visibletextmode.setIcon(QIcon(keyboardicon))
        self.mainwindow.visiblevoicemode.setIcon(QIcon(inputicon))
        self.mainwindow.chareditopen.setIcon(QIcon(charediticon))

    def langchange(self):
        value = self.languagechange.currentIndex()
        if value == 0:
            writeconfig('language', "en_US")
        elif value == 1:
            writeconfig('language', "ru_RU")
        print("Restart required")
        os.execv(sys.executable, ['python'] + sys.argv)

    def pick_background_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        self.mainwindow.set_background_color(color) 
        self.set_background_color(color)
        writeconfig('backgroundcolor', color.name())

    def pick_button_color(self):
        color = QColorDialog.getColor(self.current_button_color, self)
        self.mainwindow.set_button_color(color)
        self.set_button_color(color)
        writeconfig('buttoncolor', color.name())

    def pick_button_text_color(self):
        color = QColorDialog.getColor(self.current_button_color, self)
        self.mainwindow.set_button_text_color(color)
        self.set_button_text_color(color)
        writeconfig('buttontextcolor', color.name())

    def pick_text_color(self):
        color = QColorDialog.getColor(self.current_label_color, self)
        self.mainwindow.set_label_color(color)
        self.set_label_color(color)
        writeconfig('labelcolor', color.name())

    def allreset(self):
        keyboardicon = './images/keyboard.png'
        inputicon = './images/input.png'
        charediticon = './images/open_char_editor.png'
        self.mainwindow.visibletextmode.setIcon(QIcon(keyboardicon))
        self.mainwindow.visiblevoicemode.setIcon(QIcon(inputicon))
        self.mainwindow.chareditopen.setIcon(QIcon(charediticon))
        self.mainwindow.styles_reset()
        self.styles_reset()
        writeconfig("backgroundcolor", "")
        writeconfig("labelcolor", "")
        writeconfig("buttontextcolor", "")
        writeconfig("buttoncolor", "")

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

class FirstLaunch(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia")
        self.setFixedWidth(300)
        self.setMinimumHeight(100)

        self.layout = QVBoxLayout()

        # First Page

        self.first_launch_notification_label = QLabel(tr('FirstLaunch', 'first_launch_notification_label'))
        if pre:
            self.first_launch_notification_label.setText(f"{self.first_launch_notification_label.text()}\n{tr('FirstLaunch', 'pre_first_launch_notification_label')}")
        self.first_launch_notification_label.setWordWrap(True)

        self.first_launch_notification_button_yes = QPushButton(tr('FirstLaunch', 'first_launch_notification_button_yes'))
        self.first_launch_notification_button_yes.clicked.connect(lambda: self.second_page())

        self.first_launch_notification_button_no = QPushButton(tr('FirstLaunch', 'first_launch_notification_button_no'))
        self.first_launch_notification_button_no.clicked.connect(lambda: self.first_launch_button_no())

        fphlayout = QHBoxLayout()
        fphlayout.addWidget(self.first_launch_notification_button_yes)
        fphlayout.addWidget(self.first_launch_notification_button_no)

        self.layout.addWidget(self.first_launch_notification_label)
        self.layout.addLayout(fphlayout)

        # Second Page

        self.characterai_button = QPushButton(tr('FirstLaunch', 'characterai_button'))
        self.characterai_button.clicked.connect(lambda: self.use_characterai())


        self.sphlayout = QHBoxLayout()
        self.sphlayout.addWidget(self.characterai_button)

        # Use Char.AI

        self.ready_button = QPushButton(tr('FirstLaunch', 'ready_button'))
        self.ready_button.clicked.connect(lambda: self.enterscharaidata())

        # Enter CharAI Data

        self.CharAIDataready_button = QPushButton(tr('FirstLaunch', 'ready_button'))
        self.CharAIDataready_button.clicked.connect(lambda: self.ShowMoreFeatures())

        # Enter Voice

        self.voiceentry = QLineEdit()
        self.voiceentry.setPlaceholderText(tr('MainWindow', 'voices'))

        self.voiceready_button = QPushButton(tr('FirstLaunch', 'ready_button'))
        self.voiceready_button.clicked.connect(lambda: self.afterentervoice())

        # Page with Additional features

        self.usevtubemodel = QCheckBox(tr('FirstLaunch', 'usevtubemodel'))
        self.usevtubemodel.stateChanged.connect(self.usesvtubemodel)

        self.enableautoupdate = QCheckBox(tr('FirstLaunch', 'enableautoupdate'))
        self.enableautoupdate.stateChanged.connect(self.enablesautoupdate)

        self.relaunch_button2 = QPushButton(tr('FirstLaunch', 'relaunch_button'))
        self.relaunch_button2.clicked.connect(lambda: os.execv(sys.executable, ['python'] + sys.argv))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.layout)

    def enablesautoupdate(self, state):
        if state == 2:
            writeconfig('autoupdate_enable', "True")
        else:
            writeconfig('autoupdate_enable', "False")

    def usesvtubemodel(self, state):
        if state == 2:
            writeconfig('vtubeenable', "True")
        else:
            writeconfig('vtubeenable', "False")

    def ShowMoreFeatures(self):
        self.setMinimumHeight(150)
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'ShowMoreFeatures'))
        self.CharAIDataready_button.setVisible(False)
        self.voiceready_button.setVisible(False)
        self.voiceentry.setVisible(False)
        self.layout.addWidget(self.usevtubemodel)
        self.layout.addWidget(self.enableautoupdate)
        self.layout.addWidget(self.relaunch_button2)

    def afterentervoice(self):
        writeconfig('speaker', self.voiceentry.text())
        self.ShowMoreFeatures()

    def enterscharaidata(self):
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'enterscharaidata'))
        self.ready_button.setVisible(False)
        self.layout.addWidget(self.CharAIDataready_button)
        self.character_editor = CharacterEditor()
        self.character_editor.show()

    def use_characterai(self):
        writeconfig('aitype', 'charai')
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'use_characterai'))
        self.characterai_button.setVisible(False)
        self.layout.addWidget(self.ready_button)
        self.auth_window = EmiliaAuth()
        self.auth_window.show()

    def second_page(self):
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'second_page'))
        self.first_launch_notification_button_yes.setVisible(False)
        self.first_launch_notification_button_no.setVisible(False)
        self.layout.addLayout(self.sphlayout)

    def first_launch_button_no(self):
        writeconfig('aitype', 'charai')
        os.execv(sys.executable, ['python'] + sys.argv)

class CharacterEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Character Editor")
        self.setFixedWidth(300)

        layout = QVBoxLayout()


        id_layout = QHBoxLayout()
        self.id_entry = QLineEdit()
        self.id_entry.setPlaceholderText("ID...")

        id_layout.addWidget(QLabel(tr("MainWindow", "characterid")))
        id_layout.addWidget(self.id_entry)
        layout.addLayout(id_layout)


        voice_layout = QHBoxLayout()
        self.voice_entry = QLineEdit()
        self.voice_entry.setPlaceholderText(tr("MainWindow", "voices"))
        self.voice_entry.setToolTip(tr("MainWindow", "voices"))

        voice_layout.addWidget(QLabel(tr("MainWindow", "voice")))
        voice_layout.addWidget(self.voice_entry)
        layout.addLayout(voice_layout)


        buttons_layout = QHBoxLayout()
        self.addchar_button = QPushButton(tr("CharEditor", "addchar"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.delchar_button = QPushButton(tr("CharEditor", "delchar"))
        self.delchar_button.clicked.connect(lambda: self.delchar())

        buttons_layout.addWidget(self.addchar_button)
        buttons_layout.addWidget(self.delchar_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
    

        self.backcolor = getconfig('backgroundcolor')
        self.buttoncolor = getconfig('buttoncolor')
        self.buttontextcolor = getconfig('buttontextcolor')
        self.labelcolor = getconfig('labelcolor')
        if self.backcolor != "":
            self.set_background_color(QColor(self.backcolor))
        if self.buttoncolor != "":
            self.set_button_color(QColor(self.buttoncolor))
        if self.labelcolor != "":
            self.set_label_color(QColor(self.labelcolor))
        if self.buttontextcolor != "":
            self.set_button_text_color(QColor(self.buttontextcolor))
    
    async def addchar(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        token = aiocai.Client(getconfig('client', configfile='charaiconfig.json'))
        charid = self.id_entry.text().replace("https://character.ai/chat/", "") 
        char = await token.get_persona(charid)
        data.update({charid: {"name": char.name, "char": charid, "voice": self.voice_entry.text()}})
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        msg = QMessageBox()
        msg.setWindowTitle(tr('CharEditor', 'characteradded'))
        msg.setStyleSheet(self.styleSheet())
        response = requests.get(f"https://characterai.io/i/80/static/avatars/{char.avatar_file_name}?webp=true&anim=0")
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        msg.setWindowIcon(QIcon(pixmap))
        msg.setIconPixmap(pixmap)
        text = tr('CharEditor', 'yourchar') + char.name + tr('CharEditor', 'withid') + charid + tr('CharEditor', 'withvoice') + self.voice_entry.text() + tr('CharEditor', 'added')
        msg.setText(text)
        msg.exec()

    def delchar(self):
        charid = self.id_entry.text().replace("https://character.ai/chat/", "") 
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        if charid in data:
            del data[charid]
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            msg = QMessageBox()
            msg.setStyleSheet(self.styleSheet())
            msg.setWindowTitle(tr("CharEditor", "error"))
            msg.setWindowIcon(QIcon(emiliaicon))
            text = tr("CharEditor", "notavchar")
            msg.setText(text)
            msg.exec()
    
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

class NewCharacterEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Character Editor")
        self.setFixedWidth(300)

        layout = QVBoxLayout()


        id_layout = QHBoxLayout()
        self.id_entry = QLineEdit()
        self.id_entry.setPlaceholderText("ID...")

        id_layout.addWidget(QLabel(tr("MainWindow", "characterid")))
        id_layout.addWidget(self.id_entry)
        layout.addLayout(id_layout)


        buttons_layout = QHBoxLayout()
        self.addchar_button = QPushButton(tr("CharEditor", "addchar"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        buttons_layout.addWidget(self.addchar_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
    

        self.backcolor = getconfig('backgroundcolor')
        self.buttoncolor = getconfig('buttoncolor')
        self.buttontextcolor = getconfig('buttontextcolor')
        self.labelcolor = getconfig('labelcolor')
        if self.backcolor != "":
            self.set_background_color(QColor(self.backcolor))
        if self.buttoncolor != "":
            self.set_button_color(QColor(self.buttoncolor))
        if self.labelcolor != "":
            self.set_label_color(QColor(self.labelcolor))
        if self.buttontextcolor != "":
            self.set_button_text_color(QColor(self.buttontextcolor))
    
    async def addchar(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        charid = self.id_entry.text().replace("https://character.ai/chat/", "") 
        name, description, author, avatar_file_name = await self.get_character()
        data.update({charid: {"name": name, "char": charid,  "description": description, "author": author}})
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        msg = QMessageBox()
        msg.setWindowTitle(tr('CharEditor', 'characteradded'))
        msg.setStyleSheet(self.styleSheet())
        response = requests.get(f"https://characterai.io/i/80/static/avatars/{avatar_file_name}?webp=true&anim=0")
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        msg.setWindowIcon(QIcon(pixmap))
        msg.setIconPixmap(pixmap)
        text = tr('CharEditor', 'yourchar') + name + tr('CharEditor', 'withid') + charid + tr('CharEditor', 'added')
        msg.setText(text)
        msg.exec()
        self.close()

    async def get_character(self):
        data = {
            'external_id': self.id_entry.text().replace("https://character.ai/chat/", "")
        }
        headers = {
            "Content-Type": 'application/json',
            "Authorization": f'Token {getconfig("client", configfile="charaiconfig.json")}'
        }
        response = requests.post('https://plus.character.ai/chat/character/info/', data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            jsn = response.json()
            character = jsn.get('character', {})            
            return character.get('name', 'No Name'), character.get('description', 'No description'), character.get('user__username', 'Unknown'),character.get('avatar_file_name', '')

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

class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(QPixmap)
    
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            image = QPixmap()
            image.loadFromData(response.content)
            self.image_loaded.emit(image)
        except Exception as e:
            print(f"Error loading the image: {e}")
            self.image_loaded.emit(QPixmap())

class CharacterWidget(QWidget):
    def __init__(self, CharacterSearch, data, mode):
        super().__init__()
        self.data = data
        self.local_data = CharacterSearch.local_data
        self.CharacterSearch = CharacterSearch
        self.mode = mode

        layout = QHBoxLayout()
        self.image_label = QLabel()
        layout.addWidget(self.image_label)

        text_buttons_layout = QHBoxLayout()

        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        text_buttons_layout.addWidget(self.text_label)

        buttons_layout = QVBoxLayout()
        self.network_addnovoice_button = QPushButton('Add without voice')
        self.network_addnovoice_button.setFixedWidth(200)
        self.network_addnovoice_button.clicked.connect(self.add_without_voice)

        self.network_addvoice_button = QPushButton('Search Voice')
        self.network_addvoice_button.setFixedWidth(200)
        self.network_addvoice_button.clicked.connect(self.add_with_voice)

        self.local_select_button = QPushButton('Select')
        self.local_select_button.clicked.connect(self.local_select_char)

        if mode == "network":
            name = data.get('participant__name', 'No Name')
            title = data.get('title', 'None')
            chats = data.get('score', '0')
            author = data.get('user__username', 'Unknown')
            description = data.get('description', 'None')
            avatar = data.get('avatar_file_name', '')
            self.image_label.setFixedSize(80, 80)

            full_description = description
            if f"{description}" != 'None' and len(f"{description}") > 220:
                description = description[:220] + '...'
            self.text_label.setMaximumWidth(400)
            buttons_layout.addWidget(self.network_addvoice_button)
            buttons_layout.addWidget(self.network_addnovoice_button)

            if f"{title}" == 'None' or f"{title}" == '':
                if f"{description}" == 'None':
                    text = f'<b>{name}</b><br>{chats} chats • By {author}'
                else:
                    self.text_label.setToolTip(full_description)
                    text = f'<b>{name}</b><br>{description}<br>{chats} chats • By {author}'
            else:
                if f"{description}" == 'None':
                    text = f'<b>{name}</b> - {title}<br>{chats} chats • By {author}'
                else:
                    self.text_label.setToolTip(full_description)
                    text = f'<b>{name}</b> - {title}<br>{description}<br>{chats} chats • By {author}'
        elif mode == "recent":
            name = data.get('character_name', 'No Name')
            avatar = data.get('character_avatar_uri', '')
            local_chars = self.local_data.keys()
            self.character_id = data.get('character_id', '')
            self.image_label.setFixedSize(50, 50)

            self.local_select_button.setFixedWidth(200)

            if self.character_id in local_chars:
                buttons_layout.addWidget(self.local_select_button)
            else:
                buttons_layout.addWidget(self.network_addvoice_button)
                buttons_layout.addWidget(self.network_addnovoice_button)

            text = f'<b>{name}</b>'
        elif mode == "recommend":
            name = data.get('participant__name', 'No Name')
            avatar = data.get('avatar_file_name', '')
            self.image_label.setFixedSize(50, 50)

            buttons_layout.addWidget(self.network_addvoice_button)
            buttons_layout.addWidget(self.network_addnovoice_button)

            text = f'<b>{name}</b>'
        
        self.threads = []
        if f"{avatar}" != "None":
            thread = threading.Thread(self.load_image_async(f'https://characterai.io/i/80/static/avatars/{avatar}?webp=true&anim=0'))
            thread.start()
            self.threads.append(thread)
        self.text_label.setText(text)

        text_buttons_layout.addLayout(buttons_layout)
        layout.addLayout(text_buttons_layout)
        self.setLayout(layout)

    def load_image_async(self, url):
        def set_image(self, pixmap):
            if self.mode == "network":
                self.image_label.setPixmap(pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            elif self.mode == "recent":
                self.image_label.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            elif self.mode == "recommend":
                self.image_label.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        self.image_loader_thread = ImageLoaderThread(url)
        self.image_loader_thread.image_loaded.connect(lambda image: set_image(self, image))
        self.image_loader_thread.start()

    def add_with_voice(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        if self.mode == "network":
            charid = self.data.get('external_id', 'No ID')
            name = self.data.get('participant__name', 'No Name')
            author = self.data.get('user__username', 'Unknown')
            avatar_url = self.data.get('avatar_file_name', '')
            description = self.data.get('description', 'No Description')
            title = self.data.get('title', 'None')
        elif self.mode == "recent":
            char = self.get_character()
            charid = char['external_id']
            name = char['participant__name']
            author = char['user__username']
            avatar_url = char['avatar_file_name']
            description = char['description']
            title = char['title']
        
        data[charid] = {"name": name, "char": charid, "avatar_url": avatar_url, "description": description, "title": title, "author": author}

        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.CharacterSearch.close()
        VoiceSearch(network_data=self.data).show()

    def add_without_voice(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        if self.mode == "network":
            charid = self.data.get('external_id', 'No ID')
            name = self.data.get('participant__name', 'No Name')
            author = self.data.get('user__username', 'Unknown')
            avatar_url = self.data.get('avatar_file_name', '')
            description = self.data.get('description', 'No Description')
            title = self.data.get('title', 'None')
        elif self.mode == "recent":
            char = self.get_character()
            charid = char['external_id']
            name = char['participant__name']
            author = char['user__username']
            avatar_url = char['avatar_file_name']
            description = char['description']
            title = char['title']

        data[charid] = {"name": name, "char": charid, "avatar_url": avatar_url, "description": description, "title": title, "author": author}

        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        msg = QMessageBox()
        msg.setWindowTitle("Oh")
        msg.setStyleSheet(self.styleSheet())
        msg.setWindowIcon(QIcon(emiliaicon))
        text = "The character has been successfully added"
        msg.setText(text)
        msg.exec()
        self.CharacterSearch.close()

    def get_character(self):
        headers = {
            "Content-Type": 'application/json',
            "Authorization": f'Token {getconfig("client", configfile="charaiconfig.json")}'
        }
        data = {
            "external_id": self.data['character_id']
        }
        character = requests.post("https://plus.character.ai/chat/character/info/", headers=headers, json=data)
        if character.status_code == 200:
            data = character.json()
            char = data['character']
            return char

    class IconLoaderThread(QThread):
        image_loaded = pyqtSignal(QPixmap, QListWidgetItem)

        def __init__(self, url, item):
            super().__init__()
            self.url = url
            self.item = item

        def run(self):
            try:
                response = requests.get(self.url)
                if response.status_code == 200:
                    image = QPixmap()
                    image.loadFromData(response.content)
                    self.image_loaded.emit(image, self.item)
            except Exception as e:
                print(f"Error loading the image: {e}")
                self.image_loaded.emit(QPixmap(), self.item)

    def local_select_char(self):
        self.CharacterSearch.main_window.voice_entry.setText(self.local_data[self.character_id].get('voiceid', ''))
        self.CharacterSearch.close()

    def closeEvent(self, event):
        for thread in self.threads:
            thread.quit()
        super().closeEvent(event)

class CharacterSearch(QWidget):
    def __init__(self, mainwindow):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Character Search")
        self.setGeometry(300, 300, 800, 400)

        main_layout = QVBoxLayout(self)
        self.main_window = mainwindow

        self.addchar_button = QPushButton(tr("CharEditor", "addchar"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)


        self.network_tab = QWidget()
        self.network_layout = QVBoxLayout(self.network_tab)

        self.network_search_input = QLineEdit()
        self.network_search_input.setPlaceholderText('Введите запрос...')
        self.network_search_input.returnPressed.connect(self.search_and_load)
        self.network_layout.addWidget(self.network_search_input)

        self.network_list_widget = QListWidget()
        self.network_layout.addWidget(self.network_list_widget)

        self.network_add_button = QPushButton('Add another characher')
        self.network_add_button.clicked.connect(self.open_NewCharacherEditor)

        self.network_buttons_layout = QVBoxLayout()
        self.network_buttons_layout.addWidget(self.network_add_button)

        self.network_layout.addLayout(self.network_buttons_layout)


        self.local_tab = QWidget()
        self.local_layout = QVBoxLayout(self.local_tab)

        self.local_list_widget = QListWidget()
        self.local_list_widget.itemClicked.connect(self.display_local_details)
        self.local_layout.addWidget(self.local_list_widget)

        self.local_image_label = QLabel()
        self.local_details_label = QLabel()
        self.local_details_label.setWordWrap(True)
        self.local_details_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        local_details_layout = QHBoxLayout()
        local_details_layout.addWidget(self.local_image_label, alignment=Qt.AlignmentFlag.AlignTop)
        local_details_layout.addWidget(self.local_details_label)

        self.local_buttons_layout = QHBoxLayout()
        self.local_layout.addLayout(local_details_layout)

        self.local_sel_del_buttons_layout = QVBoxLayout()
        self.local_buttons_layout.addLayout(self.local_sel_del_buttons_layout)

        self.local_select_button = QPushButton('Select')
        self.local_select_button.clicked.connect(self.local_select_char)
        self.local_select_button.setEnabled(False)
        self.local_sel_del_buttons_layout.addWidget(self.local_select_button)

        self.local_delete_button = QPushButton('Delete')
        self.local_delete_button.clicked.connect(self.local_delete_character)
        self.local_delete_button.setEnabled(False)
        self.local_sel_del_buttons_layout.addWidget(self.local_delete_button)

        self.local_voice_buttons_layout = QVBoxLayout()
        self.local_buttons_layout.addLayout(self.local_voice_buttons_layout)
        self.local_sel_del_voice_buttons_layout = QHBoxLayout()
        self.local_voice_buttons_layout.addLayout(self.local_sel_del_voice_buttons_layout)

        self.local_edit_voice_button = QPushButton('Edit Voice')
        self.local_edit_voice_button.clicked.connect(self.local_add_char_voice)
        self.local_edit_voice_button.setEnabled(False)
        self.local_voice_buttons_layout.addWidget(self.local_edit_voice_button)

        self.local_add_voice_button = QPushButton('Add Voice')
        self.local_add_voice_button.clicked.connect(self.local_add_char_voice)
        self.local_add_voice_button.setEnabled(False)
        self.local_sel_del_voice_buttons_layout.addWidget(self.local_add_voice_button)

        self.local_delete_voice_button = QPushButton('Delete Voice')
        self.local_delete_voice_button.clicked.connect(self.local_delete_voice)
        self.local_delete_voice_button.setEnabled(False)
        self.local_sel_del_voice_buttons_layout.addWidget(self.local_delete_voice_button)
        
        self.local_layout.addLayout(self.local_buttons_layout)

        self.tab_widget.addTab(self.network_tab, "Search New Characters")
        self.tab_widget.addTab(self.local_tab, "Saved Character")

        main_layout.addWidget(self.tab_widget)

        self.setLayout(main_layout)

        self.backcolor = getconfig('backgroundcolor')
        self.buttoncolor = getconfig('buttoncolor')
        self.buttontextcolor = getconfig('buttontextcolor')
        self.labelcolor = getconfig('labelcolor')
        if self.backcolor != "":
            self.set_background_color(QColor(self.backcolor))
        if self.buttoncolor != "":
            self.set_button_color(QColor(self.buttoncolor))
        if self.labelcolor != "":
            self.set_label_color(QColor(self.labelcolor))
        if self.buttontextcolor != "":
            self.set_button_text_color(QColor(self.buttontextcolor))

        self.recommend_recent_items = []

        self.load_local_data()
        self.populate_recent_list()
        self.populate_recommend_list()

    def open_NewCharacherEditor(self):
        window = NewCharacterEditor()
        window.show()
        self.close()

    def local_delete_character(self):
        char_id = self.current_local_data.get('char', 'No ID')
        if char_id in self.local_data:
            del self.local_data[char_id]
            self.save_local_data()
            self.load_local_data()
            self.populate_local_list()
            self.local_image_label.clear()
            self.local_details_label.clear()
        else:
            msg = QMessageBox()
            msg.setStyleSheet(self.styleSheet())
            msg.setWindowTitle("Error")
            msg.setWindowIcon(QIcon(emiliaicon))
            msg.setText("Character not found in local data.")
            msg.exec()

    def local_delete_voice(self):
        char_id = self.current_local_data.get('char', 'No ID')
        if char_id in self.local_data:
            if 'voiceid' in self.local_data[char_id]:
                del self.local_data[char_id]['voiceid']
            self.save_local_data()
            self.load_local_data()
            charid = self.current_local_data.get('char', 'No ID')
            name = self.current_local_data.get('name', 'No Name')
            author = self.current_local_data.get('author', 'Unknown')
            description = self.current_local_data.get('description', 'No Description')
            self.local_details_label.setText(f"<b>{name}</b> by {author}<br>{description}<br>ID: {charid}<br>Voice ID: No Voice ID")
        else:
            msg = QMessageBox()
            msg.setStyleSheet(self.styleSheet())
            msg.setWindowTitle("Error")
            msg.setWindowIcon(QIcon(emiliaicon))
            msg.setText("Character not found in local data.")
            msg.exec()

    def local_add_char_voice(self):
        self.close()
        VoiceSearch(local_data=self.current_local_data).show()

    def local_select_char(self):
        self.main_window.voice_entry.setText(self.current_local_data.get('voiceid', ''))
        self.close()

    def populate_list(self, data, mode):
        item = QListWidgetItem()
        custom_widget = CharacterWidget(self, data, mode)
        
        item.setSizeHint(custom_widget.sizeHint())
        self.network_list_widget.addItem(item)
        self.network_list_widget.setItemWidget(item, custom_widget)

    def populate_category_header(self, category_name):
        header_item = QListWidgetItem()
        header_widget = QLabel(f"<b>{category_name}</b>")
        header_widget.setStyleSheet("font-size: 20pt;")
        header_widget.setFixedHeight(30)
        header_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_item.setSizeHint(header_widget.sizeHint())
        self.network_list_widget.addItem(header_item)
        self.network_list_widget.setItemWidget(header_item, header_widget)

    def populate_network_list(self):
        self.network_list_widget.clear()
        if not self.network_data or not isinstance(self.network_data, list):
            return

        for data in self.network_data[0].get("result", {}).get("data", {}).get("json", []):
            self.populate_list(data, "network")

        self.network_add_button.setVisible(False)

    def populate_recent_list(self):
        self.populate_category_header("Recent Chats")
        if self.main_window.recent_list:
            data = self.main_window.recent_list
            for chats in data:
                if chats['character_id'] not in self.recommend_recent_items:
                    self.recommend_recent_items.append(chats['character_id'])
                    self.populate_list(chats, "recent")
        else:
            headers = {
                "Content-Type": 'application/json',
                "Authorization": f'Token {getconfig("client", configfile="charaiconfig.json")}'
            }
            recent_list = requests.get("https://neo.character.ai/chats/recent", headers=headers)
            if recent_list.status_code == 200:
                data = recent_list.json()
                for chats in data['chats']:
                    if chats['character_id'] not in self.recommend_recent_items:
                        self.recommend_recent_items.append(chats['character_id'])
                        self.main_window.recent_list.append(chats)
                        self.populate_list(chats, "recent")

    def populate_recommend_list(self):
        self.populate_category_header("For You")
        if self.main_window.recommend_list:
            data = self.main_window.recommend_list
            for recommend in data:
                if recommend['external_id'] not in self.recommend_recent_items:
                    self.recommend_recent_items.append(recommend['external_id'])
                    self.populate_list(recommend, "recommend")
        else:
            headers = {
                "Content-Type": 'application/json',
                "Authorization": f'Token {getconfig("client", configfile="charaiconfig.json")}'
            }
            recommend_list = requests.get("https://neo.character.ai/recommendation/v1/user", headers=headers)
            if recommend_list.status_code == 200:
                data = recommend_list.json()
                for recommend in data['characters']:
                    if recommend['external_id'] not in self.recommend_recent_items:
                        self.recommend_recent_items.append(recommend['external_id'])
                        self.main_window.recommend_list.append(recommend)
                        self.populate_list(recommend, "recommend")

    def populate_local_list(self):
        self.local_list_widget.clear()
        if not self.local_data:
            return
        for charid, char_data in self.local_data.items():
            name = char_data.get('name', 'No Name')
            title = char_data.get('title', 'None')
            author = char_data.get('author', 'Unknown')
            if title == 'None' or title == '':
                list_item = QListWidgetItem(f'{name}')
            else:
                list_item = QListWidgetItem(f'{name} - {title}')
            list_item.setData(1, char_data)
            self.local_list_widget.addItem(list_item)

    def display_local_details(self, item):
        data = item.data(1)
        self.current_local_data = data
        voiceid = data.get('voiceid', 'No Voice ID')
        voice = data.get('voice', 'No Voice')
        self.local_details_label.setText(f"<b>{data.get('name', 'No Name')}</b> • By {data.get('author', 'Unknown')}<br>{data.get('description', 'No Description')}<br>ID: {data.get('char', 'No ID')}<br>Voice ID: {voiceid}")
        if voiceid == 'No Voice ID':
            self.local_add_voice_button.setEnabled(True)
            self.local_edit_voice_button.setEnabled(False)
            self.local_delete_voice_button.setEnabled(False)
        else:
            self.local_add_voice_button.setEnabled(False)
            self.local_edit_voice_button.setEnabled(True)
            self.local_delete_voice_button.setEnabled(True)
        self.local_select_button.setEnabled(True)
        self.local_delete_button.setEnabled(True)


        avatar_url = data.get('avatar_url', '')
        if avatar_url:
            self.load_image_async(f"https://characterai.io/i/80/static/avatars/{avatar_url}?webp=true&anim=0", self.local_image_label)
        else:
            self.local_image_label.clear()

    def on_tab_changed(self, index):
        if index == 1:
            self.populate_local_list()

    def load_image_async(self, url, label):
        self.image_loader_thread = ImageLoaderThread(url)
        self.image_loader_thread.image_loaded.connect(label.setPixmap)
        self.image_loader_thread.start()

    def search_and_load(self):
        search_query = self.network_search_input.text().strip()
        if not search_query:
            return

        try:
            response = requests.get(f'https://character.ai/api/trpc/search.search?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{search_query}%22%7D%7D%7D')
            if response.status_code == 200:
                self.network_data = response.json()
                self.populate_network_list()
            else:
                print(f"Error receiving data: {response.status_code}")
        except Exception as e:
            print(f"Error when executing the request: {e}")

    def load_local_data(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                self.local_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.local_data = {}

    def save_local_data(self):
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(self.local_data, f, ensure_ascii=False, indent=4)

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

class VoiceSearch(QWidget):
    def __init__(self, network_data="", local_data=""):
        super().__init__()
        self.network_data = network_data
        self.local_data = local_data

        self.setWindowTitle('Emilia: Voice Search')
        self.setWindowIcon(QIcon(emiliaicon))
        self.setGeometry(300, 300, 800, 400)

        self.addchar_button = QPushButton(tr("CharEditor", "addchar"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.search_and_load)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.display_details)

        self.details_label = QLabel()
        self.details_label.setWordWrap(True)

        self.preview_text_label = QLabel()

        self.play_button = QPushButton('Play an example')
        self.play_button.clicked.connect(self.play_audio)
        self.play_button.setEnabled(False)

        self.select_button = QPushButton('Select')
        self.select_button.clicked.connect(self.addcharvoice)
        self.select_button.setEnabled(False)

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.select_button)


        main_layout = QVBoxLayout()
        main_layout.addWidget(self.search_input)
        main_layout.addWidget(self.list_widget)
        main_layout.addWidget(self.details_label)
        main_layout.addWidget(self.preview_text_label)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def populate_list(self):
        self.list_widget.clear()
        for item in self.data['voices']:
            description = item['description']
            if description == "":
                list_item = QListWidgetItem(f"{item['name']} • By {item['creatorInfo']['username']}")
            else:
                list_item = QListWidgetItem(f"{item['name']} - {description}\n• By {item['creatorInfo']['username']}")
            list_item.setData(1, item)
            self.list_widget.addItem(list_item)

    def display_details(self, item):
        data = item.data(1)
        self.current_data = data
        self.details_label.setText(f"<b>{data['name']}</b> • By {data['creatorInfo']['username']}<br>{data['description']}")
        self.preview_text_label.setText(f"An example phrase: {data['previewText']}")
        self.current_audio_uri = data['previewAudioURI']
        self.play_button.setEnabled(True)
        self.select_button.setEnabled(True)

    def play_audio(self):
        if hasattr(self, 'current_audio_uri'):
            try:
                response = requests.get(self.current_audio_uri, stream=True)
                if response.status_code == 200:
                    audio_bytes = io.BytesIO(response.content)
                    audio_array, samplerate = sf.read(audio_bytes)
                    sd.play(audio_array, samplerate)
            except Exception as e:
                print(f"Error loading and playing audio: {e}")

    def search_and_load(self):
        search_query = self.search_input.text().strip()
        if not search_query:
            return

        try:
            url = f'https://neo.character.ai/multimodal/api/v1/voices/search?query={search_query}'
            headers = {
                "Content-Type": 'application/json',
                "Authorization": f'Token {getconfig("client", configfile="charaiconfig.json")}'
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                self.data = response.json()
                self.populate_list()
            else:
                print(f"Error receiving data: {response.status_code}")
        except Exception as e:
            print(f"Error when executing the request: {e}")

    def addcharvoice(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        if self.network_data == "":
            charid = self.local_data.get('char', 'No ID')
            name = self.local_data.get('name', 'No Name')
            avatar_url = self.local_data.get("avatar_url", '')
            author = self.local_data.get('author', 'Unknown')
            description = self.local_data.get('description', 'No Description')
            title = self.local_data.get('title', '')
            voice = self.local_data.get('voice', '')
            text = "The character has been successfully edited"
            if voice == '':
                data.update({charid: {"name": name, "char": charid, "avatar_url": avatar_url, "description": description, "title": title, "author": author, "voiceid": self.current_data['id']}})
            else:
                data.update({charid: {"name": name, "char": charid, "avatar_url": avatar_url, "description": description, "title": title, "author": author, "voice": voice, "voiceid": self.current_data['id']}})
        else:
            charid = self.network_data.get('external_id', 'No ID')
            name = self.network_data.get('participant__name', 'No Name')
            avatar_url = self.network_data.get('avatar_file_name', '')
            author = self.network_data.get('user__username', 'Unknown')
            description = self.network_data.get('description', 'No Description')
            title = self.network_data.get('title', 'None')
            text = "The character has been successfully added"
            data.update({charid: {"name": name, "char": charid, "avatar_url": avatar_url, "description": description, "title": title, "author": author, "voiceid": self.current_data['id']}})
            

        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        msg = QMessageBox()
        msg.setWindowTitle("Oh")
        msg.setStyleSheet(self.styleSheet())
        msg.setWindowIcon(QIcon(emiliaicon))
        msg.setText(text)
        msg.exec()
        self.close()

class EmiliaAuth(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Getting Token")
        self.setFixedWidth(300)
        self.setMinimumHeight(100)

        self.layout = QVBoxLayout()

        email_layout = QHBoxLayout()
        self.email_label = QLabel(tr("GetToken","youremail"))
        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("example@example.com")

        email_layout.addWidget(self.email_label)
        email_layout.addWidget(self.email_entry)
        self.layout.addLayout(email_layout)


        self.getlink_button = QPushButton(tr("GetToken", "sendemail"))
        self.getlink_button.clicked.connect(lambda: self.getlink())
        self.layout.addWidget(self.getlink_button)

        self.link_layout = QHBoxLayout()
        self.link_label = QLabel(tr("GetToken", "linkfromemail"))
        self.link_entry = QLineEdit()
        self.link_entry.setPlaceholderText("https...")

        self.link_layout.addWidget(self.link_label)
        self.link_layout.addWidget(self.link_entry)
        

        self.gettoken_button = QPushButton(tr("GetToken", "gettoken"))
        self.gettoken_button.clicked.connect(lambda: self.gettoken())
        
        self.setLayout(self.layout)

        self.backcolor = getconfig('backgroundcolor')
        self.buttoncolor = getconfig('buttoncolor')
        self.buttontextcolor = getconfig('buttontextcolor')
        self.labelcolor = getconfig('labelcolor')
        if self.backcolor != "":
            self.set_background_color(QColor(self.backcolor))
        if self.buttoncolor != "":
            self.set_button_color(QColor(self.buttoncolor))
        if self.labelcolor != "":
            self.set_label_color(QColor(self.labelcolor))
        if self.buttontextcolor != "":
            self.set_button_text_color(QColor(self.buttontextcolor))

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
            self.email_label.setText(tr("GetToken", "yourtoken") + token + tr("GetToken", "saveincharaiconfig"))
            writeconfig('client', token, 'charaiconfig.json')
        except Exception as e:
            msg = QMessageBox()
            msg.setStyleSheet(self.styleSheet())
            msg.setWindowTitle(tr("Errors", "Label"))
            msg.setWindowIcon(QIcon(emiliaicon))
            text = tr("Errors", "other") + str(e)
            msg.setText(text)
            msg.exec()

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
        self.setFixedWidth(300)
        self.setMinimumHeight(150)

        self.recommend_list = []
        self.recent_list = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        hlayout = QHBoxLayout()

        self.char_label = QLabel(tr("MainWindow", "characterid"))
        self.char_label.setWordWrap(True)

        self.char_entry = QLineEdit()
        self.char_entry.setPlaceholderText("ID...")
        self.char_entry.textChanged.connect(lambda: writeconfig("char", self.char_entry.text().replace("https://character.ai/chat/", ""), "charaiconfig.json"))
        self.char_entry.setText(getconfig('char', configfile='charaiconfig.json'))

        self.client_label = QLabel(tr("MainWindow", "charactertoken"))
        self.client_label.setWordWrap(True)

        self.client_entry = QLineEdit()
        self.client_entry.setPlaceholderText(tr("MainWindow", "token"))
        self.client_entry.textChanged.connect(lambda: writeconfig("client", self.client_entry.text(), "charaiconfig.json"))
        self.client_entry.setText(getconfig('client', configfile='charaiconfig.json'))

        hlayout.addWidget(self.char_label)
        hlayout.addWidget(self.char_entry)
        hlayout.addWidget(self.client_label)
        hlayout.addWidget(self.client_entry)
        
        self.layout.addLayout(hlayout)

        self.voice_layout = QHBoxLayout()
        self.voice_entry = QLineEdit()
        self.voice_label = QLabel()
        self.voice_label.setText(tr("MainWindow", "voiceid"))
        self.voice_entry.setToolTip(tr("MainWindow", "voiceidtooltip"))
        self.voice_entry.textChanged.connect(lambda: writeconfig("voiceid", self.voice_entry.text().replace("https://character.ai/?voiceId=", ""), "charaiconfig.json"))
        self.voice_entry.setText(getconfig('voiceid', configfile="charaiconfig.json"))
        self.voice_layout.addWidget(self.voice_label)
        self.voice_layout.addWidget(self.voice_entry)

        self.microphone = ""
        self.selected_device_index = ""

        if backcolor != "":
            self.set_background_color(QColor(backcolor))
        if buttoncolor != "":
            self.set_button_color(QColor(buttoncolor))
        if labelcolor != "":
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor != "":
            self.set_button_text_color(QColor(buttontextcolor))

        self.vstart_button = QPushButton(tr("MainWindow", "start"))
        self.vstart_button.clicked.connect(lambda: self.start_main("voice"))

        self.user_input = QLabel("")
        self.user_input.setWordWrap(True)

        self.user_aiinput = QLineEdit()
        self.user_aiinput.setPlaceholderText(tr("MainWindow", "textmodeinput"))

        self.tstart_button = QPushButton(tr("MainWindow", "starttext"))
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

        self.gettokenaction = QAction(QIcon(charaiicon), tr("MainWindow", 'gettoken'), self)
        self.gettokenaction.triggered.connect(lambda: self.gettoken())

        self.optionsopenaction = QAction(tr("MainWindow", "optionsopenaction"))
        self.optionsopenaction.triggered.connect(lambda: self.optionsopen())

        self.visibletextmode = QAction(QIcon(keyboardicon), tr("MainWindow", 'usetextmode'), self)
        self.visibletextmode.triggered.connect(lambda: self.modehide("text"))

        self.visiblevoicemode = QAction(QIcon(inputicon), tr("MainWindow", 'usevoicemode'), self)
        self.visiblevoicemode.triggered.connect(lambda: self.modehide("voice"))
        self.visiblevoicemode.setVisible(False)

        self.recognizer = sr.Recognizer()
        self.mic_list = [
            mic_name for mic_name in sr.Microphone.list_microphone_names()
            if any(keyword in mic_name.lower() for keyword in ["microphone", "mic", "input"])
        ]

        self.inputdeviceselect = QMenu(tr("MainWindow", 'inputdevice'), self)

        for index, mic_name in enumerate(self.mic_list):
            action = QAction(mic_name, self)
            action.triggered.connect(lambda checked, i=index: self.set_microphone(i))
            self.inputdeviceselect.addAction(action)

        self.outputdeviceselect = QMenu(tr("MainWindow", 'outputdevice'), self)

        self.unique_devices = {}
        for dev in sd.query_devices():
            if dev["max_output_channels"] > 0 and dev["name"] not in self.unique_devices:
                self.unique_devices[dev["name"]] = dev

        for index, (name, device) in enumerate(self.unique_devices.items()):
            action = QAction(name, self)
            action.triggered.connect(lambda checked, i=index: self.set_output_device(i))
            self.outputdeviceselect.addAction(action)

        self.charselect = self.menubar.addMenu(tr("MainWindow", 'charchoice'))
        self.chareditopen = QAction(QIcon(charediticon), tr("MainWindow", 'openchareditor'), self)
        self.chareditopen.triggered.connect(lambda: CharacterEditor().show())

        self.CharacterSearchopen = QAction(QIcon(charediticon), "Character Search", self)
        self.CharacterSearchopen.triggered.connect(lambda: self.charsopen())

        self.charrefreshlist = QAction(QIcon(refreshicon), tr("MainWindow", "refreshcharacters"))
        self.charrefreshlist.triggered.connect(lambda: self.addcharsinmenubar())

        self.charselect.addAction(self.chareditopen)
        self.charselect.addAction(self.CharacterSearchopen)
        self.charselect.addAction(self.charrefreshlist)

        self.addcharsinmenubar()

        self.aboutemi = QAction(QIcon(emiliaicon), tr("MainWindow", 'aboutemi'), self)
        self.aboutemi.triggered.connect(self.about)

        self.emi_menu.addAction(self.gettokenaction)
        self.emi_menu.addAction(self.visibletextmode)
        self.emi_menu.addAction(self.visiblevoicemode)
        self.emi_menu.addAction(self.optionsopenaction)
        self.emi_menu.addAction(self.aboutemi)
        self.emi_menu.addMenu(self.inputdeviceselect)
        self.emi_menu.addMenu(self.outputdeviceselect)

    def optionsopen(self):
        window = OptionsWindow(self)
        window.show()

    def charsopen(self):
        window = CharacterSearch(self)
        window.show()

    def addcharsinmenubar(self):
        if os.path.exists('config.json'):
            def open_json(char, speaker):
                self.char_entry.setText(char)
                self.voice_entry.setText(speaker)
            def create_action(key, value):
                def action_func():
                    open_json(value['char'], value['voiceid'])
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
                self.charselect.addAction(action)

    def set_microphone(self, index):
        self.microphone = sr.Microphone(device_index=index)

    def set_output_device(self, index):
        device = list(self.unique_devices.values())[index]
        sd.default.device = device["index"]
        self.selected_device_index = index

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

    def devicechange(self, device):
        writeconfig('devicefortorch', device)

    def langchange(self, lang):
        writeconfig('language', lang)
        os.remove("voice.pt")
        os.execv(sys.executable, ['python'] + sys.argv)

    def gettoken(self):
        self.auth_window = EmiliaAuth()
        self.auth_window.show()

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
        msg = QMessageBox()
        if pre == True:
            msg.setWindowTitle(tr("About", "aboutemi") + build)
        else:
            msg.setWindowTitle(tr("About", "aboutemi"))
        msg.setStyleSheet(self.styleSheet())
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        language = tr("About", "languagefrom")
        whatsnew = tr("About", "newin") + version + tr("About", "whatsnew")
        otherversions = tr("About", "viewallreleases")
        text = tr("About", "emiopenproject") + version + tr("About", "usever") + language + whatsnew + otherversions
        msg.setText(text)
        msg.exec()
    
    async def charai_tts(self, message):
        data = {
            'candidateId': re.search(r"candidate_id='([^']*)'", (str(message.candidates))).group(1),
            'roomId': message.turn_key.chat_id,
            'turnId': message.turn_key.turn_id,
            'voiceId': self.voice_entry.text().replace("https://character.ai/chat/", ""),
            'voiceQuery': message.name
        }
        headers = {
                "Content-Type": 'application/json',
                "Authorization": f'Token {self.client_entry.text()}'
            }
        response = requests.post('https://neo.character.ai/multimodal/api/v1/memo/replay', data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            voice = response.json()
            link = voice["replayUrl"]
            download = requests.get(link, stream=True)
            if download.status_code == 200:
                audio_bytes = io.BytesIO(download.content)
                audio_array, samplerate = sf.read(audio_bytes)
                return audio_array, samplerate
        else:
            print("Character.AI TTS Error")

    async def main(self):
        vtubeenable = getconfig('vtubeenable', "False")
        tts = getconfig('tts', 'silerotts')
        self.layout.addWidget(self.user_input)
        self.layout.addWidget(self.ai_output)
        token = aiocai.Client(self.client_entry.text())
        character = self.char_entry.text().replace("https://character.ai/chat/", "")
        Account = await token.get_me()
        try:
            chatid = await token.get_chat(character)
        except:
            chatid = await token.new_chat(character, Account.id)
        persona = await token.get_persona(character)
        username = f"{Account.name}: "
        ai = f"{persona.name}: "
        while True:
            if vtubeenable == "True":
                await EEC().UseEmote("Listening")
            recognizer = sr.Recognizer()
            self.user_input.setText(username + tr("Main", "speakup"))
            while True:
                if self.microphone != "":
                    with self.microphone as source:
                        audio = recognizer.listen(source)
                else:
                    with sr.Microphone() as source:
                        audio = recognizer.listen(source)
                try:
                    msg1 = recognizer.recognize_google(audio, language="ru-RU" if lang == "ru_RU" else "en-US")
                    break
                except sr.UnknownValueError:
                    self.user_input.setText(username + tr("Main", "sayagain"))
            self.user_input.setText(username + msg1)
            self.ai_output.setText(ai + tr("Main", "emigen"))
            if vtubeenable == "True":
                await EEC().UseEmote("Thinks")
            async with await token.connect() as chat:
                messagenotext = await chat.send_message(character, chatid.chat_id, msg1)
                message = messagenotext.text
            if vtubeenable == "True":
                await EEC().UseEmote("VoiceGen")
            self.ai_output.setText(ai + message)
            if vtubeenable == "True":
                await EEC().UseEmote("Says")
            try:
                audio, sample_rate = await self.charai_tts(messagenotext)
                device = list(self.unique_devices.values())[
                    self.selected_device_index] if self.selected_device_index != "" else None
                sd.play(audio, sample_rate, device=device["index"] if device else None)
                time.sleep(len(audio - 5) / sample_rate)
                sd.stop()
            except Exception as e:
                print(tr('Errors', 'other') + str(e))
                continue
            if vtubeenable == "True":
                await EEC().UseEmote("AfterSays")

    async def maintext(self):
        if self.user_aiinput.text() == "" or self.user_aiinput.text() == tr("MainWindow", "butemptyhere"):
            self.user_aiinput.setText(tr("MainWindow", "butemptyhere"))
        else:
            vtubeenable = getconfig('vtubeenable', "False")
            self.layout.addWidget(self.ai_output)
            token = aiocai.Client(self.client_entry.text())
            character = self.char_entry.text().replace("https://character.ai/chat/", "")
            try:
                chatid = await token.get_chat(character)
            except:
                Account = await token.get_me()
                chatid = await token.new_chat(character, Account.id)
            persona = await token.get_persona(character)
            ai = f"{persona.name}: "
            if vtubeenable == "True":
                await EEC().UseEmote("Thinks")
            msg1 = self.user_aiinput.text()
            self.ai_output.setText(ai + tr("Main", "emigen"))
            async with await token.connect() as chat:
                messagenotext = await chat.send_message(character, chatid.chat_id, msg1)
                message = messagenotext.text
            if vtubeenable == "True":
                await EEC().UseEmote("VoiceGen")
            self.ai_output.setText(ai + message)
            if vtubeenable == "True":
                await EEC().UseEmote("Says")
            try:
                audio, sample_rate = await self.charai_tts(messagenotext)
                device = list(self.unique_devices.values())[
                    self.selected_device_index] if self.selected_device_index != "" else None
                sd.play(audio, sample_rate, device=device["index"] if device else None)
                time.sleep(len(audio - 5) / sample_rate)
                sd.stop()
            except Exception as e:
                print(tr('Errors', 'other') + str(e))
            if vtubeenable == "True":
                await EEC().UseEmote("Listening")

    def start_main(self, mode):
        if mode == "voice":
            threading.Thread(target=lambda: asyncio.run(self.main())).start()
            self.char_label.setVisible(False)
            self.char_entry.setVisible(False)
            self.client_label.setVisible(False)
            self.client_entry.setVisible(False)
            self.voice_label.setVisible(False)
            self.voice_entry.setVisible(False)
            self.vstart_button.setVisible(False)
            self.tstart_button.setVisible(False)
            self.user_aiinput.setVisible(False)
            self.menubar.setVisible(False)
            self.user_input.setVisible(True)
        elif mode == "text":
            threading.Thread(target=lambda: asyncio.run(self.maintext())).start()

if __name__ == "__main__":
    if autoupdate_enable != "False":
        AutoUpdate().check_for_updates()
    app = QApplication(sys.argv)
    app.setStyle(theme)
    if not os.path.exists('config.json'):
        window = FirstLaunch()
    else:
        window = Emilia()
    if getconfig('vtubeenable', "False") == "True":
        asyncio.run(EEC().VTubeConnect())
    window.show()
    sys.exit(app.exec())