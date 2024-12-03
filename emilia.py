import os, asyncio, winreg, json, sys, webbrowser, ctypes

import sounddevice as sd
import speech_recognition as sr

from characterai import sendCode, authUser

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
                             QListWidgetItem,
                             QGroupBox,
                             QSizePolicy,
                             QStackedLayout,
                             QSlider)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor
from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtMultimedia import QMediaDevices

from modules.auto_update import check_for_updates
from modules.character_search import (CharacterSearch,
                                      ChatWithCharacter,
                                      MainMessageWidget,
                                      VoiceSearch)
from modules.config import getconfig, writeconfig, exe_check
from modules.ets import translations
from modules.other import MessageBox, Emote_File
from modules.QCustom import ResizableLabel, ResizableLineEdit, ResizableButton
from modules.QThreads import MainThreadCharAI, MainThreadGemini, ChatDataWorker

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("emilia.app")
except Exception as e:
    print(f"Ctypes error {e}")

version = "2.4b1dev2"
pre = True
sample_rate = 48000

# Global Variables
autoupdate_enable = getconfig("autoupdate_enable", False)
vtube_enable = getconfig("vtubeenable", False)
umtranslate = getconfig("umtranslate", False)
aimtranslate = getconfig("aimtranslate", False)
show_notranslate_message = getconfig("show_notranslate_message", True)
show_system_messages = getconfig("show_system_messages", True)
lang = getconfig("language", QLocale.system().name())
aitype = getconfig("aitype", "charai")
tts = getconfig("tts", "charai")
theme = getconfig("theme", "windowsvista")
iconcolor = getconfig("iconcolor", "black")
backcolor = getconfig("backgroundcolor")
buttoncolor = getconfig("buttoncolor")
buttontextcolor = getconfig("buttontextcolor")
labelcolor = getconfig("labelcolor")
trls = translations(lang)

# Gemini Variables
gemini_model = getconfig("gemini_model", "gemini-1.5-flash", "geminiconfig.json")
gemini_harassment = getconfig("harassment", 3, "geminiconfig.json")
gemini_hate = getconfig("hate", 3, "geminiconfig.json")
gemini_se_exlicit = getconfig("se_exlicit", 3, "geminiconfig.json")
gemini_dangerous_content = getconfig("dangerous_content", 3, "geminiconfig.json")
gemini_civic_integrity = getconfig("civic_integrity", 3, "geminiconfig.json")

# Icons
emiliaicon = "images/emilia.png"
if iconcolor == "white":
    refreshicon = "images/refresh_white.png"
    charediticon = "images/open_char_editor_white.png"
    sendmsgicon = "images/send_message_white.png"
    micicon = "images/mic_white.png"
    micofficon = "images/mic_off_white.png"
else:
    refreshicon = "images/refresh.png"
    charediticon = "images/open_char_editor.png"
    sendmsgicon = "images/send_message.png"
    micicon = "images/mic.png"
    micofficon = "images/mic_off.png"

if tts == "charai" and aitype != "charai":
    tts = "elevenlabs"
    writeconfig("tts", tts)

print("(｡･∀･)ﾉﾞ")

class OptionsWindow(QWidget):
    def __init__(self, mainwindow):
        super().__init__()
        self.setWindowTitle("Emilia: Options")
        self.setWindowIcon(QIcon(emiliaicon))
        self.setFixedWidth(500)
        self.setMinimumHeight(150)
        self.trl = "OptionsWindow"

        self.addchar_button = QPushButton(trls.tr("CharEditor", "add_character"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.mainwindow = mainwindow
        layout = QHBoxLayout()

        firsthalf = QVBoxLayout()
        self.firsthalf = firsthalf
        secondhalf = QVBoxLayout()

        self.system_options = QGroupBox(trls.tr(self.trl, "system_options"))
        self.system_options_layout = QVBoxLayout()
        self.system_options.setLayout(self.system_options_layout)
        firsthalf.addWidget(self.system_options)

        autoupdatelayout = QHBoxLayout()
        self.autoupdate = QCheckBox()
        if autoupdate_enable:
            self.autoupdate.setChecked(True)
        self.autoupdate.stateChanged.connect(self.autoupdatechange)


        autoupdatelayout.addWidget(QLabel(trls.tr(self.trl, "automatic_updates")))
        autoupdatelayout.addWidget(self.autoupdate)
        self.system_options_layout.addLayout(autoupdatelayout)


        langlayout = QHBoxLayout()
        self.languagechange = QComboBox()
        self.languagechange.addItems([trls.tr(self.trl, "english"), trls.tr(self.trl, "russian")])
        if lang == "ru_RU":
            self.languagechange.setCurrentIndex(1)
        self.languagechange.currentIndexChanged.connect(self.langchange)

        langlayout.addWidget(QLabel(trls.tr(self.trl, "select_language")))
        langlayout.addWidget(self.languagechange)
        self.system_options_layout.addLayout(langlayout)


        self.umlayout = QHBoxLayout()
        self.umcheck_box = QCheckBox()
        if umtranslate:
            self.umcheck_box.setChecked(True)
        self.umcheck_box.stateChanged.connect(self.umtranslate_change)

        self.umlayout.addWidget(QLabel(trls.tr(self.trl, "umlayout")))
        self.umlayout.addWidget(self.umcheck_box)
        self.system_options_layout.addLayout(self.umlayout)


        self.aimlayout = QHBoxLayout()
        self.aimcheck_box = QCheckBox()
        if aimtranslate:
            self.aimcheck_box.setChecked(True)
        self.aimcheck_box.stateChanged.connect(self.aimtranslate_change)

        self.aimlayout.addWidget(QLabel(trls.tr(self.trl, "aimlayout")))
        self.aimlayout.addWidget(self.aimcheck_box)
        self.system_options_layout.addLayout(self.aimlayout)


        self.sntmlayout = QHBoxLayout()
        self.sntmcheck_box = QCheckBox()
        if aimtranslate == False and umtranslate == False:
            self.sntmcheck_box.setEnabled(False)
        if show_notranslate_message:
            self.sntmcheck_box.setChecked(True)
        self.sntmcheck_box.stateChanged.connect(self.show_untrl_messages_change)

        self.sntmlayout.addWidget(QLabel(trls.tr(self.trl, "sntmlayout")))
        self.sntmlayout.addWidget(self.sntmcheck_box)
        self.system_options_layout.addLayout(self.sntmlayout)


        self.ssmlayout = QHBoxLayout()
        self.ssmcheck_box = QCheckBox()
        if show_system_messages:
            self.ssmcheck_box.setChecked(True)
        self.ssmcheck_box.stateChanged.connect(self.show_ss_messages_change)

        self.ssmlayout.addWidget(QLabel(trls.tr(self.trl, "ssmlayout")))
        self.ssmlayout.addWidget(self.ssmcheck_box)
        self.system_options_layout.addLayout(self.ssmlayout)


        self.other_options = QGroupBox(trls.tr(self.trl, "other_options"))
        self.other_options_layout = QVBoxLayout()
        self.other_options.setLayout(self.other_options_layout)
        firsthalf.addWidget(self.other_options)


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
        self.other_options_layout.addLayout(vtubelayout)


        self.customization_options = QGroupBox(trls.tr(self.trl, "customization_options"))
        self.customization_options_layout = QVBoxLayout()
        self.customization_options.setLayout(self.customization_options_layout)
        secondhalf.addWidget(self.customization_options)

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
        theme = getconfig("theme", "windowsvista")
        if theme == "windowsvista":
            self.themechange.setCurrentIndex(1)
        elif theme == "windows11":
            self.themechange.setCurrentIndex(2)
        elif theme == "Fuison":
            self.themechange.setCurrentIndex(0)
        self.themechange.currentIndexChanged.connect(self.changetheme)

        themelayout.addWidget(QLabel(trls.tr(self.trl, "select_theme")))
        themelayout.addWidget(self.themechange)
        self.customization_options_layout.addLayout(themelayout)


        iconcolorlayout = QHBoxLayout()
        self.iconcolorchange = QComboBox()
        self.iconcolorchange.addItems([trls.tr(self.trl, "white"), trls.tr(self.trl, "black")])
        iconcolor = getconfig("iconcolor", "white")
        if iconcolor == "black":
            self.iconcolorchange.setCurrentIndex(1)
        self.iconcolorchange.currentIndexChanged.connect(self.changeiconcolor)

        iconcolorlayout.addWidget(QLabel(trls.tr(self.trl, "pick_icon_color")))
        iconcolorlayout.addWidget(self.iconcolorchange)
        self.customization_options_layout.addLayout(iconcolorlayout)


        backgroundlayout = QHBoxLayout()
        self.pickbackground_button = QPushButton(trls.tr(self.trl, "pick_background_color"))
        self.pickbackground_button.clicked.connect(self.pick_background_color)

        backgroundlayout.addWidget(self.pickbackground_button)
        self.customization_options_layout.addLayout(backgroundlayout)


        textcolor = QHBoxLayout()
        self.picktext_button = QPushButton(trls.tr(self.trl, "pick_text_color"))
        self.picktext_button.clicked.connect(self.pick_text_color)

        textcolor.addWidget(self.picktext_button)
        self.customization_options_layout.addLayout(textcolor)


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
        self.customization_options_layout.addLayout(fullbuttoncolorslayout)


        self.reset_button = QPushButton(trls.tr(self.trl, "reset"))
        self.reset_button.clicked.connect(self.allreset)
        self.customization_options_layout.addWidget(self.reset_button)

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

    def show_ss_messages_change(self, state):
        global show_system_messages
        if state == 2:
            show_system_messages = True
        else:
            show_system_messages = False
        writeconfig("show_system_messages", show_system_messages)

    def show_untrl_messages_change(self, state):
        global show_notranslate_message
        if state == 2:
            show_notranslate_message = True
        else:
            show_notranslate_message = False
        writeconfig("show_notranslate_message", show_notranslate_message)

    def umtranslate_change(self, state):
        global umtranslate
        if state == 2:
            umtranslate = True
            self.sntmcheck_box.setEnabled(True)
        else:
            umtranslate = False
            if aimtranslate == False:
                self.sntmcheck_box.setEnabled(False)
        writeconfig("umtranslate", umtranslate)

    def aimtranslate_change(self, state):
        global aimtranslate
        if state == 2:
            aimtranslate = True
            self.sntmcheck_box.setEnabled(True)
        else:
            aimtranslate = False
            if umtranslate == False:
                self.sntmcheck_box.setEnabled(False)
        writeconfig("aimtranslate", aimtranslate)

    def vtubechange(self, state):
        global vtube_enable
        if state == 2:
            MessageBox(text="Attention, using Emilia together with the VTube model can greatly slow down the generation of responses")
            vtube_enable = True
        else:
            vtube_enable = False
        writeconfig("vtubeenable", vtube_enable)

    def autoupdatechange(self, state):
        global autoupdate_enable
        if state == 2:
            autoupdate_enable = True
        else:
            autoupdate_enable = False
        writeconfig("autoupdate_enable", autoupdate_enable)

    def changetheme(self, value):
        global theme
        if value == 0:
            theme = "fusion"
        elif value == 1:
            theme = "windowsvista"
        elif value == 2:
            theme = "windows11"
        app.setStyle(theme)
        writeconfig("theme", theme)

    def changeiconcolor(self, value):
        global iconcolor, micofficon
        if value == 0:
            refreshicon = "images/refresh_white.png"
            charediticon = "images/open_char_editor_white.png"
            sendmsgicon = "images/send_message_white.png"
            micicon = "images/mic_white.png"
            micofficon = "images/mic_off_white.png"
            iconcolor = "white"
        elif value == 1:
            refreshicon = "images/refresh.png"
            charediticon = "images/open_char_editor.png"
            sendmsgicon = "images/send_message.png"
            micicon = "images/mic.png"
            micofficon = "images/mic_off.png"
            iconcolor = "black"
        writeconfig("iconcolor", iconcolor)
        self.mainwindow.CharacterSearchopen.setIcon(QIcon(charediticon))
        self.mainwindow.charrefreshlist.setIcon(QIcon(refreshicon))
        self.mainwindow.send_user_message_button.setIcon(QIcon(sendmsgicon))
        self.mainwindow.mute_microphone_button.setIcon(QIcon(micicon))

    def langchange(self, value):
        if value == 0:
            writeconfig("language", "en_US")
        elif value == 1:
            writeconfig("language", "ru_RU")
        print("Restart required")
        if not exe_check():
            os.execv(sys.executable, ["python"] + sys.argv)
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)

    def pick_background_color(self):
        globals()["backcolor"] = QColorDialog.getColor(self.current_color, self)
        self.mainwindow.set_background_color(backcolor) 
        self.set_background_color(backcolor)
        writeconfig("backgroundcolor", backcolor.name())

    def pick_button_color(self):
        globals()["buttoncolor"] = QColorDialog.getColor(self.current_button_color, self)
        self.mainwindow.set_button_color(buttoncolor)
        self.set_button_color(buttoncolor)
        writeconfig("buttoncolor", buttoncolor.name())

    def pick_button_text_color(self):
        globals()["buttontextcolor"] = QColorDialog.getColor(self.current_button_color, self)
        self.mainwindow.set_button_text_color(buttontextcolor)
        self.set_button_text_color(buttontextcolor)
        writeconfig("buttontextcolor", buttontextcolor.name())

    def pick_text_color(self):
        globals()["labelcolor"] = QColorDialog.getColor(self.current_label_color, self)
        self.mainwindow.set_label_color(labelcolor)
        self.set_label_color(labelcolor)
        writeconfig("labelcolor", labelcolor.name())

    def allreset(self):
        global iconcolor, backcolor, buttoncolor, buttontextcolor, labelcolor, charediticon
        globals().update({
            "backcolor": "",
            "buttoncolor": "",
            "buttontextcolor": "",
            "labelcolor": ""
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

class Gemini_Safety_Settings(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Safety Settings")
        self.setFixedWidth(300)
        self.setMinimumHeight(100)

        self.addchar_button = QPushButton(trls.tr("CharEditor", "add_character"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.layout = QVBoxLayout()
        self.trl = "Gemini_Safety_Settings"

        harassment_layout = QHBoxLayout()
        self.harassment_label = QLabel(trls.tr(self.trl, "label_harassment"))

        harassment_slider_layout = QVBoxLayout()
        self.harassment_slider_label = QLabel(trls.tr(self.trl, "block_none"))
        self.harassment_slider = QSlider(Qt.Orientation.Horizontal)
        self.harassment_slider.setMinimum(1)
        self.harassment_slider.setMaximum(4)
        self.harassment_slider.valueChanged.connect(self.harassment_update_status)
        self.harassment_slider.setValue(gemini_harassment)
        harassment_slider_layout.addWidget(self.harassment_slider_label, alignment=Qt.AlignmentFlag.AlignCenter)
        harassment_slider_layout.addWidget(self.harassment_slider)

        harassment_layout.addWidget(self.harassment_label)
        harassment_layout.addLayout(harassment_slider_layout)
        self.layout.addLayout(harassment_layout)


        hate_layout = QHBoxLayout()
        self.hate_label = QLabel(trls.tr(self.trl, "label_hate"))

        hate_slider_layout = QVBoxLayout()
        self.hate_slider_label = QLabel(trls.tr(self.trl, "block_none"))
        self.hate_slider = QSlider(Qt.Orientation.Horizontal)
        self.hate_slider.setMinimum(1)
        self.hate_slider.setMaximum(4)
        self.hate_slider.valueChanged.connect(self.hate_update_status)
        self.hate_slider.setValue(gemini_hate)
        hate_slider_layout.addWidget(self.hate_slider_label, alignment=Qt.AlignmentFlag.AlignCenter)
        hate_slider_layout.addWidget(self.hate_slider)

        hate_layout.addWidget(self.hate_label)
        hate_layout.addLayout(hate_slider_layout)
        self.layout.addLayout(hate_layout)


        se_exlicit_layout = QHBoxLayout()
        self.se_exlicit_label = QLabel(trls.tr(self.trl, "label_se_exlicit"))

        se_exlicit_slider_layout = QVBoxLayout()
        self.se_exlicit_slider_label = QLabel(trls.tr(self.trl, "block_none"))
        self.se_exlicit_slider = QSlider(Qt.Orientation.Horizontal)
        self.se_exlicit_slider.setMinimum(1)
        self.se_exlicit_slider.setMaximum(4)
        self.se_exlicit_slider.valueChanged.connect(self.se_exlicit_update_status)
        self.se_exlicit_slider.setValue(gemini_se_exlicit)
        se_exlicit_slider_layout.addWidget(self.se_exlicit_slider_label, alignment=Qt.AlignmentFlag.AlignCenter)
        se_exlicit_slider_layout.addWidget(self.se_exlicit_slider)

        se_exlicit_layout.addWidget(self.se_exlicit_label)
        se_exlicit_layout.addLayout(se_exlicit_slider_layout)
        self.layout.addLayout(se_exlicit_layout)


        dangerous_content_layout = QHBoxLayout()
        self.dangerous_content_label = QLabel(trls.tr(self.trl, "label_dangerous_content"))

        dangerous_content_slider_layout = QVBoxLayout()
        self.dangerous_content_slider_label = QLabel(trls.tr(self.trl, "block_none"))
        self.dangerous_content_slider = QSlider(Qt.Orientation.Horizontal)
        self.dangerous_content_slider.setMinimum(1)
        self.dangerous_content_slider.setMaximum(4)
        self.dangerous_content_slider.valueChanged.connect(self.dangerous_content_update_status)
        self.dangerous_content_slider.setValue(gemini_dangerous_content)
        dangerous_content_slider_layout.addWidget(self.dangerous_content_slider_label, alignment=Qt.AlignmentFlag.AlignCenter)
        dangerous_content_slider_layout.addWidget(self.dangerous_content_slider)

        dangerous_content_layout.addWidget(self.dangerous_content_label)
        dangerous_content_layout.addLayout(dangerous_content_slider_layout)
        self.layout.addLayout(dangerous_content_layout)


        civic_integrity_layout = QHBoxLayout()
        self.civic_integrity_label = QLabel(trls.tr(self.trl, "label_civic_integrity"))

        civic_integrity_slider_layout = QVBoxLayout()
        self.civic_integrity_slider_label = QLabel(trls.tr(self.trl, "block_none"))
        self.civic_integrity_slider = QSlider(Qt.Orientation.Horizontal)
        self.civic_integrity_slider.setMinimum(1)
        self.civic_integrity_slider.setMaximum(4)
        self.civic_integrity_slider.valueChanged.connect(self.civic_integrity_update_status)
        self.civic_integrity_slider.setValue(gemini_civic_integrity)
        civic_integrity_slider_layout.addWidget(self.civic_integrity_slider_label, alignment=Qt.AlignmentFlag.AlignCenter)
        civic_integrity_slider_layout.addWidget(self.civic_integrity_slider)

        civic_integrity_layout.addWidget(self.civic_integrity_label)
        civic_integrity_layout.addLayout(civic_integrity_slider_layout)
        self.layout.addLayout(civic_integrity_layout)


        self.setLayout(self.layout)

        if backcolor:
            self.set_background_color(QColor(backcolor))
        if buttoncolor:
            self.set_button_color(QColor(buttoncolor))
        if labelcolor:
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor:
            self.set_button_text_color(QColor(buttontextcolor))

    def harassment_update_status(self, value):
        globals()["gemini_harassment"] = value
        self.harassment_slider_label.setText(self.block_status(value))
        writeconfig("harassment", value, "geminiconfig.json")

    def hate_update_status(self, value):
        globals()["gemini_hate"] = value
        self.hate_slider_label.setText(self.block_status(value))
        writeconfig("hate", value, "geminiconfig.json")

    def se_exlicit_update_status(self, value):
        globals()["gemini_se_exlicit"] = value
        self.se_exlicit_slider_label.setText(self.block_status(value))
        writeconfig("se_exlicit", value, "geminiconfig.json")

    def dangerous_content_update_status(self, value):
        globals()["gemini_dangerous_content"] = value
        self.dangerous_content_slider_label.setText(self.block_status(value))
        writeconfig("dangerous_content", value, "geminiconfig.json")

    def civic_integrity_update_status(self, value):
        globals()["gemini_civic_integrity"] = value
        self.civic_integrity_slider_label.setText(self.block_status(value))
        writeconfig("civic_integrity", value, "geminiconfig.json")

    def block_status(self, value):
        if value == 1:
            return trls.tr(self.trl, "block_none")
        elif value == 2:
            return trls.tr(self.trl, "block_few")
        elif value == 3:
            return trls.tr(self.trl, "block_some")
        elif value == 4:
            return trls.tr(self.trl, "block_most")

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
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

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
            self.parent.charai_token_entry.setText(token)
            writeconfig("client", token, "charaiconfig.json")
            self.parent.start_fetching_data()
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

        self.characters_list = []
        self.connect = None
        self.microphone_muted = False
        self.ev_close = False

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        self.select_ai_layout = QHBoxLayout()
        self.layout.addLayout(self.select_ai_layout)

        self.select_ai_label = QLabel(trls.tr("MainWindow", "select_ai_label"))
        self.select_ai_layout.addWidget(self.select_ai_label)

        self.select_ai_box = QComboBox()
        self.select_ai_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.select_ai_box.addItems(["Character.AI", "Google Gemini"])
        if aitype == "gemini":
            self.select_ai_box.setCurrentIndex(1)
        self.select_ai_box.currentIndexChanged.connect(self.select_ai)
        self.select_ai_layout.addWidget(self.select_ai_box)


        self.gemini_widget = QWidget()
        self.gemini_layout_main = QHBoxLayout()
        self.gemini_layout = QVBoxLayout()
        self.gemini_layout_main.addLayout(self.gemini_layout)
        self.gemini_widget.setLayout(self.gemini_layout_main)

        gemini_token_layout = QHBoxLayout()
        self.gemini_layout.addLayout(gemini_token_layout)

        self.gemini_token_label = QLabel(trls.tr("MainWindow", "gemini_token"))
        self.gemini_token_label.setWordWrap(True)
        gemini_token_layout.addWidget(self.gemini_token_label)

        self.gemini_token_entry = QLineEdit()
        self.gemini_token_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_token_entry.setPlaceholderText(trls.tr("MainWindow", "token"))
        self.gemini_token_entry.textChanged.connect(lambda: writeconfig("token", self.gemini_token_entry.text(), "geminiconfig.json"))
        self.gemini_token_entry.setText(getconfig("token", configfile="geminiconfig.json"))
        gemini_token_layout.addWidget(self.gemini_token_entry)

        gemini_model_layout = QHBoxLayout()
        self.gemini_layout.addLayout(gemini_model_layout)

        self.gemini_model_label = QLabel(trls.tr("MainWindow", "gemini_model"))
        self.gemini_model_label.setWordWrap(True)
        gemini_model_layout.addWidget(self.gemini_model_label)

        self.gemini_model_box = QComboBox()
        self.gemini_model_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.gemini_model_box.addItems(["Gemini 1.5 Flash", "Gemini 1.5 Pro"])
        self.gemini_model_box.currentIndexChanged.connect(self.select_gemini_model)
        gemini_model_layout.addWidget(self.gemini_model_box)

        self.gemini_safety_button = ResizableButton()
        self.gemini_safety_button.setText(trls.tr("MainWindow", "gemini_safety_settings"))
        self.gemini_safety_button.clicked.connect(self.open_gemini_safety_settings)
        self.gemini_layout_main.addWidget(self.gemini_safety_button)


        self.charai_layout = QVBoxLayout()
        self.charai_widget = QWidget()
        self.charai_widget.setLayout(self.charai_layout)

        charai_token_layout = QHBoxLayout()
        self.charai_layout.addLayout(charai_token_layout)

        self.charai_token_label = QLabel(trls.tr("MainWindow", "character_token"))
        self.charai_token_label.setWordWrap(True)
        charai_token_layout.addWidget(self.charai_token_label)

        self.charai_token_entry = QLineEdit()
        self.charai_token_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.charai_token_entry.setPlaceholderText(trls.tr("MainWindow", "token"))
        self.charai_token_entry.textChanged.connect(lambda: writeconfig("client", self.charai_token_entry.text(), "charaiconfig.json"))
        self.charai_token_entry.setText(getconfig("client", configfile="charaiconfig.json"))
        charai_token_layout.addWidget(self.charai_token_entry)

        charai_char_layout = QHBoxLayout()
        self.charai_layout.addLayout(charai_char_layout)

        self.charai_char_label = QLabel(trls.tr("MainWindow", "character_id"))
        self.charai_char_label.setWordWrap(True)
        charai_char_layout.addWidget(self.charai_char_label)

        self.charai_char_entry = QLineEdit()
        self.charai_char_entry.setPlaceholderText("ID...")
        self.charai_char_entry.textChanged.connect(lambda: writeconfig("char", self.charai_char_entry.text().replace("https://character.ai/chat/", ""), "charaiconfig.json"))
        self.charai_char_entry.setText(getconfig("char", configfile="charaiconfig.json"))
        charai_char_layout.addWidget(self.charai_char_entry)

        self.ai_layout = QStackedLayout()
        self.ai_layout.addWidget(self.gemini_widget)
        self.ai_layout.addWidget(self.charai_widget)
        self.ai_frame = QGroupBox()
        self.ai_frame.setLayout(self.ai_layout)

        if aitype == "gemini":
            self.ai_frame.setTitle(f"Gemini {trls.tr('MainWindow', 'settings')}")
            self.ai_layout.setCurrentIndex(0)
            if gemini_model == "gemini-1.5-flash":
                self.gemini_model_box.setCurrentIndex(0)
            elif gemini_model == "gemini-1.5-pro":
                self.gemini_model_box.setCurrentIndex(1)
            elif gemini_model == "gemini-1.0-pro":
                self.gemini_model_box.setCurrentIndex(1)
        elif aitype == 'charai':
            self.ai_frame.setTitle(f"Character.AI {trls.tr('MainWindow', 'settings')}")
            self.ai_layout.setCurrentIndex(1)
        
        self.layout.addWidget(self.ai_frame)

        self.TTSs_layout = QHBoxLayout()
        self.layout.addLayout(self.TTSs_layout)


        self.elevenlabs_main_layout = QVBoxLayout()
        self.TTSs_layout.addLayout(self.elevenlabs_main_layout)

        self.elevenlabs_frame = QGroupBox("ElevenLabs")
        self.elevenlabs_main_layout.addWidget(self.elevenlabs_frame)

        self.elevenlabs_layout = QVBoxLayout()
        self.elevenlabs_frame.setLayout(self.elevenlabs_layout)

        elevenlabs_token_layout = QHBoxLayout()
        self.elevenlabs_layout.addLayout(elevenlabs_token_layout)

        self.elevenlabs_token_label = QLabel(trls.tr("MainWindow", "elevenlabs_api_key"))
        elevenlabs_token_layout.addWidget(self.elevenlabs_token_label)

        self.elevenlabs_token_entry = QLineEdit()
        self.elevenlabs_token_entry.setPlaceholderText(trls.tr("MainWindow", "elevenlabs_api_key"))
        self.elevenlabs_token_entry.setText(getconfig("elevenlabs_api_key"))
        self.elevenlabs_token_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.elevenlabs_token_entry.textChanged.connect(lambda: writeconfig("elevenlabs_api_key", self.elevenlabs_token_entry.text()))
        elevenlabs_token_layout.addWidget(self.elevenlabs_token_entry)


        elevenlabs_voice_layout = QHBoxLayout()
        self.elevenlabs_layout.addLayout(elevenlabs_voice_layout)

        self.elevenlabs_voice_label = QLabel(trls.tr("MainWindow", "voice"))
        elevenlabs_voice_layout.addWidget(self.elevenlabs_voice_label)

        self.elevenlabs_voice_entry = QLineEdit()
        self.elevenlabs_voice_entry.setPlaceholderText(trls.tr("MainWindow", "voice"))
        self.elevenlabs_voice_entry.setText(getconfig("elevenlabs_voice", configfile="charaiconfig.json"))
        self.elevenlabs_voice_entry.textChanged.connect(lambda: writeconfig("elevenlabs_voice", self.elevenlabs_voice_entry.text(), "charaiconfig.json"))
        elevenlabs_voice_layout.addWidget(self.elevenlabs_voice_entry)

        self.elevenlabs_start_button = QPushButton(f"{trls.tr('MainWindow', 'start')} ElevenLabs")
        self.elevenlabs_start_button.clicked.connect(lambda: self.start_main("elevenlabs"))
        self.elevenlabs_main_layout.addWidget(self.elevenlabs_start_button)


        self.charaitts_main_layout = QVBoxLayout()
        self.TTSs_layout.addLayout(self.charaitts_main_layout)

        self.charaitts_frame = QGroupBox("Character.AI TTS")
        self.charaitts_main_layout.addWidget(self.charaitts_frame)

        self.charaitts_layout = QVBoxLayout()
        self.charaitts_frame.setLayout(self.charaitts_layout)

        charaitts_voice_layout = QHBoxLayout()
        self.charaitts_layout.addLayout(charaitts_voice_layout)

        self.charaitts_voice_label = QLabel(trls.tr("MainWindow", "voice_id"))
        charaitts_voice_layout.addWidget(self.charaitts_voice_label)

        self.charaitts_voice_entry = QLineEdit()
        self.charaitts_voice_entry.setText(getconfig("voiceid", configfile="charaiconfig.json"))
        self.charaitts_voice_entry.setToolTip(trls.tr("MainWindow", "voice_id_tooltip"))
        self.charaitts_voice_entry.textChanged.connect(lambda: writeconfig("voiceid", self.charaitts_voice_entry.text().replace("https://character.ai/?voiceId=", ""), "charaiconfig.json"))
        charaitts_voice_layout.addWidget(self.charaitts_voice_entry)

        self.charaitts_voice_button = QPushButton()
        self.charaitts_voice_button.setText("Search Voice")
        self.charaitts_voice_button.clicked.connect(lambda: VoiceSearch(self.charai_char_entry.text()).show())
        self.charaitts_layout.addWidget(self.charaitts_voice_button)

        self.charaitts_start_button = QPushButton(f"{trls.tr('MainWindow', 'start')} Character.AI TTS")
        self.charaitts_start_button.clicked.connect(lambda: self.start_main("charai"))
        self.charaitts_main_layout.addWidget(self.charaitts_start_button)

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

        self.central_widget.setLayout(self.layout)

        # Chat

        self.chat_widget = QListWidget()
        
        self.mute_microphone_button = QPushButton()
        self.mute_microphone_button.setIcon(QIcon(micicon))
        self.mute_microphone_button.setCheckable(True)
        self.mute_microphone_button.clicked.connect(self.toggle_microphone_mute)

        # MenuBar
        self.menubar = self.menuBar()
        self.emi_menu = self.menubar.addMenu(f"&Emilia {version}")

        if aitype == "charai":
            self.gettokenaction = QAction(trls.tr("MainWindow", "get_token"), self)
        elif aitype == "gemini":
            self.gettokenaction = QAction(trls.tr("MainWindow", "get_token"), self)
        self.gettokenaction.triggered.connect(self.gettoken)

        self.show_chat = QAction(trls.tr("MainWindow", "show_chat"), self)
        self.show_chat.triggered.connect(self.open_chat)

        self.optionsopenaction = QAction(trls.tr("MainWindow", "options"))
        self.optionsopenaction.triggered.connect(self.optionsopen)

        self.mute_microphone_action = QAction(trls.tr("MainWindow", "mute_microphone"), self)
        self.mute_microphone_action.setCheckable(True)
        self.mute_microphone_action.triggered.connect(self.toggle_microphone_mute)

        self.inputdeviceselect = QMenu(trls.tr("MainWindow", "input_device"), self)
        
        input_devices = QMediaDevices.audioInputs()
        
        for index, device in enumerate(input_devices):
            device_name = device.description()
            action = QAction(device_name, self)
            action.triggered.connect(lambda checked, i=index: self.set_microphone(i))
            self.inputdeviceselect.addAction(action)

        self.outputdeviceselect = QMenu(trls.tr("MainWindow", "output_device"), self)
        
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

        self.charselect = self.menubar.addMenu(trls.tr("MainWindow", "character_choice"))

        self.CharacterSearchopen = QAction(QIcon(charediticon), trls.tr("MainWindow", "open_character_search"), self)
        self.CharacterSearchopen.triggered.connect(self.charsopen)

        self.charrefreshlist = QAction(QIcon(refreshicon), trls.tr("MainWindow", "refresh_list"))
        self.charrefreshlist.triggered.connect(self.refreshcharsinmenubar)

        self.charselect.addAction(self.CharacterSearchopen)
        self.charselect.addAction(self.charrefreshlist)
        
        self.addcharsinmenubar()
        if aitype == "charai":
            self.start_fetching_data()

        self.aboutemi = QAction(QIcon(emiliaicon), trls.tr("MainWindow", "about_emilia"), self)
        self.aboutemi.triggered.connect(self.about)

        self.emi_menu.addAction(self.gettokenaction)
        self.emi_menu.addAction(self.show_chat)
        if aitype != "charai":
            self.charaitts_frame.setEnabled(False)
            self.show_chat.setVisible(False)
            self.charselect.setEnabled(False)
            self.charaitts_start_button.setEnabled(False)
        self.emi_menu.addAction(self.optionsopenaction)
        self.emi_menu.addAction(self.aboutemi)
        self.emi_menu.addMenu(self.inputdeviceselect)
        self.emi_menu.addMenu(self.outputdeviceselect)

    def select_gemini_model(self, index):
        global gemini_model
        if index == 0:
            gemini_model = "gemini-1.5-flash"
        elif index == 1:
            gemini_model = "gemini-1.5-pro"
        writeconfig("gemini_model", gemini_model, "geminiconfig.json")
        
    def select_ai(self, index):
        global aitype
        if index == 0:
            index = 1
            aitype = "charai"
            title = "Character.AI Settings"
            self.charaitts_frame.setEnabled(True)
            self.show_chat.setVisible(True)
            self.charselect.setEnabled(True)
            self.charaitts_start_button.setEnabled(True)
        elif index == 1:
            index = 0
            aitype = "gemini"
            title = "Gemini Settings"
            self.charaitts_frame.setEnabled(False)
            self.show_chat.setVisible(False)
            self.charselect.setEnabled(False)
            self.charaitts_start_button.setEnabled(False)
        self.ai_frame.setTitle(title)
        self.ai_layout.setCurrentIndex(index)
        writeconfig("aitype", aitype)

    def start_fetching_data(self):
        try:
            if self.charai_token_entry.text() != "":
                self.CharacterSearchopen.setEnabled(False)
                self.chat_data_worker = ChatDataWorker()
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
        if self.microphone_muted:
            self.mute_microphone_button.setIcon(QIcon(micofficon))
        else:
            self.mute_microphone_button.setIcon(QIcon(micicon))

    def open_gemini_safety_settings(self):
        window = Gemini_Safety_Settings()
        window.show()

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
        if os.path.exists("data.json"):
            def open_json(char, speaker):
                self.charai_char_entry.setText(char)
                if tts == "charai":
                    self.charaitts_voice_entry.setText(speaker)
                elif tts == "elevenlabs":
                    self.elevenlabs_voice_entry.setText(speaker)
            def create_action(key, value):
                def action_func():
                    if tts == "charai":
                        open_json(value["char"], value.get("voiceid", ""))
                    elif tts == "elevenlabs":
                        open_json(value["char"], value.get("voice", ""))
                action = QAction(value["name"], self)
                action.triggered.connect(action_func)
                return action
            try:
                with open("data.json", "r", encoding="utf-8") as file:
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
            if dev["name"] == device_name and dev["max_output_channels"] > 0:
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
            self.auth_window = EmiliaAuth(self)
            self.auth_window.show()
        elif aitype == "gemini":
            webbrowser.open("https://aistudio.google.com/app/apikey")

    def about(self):
        if pre == True:
            title = trls.tr("About", "about_emilia") + version
        else:
            title = trls.tr("About", "about_emilia")
        pixmap = QPixmap(emiliaicon).scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        language = trls.tr("About", "language_from")
        whatsnew = trls.tr("About", "new_in") + version + trls.tr("About", "whats_new")
        otherversions = trls.tr("About", "show_all_releases")
        text = trls.tr("About", "emilia_is_open_source") + version + trls.tr("About", "use_version") + language + whatsnew + otherversions
        text = text.replace("\n", "<br>")
        MessageBox(title, text, pixmap=pixmap, self=self)

    def start_main(self, tts):
        if tts == "elevenlabs" and self.elevenlabs_voice_entry.text() == "":
            MessageBox(text="Voice?")
            return
        
        for actions in self.emi_menu.actions():
            actions.setVisible(False)
        
        for button in self.findChildren(QWidget):
            if any(isinstance(button, type) for type in [QGroupBox, QLabel, QComboBox, QPushButton]):
                button.setVisible(False)

        self.emi_menu.addAction(self.mute_microphone_action)
        self.mute_microphone_action.setVisible(True)
        self.setGeometry(300, 300, 800, 400)

        writeconfig("tts", tts)

        if aitype == "charai":
            self.charai_start_main(tts)
        elif aitype == "gemini":
            self.gemini_start_main(tts)

    def charai_start_main(self, tts):
        self.layout.addWidget(self.chat_widget)
        self.layout.addWidget(self.mute_microphone_button)
        self.main_thread_charai = MainThreadCharAI(self, tts)
        self.main_thread_charai.chatLoaded.connect(self.populate_list)
        self.main_thread_charai.ouinput_signal.connect(self.populate_list)
        self.main_thread_charai.start()

    def gemini_start_main(self, tts):
        self.layout.addWidget(self.chat_widget)
        self.layout.addWidget(self.mute_microphone_button)
        self.main_thread_charai = MainThreadGemini(self, tts)
        self.main_thread_charai.ouinput_signal.connect(self.populate_list)
        self.main_thread_charai.start()

    def populate_list(self, data = "zxc", is_human = "zxc", text = None, audio_len = 100, new = False, translated = False):
        if data != "zxc":
            for turn in data:
                if is_human == "zxc":
                    is_human = turn.author.is_human
                    if is_human:
                        is_human = "human"
                    else:
                        is_human = "ai"
                    text = turn.candidates[0].raw_content
                custom_widget = MainMessageWidget(self, is_human, text, audio_len, new, translated)
                item = QListWidgetItem()
                item.setSizeHint(custom_widget.sizeHint())
                self.chat_widget.addItem(item)
                self.chat_widget.setItemWidget(item, custom_widget)
                is_human = "zxc"
        else:
            custom_widget = MainMessageWidget(self, is_human, text, audio_len, new, translated)
            item = QListWidgetItem()
            item.setSizeHint(custom_widget.sizeHint())
            self.chat_widget.addItem(item)
            self.chat_widget.setItemWidget(item, custom_widget)
        self.chat_widget.scrollToBottom()

    def closeEvent(self, event):
        self.ev_close = True
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(theme)
    window = Emilia()
    if autoupdate_enable:
        check_for_updates(version, "Emilia.zip", pre, window)
    if vtube_enable:
        Emote_File()
    window.show()
    sys.exit(app.exec())