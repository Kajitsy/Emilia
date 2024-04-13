import os
import json
import sys
import webbrowser
from characterai import sendCode, authUser
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap

ver = "2.1"
build = "241304.1"
pre = "True"
if pre == "True":
    version = "pre" + ver
else:
    version = ver
devmode = "false"

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
        self.setWindowTitle("Emilia: Getting a Token")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        global link_label, gettoken_button, link_entry, email_label, email_entry, getlink_button
        email_label = QLabel("Ваша электронная почта:")
        self.layout.addWidget(email_label)
        email_entry = QLineEdit()
        self.layout.addWidget(email_entry)
        email_entry.setPlaceholderText("example@example.com")

        getlink_button = QPushButton("Отправить письмо с ссылкой")
        getlink_button.clicked.connect(lambda: self.getlink(email_entry.text()))
        self.layout.addWidget(getlink_button)

        link_label = QLabel("Ссылка с почты:")
        self.layout.addWidget(link_label)
        link_entry = QLineEdit()
        self.layout.addWidget(link_entry)
        link_entry.setPlaceholderText("https...")

        gettoken_button = QPushButton("Получить токен")
        gettoken_button.clicked.connect(lambda: self.gettoken(email_entry.text(), link_entry.text()))
        self.layout.addWidget(gettoken_button)
        link_label.setVisible(False)
        link_entry.setVisible(False)
        gettoken_button.setVisible(False)

        self.central_widget.setLayout(self.layout)
        menubar = self.menuBar()
        emi_menu = menubar.addMenu('&Emilia')
        spacer = menubar.addMenu('                                               ')
        spacer.setEnabled(False)
        ver_menu = menubar.addMenu('&Версия: ' + version)
        ver_menu.setEnabled(False)

        issues = QAction(QIcon(githubicon), '&Сообщить об ошибке', self)
        issues.triggered.connect(self.issuesopen)
        emi_menu.addAction(issues)
        
        aboutemi = QAction(QIcon(emiliaicon), '&Об Emilia', self)
        aboutemi.triggered.connect(self.about)
        emi_menu.addAction(aboutemi)

    def setconfig(self, token):
        if devmode == "true":
            print("Запись истории чата")
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
        email_label.setText("Ваш токен: \n" + token + "\nЕсли что он уже сохранён в charaiconfig.json")
        self.setconfig(token)

    def issuesopen(self):
        webbrowser.open("https://github.com/Kajitsy/Emilia/issues")

    def about(self):
        msg = QMessageBox()
        if pre == "True":
            msg.setWindowTitle("Об Emilia " + build)
        else:
            msg.setWindowTitle("Об Emilia")
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        whatsnew = "Что нового в " + version + ": <br>• Проект на GitHub переименован с Soul-Of-Waifu-Work на Emilia <br>• Добавлена возможность общения с Google Gemini 1.5 Pro<br>• Добавлена тёмная тема<br>• Добавлена возможность получения токена без необходимости искать его в DevTools"
        otherversions = "<br><br><a href='https://github.com/Kajitsy/Emilia/releases'>Чтобы посмотреть все прошлые релизы кликай сюда</a>"
        text = "Emilia - проект с открытым исходным кодом, являющийся графическим интерфейсом для <a href='https://github.com/jofizcd/Soul-of-Waifu'>Soul of Waifu</a>.<br> На данный момент вы используете версию " + version + ", и она полностью бесплатно распространяется на <a href='https://github.com/Kajitsy/Emilia'>GitHub</a><br><br>" + whatsnew + otherversions
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