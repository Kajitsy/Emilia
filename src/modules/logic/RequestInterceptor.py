import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor


class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    authorization_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_token = None

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if "character.ai" in url:
            headers = info.httpHeaders()
            for header, value in headers.items():
                if header.data().decode().lower() == "authorization":
                    raw_val = value.data().decode()
                    token = raw_val.replace("Token ", "").replace("Bearer ", "").strip()
                    if token and token != self.last_token:
                        self.last_token = token
                        self.authorization_signal.emit(token)
                    break
        if "character.ai/login/polling" in url:
            logging.debug("Login Polling...")
