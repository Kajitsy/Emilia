# pyinstaller --noconfirm --onefile --windowed --icon "Emilia\images\premilia.ico" --add-data "Emilia\images;images/" --add-data "Emilia\locales;locales/"  "Emilia\emilia_charai.py"

import io
import os
import asyncio
import winreg
import threading
import zipfile
import requests
import aiohttp
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

version = "2.2.2"
build = "20240803"
pre = True
sample_rate = 48000

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
    emotesjson = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/Emotes.json")
    emotesjson.raise_for_status()
    with open("Emotes.json", "wb") as f:
            f.write(emotesjson.content)

def MessageBox(title = "Emilia", text = "Hm?", icon = emiliaicon, pixmap = None,self = None): 
    msg = QMessageBox()
    msg.setWindowTitle(title)
    if self: msg.setStyleSheet(self.styleSheet())
    if pixmap: msg.setIconPixmap(pixmap)
    msg.setWindowIcon(QIcon(icon))
    msg.setText(text)
    msg.exec()

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
        print(f"{tr('AutoUpdate', 'upgrade_to')} {build}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"{tr('Errors', 'UpdateDownloadError')} {e}")
            writeconfig('autoupdate_enable', 'False')
            return
        with open(f"Emilia_{build}.zip", "wb") as f:
            f.write(response.content)

        with zipfile.ZipFile(f"Emilia_{build}.zip", "r") as zip_ref:
            zip_ref.extractall(".")

        os.remove(f"Emilia_{build}.zip")

        MessageBox("Update!", f"{tr('AutoUpdate', 'emilia_updated')} {build}!")

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

        self.first_launch_notification_label = QLabel(tr('FirstLaunch', 'first_launch_notification_label'))
        self.first_launch_notification_label.setWordWrap(True)
        self.layout.addWidget(self.first_launch_notification_label)

        fphlayout = QHBoxLayout()
        self.layout.addLayout(fphlayout)
        self.first_launch_notification_button_yes = QPushButton(tr('FirstLaunch', 'first_launch_notification_button_yes'))
        self.first_launch_notification_button_yes.clicked.connect(self.second_page)
        fphlayout.addWidget(self.first_launch_notification_button_yes)

        self.first_launch_notification_button_no = QPushButton(tr('FirstLaunch', 'first_launch_notification_button_no'))
        self.first_launch_notification_button_no.clicked.connect(self.first_launch_button_no)
        fphlayout.addWidget(self.first_launch_notification_button_no)
        
        self.central_widget.setLayout(self.layout)

        # Second Page

        self.second_page_widget = QWidget()
        self.second_page_layout = QVBoxLayout()
        self.second_page_widget.setLayout(self.second_page_layout)

        self.autoupdate_layout = QHBoxLayout()
        self.autoupdate = QCheckBox()
        if getconfig('autoupdate_enable', 'False') == "True":
            self.autoupdate.setChecked(True)
        self.autoupdate.stateChanged.connect(self.autoupdate_change)

        self.autoupdate_layout.addWidget(QLabel(tr("OptionsWindow", 'automatic_updates')))
        self.autoupdate_layout.addWidget(self.autoupdate)
        self.second_page_layout.addLayout(self.autoupdate_layout)


        self.vtubelayout = QHBoxLayout()
        self.vtubecheck = QCheckBox()
        if getconfig('vtubeenable', 'False') == "True":
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

        self.theme_layout.addWidget(QLabel(tr("OptionsWindow", "select_theme")))
        self.theme_layout.addWidget(self.themechange)
        self.second_page_layout.addLayout(self.theme_layout)


        self.iconcolorlayout = QHBoxLayout()
        self.iconcolorchange = QComboBox()
        self.iconcolorchange.addItems([tr("OptionsWindow", 'white'), tr("OptionsWindow", 'black')])
        iconcolor = getconfig('iconcolor', 'white')
        if iconcolor == 'black':
            self.iconcolorchange.setCurrentIndex(1)
        self.iconcolorchange.currentTextChanged.connect(self.changeiconcolor)

        self.iconcolorlayout.addWidget(QLabel(tr("OptionsWindow", "pick_icon_color")))
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
        self.email_label = QLabel(tr("GetToken","your_email"))
        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("example@example.com")

        email_layout.addWidget(self.email_label)
        email_layout.addWidget(self.email_entry)
        self.third_page_layout.addLayout(email_layout)

        self.getlink_button = QPushButton(tr("GetToken", "send_email"))
        self.getlink_button.clicked.connect(lambda: self.getlink())
        self.third_page_layout.addWidget(self.getlink_button)

        self.getlink_button = QPushButton(tr("GetToken", "send_email"))
        self.getlink_button.clicked.connect(self.getlink)

        self.link_layout = QHBoxLayout()
        self.link_label = QLabel(tr("GetToken", "link_from_email"))
        self.link_entry = QLineEdit()
        self.link_entry.setPlaceholderText("https...")

        self.link_layout.addWidget(self.link_label)
        self.link_layout.addWidget(self.link_entry)

        self.gettoken_button = QPushButton(tr("GetToken", "get_token"))
        self.gettoken_button.clicked.connect(self.gettoken)

        # Fourth Page

        self.fourth_page_widget = QWidget()
        self.fourth_page_layout = QVBoxLayout()
        self.fourth_page_widget.setLayout(self.fourth_page_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("CharEditor", 'network_search_input'))
        self.search_input.returnPressed.connect(self.search_and_load)
        self.fourth_page_layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.fourth_page_layout.addWidget(self.list_widget)

        self.add_another_charcter_button = QPushButton(tr("CharEditor", 'add_another_charcter_button'))
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
                MessageBox(tr('Errors', 'Label'), f"Error receiving data: {response.status_code}")
        except Exception as e:
            MessageBox(tr('Errors', 'Label'), f"Error when executing the request: {e}")

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
            MessageBox(text=tr('FirstLaunch', 'token_saves'))
            writeconfig('client', token, 'charaiconfig.json')
            self.first_launch_notification_label.setText(tr('FirstLaunch', 'third_page'))
            self.layout.addWidget(self.fourth_page_widget)
        except Exception as e:
            MessageBox(tr("Errors", "Label"), tr("Errors", "other") + str(e))

    def getlink(self):
        try:
            sendCode(self.email_entry.text())
            self.email_entry.setEnabled(False)
            self.getlink_button.setEnabled(False)
            self.third_page_layout.addLayout(self.link_layout)
            self.third_page_layout.addWidget(self.gettoken_button)
        except Exception as e:
            MessageBox(tr("Errors", "Label"), tr("Errors", "other") + str(e))

    def second_page_continue(self):
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'use_characterai'))
        self.second_page_widget.setVisible(False)
        self.layout.addWidget(self.third_page_widget)

    def vtubechange(self, state):
        if state == 2:
            writeconfig('vtubeenable', "True")
        else:
            writeconfig('vtubeenable', "False")

    def change_theme(self):
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
            writeconfig('iconcolor', 'white')
        elif value == 1:
            writeconfig('iconcolor', 'black')

    def autoupdate_change(self, state):
        if state == 2:
            writeconfig('autoupdate_enable', "True")
        else:
            writeconfig('autoupdate_enable', "False")

    def second_page(self):
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'second_page'))
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
        if getconfig('autoupdate_enable', 'False') == "True":
            self.autoupdate.setChecked(True)
        self.autoupdate.stateChanged.connect(self.autoupdatechange)


        autoupdatelayout.addWidget(QLabel(tr(self.trl, 'automatic_updates')))
        autoupdatelayout.addWidget(self.autoupdate)
        firsthalf.addLayout(autoupdatelayout)


        langlayout = QHBoxLayout()
        self.languagechange = QComboBox()
        self.languagechange.addItems([tr(self.trl, 'english'), tr(self.trl, 'russian')])
        if lang == "ru_RU":
            self.languagechange.setCurrentIndex(1)
        self.languagechange.currentTextChanged.connect(lambda: self.langchange())

        langlayout.addWidget(QLabel(tr(self.trl, 'select_language')))
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

        themelayout.addWidget(QLabel(tr(self.trl, "select_theme")))
        themelayout.addWidget(self.themechange)
        firsthalf.addLayout(themelayout)


        iconcolorlayout = QHBoxLayout()
        self.iconcolorchange = QComboBox()
        self.iconcolorchange.addItems([tr(self.trl, 'white'), tr(self.trl, 'black')])
        iconcolor = getconfig('iconcolor', 'white')
        if iconcolor == 'black':
            self.iconcolorchange.setCurrentIndex(1)
        self.iconcolorchange.currentTextChanged.connect(lambda: self.changeiconcolor())

        iconcolorlayout.addWidget(QLabel(tr(self.trl, "pick_icon_color")))
        iconcolorlayout.addWidget(self.iconcolorchange)
        firsthalf.addLayout(iconcolorlayout)


        backgroundlayout = QHBoxLayout()
        self.pickbackground_button = QPushButton(tr(self.trl, "pick_background_color"))
        self.pickbackground_button.clicked.connect(self.pick_background_color)

        backgroundlayout.addWidget(self.pickbackground_button)
        secondhalf.addLayout(backgroundlayout)


        textcolor = QHBoxLayout()
        self.picktext_button = QPushButton(tr(self.trl, "pick_text_color"))
        self.picktext_button.clicked.connect(self.pick_text_color)

        textcolor.addWidget(self.picktext_button)
        secondhalf.addLayout(textcolor)


        fullbuttoncolorslayout = QVBoxLayout()
        buttoncolorslayout = QHBoxLayout()
        self.button_label = QLabel(tr(self.trl, "button_colors"))
        self.pickbutton_button = QPushButton(tr(self.trl, "pick_background_color"))
        self.pickbutton_button.clicked.connect(self.pick_button_color)
        self.pickbuttontext_button = QPushButton(tr(self.trl, "pick_text_color"))
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
        if imagesfolder == "images":
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)

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

        id_layout.addWidget(QLabel(tr("MainWindow", "character_id")))
        id_layout.addWidget(self.id_entry)
        layout.addLayout(id_layout)


        buttons_layout = QHBoxLayout()
        self.add_character_button = QPushButton(tr("CharEditor", "add_character"))
        self.add_character_button.clicked.connect(lambda: asyncio.run(self.add_character()))

        buttons_layout.addWidget(self.add_character_button)
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
    
    async def add_character(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        charid = self.id_entry.text().replace("https://character.ai/chat/", "") 
        character = await CustomCharAI().get_character(charid)
        data.update({charid: {"name": character['name'], "char": charid, "avatar_url": character['avatar_file_name'], "description": character['description'], "author": character['user__username']}})
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        response = requests.get(f"https://characterai.io/i/80/static/avatars/{character['avatar_file_name']}?webp=true&anim=0")
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        text = tr('CharEditor', 'yourchar') + character['name'] + tr('CharEditor', 'withid') + charid + tr('CharEditor', 'added')
        MessageBox(tr('CharEditor', 'character_added'), text, pixmap, pixmap, self)
        self.close()

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
            MessageBox(tr('Errors', 'Label'), f"Error loading the image: {e}", self)
            self.image_loaded.emit(QPixmap())

class CustomCharAI():
    async def request(self, endpoint, data = None, method = "get", neo = False):
        headers = {
            "Content-Type": 'application/json',
            "Authorization": f'Token {getconfig("client", configfile="charaiconfig.json")}'
        }

        if neo:
            url = f"https://neo.character.ai/{endpoint}"
        else:
            url = f"https://plus.character.ai/{endpoint}"

        async with aiohttp.ClientSession() as session:
            if method == "get":
                async with session.get(url, headers=headers, params=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Failed to get data, status code: {response.status}")
            elif method == "post":
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Failed to get data, status code: {response.status}")
            else:
                raise ValueError("Invalid method")

    async def get_character(self, character_id):
        data = {
            "external_id": character_id
        }
        response = await self.request("chat/character/info/", data, "post")
        return response['character']

    async def get_recommend_chats(self):
        response = await self.request("recommendation/v1/user", neo=True)
        return response['characters']

    async def get_recent_chats(self):
        response = await self.request("chats/recent", neo=True)
        return response['chats']

class CharacterWidget(QWidget):
    def __init__(self, CharacterSearch, data, mode):
        super().__init__()
        self.data = data
        self.local_data = None
        if mode != "firstlaunch":
            self.local_data = CharacterSearch.local_data
        self.CharacterSearch = CharacterSearch
        self.mode = mode
        self.trl = 'CharEditor'

        layout = QHBoxLayout()
        self.image_label = QLabel()
        layout.addWidget(self.image_label)

        text_buttons_layout = QHBoxLayout()
        local_text_buttons_layout = QVBoxLayout()

        self.text_label = QLabel()
        self.text_label.setWordWrap(True)

        buttons_layout = QVBoxLayout()
        self.network_addnovoice_button = QPushButton(tr(self.trl, 'add_without_voice'))
        self.network_addnovoice_button.setFixedWidth(200)
        self.network_addnovoice_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.network_addnovoice_button.clicked.connect(self.add_without_voice)

        self.network_addvoice_button = QPushButton(tr(self.trl, 'search_voice'))
        self.network_addvoice_button.setFixedWidth(200)
        self.network_addvoice_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.network_addvoice_button.clicked.connect(self.add_with_voice)

        local_seldel_buttons = QHBoxLayout()

        if mode != "local":
            self.local_select_button = self.ResizableButton(tr(self.trl,'select'))
            self.local_select_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        else:
            self.local_select_button = QPushButton(tr(self.trl,'select'))
        self.local_select_button.clicked.connect(self.select_char)
        local_seldel_buttons.addWidget(self.local_select_button)

        self.local_delete_button = QPushButton(tr(self.trl,'delete'))
        self.local_delete_button.clicked.connect(self.local_delete_character)
        local_seldel_buttons.addWidget(self.local_delete_button)

        self.local_edit_voice_button = self.ResizableButton(tr(self.trl,'edit_voice'))
        self.local_edit_voice_button.clicked.connect(self.local_add_char_voice)
        self.local_edit_voice_button.setFixedWidth(200)
        self.local_edit_voice_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.local_add_voice_button = self.ResizableButton(tr(self.trl,'add_voice'))
        self.local_add_voice_button.setFixedWidth(200)
        self.local_add_voice_button.clicked.connect(self.local_add_char_voice)
        self.local_add_voice_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.local_delete_voice_button = self.ResizableButton(tr(self.trl,'delete_voice'))
        self.local_delete_voice_button.setFixedWidth(200)
        self.local_delete_voice_button.clicked.connect(self.local_delete_voice)
        self.local_delete_voice_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if self.data.get('voiceid', '') == "":
            self.local_delete_voice_button.setEnabled(False)

        local_text_buttons_layout.addWidget(self.text_label)
        local_text_buttons_layout.addLayout(local_seldel_buttons)
        if mode == "local":
            text_buttons_layout.addLayout(local_text_buttons_layout)
        else:
            text_buttons_layout.addWidget(self.text_label)
        
        if mode == "network":
            self.author_label = tr(self.trl, 'author_label')
            self.char = data.get('external_id')
            self.name = data.get('participant__name', 'No Name')
            self.title = data.get('title', 'None')
            self.chats = data.get('score', '0')
            self.author = data.get('user__username', 'Unknown')
            self.description = data.get('description', 'None')
            self.avatar_url = data.get('avatar_file_name', '')

            self.image_label.setFixedSize(80, 80)

            self.full_description = self.description
            if f"{self.description}" != 'None' and len(f"{self.description}") > 220:
                self.description = self.description[:220] + '...'
            self.text_label.setMaximumWidth(400)
            self.local_chars = self.local_data.keys()
            if self.char in self.local_chars:
                buttons_layout.addWidget(self.local_select_button)
                self.local_select_button.setFixedWidth(200)
            else:
                buttons_layout.addWidget(self.network_addvoice_button)
                buttons_layout.addWidget(self.network_addnovoice_button)

            if f"{self.title}" == 'None' or f"{self.title}" == '':
                if f"{self.description}" == 'None' or f"{self.description}" == '':
                    text = f'<b>{self.name}</b><br>{self.chats} {tr(self.trl, "chats_label")} • {self.author_label}: {self.author}'
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f'<b>{self.name}</b><br>{self.description}<br>{self.chats} {tr(self.trl, "chats_label")} • {self.author_label}: {self.author}'
            else:
                if f"{self.description}" == 'None' or f"{self.description}" == '':
                    text = f'<b>{self.name}</b> - {self.title}<br>{self.chats} {tr(self.trl, "chats_label")} • {self.author_label}: {self.author}'
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f'<b>{self.name}</b> - {self.title}<br>{self.description}<br>{self.chats} {tr(self.trl, "chats_label")} • {self.author_label}: {self.author}'
        elif mode == "recent":
            self.char = data.get('character_id')
            self.name = data.get('character_name', 'No Name')
            self.avatar_url = data.get('character_avatar_uri', '')
            self.local_chars = self.local_data.keys()
            self.image_label.setFixedSize(50, 50)

            self.local_select_button.setFixedWidth(200)

            if self.char in self.local_chars:
                buttons_layout.addWidget(self.local_select_button)
            else:
                buttons_layout.addWidget(self.network_addvoice_button)
                buttons_layout.addWidget(self.network_addnovoice_button)

            text = f'<b>{self.name}</b>'
        elif mode == "recommend":
            self.char = data.get('external_id')
            self.name = data.get('participant__name', 'No Name')
            self.avatar_url = data.get('avatar_file_name', '')
            self.image_label.setFixedSize(50, 50)

            buttons_layout.addWidget(self.network_addvoice_button)
            buttons_layout.addWidget(self.network_addnovoice_button)

            text = f'<b>{self.name}</b>'
        elif mode == "local":
            self.author_label = tr(self.trl, 'author_label')
            self.name = data.get('name', 'No Name')
            self.char = data.get('char', '')
            self.title = data.get('title', 'None')
            self.author = data.get('author', 'Unknown')
            self.description = data.get('description', 'None')
            self.avatar_url = data.get('avatar_url', '')
            self.voiceid = data.get('voiceid', '')
            self.image_label.setFixedSize(80, 80)

            self.full_description = self.description
            if f"{self.description}" != 'None' and len(f"{self.description}") > 220:
                self.description = self.description[:220] + '...'
            self.text_label.setMaximumWidth(400)
            if self.voiceid == '':
                buttons_layout.addWidget(self.local_add_voice_button)
            else:
                buttons_layout.addWidget(self.local_edit_voice_button)
            buttons_layout.addWidget(self.local_delete_voice_button)

            if f"{self.title}" == 'None' or f"{self.title}" == '':
                if f"{self.description}" == 'None' or f"{self.description}" == '':
                    text = f'<b>{self.name}</b><br>• {self.author_label}: {self.author}'
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f'<b>{self.name}</b><br>{self.description}<br> • {self.author_label}: {self.author}'
            else:
                if f"{self.description}" == 'None' or f"{self.description}" == '':
                    text = f'<b>{self.name}</b> - {self.title}<br> • {self.author_label}: {self.author}'
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f'<b>{self.name}</b> - {self.title}<br>{self.description}<br>• {self.author_label}: {self.author}'
        elif mode == "firstlaunch":
            self.author_label = tr(self.trl, 'author_label')
            self.char = data.get('external_id')
            self.name = data.get('participant__name', 'No Name')
            self.title = data.get('title', 'None')
            self.chats = data.get('score', '0')
            self.author = data.get('user__username', 'Unknown')
            self.description = data.get('description', 'None')
            self.avatar_url = data.get('avatar_file_name', '')

            self.image_label.setFixedSize(80, 80)

            self.full_description = self.description
            if f"{self.description}" != 'None' and len(f"{self.description}") > 220:
                self.description = self.description[:220] + '...'
            self.text_label.setMaximumWidth(400)
            buttons_layout.addWidget(self.network_addvoice_button)
            buttons_layout.addWidget(self.network_addnovoice_button)

            if f"{self.title}" == 'None' or f"{self.title}" == '':
                if f"{self.description}" == 'None' or f"{self.description}" == '':
                    text = f'<b>{self.name}</b><br>{self.chats} {tr(self.trl, "chats_label")} • {self.author_label}: {self.author}'
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f'<b>{self.name}</b><br>{self.description}<br>{self.chats} {tr(self.trl, "chats_label")} • {self.author_label}: {self.author}'
            else:
                if f"{self.description}" == 'None' or f"{self.description}" == '':
                    text = f'<b>{self.name}</b> - {self.title}<br>{self.chats} {tr(self.trl, "chats_label")} • {self.author_label}: {self.author}'
                else:
                    self.text_label.setToolTip(self.full_description)
                    text = f'<b>{self.name}</b> - {self.title}<br>{self.description}<br>{self.chats} {tr(self.trl, "chats_label")} • {self.author_label}: {self.author}'

        self.threads = []
        if f"{self.avatar_url}" != "None" and f"{self.avatar_url}" != "" :
            thread = threading.Thread(self.load_image_async(f'https://characterai.io/i/80/static/avatars/{self.avatar_url}?webp=true&anim=0'))
            thread.start()
            self.threads.append(thread)
        self.text_label.setText(text)

        text_buttons_layout.addLayout(buttons_layout)
        layout.addLayout(text_buttons_layout)
        self.setLayout(layout)

    def load_image_async(self, url):
        def set_image(self, pixmap):
            if self.mode == "network" or self.mode == "local" or self.mode == "firstlaunch":
                self.image_label.setPixmap(pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            elif self.mode == "recent" or self.mode == "recommend":
                self.image_label.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        self.image_loader_thread = ImageLoaderThread(url)
        self.image_loader_thread.image_loaded.connect(lambda image: set_image(self, image))
        self.image_loader_thread.start()

    def add_with_voice(self):
        self.load_data()
        if self.mode == "recent" or self.mode == "recommend":
            self.get_recent_data()

        self.datafile.update({self.char: {"name": self.name, "char": self.char, "avatar_url": self.avatar_url, "description": self.description, "title": self.title, "author": self.author}})
        self.save_data()

        if self.mode != "firstlaunch":
            self.CharacterSearch.close()
        VoiceSearch(self.char).show()

    def add_without_voice(self):
        self.load_data()
        if self.mode == "recent" or self.mode == "recommend":
            self.get_recent_data()

        self.datafile.update({self.char: {"name": self.name, "char": self.char, "avatar_url": self.avatar_url, "description": self.description, "title": self.title, "author": self.author}})
        self.save_data()

        MessageBox(tr(self.trl, 'character_added'), tr(self.trl, 'character_added_text'), self=self)

        if self.mode != "firstlaunch":
            self.CharacterSearch.close()

    def load_data(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                self.datafile = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.datafile = {}

    def save_data(self):
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(self.datafile, f, ensure_ascii=False, indent=4)

    def get_recent_data(self):
        char = asyncio.run(CustomCharAI().get_character(self.char))
        self.name = char.get('participant__name', 'No Name')
        self.author = char.get('user__username', 'Unknown')
        self.avatar_url = char.get('avatar_file_name', '')
        self.description = char.get('description', '')
        self.title = char.get('title', '')

    def local_add_char_voice(self):
        if self.mode != "firstlaunch":
            self.CharacterSearch.close()
        VoiceSearch(self.char).show()

    def local_delete_character(self):
        self.load_data()
        del self.datafile[self.char]
        self.save_data()
        self.CharacterSearch.main_window.refreshcharsinmenubar()
        self.CharacterSearch.load_local_data()
        self.CharacterSearch.populate_local_list()

    def local_delete_voice(self):
        self.load_data()
        if self.char in self.datafile:
            if 'voiceid' in self.datafile[self.char]:
                del self.datafile[self.char]['voiceid']
        self.save_data()
        self.CharacterSearch.main_window.refreshcharsinmenubar()
        self.CharacterSearch.load_local_data()
        self.CharacterSearch.populate_local_list()

    class ResizableButton(QPushButton):
        def resizeEvent(self, event):
            super().resizeEvent(event)
            self.adjustFontSize()
    
        def adjustFontSize(self):
            button_width = self.width()
            button_height = self.height()

            base_size = min(button_width, button_height) // 5
            min_font_size = 10
            font_size = max(base_size, min_font_size)
            font = self.font()
            font.setPointSize(font_size)
            self.setFont(font)

    def select_char(self):
        if self.mode == "network" or self.mode == "recent":
            self.load_data()
            self.voiceid = self.datafile[self.char].get('voiceid', '')
        elif self.mode == "local":
            self.voiceid = self.data.get('voiceid', '')
        self.CharacterSearch.main_window.char_entry.setText(self.char)
        self.CharacterSearch.main_window.voice_entry.setText(self.voiceid)
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

        self.trl = "CharEditor"

        main_layout = QVBoxLayout(self)
        self.main_window = mainwindow

        self.addchar_button = QPushButton(tr("CharEditor", "add_character"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)


        self.network_tab = QWidget()
        self.network_layout = QVBoxLayout(self.network_tab)

        self.network_search_input = QLineEdit()
        self.network_search_input.setPlaceholderText(tr(self.trl, 'network_search_input'))
        self.network_search_input.returnPressed.connect(self.search_and_load)
        self.network_layout.addWidget(self.network_search_input)

        self.network_list_widget = QListWidget()
        self.network_layout.addWidget(self.network_list_widget)

        self.add_another_charcter_button = QPushButton(tr(self.trl, 'add_another_charcter_button'))
        self.add_another_charcter_button.clicked.connect(self.open_NewCharacherEditor)

        self.network_buttons_layout = QVBoxLayout()
        self.network_buttons_layout.addWidget(self.add_another_charcter_button)

        self.network_layout.addLayout(self.network_buttons_layout)


        self.local_tab = QWidget()
        self.local_layout = QVBoxLayout(self.local_tab)

        self.local_list_widget = QListWidget()
        self.local_layout.addWidget(self.local_list_widget)

        self.local_image_label = QLabel()
        self.local_details_label = QLabel()
        self.local_details_label.setWordWrap(True)
        self.local_details_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tab_widget.addTab(self.network_tab, tr(self.trl, 'network_tab'))
        self.tab_widget.addTab(self.local_tab, tr(self.trl, 'local_tab'))

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

    def populate_list(self, data, mode):
        item = QListWidgetItem()
        custom_widget = CharacterWidget(self, data, mode)
        
        item.setSizeHint(custom_widget.sizeHint())
        if mode == 'local':
            self.local_list_widget.addItem(item)
            self.local_list_widget.setItemWidget(item, custom_widget)
            return
        self.network_list_widget.addItem(item)
        self.network_list_widget.setItemWidget(item, custom_widget)

    def populate_category_header(self, category_name):
        header_item = QListWidgetItem()
        header_widget = QLabel(f"<b>{category_name}</b>")
        header_widget.setStyleSheet("font-size: 15px; font-weight: bold;")
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

        self.add_another_charcter_button.setVisible(False)

    def populate_recent_list(self):
        self.populate_category_header(tr(self.trl, 'recent_chats'))
        if self.main_window.recent_chats:
            for chats in self.main_window.recent_chats:
                    if chats['character_id'] not in self.recommend_recent_items:
                        self.recommend_recent_items.append(chats['character_id'])
                        self.populate_list(chats, "recent")
        else:
            self.populate_category_header(f"{tr(self.trl, 'empty_chats')}... <(＿　＿)>")

    def populate_recommend_list(self):
        self.populate_category_header(tr(self.trl, 'recommend_chats'))
        if self.main_window.recommend_chats:
            for recommend in self.main_window.recommend_chats:
                if recommend['external_id'] not in self.recommend_recent_items:
                    self.recommend_recent_items.append(recommend['external_id'])
                    self.populate_list(recommend, "recommend")
        else:
            self.populate_category_header(f"{tr(self.trl, 'empty_chats')}... <(＿　＿)>")

    def populate_local_list(self):
        self.local_list_widget.clear()
        if not self.local_data:
            return
        for charid, char_data in self.local_data.items():
            self.populate_list(char_data, 'local')

    def on_tab_changed(self, index):
        if index == 1:
            self.populate_local_list()

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
                MessageBox(tr('Errors', 'Label'), f"Error receiving data: {response.status_code}")
        except Exception as e:
            MessageBox(tr('Errors', 'Label'), f"Error when executing the request: {e}")

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

    def closeEvent(self, event):
        if self.main_window:
            self.main_window.refreshcharsinmenubar()
        super().closeEvent(event)

    def styles_reset(self):
        self.setStyleSheet("")

class VoiceSearch(QWidget):
    def __init__(self, character_id):
        super().__init__()
        self.character_id = character_id
        self.trl = "CharEditor"

        self.setWindowTitle('Emilia: Voice Search')
        self.setWindowIcon(QIcon(emiliaicon))
        self.setGeometry(300, 300, 800, 400)

        self.addchar_button = QPushButton(tr("CharEditor", "add_character"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.search_and_load)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.display_details)

        self.details_label = QLabel()
        self.details_label.setWordWrap(True)

        self.preview_text_label = QLabel()

        self.play_button = QPushButton(tr(self.trl, 'play_an_example'))
        self.play_button.clicked.connect(self.play_audio)
        self.play_button.setEnabled(False)

        self.select_button = QPushButton(tr(self.trl, 'select'))
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
                list_item = QListWidgetItem(f"{item['name']} • {tr(self.trl, 'author_label')}: {item['creatorInfo']['username']}")
            else:
                list_item = QListWidgetItem(f"{item['name']} - {description}\n• {tr(self.trl, 'author_label')}: {item['creatorInfo']['username']}")
            list_item.setData(1, item)
            self.list_widget.addItem(list_item)

    def display_details(self, item):
        data = item.data(1)
        self.current_data = data
        self.details_label.setText(f"<b>{data['name']}</b> • {tr(self.trl, 'author_label')}: {data['creatorInfo']['username']}<br>{data['description']}")
        self.preview_text_label.setText(f"{tr(self.trl, 'example_phrase')}: {data['previewText']}")
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
                MessageBox(tr('Errors', 'Label'), f"Error loading and playing audio: {e}")

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
                MessageBox(tr('Errors', 'Label'), f"Error receiving data: {response.status_code}")
        except Exception as e:
            MessageBox(tr('Errors', 'Label'), f"Error when executing the request: {e}")

    def addcharvoice(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
            
        data.update({self.character_id: {"name": data[self.character_id]["name"], "char": data[self.character_id]["char"], "avatar_url": data[self.character_id]["avatar_url"], "description": data[self.character_id]['description'], "title": data[self.character_id]['title'], "author": data[self.character_id]["author"],"voiceid": self.current_data['id']}})

        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        MessageBox(text=tr(self.trl, 'character_voice_changed'))
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
        self.email_label = QLabel(tr("GetToken","your_email"))
        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("example@example.com")

        email_layout.addWidget(self.email_label)
        email_layout.addWidget(self.email_entry)
        self.layout.addLayout(email_layout)


        self.getlink_button = QPushButton(tr("GetToken", "send_email"))
        self.getlink_button.clicked.connect(self.getlink)
        self.layout.addWidget(self.getlink_button)

        self.link_layout = QHBoxLayout()
        self.link_label = QLabel(tr("GetToken", "link_from_email"))
        self.link_entry = QLineEdit()
        self.link_entry.setPlaceholderText("https...")

        self.link_layout.addWidget(self.link_label)
        self.link_layout.addWidget(self.link_entry)
        

        self.gettoken_button = QPushButton(tr("GetToken", "get_token"))
        self.gettoken_button.clicked.connect(self.gettoken)
        
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
            self.email_label.setText(tr("GetToken", "your_token") + token + tr("GetToken", "save_in_charaiconfig"))
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

        self.characters_list = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        hlayout = QHBoxLayout()

        self.char_label = QLabel(tr("MainWindow", "character_id"))
        self.char_label.setWordWrap(True)

        self.char_entry = QLineEdit()
        self.char_entry.setPlaceholderText("ID...")
        self.char_entry.textChanged.connect(lambda: writeconfig("char", self.char_entry.text().replace("https://character.ai/chat/", ""), "charaiconfig.json"))
        self.char_entry.setText(getconfig('char', configfile='charaiconfig.json'))

        self.client_label = QLabel(tr("MainWindow", "character_token"))
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

        if self.client_entry.text() != "":
            try:
                self.recommend_chats = asyncio.run(CustomCharAI().get_recommend_chats())
                self.recent_chats = asyncio.run(CustomCharAI().get_recent_chats())
            except Exception as e:
                self.recommend_chats = None
                self.recent_chats = None
                MessageBox(tr("Errors", "Label"), tr("Errors", "other") + str(e))
        else:
            self.recommend_chats = None
            self.recent_chats = None
            
        self.voice_layout = QHBoxLayout()
        self.voice_entry = QLineEdit()
        self.voice_label = QLabel()
        self.voice_label.setText(tr("MainWindow", "voice_id"))
        self.voice_entry.setToolTip(tr("MainWindow", "voice_id_tooltip"))
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
        self.user_aiinput.setPlaceholderText(tr("MainWindow", "before_pressing"))

        self.tstart_button = QPushButton(tr("MainWindow", "start_text_mode"))
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

        self.gettokenaction = QAction(QIcon(charaiicon), tr("MainWindow", 'get_token'), self)
        self.gettokenaction.triggered.connect(self.gettoken)

        self.optionsopenaction = QAction(tr("MainWindow", "options"))
        self.optionsopenaction.triggered.connect(self.optionsopen)

        self.visibletextmode = QAction(QIcon(keyboardicon), tr("MainWindow", 'use_text_mode'), self)
        self.visibletextmode.triggered.connect(lambda: self.modehide("text"))

        self.visiblevoicemode = QAction(QIcon(inputicon), tr("MainWindow", 'use_voice_mode'), self)
        self.visiblevoicemode.triggered.connect(lambda: self.modehide("voice"))
        self.visiblevoicemode.setVisible(False)

        self.recognizer = sr.Recognizer()
        self.mic_list = [
            mic_name for mic_name in sr.Microphone.list_microphone_names()
            if any(keyword in mic_name.lower() for keyword in ["microphone", "mic", "input"])
        ]

        self.inputdeviceselect = QMenu(tr("MainWindow", 'input_device'), self)

        for index, mic_name in enumerate(self.mic_list):
            action = QAction(mic_name, self)
            action.triggered.connect(lambda checked, i=index: self.set_microphone(i))
            self.inputdeviceselect.addAction(action)

        self.outputdeviceselect = QMenu(tr("MainWindow", 'output_device'), self)

        self.unique_devices = {}
        for dev in sd.query_devices():
            if dev["max_output_channels"] > 0 and dev["name"] not in self.unique_devices:
                self.unique_devices[dev["name"]] = dev

        for index, (name, device) in enumerate(self.unique_devices.items()):
            action = QAction(name, self)
            action.triggered.connect(lambda checked, i=index: self.set_output_device(i))
            self.outputdeviceselect.addAction(action)

        self.charselect = self.menubar.addMenu(tr("MainWindow", 'character_choice'))

        self.CharacterSearchopen = QAction(QIcon(charediticon), tr('MainWindow', 'open_character_search'), self)
        self.CharacterSearchopen.triggered.connect(self.charsopen)

        self.charrefreshlist = QAction(QIcon(refreshicon), tr("MainWindow", "refresh_list"))
        self.charrefreshlist.triggered.connect(self.refreshcharsinmenubar)

        self.charselect.addAction(self.CharacterSearchopen)
        self.charselect.addAction(self.charrefreshlist)

        self.addcharsinmenubar()

        self.aboutemi = QAction(QIcon(emiliaicon), tr("MainWindow", 'about_emilia'), self)
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
            msg.setWindowTitle(tr("About", "about_emilia") + build)
        else:
            msg.setWindowTitle(tr("About", "about_emilia"))
        msg.setStyleSheet(self.styleSheet())
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        language = tr("About", "language_from")
        whatsnew = tr("About", "new_in") + version + tr("About", "whats_new")
        otherversions = tr("About", "show_all_releases")
        text = tr("About", "emilia_is_open_source") + version + tr("About", "use_version") + language + whatsnew + otherversions
        msg.setText(text)
        msg.exec()
    
    async def charai_tts(self):
        message = self.messagenotext
        voiceid = self.voice_entry.text().replace("https://character.ai/chat/", "")
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

    async def main(self):
        try:
            self.vtubeenable = getconfig('vtubeenable', "False") == "True"
            self.tts = getconfig('tts', 'silerotts')
            self.layout.addWidget(self.user_input)
            self.layout.addWidget(self.ai_output)
            self.username, self.ai_name, self.chat, self.character, self.token = await self.setup_ai()
            while True:
                await self.process_user_input()
        except Exception as e:
            MessageBox(tr('Error', 'Label'), str(e), self=self)

    async def setup_ai(self):
        token = aiocai.Client(self.client_entry.text())
        character = self.char_entry.text().replace("https://character.ai/chat/", "")
        account = await token.get_me()
        try:
            chatid = await token.get_chat(character)
        except:
            chatid = await token.new_chat(character, account.id)
        persona = await CustomCharAI().get_character(character)
        try:
            username = f"{account.name}: "
        except Exception as e:
            username = tr("MainWindow", "user")
            print(e)
        ai_name = f"{persona['name']}: "
        return username, ai_name, chatid, character, token

    async def process_user_input(self):
        if self.vtubeenable:
            await EEC().UseEmote("Listening")

        recognizer = sr.Recognizer()
        self.user_input.setText(self.username + tr("Main", "speak"))
        msg1 = await self.recognize_speech(recognizer)

        self.user_input.setText(self.username + msg1)
        self.ai_output.setText(self.ai_name + tr("Main", "generation"))
        
        if self.vtubeenable:
            await EEC().UseEmote("Thinks")

        message = await self.generate_ai_response(msg1)

        if self.vtubeenable:
            await EEC().UseEmote("VoiceGen")

        self.ai_output.setText(self.ai_name + message)

        if self.vtubeenable:
            await EEC().UseEmote("Says")

        await self.play_audio_response()

        if self.vtubeenable:
            await EEC().UseEmote("AfterSays")

    async def recognize_speech(self, recognizer):
        while True:
            try:
                audio = await self.listen_to_microphone(recognizer)
                return recognizer.recognize_google(audio, language="ru-RU" if lang == "ru_RU" else "en-US")
            except sr.UnknownValueError:
                self.user_input.setText(self.username + tr("Main", "say_again"))

    async def listen_to_microphone(self, recognizer):
        if self.microphone:
            with self.microphone as source:
                return recognizer.listen(source)
        else:
            with sr.Microphone() as source:
                return recognizer.listen(source)

    async def generate_ai_response(self, msg1):
        async with await self.token.connect() as chat:
            self.messagenotext = await chat.send_message(self.character, self.chat.chat_id, msg1)
            return self.messagenotext.text

    async def play_audio_response(self):
        try:
            audio, sample_rate = await self.charai_tts()

            device = self.get_audio_device()

            sd.play(audio, sample_rate, device=device["index"] if device else None)
            await asyncio.sleep(len(audio) / sample_rate)
            sd.stop()
        except Exception as e:
            MessageBox(tr('Errors', 'Label'), str(e))

    def get_audio_device(self):
        return list(self.unique_devices.values())[self.selected_device_index] if self.selected_device_index else None

    async def maintext(self):
        if self.user_aiinput.text() == "" or self.user_aiinput.text() == tr("MainWindow", "but_it_is_empty"):
            self.user_aiinput.setText(tr("MainWindow", "but_it_is_empty"))
        else:
            self.vtubeenable = getconfig('vtubeenable', "False")
            self.layout.addWidget(self.ai_output)
            self.username, self.ai_name, self.chat, self.character, self.token = await self.setup_ai()
                
            msg1 = self.user_aiinput.text()

            self.ai_output.setText(self.ai_name + tr("Main", "generation"))

            if self.vtubeenable == "True":
                await EEC().UseEmote("Thinks")

            message = await self.generate_ai_response(msg1)

            if self.vtubeenable == "True":
                await EEC().UseEmote("VoiceGen")
                
            self.ai_output.setText(self.ai_name + message)

            if self.vtubeenable == "True":
                await EEC().UseEmote("Says")

            await self.play_audio_response()

            if self.vtubeenable == "True":
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
