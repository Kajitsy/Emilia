import math
import os
import time

import cv2
from PIL import Image
from PyQt6.QtCore import (
    QRect,
    Qt,
    QThread,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QImage,
    QMovie,
    QPainter,
    QPixmap,
)
from PyQt6.QtWidgets import QWidget


class VideoBackgroundThread(QThread):
    """
    Dedicated worker thread for hardware/OpenCV video frame decoding.
    Handles looped playback, FPS throttling, resolution downscaling, and clean termination.
    """

    frame_ready = pyqtSignal(QImage)

    def __init__(self, media_path: str, fps=30, quality="original", parent=None):
        super().__init__(parent)
        self.media_path = media_path
        self.target_fps = fps
        self.quality = quality
        self._running = True
        self._paused = False

    def run(self):
        if not self.media_path or not os.path.exists(self.media_path):
            return

        cap = cv2.VideoCapture(self.media_path)
        if not cap.isOpened():
            return

        try:
            native_fps = cap.get(cv2.CAP_PROP_FPS)
            if (
                not native_fps
                or math.isnan(native_fps)
                or native_fps <= 0
                or native_fps > 240
            ):
                native_fps = 30.0

            target_fps = native_fps
            if str(self.target_fps).isdigit() and int(self.target_fps) > 0:
                target_fps = float(self.target_fps)
            elif self.target_fps == "auto":
                target_fps = min(30.0, native_fps)

            frame_interval = 1.0 / max(1.0, min(60.0, target_fps))

            while self._running:
                if self._paused:
                    self.msleep(30)
                    continue

                t_start = time.time()
                ret, frame = cap.read()
                if not ret:
                    if not self._running:
                        break
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        break

                if not self._running:
                    break

                h, w, _ = frame.shape
                target_h = h
                if self.quality == "360p" and h > 360:
                    target_h = 360
                elif self.quality == "480p" and h > 480:
                    target_h = 480
                elif self.quality == "720p" and h > 720:
                    target_h = 720
                elif h > 1080:
                    target_h = 1080

                if target_h != h:
                    scale = target_h / float(h)
                    target_w = int(w * scale)
                    frame = cv2.resize(
                        frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR
                    )
                    h, w, _ = frame.shape

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytes_per_line = 3 * w
                q_img = QImage(
                    rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
                ).copy()

                if not self._running:
                    break

                self.frame_ready.emit(q_img)

                elapsed = time.time() - t_start
                sleep_time = frame_interval - elapsed
                if sleep_time > 0 and self._running:
                    sleep_ms = int(sleep_time * 1000)
                    while sleep_ms > 0 and self._running and not self._paused:
                        chunk = min(sleep_ms, 10)
                        self.msleep(chunk)
                        sleep_ms -= chunk
        finally:
            cap.release()

    def stop(self):
        """Signals the thread to stop and waits synchronously for completion."""
        self._running = False
        self._paused = False
        if self.isRunning():
            self.wait()

    def pause(self):
        """Pauses frame emission without stopping the thread."""
        self._paused = True

    def resume(self):
        """Resumes frame emission."""
        self._paused = False


class AnimatedBackgroundWidget(QWidget):
    """
    Reusable background widget supporting static images, animated GIFs, and video files.
    Features:
      - Formats: Images (.png, .jpg, .jpeg, .webp, .bmp), GIF (.gif), Videos (.mp4, .webm, .mov, .mkv, .avi)
      - Scaling modes: cover, contain, stretch, center
      - FPS and quality control
      - Auto pause/resume on hide/show
      - Mouse event passthrough
    """

    def __init__(self, parent=None, mouse_transparent=True):
        super().__init__(parent)
        if mouse_transparent:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.media_path = ""
        self.scale_mode = "cover"
        self.fps = "auto"
        self.quality = "original"

        self.video_thread = None
        self.movie = None
        self.pixmap = None
        self.current_img = None
        self.is_video = False
        self.is_gif = False

    def _on_frame_ready(self, img: QImage):
        if not self.isVisible() or img.isNull():
            return
        self.current_img = img
        self.update()

    def set_media(self, path: str, scale_mode="cover", fps="auto", quality="original"):
        """
        Sets and starts playback/rendering of the specified media file.
        """
        self.scale_mode = scale_mode or "cover"
        self.fps = fps or "auto"
        self.quality = quality or "original"

        if not path or not os.path.exists(path):
            self.clear()
            return

        self.media_path = path
        ext = os.path.splitext(path)[1].lower()
        video_exts = {".mp4", ".webm", ".mov", ".mkv", ".avi"}

        if self.video_thread is not None:
            self.video_thread.stop()
            self.video_thread = None

        if self.movie is not None:
            self.movie.stop()
            self.movie = None

        if ext in video_exts:
            self.is_video = True
            self.is_gif = False
            self.pixmap = None
            self.current_img = None

            self.video_thread = VideoBackgroundThread(
                self.media_path, self.fps, self.quality
            )
            self.video_thread.frame_ready.connect(self._on_frame_ready)
            if self.isVisible():
                self.video_thread.start()
            self.update()
        elif ext == ".gif":
            self.is_video = False
            self.is_gif = True
            self.current_img = None
            self.pixmap = None
            self.movie = QMovie(self.media_path)
            if str(self.fps).isdigit() and int(self.fps) > 0:
                ratio = int((float(self.fps) / 30.0) * 100)
                self.movie.setSpeed(max(10, ratio))
            self.movie.frameChanged.connect(lambda _: self.update())
            if self.isVisible():
                self.movie.start()
            self.update()
        else:
            self.is_video = False
            self.is_gif = False
            self.current_img = None
            self.pixmap = QPixmap(self.media_path)
            self.update()

    def pause(self):
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.pause()
        if self.movie and self.movie.state() == QMovie.MovieState.Running:
            self.movie.setPaused(True)

    def resume(self):
        if self.video_thread:
            if not self.video_thread.isRunning():
                self.video_thread.start()
            else:
                self.video_thread.resume()
        if self.movie and self.movie.state() == QMovie.MovieState.Paused:
            self.movie.setPaused(False)

    def hideEvent(self, event):
        self.pause()
        super().hideEvent(event)

    def showEvent(self, event):
        self.resume()
        super().showEvent(event)

    def clear(self):
        """Stops all threads, animations, and clears media."""
        if self.video_thread is not None:
            self.video_thread.stop()
            self.video_thread = None
        if self.movie is not None:
            self.movie.stop()
            self.movie = None
        self.media_path = ""
        self.pixmap = None
        self.current_img = None
        self.is_video = False
        self.is_gif = False
        self.update()

    def closeEvent(self, event):
        self.clear()
        super().closeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        img_w, img_h = 0, 0
        img_to_draw = None
        is_qimage = False

        if self.is_video and self.current_img and not self.current_img.isNull():
            img_to_draw = self.current_img
            img_w = img_to_draw.width()
            img_h = img_to_draw.height()
            is_qimage = True
        elif self.is_gif and self.movie:
            img_to_draw = self.movie.currentPixmap()
            if img_to_draw and not img_to_draw.isNull():
                img_w = img_to_draw.width()
                img_h = img_to_draw.height()
                is_qimage = False
        elif self.pixmap and not self.pixmap.isNull():
            img_to_draw = self.pixmap
            img_w = img_to_draw.width()
            img_h = img_to_draw.height()
            is_qimage = False

        if not img_to_draw or img_w <= 0 or img_h <= 0:
            return

        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        if self.scale_mode == "cover":
            w_ratio = rect.width() / img_w
            h_ratio = rect.height() / img_h
            scale = max(w_ratio, h_ratio)
            tw = int(img_w * scale)
            th = int(img_h * scale)
            tx = (rect.width() - tw) // 2
            ty = (rect.height() - th) // 2
            target_rect = QRect(tx, ty, tw, th)
        elif self.scale_mode == "contain":
            w_ratio = rect.width() / img_w
            h_ratio = rect.height() / img_h
            scale = min(w_ratio, h_ratio)
            tw = int(img_w * scale)
            th = int(img_h * scale)
            tx = (rect.width() - tw) // 2
            ty = (rect.height() - th) // 2
            target_rect = QRect(tx, ty, tw, th)
        elif self.scale_mode == "stretch":
            target_rect = rect
        elif self.scale_mode == "center":
            tx = (rect.width() - img_w) // 2
            ty = (rect.height() - img_h) // 2
            target_rect = QRect(tx, ty, img_w, img_h)
        else:
            target_rect = rect

        if is_qimage:
            painter.drawImage(target_rect, img_to_draw)
        else:
            painter.drawPixmap(target_rect, img_to_draw)


# Aliases for backward compatibility and flexibility
MediaBackgroundWidget = AnimatedBackgroundWidget
ChatBackgroundWidget = AnimatedBackgroundWidget


def extract_media_palette(media_path: str):
    """
    Extracts a balanced color theme palette from an image, gif, or video file.
    Returns a dict with char_back, char_text, user_back, user_text or None.
    """
    try:
        ext = os.path.splitext(media_path)[1].lower()
        if ext in {".mp4", ".webm", ".mov", ".mkv", ".avi"}:
            cap = cv2.VideoCapture(media_path)
            if not cap.isOpened():
                return None
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return None
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
        else:
            img = Image.open(media_path)

        img = img.convert("RGB").resize((150, 150))
        result = img.quantize(colors=6)
        palette = result.getpalette()

        colors = []
        for i in range(0, 18, 3):
            rgb = (palette[i], palette[i + 1], palette[i + 2])
            colors.append(rgb)

        def rgb_to_hex(rgb):
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        def get_brightness(rgb):
            return (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000

        char_rgb = colors[0]
        user_rgb = colors[1] if len(colors) > 1 else colors[0]

        for c in colors[1:]:
            dist = math.sqrt(sum([(a - b) ** 2 for a, b in zip(char_rgb, c)]))
            if dist > 30:
                user_rgb = c
                break

        char_b = get_brightness(char_rgb)
        user_b = get_brightness(user_rgb)

        char_text = "#ffffff" if char_b < 130 else "#111111"
        user_text = "#ffffff" if user_b < 130 else "#111111"

        return {
            "char_back": rgb_to_hex(char_rgb),
            "char_text": char_text,
            "user_back": rgb_to_hex(user_rgb),
            "user_text": user_text,
        }
    except Exception as e:
        print(f"Error extracting colors: {e}")
        return None
