import os
import json
import sys
import webbrowser
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtGui import QIcon, QAction, QPixmap
from PyQt6.QtCore import QLocale

locale = QLocale.system().name()
def load_translations(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Translation file not found: {filename}")
        return {}

def tr(context, text):
    if context in translations and text in translations[context]:
        return translations[context][text]
    else:
        return text 

translations = load_translations(f"locales/{locale}.json")

ver = "2.1.1"
build = "242204"
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
else:
    guitheme = 'windowsvista'

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
        global name_label, name_entry, id_label, id_entry

        name_label = QLabel(tr("CharEditor", "Character Name:"))
        self.layout.addWidget(name_label)
        name_entry = QLineEdit()
        name_entry.setPlaceholderText("Emilia...")
        self.layout.addWidget(name_entry)

        id_label = QLabel(tr("MainWindow", "Character ID:"))
        self.layout.addWidget(id_label)
        id_entry = QLineEdit()
        id_entry.setPlaceholderText("ID...")
        self.layout.addWidget(id_entry)

        addchar_button = QPushButton(tr("CharEditor", "Add a character"))
        addchar_button.clicked.connect(lambda: self.addchar(name_entry.text(), id_entry.text()))
        self.layout.addWidget(addchar_button)

        delchar_button = QPushButton(tr("CharEditor", "Delete a character"))
        delchar_button.clicked.connect(lambda: self.delchar(name_entry.text()))
        self.layout.addWidget(delchar_button)

        self.central_widget.setLayout(self.layout)
        menubar = self.menuBar()
        emi_menu = menubar.addMenu('&Emilia')
        if guitheme == 'windowsvista':
            spacer = menubar.addMenu('                                            ')
        else:
            spacer = menubar.addMenu('                                              ')
        spacer.setEnabled(False)
        ver_menu = menubar.addMenu(tr("MainWindow", '&Version: ') + version)
        ver_menu.setEnabled(False)

        issues = QAction(QIcon(githubicon), tr("MainWindow", '&Report a bug'), self)
        issues.triggered.connect(self.issuesopen)
        emi_menu.addAction(issues)
        
        aboutemi = QAction(QIcon(emiliaicon), tr("MainWindow", '&About Emilia'), self)
        aboutemi.triggered.connect(self.about)
        emi_menu.addAction(aboutemi)

    def addchar(self, name, char):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({name: {"char": char}})
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
                msg.setWindowTitle(tr("CharEditor", "ERROR ") + build)
            else:   
                msg.setWindowTitle(tr("CharEditor", "ERROR "))
            msg.setWindowIcon(QIcon(emiliaicon))
            pixmap = QPixmap(emiliaicon).scaled(64, 64)
            msg.setIconPixmap(pixmap)
            text = tr("CharEditor", "Your character is not in the code")
            msg.setText(text)
            msg.exec()
            self.central_widget.setLayout(self.layout)

    def issuesopen(self):
        webbrowser.open("https://github.com/Kajitsy/Emilia/issues")
    
    def about(self):
        msg = QMessageBox()
        if pre == "True":
            msg.setWindowTitle(tr("About", "About Emilia ") + build)
        else:
            msg.setWindowTitle(tr("About", "About Emilia "))
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        language = tr("About", "<br><br>English from <a href='https://github.com/Kajitsy'>@Kajitsy</a>, from the author, yeah yeah)")
        whatsnew = tr("About", "<br><br>New in ") + version + tr("About", ": <br>• Other improvements and bug fixes...")
        otherversions = tr("About", "<br><br><a href='https://github.com/Kajitsy/Emilia/releases'>To view all previous releases, click here</a>")
        text = tr("About", "Emilia is an open source project that is a graphical interface for <a href='https://github.com/jofizcd/Soul-of-Waifu'>Soul of Waifu</a>.<br> At the moment you are using the ") + version + tr("About", " version, and it is completely free of charge for <a href='https://github.com/Kajitsy/Emilia'>GitHub</a>") + language + whatsnew + otherversions
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