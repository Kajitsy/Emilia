import ctypes
import platform
import webbrowser, os, logging,  json, inspect
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QFrame, QFileDialog, QApplication)
from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator, QKeySequence
from PyQt6.QtCore import QDateTime, QRegularExpression, Qt, QTranslator
from platformdirs import user_log_dir

from modules import ChatThread
from modules.ui import TM
from modules.ui.Elements import (PushButton, LineEdit, CheckBox, KeySequenceEdit,
                                 ComboBox, VerticalScrollPage, CardFrame)
from modules.Utils import format_text
from modules.logic.QThreads import DiscordRPCThread
from modules.ui.cards import UserCards, CookieCards, ThemeCards
from modules.ui.mainwindow import MainPage

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout()
        self.mw: MainPage | None = parent
        self.chat_thread: ChatThread | None = self.mw.chat_thread
        self.discord_thread: DiscordRPCThread | None = self.mw.discord_thread
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.languages = {
            "en_US": {"title": self.tr("English"), "lang_available": True, "google_code": "en"},
            "ru_RU": {"title": self.tr("Russian"), "lang_available": True, "google_code": "ru"},
            "fr_FR": {"title": self.tr("French"), "lang_available": False, "google_code": "fr"},
            "es_ES": {"title": self.tr("Spanish"), "lang_available": True, "google_code": "es"},
            "af_ZA": {"title": self.tr("Afrikaans"), "lang_available": False, "google_code": "af"},
            "sq_AL": {"title": self.tr("Albanian"), "lang_available": False, "google_code": "sq"},
            "am_ET": {"title": self.tr("Amharic"), "lang_available": False, "google_code": "am"},
            "ar_SA": {"title": self.tr("Arabic"), "lang_available": False, "google_code": "ar"},
            "hy_AM": {"title": self.tr("Armenian"), "lang_available": False, "google_code": "hy"},
            "az_AZ": {"title": self.tr("Azerbaijani"), "lang_available": False, "google_code": "az"},
            "eu_ES": {"title": self.tr("Basque"), "lang_available": False, "google_code": "eu"},
            "bn_BD": {"title": self.tr("Bengali"), "lang_available": False, "google_code": "bn"},
            "bg_BG": {"title": self.tr("Bulgarian"), "lang_available": False, "google_code": "bg"},
            "ca_ES": {"title": self.tr("Catalan"), "lang_available": False, "google_code": "ca"},
            "hr_HR": {"title": self.tr("Croatian"), "lang_available": False, "google_code": "hr"},
            "cs_CZ": {"title": self.tr("Czech"), "lang_available": False, "google_code": "cs"},
            "da_DK": {"title": self.tr("Danish"), "lang_available": False, "google_code": "da"},
            "nl_NL": {"title": self.tr("Dutch"), "lang_available": False, "google_code": "nl"},
            "et_EE": {"title": self.tr("Estonian"), "lang_available": False, "google_code": "et"},
            "tl_PH": {"title": self.tr("Filipino"), "lang_available": False, "google_code": "tl"},
            "fi_FI": {"title": self.tr("Finnish"), "lang_available": False, "google_code": "fi"},
            "ka_GE": {"title": self.tr("Georgian"), "lang_available": False, "google_code": "ka"},
            "de_DE": {"title": self.tr("German"), "lang_available": True, "google_code": "de"},
            "el_GR": {"title": self.tr("Greek"), "lang_available": False, "google_code": "el"},
            "gu_IN": {"title": self.tr("Gujarati"), "lang_available": False, "google_code": "gu"},
            "he_IL": {"title": self.tr("Hebrew"), "lang_available": False, "google_code": "he"},
            "hi_IN": {"title": self.tr("Hindi"), "lang_available": False, "google_code": "hi"},
            "hu_HU": {"title": self.tr("Hungarian"), "lang_available": False, "google_code": "hu"},
            "is_IS": {"title": self.tr("Icelandic"), "lang_available": False, "google_code": "is"},
            "id_ID": {"title": self.tr("Indonesian"), "lang_available": False, "google_code": "id"},
            "ga_IE": {"title": self.tr("Irish"), "lang_available": False, "google_code": "ga"},
            "it_IT": {"title": self.tr("Italian"), "lang_available": False, "google_code": "it"},
            "ja_JP": {"title": self.tr("Japanese"), "lang_available": False, "google_code": "ja"},
            "kn_IN": {"title": self.tr("Kannada"), "lang_available": False, "google_code": "kn"},
            "kk_KZ": {"title": self.tr("Kazakh"), "lang_available": False, "google_code": "kk"},
            "ko_KR": {"title": self.tr("Korean"), "lang_available": False, "google_code": "ko"},
            "lo_LA": {"title": self.tr("Lao"), "lang_available": False, "google_code": "lo"},
            "lv_LV": {"title": self.tr("Latvian"), "lang_available": False, "google_code": "lv"},
            "lt_LT": {"title": self.tr("Lithuanian"), "lang_available": False, "google_code": "lt"},
            "mk_MK": {"title": self.tr("Macedonian"), "lang_available": False, "google_code": "mk"},
            "ms_MY": {"title": self.tr("Malay"), "lang_available": False, "google_code": "ms"},
            "ml_IN": {"title": self.tr("Malayalam"), "lang_available": False, "google_code": "ml"},
            "mt_MT": {"title": self.tr("Maltese"), "lang_available": False, "google_code": "mt"},
            "mn_MN": {"title": self.tr("Mongolian"), "lang_available": False, "google_code": "mn"},
            "ne_NP": {"title": self.tr("Nepali"), "lang_available": False, "google_code": "ne"},
            "no_NO": {"title": self.tr("Norwegian"), "lang_available": False, "google_code": "no"},
            "fa_IR": {"title": self.tr("Persian"), "lang_available": False, "google_code": "fa"},
            "pl_PL": {"title": self.tr("Polish"), "lang_available": False, "google_code": "pl"},
            "pt_PT": {"title": self.tr("Portuguese"), "lang_available": True, "google_code": "pt"},
            "pa_IN": {"title": self.tr("Punjabi"), "lang_available": False, "google_code": "pa"},
            "ro_RO": {"title": self.tr("Romanian"), "lang_available": False, "google_code": "ro"},
            "sr_RS": {"title": self.tr("Serbian"), "lang_available": False, "google_code": "sr"},
            "sk_SK": {"title": self.tr("Slovak"), "lang_available": False, "google_code": "sk"},
            "sl_SI": {"title": self.tr("Slovenian"), "lang_available": False, "google_code": "sl"},
            "sw_KE": {"title": self.tr("Swahili"), "lang_available": False, "google_code": "sw"},
            "sv_SE": {"title": self.tr("Swedish"), "lang_available": False, "google_code": "sv"},
            "ta_IN": {"title": self.tr("Tamil"), "lang_available": False, "google_code": "ta"},
            "te_IN": {"title": self.tr("Telugu"), "lang_available": False, "google_code": "te"},
            "th_TH": {"title": self.tr("Thai"), "lang_available": False, "google_code": "th"},
            "tr_TR": {"title": self.tr("Turkish"), "lang_available": False, "google_code": "tr"},
            "uk_UA": {"title": self.tr("Ukrainian"), "lang_available": True, "google_code": "uk"},
            "ur_PK": {"title": self.tr("Urdu"), "lang_available": False, "google_code": "ur"},
            "vi_VN": {"title": self.tr("Vietnamese"), "lang_available": False, "google_code": "vi"},
            "cy_GB": {"title": self.tr("Welsh"), "lang_available": False, "google_code": "cy"},
            "xh_ZA": {"title": self.tr("Xhosa"), "lang_available": False, "google_code": "xh"}
        }
        self.update_servers = {}
        self.ud_added = False
        self.settings_data = [
            {
                "label": self.tr("Character.AI Settings"),
                "settings": [
                    {"type": "pushbutton", "label": self.tr("Character.AI Login") + "\n" + self.tr("Valid until: ") + self.mw.settings.value('cai_auth/expiration_date') if self.mw.settings.value('cai_auth/expiration_date') else self.tr("Character.AI Login"),
                     "buttonlabel": self.tr("Re-Auth with Character.AI") if self.mw.token else self.tr("Auth with Character.AI") ,
                     "key": "auth_cookie_get", "click": self.getCookies},
                    {"type": "pushbutton", "label": self.tr("User Settings"), "buttonlabel": self.tr("Open"), "key": "cai_edit", "click": self.openUserSettings}
                ]
            }, {
                "label": self.tr("Emilia Settings"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Automatically hide the sidebar when the window is narrow"), "key": "auto_collapse_sidebar"},
                    {"type": "combobox", "label": self.tr("App theme"), "items": TM.get_themes_name(), "key": "app_theme"},
                    {"type": "pushbutton", "label": self.tr("Theme Catalog"), "buttonlabel": self.tr("Open"), "key": "app_theme_catalog", "click": self.openThemeCatalog},
                    {"type": "checkbox", "label": self.tr("Sync theme with system theme"), "key": "app_theme_system_sync"},
                    {"type": "checkbox", "label": self.tr("Working in the background"), "key": "backwork", "def_value": True},
                    {"type": "checkbox", "label": self.tr("Display text formatting buttons"), "key": "show_format_buttons", "def_value": False},
                    {"type": "combobox", "label": self.tr("Update Server"), "items": list(self.update_servers.values()), "key": "update_server", "def_value": "https://germany.emiupd.ateez.ru/"},
                    {"type": "combobox", "label": self.tr("Input Device"), "items": self.mw.input_devices.values(), "key": "input_device"},
                    {"type": "combobox", "label": self.tr("Output Device"), "items": self.mw.output_devices.values(), "key": "output_device"},
                    {"type": "keybind", "label": self.tr("Microphone mute key"), "def_value": "Ctrl+M", "key": "microphone_mute_key_bind"},
                    {"type": "checkbox", "label": self.tr("Use the old implementation of voice chat"), "key": "use_old_voice_chat"},
                ]
            }, {
                "label": self.tr("VTube Studio Plugin"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Use VTube Studio"), "key": "vtube/use", "def_value": False},
                    {"type": "lineedit", "label": self.tr("VTube Studio Address"), "key": "vtube/address",
                     "def_value": "127.0.0.1", "may_be_empty": False},
                    {"type": "lineedit", "label": self.tr("VTube Studio Port"), "key": "vtube/port",
                     "validator": QIntValidator(0, 99999999), "def_value": 8001, "may_be_empty": False},
                    {"type": "pushbutton", "label": self.tr("VTube Emotes Editor"),
                     "buttonlabel": self.tr("Open"), "key": "vtube/emotes_editor", "click": self.openEmotesEditor},
                    {"type": "pushbutton", "label": self.tr("Check the connection to VTube Studio"), "buttonlabel": self.tr("Check"),
                     "key": "vtube/check_connect", "click": self.vtubeCheck},
                ]
            }, {
                "label": self.tr("Virtual Model Plugin (VModel)"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Use VModel"), "key": "vmodel/use", "def_value": False},
                    {"type": "pushbutton", "label": self.tr("Models folder"),
                     "buttonlabel": self.tr("Change"), "key": "vmodel/change_default_folder", "click": self.changeVModelFolder},
                    {"type": "lineedit", "label": self.tr("FPS"), "key": "vmodel/fps",
                     "def_value": "60", "may_be_empty": False},
                    {"type": "checkbox", "label": self.tr("Cursor Tracking"), "key": "vmodel/cursor_tracking", "def_value": True},
                    {"type": "checkbox", "label": self.tr("Auto Blink"), "key": "vmodel/auto_blink", "def_value": True},
                    {"type": "lineedit", "label": self.tr("Volume Smoothing"), "key": "vmodel/volume_smoothing",
                     "def_value": "0.6", "may_be_empty": False},
                ]
            }, {
                "label": self.tr("Discord Rich Presence"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Enable DiscordRPC"), "key": "discord_rpc/enable", "def_value": True},
                    {"type": "checkbox", "label": self.tr("Display the current page"), "key": "discord_rpc/show_current_page", "def_value": True},
                    {"type": "checkbox", "label": self.tr("Displaying the chat name"), "key": "discord_rpc/show_chat_name", "def_value": False},
                    {"type": "checkbox", "label": self.tr("Displaying the nickname of the profile being viewed"), "key": "discord_rpc/show_username", "def_value": False}
                ]
            }, {
                "label": self.tr("Languages of Emilia"),
                "settings": [
                    {"type": "combobox", "label": self.tr("Emilia Language"), "items": [lang["title"] for lang in self.languages.values() if lang.get("lang_available", False)], "key": "emilia_language"},
                    {"type": "checkbox", "label": self.tr("Translate user's messages"), "key": "tr_user_msg"},
                    {"type": "combobox", "label": self.tr("Translate user's messages to"), "items": [lang["title"] for lang in self.languages.values()], "key": "tr_user_msg_to"},
                    {"type": "checkbox", "label": self.tr("Translate character messages"), "key": "tr_char_msg"},
                    {"type": "combobox", "label": self.tr("Translate character messages to"), "items": [lang["title"] for lang in self.languages.values()], "key": "tr_char_msg_to"},
                ]
            }, {
                "label": self.tr("Other"),
                "settings": [
                    {"type": "pushbutton", "label": self.tr("Did you find a problem?"),
                     "buttonlabel": self.tr("Report a Problem"),
                     "key": "other/report_a_problem", "click": lambda: webbrowser.open("https://github.com/Kajitsy/Emilia/issues")},
                    {"type": "pushbutton", "label": self.tr("Settings Folder"),
                     "buttonlabel": self.tr("Open"),
                     "key": "other/settings_folder",
                     "click": lambda: os.startfile(os.path.dirname(self.mw.settings.fileName()))},
                    {"type": "pushbutton", "label": self.tr("Logs Folder"),
                     "buttonlabel": self.tr("Open"),
                     "key": "other/logs_folder",
                     "click": lambda: os.startfile(Path(user_log_dir("Emilia", False)))},
                ]
            }, {
                "label": f"{self.tr('About Emilia')} {self.mw.version}",
                "settings": [
                    {
                        "label": self.tr("Emilia is a desktop version of Character.AI with several improvements and additional features.")+
                                 "\n"+self.tr("The program is distributed free of charge under the MIT License."),
                        "key": "about/title"},
                    {
                        "label": self.tr("By using Emilia, you accept the Terms of Use Character.AI and confirm that you have read the Privacy Policy Character.AI"),
                        "key": "about/tos"
                    }
                ]
            },
        ]

        self.setting_widgets = {}
        self.setting_data = {}

        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.scroll_area, self.settings_viewport, self.settings_layout = self.createMainContentPage()
        self.button_bar, self.button_layout = self.createButtonBar()

        main_layout.addWidget(self.scroll_area, alignment=Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(self.button_bar, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)

    def openUserSettings(self):
        overlay = UserCards.EditCard(self.mw)
        self.mw.showOverlay(overlay)

    def openThemeCatalog(self):
        overlay = ThemeCards.SearchCard(self.mw)
        self.mw.showOverlay(overlay)

    def changeVModelFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select folder", self.mw.settings.value("vmodel/default_folder", "./vtubes"))
        if os.path.exists(folder_path):
            models_count = 0
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(".vtube.json"):
                        models_count += 1
            self.mw.settings.setValue("vmodel/default_folder", folder_path)
            self.mw.showNotification(self.tr("(mc) models found").replace("(mc)", str(models_count)))

    def openEmotesEditor(self):
        with open(f"./data/VTube_Emotes.json", "r") as f:
            emotes_data = json.load(f)

        def createEmoteSlot(emote, param_name="", random_value=False, value=0, value_1=0, value_2=100):
            def updateRandom():
                nonlocal random_value
                random_value = random_checkbox.isChecked()
                if random_value:
                    value_1_edit.setVisible(True)
                    value_2_edit.setVisible(True)
                    value_edit.setVisible(False)
                else:
                    value_1_edit.setVisible(False)
                    value_2_edit.setVisible(False)
                    value_edit.setVisible(True)
                updateParamName(param_name_edit.text(), param_name)

            def updateParamName(text, pn):
                if pn in emotes_data[emote]['params']:
                    del emotes_data[emote]['params'][pn]
                nonlocal param_name
                param_name = text
                if random_value:
                    emotes_data[emote]['params'][text] = f"rndm({value_1}, {value_2})"
                else:
                    emotes_data[emote]['params'][text] = value

            def updateParamValue(text):
                nonlocal value
                value = text
                emotes_data[emote]['params'][param_name] = value

            def updateParamValue1(text):
                nonlocal value_1
                value_1 = text
                if random_value:
                    emotes_data[emote]['params'][param_name] = f"rndm({value_1}, {value_2})"

            def updateParamValue2(text):
                nonlocal value_2
                value_2 = text
                if random_value:
                    emotes_data[emote]['params'][param_name] = f"rndm({value_1}, {value_2})"

            def removeParameter():
                if param_name in emotes_data[emote]['params']:
                    del emotes_data[emote]['params'][param_name]
                u_widget.hide()
                u_widget.deleteLater()

            validator = QRegularExpressionValidator(QRegularExpression(r"[^\s]+"))
            u_widget = CardFrame()
            u_widget.setCursor(Qt.CursorShape.LastCursor)
            u_layout = QHBoxLayout(u_widget)
            u_widget.setLayout(u_layout)

            param_name_edit = LineEdit()
            param_name_edit.setValidator(validator)
            param_name_edit.textChanged.connect(lambda t: updateParamName(t, param_name))
            param_name_edit.setPlaceholderText(self.tr("Parameter Name"))
            param_name_edit.setText(param_name)
            param_name_edit.setFixedWidth(150)
            u_layout.addWidget(param_name_edit)

            remove_button = PushButton()
            remove_button.clicked.connect(removeParameter)
            remove_button.setIcon(self.mw.svg_icons.close(TM.c("icon")))
            u_layout.addWidget(remove_button)

            u_layout.addStretch()

            random_checkbox = CheckBox()
            random_checkbox.setChecked(random_value)
            random_checkbox.clicked.connect(updateRandom)
            u_layout.addWidget(random_checkbox)

            random_label = QLabel(self.tr("Use Random Value"))
            u_layout.addWidget(random_label)

            value_1_edit = LineEdit()
            value_1_edit.setValidator(validator)
            value_1_edit.textEdited.connect(updateParamValue1)
            value_1_edit.setPlaceholderText(self.tr("From"))
            value_1_edit.setText(str(value_1))
            value_1_edit.setFixedWidth(50)
            u_layout.addWidget(value_1_edit)
            value_1_edit.setVisible(random_value)

            value_2_edit = LineEdit()
            value_2_edit.setValidator(validator)
            value_2_edit.textEdited.connect(updateParamValue2)
            value_2_edit.setPlaceholderText(self.tr("To"))
            value_2_edit.setText(str(value_2))
            value_2_edit.setFixedWidth(50)
            u_layout.addWidget(value_2_edit)
            value_2_edit.setVisible(random_value)

            value_edit = LineEdit()
            value_edit.setValidator(validator)
            value_edit.textEdited.connect(updateParamValue)
            value_edit.setPlaceholderText(self.tr("Value"))
            value_edit.setText(str(value))
            value_edit.setFixedWidth(106)
            u_layout.addWidget(value_edit)
            value_edit.setVisible(not random_value)

            return u_widget

        def createParameter(button, layout, emote):
            layout.removeWidget(button)
            layout.addWidget(createEmoteSlot(emote))
            layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)

        def save():
            with open("./data/VTube_Emotes.json", "w", encoding="utf-8") as f:
                json.dump(emotes_data, f, ensure_ascii=False, indent=4)
            self.mw.showNotification(self.tr("The values for emotions are saved"))
            self.mw.hideOverlay()

        scroll_page = VerticalScrollPage()
        scroll_viewport = scroll_page.viewport
        scroll_layout = scroll_page.layout
        scroll_viewport.setStyleSheet("background-color: transparent; border: none;")

        for emote_name in emotes_data.keys():
            e_widget = QWidget()
            e_layout = QVBoxLayout()
            e_widget.setLayout(e_layout)
            emote_data = emotes_data[emote_name]
            if emote_data.get("version", 1) == 1:
                break
            params = emote_data['params']

            head_layout = QHBoxLayout()
            head_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            group_label = QLabel(emote_data["label"])
            font = group_label.font()
            font.setBold(True)
            font.setPointSize(14)
            group_label.setFont(font)
            head_layout.addWidget(group_label)
            test_emote_button = QPushButton(self.tr(" | Test"))
            test_emote_button.setFont(font)
            test_emote_button.setCursor(Qt.CursorShape.PointingHandCursor)
            test_emote_button.clicked.connect(lambda _, e=emote_name: self.chat_thread.vtube_use_emote(e))
            head_layout.addWidget(test_emote_button)
            e_layout.addLayout(head_layout)

            for param in list(params.keys()):
                random_value = str(params[param]).startswith("rndm")
                if random_value:
                    param_widget = createEmoteSlot(emote_name, param, random_value, value_1=params[param].strip("rndm ()").split(", ")[0],
                                                   value_2=params[param].strip("rndm ()").split(", ")[1])
                else:
                    param_widget = createEmoteSlot(emote_name, param, random_value, params[param])
                e_layout.addWidget(param_widget)
            add_button = PushButton(self.tr("Add parameter"))
            add_button.clicked.connect(lambda _, b=add_button, l=e_layout, e=emote_name: createParameter(b, l, e))
            e_layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignHCenter)
            scroll_layout.addWidget(e_widget)

        widget = QWidget()
        widget.setFixedSize(750, 750)
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)

        buttons_frame = QWidget(widget)
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        buttons_frame.setLayout(buttons_layout)

        save_button = PushButton(self.tr("Save"))
        save_button.clicked.connect(save)
        buttons_layout.addWidget(save_button)

        close_button = PushButton(self.tr("Close"))
        close_button.clicked.connect(self.mw.hideOverlay)
        buttons_layout.addWidget(close_button)

        layout.addWidget(scroll_page)
        layout.addWidget(buttons_frame)
        self.mw.showOverlay(widget)

    def _vtubeCheck(self, text):
        self.mw.showNotification(text)
        self.chat_thread.vtube_connect_signal.disconnect()

    def vtubeCheck(self):
        self.chat_thread.vtube_connect_signal.connect(self._vtubeCheck)
        self.chat_thread.check_vtube_connect()

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(0)
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def createMainContentPage(self):
        scroll_area = VerticalScrollPage()
        scroll_area.setFixedWidth(800)

        settings_viewport = scroll_area.viewport
        settings_layout = scroll_area.layout
        scroll_area.setWidget(settings_viewport)

        for setting_group in self.settings_data:
            group_layout = QVBoxLayout()
            group_beta = setting_group.get('beta', False)
            group_label = QLabel(format_text(setting_group["label"]))
            if group_beta:
                group_label.setText(f'{format_text(setting_group["label"])} {self.tr("(Beta)")}')
            font = group_label.font()
            font.setBold(True)
            font.setPointSize(14)
            group_label.setFont(font)
            group_layout.addWidget(group_label, alignment=Qt.AlignmentFlag.AlignHCenter)

            for setting in setting_group["settings"]:
                layout = QHBoxLayout()
                if setting.get("label"):
                    label = QLabel()
                    label.setText(format_text(setting["label"]))
                    label.setWordWrap(True)
                    layout.addWidget(label, 1)

                key = setting["key"]

                if setting.get('type'):
                    if setting["type"] == "lineedit":
                        widget = LineEdit()
                        if setting.get("validator"):
                            widget.setValidator(setting["validator"])
                        widget.setObjectName(key)
                        widget.setEchoMode(setting.get("echo", LineEdit.EchoMode.Normal))
                    elif setting["type"] == "checkbox":
                        widget = CheckBox()
                        widget.setObjectName(key)
                    elif setting["type"] == "pushbutton":
                        widget = PushButton(setting["buttonlabel"])
                        widget.setObjectName(key)
                        widget.clicked.connect(setting["click"])
                    elif setting["type"] == "combobox":
                        widget = ComboBox()
                        widget.setObjectName(key)
                        widget.addItems(setting['items'])
                    elif setting["type"] == "keybind":
                        widget = KeySequenceEdit()
                        widget.setObjectName(key)
                        widget.keySequenceChanged.connect(lambda seq, edit=widget: edit.setKeySequence(QKeySequence(seq[0])) if seq.count() > 1 else None)

                    layout.addWidget(widget)

                if group_beta:
                    if self.mw.beta:
                        group_layout.addLayout(layout)
                        self.setting_widgets[setting["key"]] = widget
                        self.setting_data[setting["key"]] = setting
                else:
                    group_layout.addLayout(layout)
                    self.setting_widgets[setting["key"]] = widget
                    self.setting_data[setting["key"]] = setting

            if group_beta:
                if self.mw.beta:
                    settings_layout.addLayout(group_layout)
                    settings_layout.addWidget(QFrame())
            else:
                settings_layout.addLayout(group_layout)
                settings_layout.addWidget(QFrame())

        return scroll_area, settings_viewport, settings_layout

    def createButtonBar(self):
        button_bar = QWidget()
        button_layout = QHBoxLayout()
        button_bar.setLayout(button_layout)
        self.save_button = PushButton(self.tr("Save"))
        self.save_button.clicked.connect(self.saveSettings)
        self.cancel_button = PushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.loadSettings)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        return button_bar, button_layout

    def createTopBar(self):
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def getCookies(self):
        self.cookie_available = False
        self.token_available = False
        def cl():
            self.mw.hideOverlay()
            cookies.close()
            self.loadSettings()
            self.mw.showNotification(self.tr("The token is being updated..."))

            self.chat_thread.chat_histories = {}
            self.chat_thread.me = None
            for i in range(self.mw.recommended_layout.count()):
                item = self.mw.recommended_layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()
            if self.mw.featured_chats:
                for i in range(self.mw.for_you_layout.count()):
                    item = self.mw.for_you_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()
            if self.mw.recent_chats:
                for i in range(self.mw.recent_chat_scroll_layout.count()):
                    item = self.mw.recent_chat_scroll_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()

            self.chat_thread.token = self.mw.token
            self.chat_thread.cookie = self.mw.cookie
            self.chat_thread.create_connect()

            self.chat_thread.get_recent_chats()
            self.chat_thread.get_main_page_chats()
            self.chat_thread.get_me()
        def get(auth_token, expiration_date: QDateTime):
            self.cookie_available = True
            self.mw.settings.setValue("cai_auth/cookie", auth_token)
            self.mw.settings.setValue("cai_auth/expiration_date", expiration_date.toString("yyyy.MM.dd HH:mm"))
            if self.token_available: cl(self)
        def token_get(token):
            self.token_available = True
            self.mw.settings.setValue("cai_auth/token", token)
            self.mw.token = token
            if self.cookie_available: cl()
        cookies = CookieCards.MainCard()
        self.mw.showOverlay(cookies)
        cookies.auth_cookie_signal.connect(lambda token, date: get(token, date))
        cookies.authorization_signal.connect(lambda token: token_get(token))
        cookies.notification_signal.connect(self.mw.showNotification)

    def back(self):
        self.mw.main_content_area.setCurrentWidget(self.mw.main_page)
        self.mw.left_sidebar.setEnabled(True)

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)
        self.loadSettings()
        if self.mw.drpc_enable and self.mw.drpc_show_current_page: self.discord_thread.update(details=self.tr("Looking at the settings..."))

    def loadSettings(self):
        for key, widget in self.setting_widgets.items():
            value = self.mw.settings.value(key, str(self.setting_data[key].get('def_value')))
            if isinstance(widget, LineEdit):
                widget.setText(value if value is not None else "")
            elif isinstance(widget, CheckBox):
                value = self.mw.settings.value(key, self.setting_data[key].get('def_value'), type=bool)
                widget.setChecked(value)
            elif isinstance(widget, ComboBox):
                if key == "emilia_language":
                    widget.setCurrentText(self.languages.get(self.mw.current_language, {}).get("title", self.tr("English")))
                elif key == "update_server":
                    if not self.ud_added:
                        for server in self.mw.update_servers:
                            widget.addItem(server['name'])
                        self.ud_added = True
                    widget.setCurrentText(self.update_servers.get(value, self.tr("Germany")))
                elif key in {"tr_char_msg_to", "tr_user_msg_to"}:
                    widget.setCurrentText(self.languages.get(value, {}).get("title", self.tr("English")))
                elif key in {"input_device", "output_device"}:
                    if key == "input_device":
                        text = self.mw.input_devices.get(value)
                    elif key == "output_device":
                        text = self.mw.output_devices.get(value)
                    widget.setCurrentText(text)
                else:
                    widget.setCurrentText(value)
            elif isinstance(widget, KeySequenceEdit):
                widget.setKeySequence(QKeySequence(value))
        logging.debug(f"main.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Settings are loaded")

    def saveSettings(self):
        app = QApplication.instance()
        translator = QTranslator()
        for key, widget in self.setting_widgets.items():
            if isinstance(widget, LineEdit):
                if not self.setting_data.get(key).get('may_be_empty', True) and not widget.text():
                    self.mw.showNotification(self.setting_data[key]['label'] + self.tr(" cannot be empty"))
                    return
                self.mw.settings.setValue(key, widget.text())
                if key == "vtube/port":
                    self.chat_thread.eec.set_port(int(widget.text()))
                if key == "vtube/address":
                    self.chat_thread.eec.set_host(str(widget.text()))
            elif isinstance(widget, CheckBox):
                self.mw.settings.setValue(key, 'true' if widget.isChecked() else 'false')
                if key == "discord_rpc/enable":
                    self.mw.drpc_enable = widget.isChecked()
                    if self.mw.drpc_enable:
                        self.discord_thread.connect()
                    else:
                        self.discord_thread.clear()
                        self.discord_thread.close()
                if key == "discord_rpc/show_chat_name":
                    self.mw.drpc_show_chat_name = widget.isChecked()
                if key == "discord_rpc/show_username":
                    self.mw.drpc_show_username = widget.isChecked()
                if key == "discord_rpc/show_current_page":
                    self.mw.drpc_show_current_page = widget.isChecked()
                if self.mw.drpc_enable:
                    if self.mw.drpc_show_current_page:
                        self.discord_thread.update(state=self.tr("Looking at the settings..."))
                    else:
                        self.discord_thread.update()
            elif isinstance(widget, ComboBox):
                if key == "emilia_language":
                    lang = next((k for k, v in self.languages.items() if v["title"] == widget.currentText() and v.get("lang_available", False)), None)
                    if lang != self.mw.current_language:
                        self.mw.settings.setValue(key, lang)
                        self.mw.current_language = lang
                        translator.load(f"lang/{lang}.qm")
                        app.removeTranslator(translator)
                        if lang != "en_US":
                            app.installTranslator(translator)
                        self.mw.close()
                        main_window = MainPage.MainPage()
                        main_window.show()
                elif key == "update_server":
                    url = next((k for k, v in self.update_servers.items() if v == widget.currentText()), "https://germany.emiupd.ateez.ru/")
                    self.mw.settings.setValue(key, url)
                elif key in {"tr_char_msg_to", "tr_user_msg_to"}:
                    lang = next(k for k, v in self.languages.items() if v["title"] == widget.currentText())
                    self.mw.settings.setValue(key, lang)
                elif key in {"input_device", "output_device"}:
                    if key == "input_device": index = next(k for k, v in self.mw.input_devices.items() if v == widget.currentText())
                    elif key == "output_device":
                        index = next(k for k, v in self.mw.output_devices.items() if v == widget.currentText())
                        self.mw.setOutputDevice(index)
                    self.mw.settings.setValue(key, index)
                elif key == "app_theme":
                    theme = widget.currentText()
                    TM.set_theme(theme)
                    if platform.system() == 'Windows':
                        from modules.logic.WinDarkTheme import ChangeDWMAttrib, detect
                        if TM.get_theme(theme).get('titlebar', 'dark') == 'dark':
                            ChangeDWMAttrib(detect(self), 19, ctypes.c_int(1))
                            ChangeDWMAttrib(detect(self), 20, ctypes.c_int(1))
                        elif TM.get_theme(theme).get('titlebar', 'dark') == 'light':
                            ChangeDWMAttrib(detect(self), 19, ctypes.c_int(0))
                            ChangeDWMAttrib(detect(self), 20, ctypes.c_int(0))
                    self.mw.theme = theme
                    self.mw.settings.setValue(key, theme)
            elif isinstance(widget, KeySequenceEdit):
                self.mw.settings.setValue(key, widget.keySequence().toString())
        self.mw.showNotification(self.tr("Settings saved successfully"))
        logging.debug(f"main.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Settings saved successfully")