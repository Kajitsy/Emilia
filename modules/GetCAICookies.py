import sys, logging
import webbrowser

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor, QWebEngineNewWindowRequest
from PyQt6.QtCore import QUrl, QDateTime, pyqtSignal, Qt
from PyQt6.QtNetwork import QNetworkCookie
from modules.styles import icon_button_style, SvgIcons, lineedit_style

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    authorization_signal = pyqtSignal(str)

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if url == "https://plus.character.ai/chat/user/settings/":
            headers = info.httpHeaders()
            for header, value in headers.items():
                if header.data().decode().lower() == "authorization":
                    token = value.data().decode().replace("Token ", "")
                    self.authorization_signal.emit(token)
                    break
        elif url[:34] == "https://character.ai/login/polling":
            logging.debug("Login Pooling...")

class GetCookies(QWidget):
    auth_cookie_signal = pyqtSignal(str, QDateTime)
    authorization_signal = pyqtSignal(str)
    notification_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.browser = QWebEngineView()
        self.profile = QWebEngineProfile.defaultProfile()
        self.interceptor = RequestInterceptor()
        self.svg_icons = SvgIcons()

        self.browser.page().newWindowRequested.connect(self.on_new_window_requested)

        self.interceptor.authorization_signal.connect(self.on_authorization_received)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self.profile.cookieStore().cookieAdded.connect(self.on_cookie_added)
        self.browser.load(QUrl("https://character.ai"))

        self.link_label = QLabel(self.tr("You can also insert a link from the email"))

        link_layout = QHBoxLayout()
        self.link_edit = QLineEdit()
        self.link_edit.setStyleSheet(lineedit_style())
        self.link_edit.keyPress = lambda: self.open_link()
        self.link_button = QPushButton()
        self.link_button.setIcon(self.svg_icons.send())
        self.link_button.setStyleSheet(icon_button_style())
        self.link_button.clicked.connect(self.open_link)
        link_layout.addWidget(self.link_edit)
        link_layout.addWidget(self.link_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(self.tr("Please log in to your account")),
                         alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(QLabel(self.tr("(To log in via Apple/Google, specify the email address of your Apple/Google account.)")),
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.browser)
        layout.addStretch()
        layout.addWidget(self.link_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(link_layout)
        self.setLayout(layout)

    def open_link(self):
        link = self.link_edit.text()
        if link:
            self.browser.load(QUrl(link))

    def on_cookie_added(self, cookie: QNetworkCookie):
        name = cookie.name().data().decode()
        if name == "web-next-auth":
            value = cookie.value().data().decode()
            expirationDate = cookie.expirationDate()
            expirationDate: QDateTime = expirationDate
            self.auth_cookie_signal.emit(value, expirationDate)

    def on_authorization_received(self, token: str):
        self.authorization_signal.emit(token)

    def on_new_window_requested(self, data: QWebEngineNewWindowRequest):
        self.notification_signal.emit(self.tr("(To log in via Apple/Google, specify the email address of your Apple/Google account.)"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setCentralWidget(GetCookies())
    window.show()
    sys.exit(app.exec())