from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineNewWindowRequest
from PyQt6.QtCore import QUrl, QDateTime, pyqtSignal, Qt
from PyQt6.QtNetwork import QNetworkCookie

from modules.ui.Elements import PushButton, LineEdit
from modules.ui.Icons import Svg
from modules.logic import RequestInterceptor

class MainCard(QWidget):
    auth_cookie_signal = pyqtSignal(str, QDateTime)
    authorization_signal = pyqtSignal(str)
    notification_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.browser = QWebEngineView()
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0")
        self.interceptor = RequestInterceptor()
        self.svg_icons = Svg()

        self.browser.page().newWindowRequested.connect(self.on_new_window_requested)

        self.interceptor.authorization_signal.connect(self.on_authorization_received)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self.profile.cookieStore().cookieAdded.connect(self.on_cookie_added)
        self.browser.load(QUrl("https://character.ai"))

        self.link_label = QLabel(self.tr("You can also insert a link from the email"))

        link_layout = QHBoxLayout()
        self.link_edit = LineEdit()
        self.link_edit.keyPress = lambda: self.open_link()
        self.link_button = PushButton()
        self.link_button.setIcon(self.svg_icons.send())
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