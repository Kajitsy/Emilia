import os
import json
import sys
import webbrowser
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QPalette
from PyQt6.QtCore import QLocale

locale = QLocale.system().name()
def load_translations(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        with open("locales/en_US.json", "r", encoding="utf-8") as f:
            return json.load(f)

def tr(context, text):
    if context in translations and text in translations[context]:
        return translations[context][text]
    else:
        return text 

translations = load_translations(f"locales/{locale}.json")

ver = "2.1.1"
build = "242604"
pre = "False"
if pre == "True":
    version = "pre" + ver
else:
    version = ver

if os.path.exists('config.json'):
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        theme = config.get('theme', '')
        if theme == "dark":
            guitheme = 'Fusion'
        else:
            guitheme = 'windowsvista'
        backcolor = config.get('backgroundcolor', "")
        buttoncolor = config.get('buttoncolor', "")
        buttontextcolor = config.get('buttontextcolor', "")
        labelcolor = config.get('labelcolor', "")
else:
    guitheme = 'windowsvista'
    backcolor = ""
    buttoncolor = ""
    buttontextcolor = ""
    labelcolor = ""

#Иконки
if pre == "True":
    emiliaicon = './images/premilia.png'
else:
    emiliaicon = './images/emilia.png'

if guitheme == 'Fusion':
    githubicon = './images/github_white.png'
else:
    githubicon = './images/github.png'

class EmiliaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emilia: Character Editor")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        global name_label, name_entry, id_label, id_entry, voice_entry, voice_label

        name_label = QLabel(tr("CharEditor", "charname"))
        self.layout.addWidget(name_label)
        name_entry = QLineEdit()
        name_entry.setPlaceholderText("Emilia...")
        self.layout.addWidget(name_entry)

        id_label = QLabel(tr("MainWindow", "characterid"))
        self.layout.addWidget(id_label)
        id_entry = QLineEdit()
        id_entry.setPlaceholderText("ID...")
        self.layout.addWidget(id_entry)

        voice_label = QLabel(tr("MainWindow", "voice"))
        self.layout.addWidget(voice_label)
        voice_entry = QLineEdit()
        voice_entry.setPlaceholderText(tr("MainWindow", "voices"))
        self.layout.addWidget(voice_entry)

        addchar_button = QPushButton(tr("CharEditor", "addchar"))
        addchar_button.clicked.connect(lambda: self.addchar(name_entry.text(), id_entry.text(), voice_entry.text()))
        self.layout.addWidget(addchar_button)

        delchar_button = QPushButton(tr("CharEditor", "delchar"))
        delchar_button.clicked.connect(lambda: self.delchar(name_entry.text()))
        self.layout.addWidget(delchar_button)

        if backcolor != "":
            self.set_background_color(QColor(backcolor))
        if buttoncolor != "":
            self.set_button_color(QColor(buttoncolor))
        if labelcolor != "":
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor != "":
            self.set_button_text_color(QColor(buttontextcolor))

        self.central_widget.setLayout(self.layout)
        menubar = self.menuBar()
        emi_menu = menubar.addMenu('&Emilia')
        charselect = menubar.addMenu(tr("MainWindow", 'charchoice'))
        if os.path.exists('config.json'):
            def create_action(key, value):
                def action_func():
                    self.open_json(value['name'], value['char'], value['voice'])
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
        if guitheme == 'windowsvista':
            spacer = menubar.addMenu(tr("MainWindow", "spacerwincharai"))
        else:
            spacer = menubar.addMenu(tr("MainWindow", "spacerfusioncharai"))
        spacer.setEnabled(False)
        ver_menu = menubar.addMenu(tr("MainWindow", 'version') + version)
        ver_menu.setEnabled(False)

        issues = QAction(QIcon(githubicon), tr("MainWindow", 'BUUUG'), self)
        issues.triggered.connect(self.issuesopen)
        emi_menu.addAction(issues)
        
        aboutemi = QAction(QIcon(emiliaicon), tr("MainWindow", 'aboutemi'), self)
        aboutemi.triggered.connect(self.about)
        emi_menu.addAction(aboutemi)

    def open_json(self, value, value2, pup):
        name_entry.setText(value)
        id_entry.setText(value2)
        voice_entry.setText(pup)

    def set_background_color(self, color):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        self.setPalette(palette)

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
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def addchar(self, name, char, voice):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({name: {"name": name,"char": char, "voice": voice}})
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
    def delchar(self, name):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        if name in data:
            del data[name]
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            msg = QMessageBox()
            if pre == "True":
                msg.setWindowTitle(tr("CharEditor", "error") + build)
            else:   
                msg.setWindowTitle(tr("CharEditor", "error"))
            msg.setWindowIcon(QIcon(emiliaicon))
            text = tr("CharEditor", "notavchar")
            msg.setText(text)
            msg.exec()
            self.central_widget.setLayout(self.layout)

    def issuesopen(self):
        webbrowser.open("https://github.com/Kajitsy/Emilia/issues")
    
    def about(self):
        msg = QMessageBox()
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(guitheme)
    window = EmiliaGUI()
    window.setFixedWidth(300)
    window.setWindowIcon(QIcon(emiliaicon))
    window.show()
    sys.exit(app.exec())