import sys, logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor
from PyQt6.QtCore import QUrl, QDateTime, pyqtSignal, Qt
from PyQt6.QtNetwork import QNetworkCookie

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

    def __init__(self):
        super().__init__()
        self.browser = QWebEngineView()
        self.profile = QWebEngineProfile.defaultProfile()
        self.interceptor = RequestInterceptor()

        self.interceptor.authorization_signal.connect(self.on_authorization_received)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self.profile.cookieStore().cookieAdded.connect(self.on_cookie_added)
        self.browser.load(QUrl("https://character.ai"))

        layout = QVBoxLayout()
        layout.addWidget(QLabel(self.tr("Please log in to your account")),
                         alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.browser)
        self.setLayout(layout)

    def on_cookie_added(self, cookie: QNetworkCookie):
        name = cookie.name().data().decode()
        if name == "web-next-auth":
            value = cookie.value().data().decode()
            expirationDate = cookie.expirationDate()
            expirationDate: QDateTime = expirationDate
            self.auth_cookie_signal.emit(value, expirationDate)

    def on_authorization_received(self, token: str):
        self.authorization_signal.emit(token)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setCentralWidget(GetCookies())
    window.show()
    sys.exit(app.exec())