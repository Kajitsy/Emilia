import os
import json
import sys
import webbrowser
from characterai import sendCode, authUser
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QMenu
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
pre = "True"
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
        self.setWindowTitle("Emilia: Getting a Token")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        global link_label, gettoken_button, link_entry, email_label, email_entry, getlink_button
        email_label = QLabel(tr("GetToken", "youremail"))
        self.layout.addWidget(email_label)
        email_entry = QLineEdit()
        self.layout.addWidget(email_entry)
        email_entry.setPlaceholderText("example@example.com")

        getlink_button = QPushButton(tr("GetToken", "sendemail"))
        getlink_button.clicked.connect(lambda: self.getlink(email_entry.text()))
        self.layout.addWidget(getlink_button)

        link_label = QLabel(tr("GetToken", "linkfromemail"))
        self.layout.addWidget(link_label)
        link_entry = QLineEdit()
        self.layout.addWidget(link_entry)
        link_entry.setPlaceholderText("https...")

        gettoken_button = QPushButton(tr("GetToken", "gettoken"))
        gettoken_button.clicked.connect(lambda: self.gettoken(email_entry.text(), link_entry.text()))
        self.layout.addWidget(gettoken_button)
        link_label.setVisible(False)
        link_entry.setVisible(False)
        gettoken_button.setVisible(False)

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
        if guitheme == 'windowsvista':
            spacer = menubar.addMenu(tr("MainWindow", "spacerwingemini"))
        else:
            spacer = menubar.addMenu(tr("MainWindow", "spacerfusiongemini"))
        spacer.setEnabled(False)
        ver_menu = menubar.addMenu(tr("MainWindow", 'version') + version)
        ver_menu.setEnabled(False)

        issues = QAction(QIcon(githubicon), tr("MainWindow", 'BUUUG'), self)
        issues.triggered.connect(self.issuesopen)
        emi_menu.addAction(issues)
        
        aboutemi = QAction(QIcon(emiliaicon), tr("MainWindow", 'aboutemi'), self)
        aboutemi.triggered.connect(self.about)
        emi_menu.addAction(aboutemi)

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

    def setconfig(self, token):
        try:
            with open('charaiconfig.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}

        data.update({"client": token})

        with open('charaiconfig.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def getlink(self, email):
        sendCode(email)
        link_label.setVisible(True)
        link_entry.setVisible(True)
        gettoken_button.setVisible(True)
        
    def gettoken(self, email, link):
        token = authUser(link, email)
        link_label.setVisible(False)
        link_entry.setVisible(False)
        gettoken_button.setVisible(False)
        email_entry.setVisible(False)
        getlink_button.setVisible(False)
        email_label.setText(tr("GetToken", "yourtoken") + token + tr("GetToken", "saveincharaiconfig"))
        self.setconfig(token)

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