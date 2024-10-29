import os, asyncio, winreg, sys, webbrowser
import requests

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
                             QListWidget, 
                             QListWidgetItem,
                             QGroupBox)
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import QLocale, Qt

from modules.config import getconfig, writeconfig, resource_path 
from modules.character_search import (CharacterWidget, 
                                      NewCharacterEditor, 
                                      MainMessageWidget)
from modules.translations import translations
from modules.other import MessageBox

version = "2.3b2dev1"
pre = True
sample_rate = 48000

# Global Variables
autoupdate_enable = getconfig('autoupdate_enable', False)
vtube_enable = getconfig('vtubeenable', False)
umtranslate = getconfig('umtranslate', False)
aimtranslate = getconfig('aimtranslate', False)
show_notranslate_message = getconfig('show_notranslate_message', True)
show_system_messages = getconfig('show_system_messages', True)
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

# Gemini Variables
gemini_model = getconfig('gemini_model', 'gemini-1.5-flash', 'geminiconfig.json')
gemini_harassment = getconfig('harassment', 3, 'geminiconfig.json')
gemini_hate = getconfig('hate', 3, 'geminiconfig.json')
gemini_se_exlicit = getconfig('se_exlicit', 3, 'geminiconfig.json')
gemini_dangerous_content = getconfig('dangerous_content', 3, 'geminiconfig.json')
gemini_civic_integrity = getconfig('civic_integrity', 3, 'geminiconfig.json')

# Icons
emiliaicon = f'{imagesfolder}/emilia.png'
googleicon = f'{imagesfolder}/google.png'
charaiicon = f'{imagesfolder}/charai.png'
refreshicon = f'{imagesfolder}/refresh.png'
if iconcolor == 'white':
    keyboardicon = f'{imagesfolder}/keyboard_white.png'
    charediticon = f'{imagesfolder}/open_char_editor_white.png'
else:
    keyboardicon = f'{imagesfolder}/keyboard.png'
    charediticon = f'{imagesfolder}/open_char_editor.png'

if tts == 'charai' and aitype != 'charai':
    tts = 'elevenlabs'
    writeconfig('tts', tts)

class FirstLaunch(QMainWindow):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

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
        self.layout.addWidget(self.first_launch_notification_label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)

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
        self.chat_example = ChatExample()
        self.second_page_layout = QVBoxLayout()
        self.second_page_widget.setLayout(self.second_page_layout)

        self.second_page_layout.addWidget(OptionsWindow(self, self.chat_example))
        self.second_page_layout.addWidget(self.chat_example)

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
        self.getlink_button.clicked.connect(self.getlink)
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
        self.parent.show()
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
        self.setMinimumWidth(300)
        self.setMaximumWidth(300)
        self.setMinimumHeight(120)
        self.setMaximumHeight(120)
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
        global iconcolor, charediticon
        if value == 0:
            charediticon = f'{imagesfolder}/open_char_editor_white.png'
            iconcolor = 'white'
        elif value == 1:
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
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)

    def first_launch_button_no(self):
        writeconfig('aitype', 'charai')
        if imagesfolder == "images":
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)

class OptionsWindow(QWidget):
    def __init__(self, mainwindow, chat_example):
        super().__init__()
        self.setMinimumHeight(150)
        self.trl = "OptionsWindow"

        self.addchar_button = QPushButton(trls.tr("CharEditor", "add_character"))
        self.addchar_button.clicked.connect(lambda: asyncio.run(self.addchar()))

        self.mainwindow = mainwindow
        self.chat_example = chat_example
        layout = QHBoxLayout()

        firsthalf = QVBoxLayout()
        self.firsthalf = firsthalf
        secondhalf = QVBoxLayout()

        self.system_options = QGroupBox(trls.tr(self.trl, 'system_options'))
        self.system_options_layout = QVBoxLayout()
        self.system_options.setLayout(self.system_options_layout)
        firsthalf.addWidget(self.system_options)

        autoupdatelayout = QHBoxLayout()
        self.autoupdate = QCheckBox()
        if autoupdate_enable:
            self.autoupdate.setChecked(True)
        self.autoupdate.stateChanged.connect(self.autoupdatechange)


        autoupdatelayout.addWidget(QLabel(trls.tr(self.trl, 'automatic_updates')))
        autoupdatelayout.addWidget(self.autoupdate)
        self.system_options_layout.addLayout(autoupdatelayout)


        self.umlayout = QHBoxLayout()
        self.umcheck_box = QCheckBox()
        if umtranslate:
            self.umcheck_box.setChecked(True)
        self.umcheck_box.stateChanged.connect(self.umtranslate_change)

        self.umlayout.addWidget(QLabel(trls.tr(self.trl, 'umlayout')))
        self.umlayout.addWidget(self.umcheck_box)
        self.system_options_layout.addLayout(self.umlayout)


        self.aimlayout = QHBoxLayout()
        self.aimcheck_box = QCheckBox()
        if aimtranslate:
            self.aimcheck_box.setChecked(True)
        self.aimcheck_box.stateChanged.connect(self.aimtranslate_change)

        self.aimlayout.addWidget(QLabel(trls.tr(self.trl, 'aimlayout')))
        self.aimlayout.addWidget(self.aimcheck_box)
        self.system_options_layout.addLayout(self.aimlayout)


        self.sntmlayout = QHBoxLayout()
        self.sntmcheck_box = QCheckBox()
        if aimtranslate == False and umtranslate == False:
            self.sntmcheck_box.setEnabled(False)
        if show_notranslate_message:
            self.sntmcheck_box.setChecked(True)
        self.sntmcheck_box.stateChanged.connect(self.show_untrl_messages_change)

        self.sntmlayout.addWidget(QLabel(trls.tr(self.trl, 'sntmlayout')))
        self.sntmlayout.addWidget(self.sntmcheck_box)
        self.system_options_layout.addLayout(self.sntmlayout)


        self.ssmlayout = QHBoxLayout()
        self.ssmcheck_box = QCheckBox()
        if show_system_messages:
            self.ssmcheck_box.setChecked(True)
        self.ssmcheck_box.stateChanged.connect(self.show_ss_messages_change)

        self.ssmlayout.addWidget(QLabel(trls.tr(self.trl, 'ssmlayout')))
        self.ssmlayout.addWidget(self.ssmcheck_box)
        self.system_options_layout.addLayout(self.ssmlayout)


        self.other_options = QGroupBox(trls.tr(self.trl, 'other_options'))
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


        self.customization_options = QGroupBox(trls.tr(self.trl, 'customization_options'))
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
        theme = getconfig('theme', 'windowsvista')
        if theme == 'windowsvista':
            self.themechange.setCurrentIndex(1)
        elif theme == 'windows11':
            self.themechange.setCurrentIndex(2)
        elif theme == 'Fuison':
            self.themechange.setCurrentIndex(0)
        self.themechange.currentIndexChanged.connect(self.changetheme)

        themelayout.addWidget(QLabel(trls.tr(self.trl, "select_theme")))
        themelayout.addWidget(self.themechange)
        self.customization_options_layout.addLayout(themelayout)


        iconcolorlayout = QHBoxLayout()
        self.iconcolorchange = QComboBox()
        self.iconcolorchange.addItems([trls.tr(self.trl, 'white'), trls.tr(self.trl, 'black')])
        iconcolor = getconfig('iconcolor', 'white')
        if iconcolor == 'black':
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

        self.reload_chat()

    def reload_chat(self):
        chat = self.chat_example
        chat.chat_widget.clear()
        sys_message = 'System Message'
        ai_message = 'AI Message'
        us_message = 'User Message'
        if aimtranslate and show_notranslate_message:
            ai_message = ai_message + '<p style="color: gray; font-style: italic; font-size: 12px;">Original AI Message</p>'
        if umtranslate and show_notranslate_message:
            us_message = us_message + '<p style="color: gray; font-style: italic; font-size: 12px;">Original User Message</p>'
        
        chat.populate_list(ai_message, 'ai', aimtranslate)
        chat.populate_list(us_message, 'human', umtranslate)
        if show_system_messages:
            chat.populate_list(sys_message, 'sys', False)

    def show_ss_messages_change(self, state):
        global show_system_messages
        if state == 2:
            show_system_messages = True
        else:
            show_system_messages = False
        writeconfig('show_system_messages', show_system_messages)
        self.reload_chat()

    def show_untrl_messages_change(self, state):
        global show_notranslate_message
        if state == 2:
            show_notranslate_message = True
        else:
            show_notranslate_message = False
        writeconfig('show_notranslate_message', show_notranslate_message)
        self.reload_chat()

    def umtranslate_change(self, state):
        global umtranslate
        if state == 2:
            umtranslate = True
            self.sntmcheck_box.setEnabled(True)
        else:
            umtranslate = False
            if aimtranslate == False:
                self.sntmcheck_box.setEnabled(False)
        writeconfig('umtranslate', umtranslate)
        self.reload_chat()

    def aimtranslate_change(self, state):
        global aimtranslate
        if state == 2:
            aimtranslate = True
            self.sntmcheck_box.setEnabled(True)
        else:
            aimtranslate = False
            if umtranslate == False:
                self.sntmcheck_box.setEnabled(False)
        writeconfig('aimtranslate', aimtranslate)
        self.reload_chat()

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

    def changetheme(self, value):
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

    def changeiconcolor(self, value):
        global iconcolor
        if value == 0:
            charediticon = f'{imagesfolder}/open_char_editor_white.png'
            iconcolor = 'white'
        elif value == 1:
            charediticon = f'{imagesfolder}/open_char_editor.png'
            iconcolor = 'black'
        writeconfig('iconcolor', iconcolor)
        self.mainwindow.CharacterSearchopen.setIcon(QIcon(charediticon))

    def langchange(self, value):
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
        globals()['backcolor'] = QColorDialog.getColor(self.current_color, self)
        self.mainwindow.set_background_color(backcolor) 
        self.set_background_color(backcolor)
        writeconfig('backgroundcolor', backcolor.name())

    def pick_button_color(self):
        globals()['buttoncolor'] = QColorDialog.getColor(self.current_button_color, self)
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
        global iconcolor, backcolor, buttoncolor, buttontextcolor, labelcolor, charediticon
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

class ChatExample(QWidget):
    def __init__(self):
        super().__init__()
        self.trl = "ChatWithCharacter"

        self.chat_widget = QListWidget()

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.chat_widget)

        self.setLayout(self.main_layout)

    def populate_list(self, text, mode, translated):
        custom_widget = MainMessageWidget(self, mode, text, 0, False, translated)
        item = QListWidgetItem()
        item.setSizeHint(custom_widget.sizeHint())
        self.chat_widget.addItem(item)
        self.chat_widget.setItemWidget(item, custom_widget)

        self.chat_widget.scrollToBottom()

    def on_chat_load_finish(self):
        self.chat_widget.setEnabled(True)