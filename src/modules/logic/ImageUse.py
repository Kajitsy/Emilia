import hashlib, os, requests

from PyQt6.QtCore import QThreadPool, QObject, Qt, QRectF, QRunnable, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath
from PyQt6.sip import isdeleted


class ImageSignals(QObject):
    finished = pyqtSignal(QImage)
    error = pyqtSignal(object)

class ImageTask(QRunnable):
    def __init__(self, url: str, w: int, h: int, radius: int, cache_dir: str):
        super().__init__()
        self.url = url
        self.w = w
        self.h = h
        self.radius = radius
        self.cache_dir = cache_dir
        self.signals = ImageSignals()
        self.setAutoDelete(True)

        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_path(self):
        name = hashlib.md5(self.url.encode()).hexdigest() + ".png"
        return os.path.join(self.cache_dir, name)

    def _round(self, img: QImage) -> QImage:
        out = QImage(self.w, self.h, QImage.Format.Format_ARGB32)
        out.fill(0)

        p = QPainter(out)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.w, self.h), self.radius, self.radius)
        p.setClipPath(path)

        scaled = img.scaled(
            self.w, self.h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        p.drawImage(
            (self.w - scaled.width()) // 2,
            (self.h - scaled.height()) // 2,
            scaled
        )
        p.end()
        return out

    def run(self):
        try:

            if os.path.exists(self.url) and os.path.isfile(self.url):
                img = QImage(self.url)
                if img.isNull():
                    raise RuntimeError(f"Не удалось прочитать локальный файл: {self.url}")
            else:
                cache_path = self._cache_path()

                if os.path.exists(cache_path):
                    img = QImage(cache_path)
                    if img.isNull():
                        os.remove(cache_path)
                        raise RuntimeError("Broken cache image")
                else:
                    r = requests.get(self.url, timeout=10)
                    r.raise_for_status()
                    img = QImage.fromData(r.content)
                    if img.isNull():
                        raise RuntimeError("Invalid image data")
                    img.save(cache_path, "PNG")

            result = self._round(img)
            self.signals.finished.emit(result)

        except Exception as e:
            self.signals.error.emit(e)

class ImageLoader(QObject):
    def __init__(self):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(12)

    def load(self, url, w, h, radius, callback=None, label=None, error_cb=None, cache_dir="cache/avatars"):
        """callback or label"""
        task = ImageTask(url, w, h, radius, cache_dir)
        if callback and not label:
            task.signals.finished.connect(lambda img: callback(QPixmap.fromImage(img)))
        elif not callback and label:
            def apply(img):
                if not isdeleted(label):
                    pixmap = QPixmap.fromImage(img)
                    label.setPixmap(pixmap)

            task.signals.finished.connect(apply)

        if error_cb:
            task.signals.error.connect(error_cb)

        self.pool.start(task)
