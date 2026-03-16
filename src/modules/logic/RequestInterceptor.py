import logging

from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt6.QtCore import pyqtSignal

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
