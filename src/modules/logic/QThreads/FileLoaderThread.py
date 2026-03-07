import logging, inspect, requests
from PyQt6.QtCore import QThread, pyqtSignal

class FileLoaderThread(QThread):
    file = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, url, headers={}, save_path=""):
        super().__init__()
        self.url = url
        self.headers = headers
        self.save_path = save_path

    def run(self):
        if self.save_path:
            try:
                response = requests.get(self.url, headers=self.headers, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                with open(self.save_path, 'wb') as file:
                    for chunk in response.iter_content(4096):
                        if chunk:
                            file.write(chunk)
                            downloaded_size += len(chunk)
                            percent = int((downloaded_size / total_size) * 100)
                            self.progress.emit(percent)

                self.finished.emit(self.save_path)
            except Exception as e:
                self.finished.emit(str(e))
        else:
            try:
                response = requests.get(self.url, headers=self.headers)
                if response.status_code == 200:
                    self.file.emit(response.content)
                else:
                    logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): File download error: {response.status_code}")
            except Exception as e:
                logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): File download error: {e}")
