import time, math
import random

import OpenGL.GL as gl
from PyQt6.QtCore import QTimerEvent, Qt, QRectF, QPropertyAnimation, pyqtProperty, QObject, pyqtSignal, QLocale
from PyQt6.QtGui import QMouseEvent, QCursor, QFont, QPainter, QColor, QWheelEvent, QGuiApplication, QTextDocument
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget

import live2d.v3 as live2d
from live2d.v3 import StandardParams
from live2d.utils import log
from live2d.utils.lipsync import WavHandler

from modules.config import getconfig
from modules.ets import translations



class Win(QOpenGLWidget):
    class AnimatedParameter(QObject):
        value_changed = pyqtSignal(float)

        def __init__(self, initial_value=0.0):
            super().__init__()
            self._value = initial_value

        @pyqtProperty(float, notify=value_changed)
        def value(self):
            return self._value

        @value.setter
        def value(self, new_value):
            self._value = new_value
            self.value_changed.emit(new_value)

    class SpeedSegmentAnimation(QPropertyAnimation):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def updateCurrentTime(self, currentTime):
            duration = self.duration()
            if duration == 0:
                return

            normalizedTime = currentTime / duration
            if normalizedTime < 0.75:
                super().updateCurrentTime(int(normalizedTime / 0.75 * duration))
            else:
                remainingTimeRatio = (normalizedTime - 0.75) / 0.25
                adjustedTime = 0.75 * duration + remainingTimeRatio * 0.25 * duration
                super().updateCurrentTime(int(adjustedTime))

    def __init__(self) -> None:
        super().__init__()
        self.fps = 60
        self.always_on_top = False
        self.auto_blink_enabled = True
        self.cursor_tracking_enabled = True
        self.window_move_threshold = 1
        self.model_window_move_threshold = 1
        self.translucent = True
        self.systemScale = QGuiApplication.primaryScreen().devicePixelRatio()

        self.emote_data = {}
        self.talking = False
        self.model_path = "E:/SteamLibrary/steamapps/common/VTube Studio/VTube Studio_Data/StreamingAssets/Live2DModels/PinkHair_workshop_2802653785/yiyi_chair.model3.json"

        self.is_dragging_model = False
        self.is_dragging_text = False

        self.setGeometry(500,500,500,500)
        if self.translucent: self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, self.translucent)

        self.model: live2d.LAppModel | None = None
        self.model_x = 0
        self.model_y = 0
        self.model_scale = 1

        self.text_in_model_center = ""
        self.text_rect = QRectF()
        self.text_x = self.width() / 2
        self.text_y = self.height() / 2
        self.text_scale = 1.0

        self.wavhandler = WavHandler()
        self.lipSyncN = 2.5
        self.audioPlayed = False

        self._animated_parameters = {}
        self.animations = {}

        self.is_blinking = False
        self.blink_start_time = 0.0
        self.blink_duration = 0.2
        self.blink_interval = 3.0 + random.random() * 2.0
        self.last_blink_time = time.time()

        self.on = trls.tr('VModel', 'on')
        self.off = trls.tr('VModel', 'off')

        self.control_panel = QWidget()
        self.blink_button = QPushButton(f"{trls.tr('VModel', 'blink_button')}: {self.on}")
        self.blink_button.clicked.connect(self.toggle_blinking)
        self.cursor_button = QPushButton(f"{trls.tr('VModel', 'cursor_button')}: {self.on}")
        self.cursor_button.clicked.connect(self.toggle_cursor_tracking)
        self.top_button = QPushButton(f"{trls.tr('VModel', 'top_button')}: {self.off}")
        self.top_button.clicked.connect(self.toggle_always_on_top)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.blink_button)
        controls_layout.addWidget(self.cursor_button)
        controls_layout.addWidget(self.top_button)
        self.control_panel.setLayout(controls_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self)
        main_layout.addWidget(self.control_panel)
        self.control_panel.setVisible(not self.translucent)
        self.setLayout(main_layout)

    def set_window_stay_on_top(self, stay_on_top):
        flags = self.windowFlags()
        if stay_on_top:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.update_top_button_text()
        self.set_window_stay_on_top(self.always_on_top)

    def update_top_button_text(self):
        self.top_button.setText(f"{trls.tr('VModel', 'top_button')}: {self.on if self.always_on_top else self.off}")

    def toggle_blinking(self):
        self.auto_blink_enabled = not self.auto_blink_enabled
        self.blink_button.setText(f"{trls.tr('VModel', 'blink_button')}: {self.on if self.auto_blink_enabled else self.off}")

    def toggle_cursor_tracking(self):
        self.cursor_tracking_enabled = not self.cursor_tracking_enabled
        self.cursor_button.setText(f"{trls.tr('VModel', 'cursor_button')}: {self.on if self.cursor_tracking_enabled else self.off}")

    def _get_parameter_value_from_model(self, parameter_id):
        if self.model:
            for i in range(self.model.GetParameterCount()):
                param = self.model.GetParameter(i)
                if param.id == parameter_id:
                    return param.value
        return 0.0

    def animate_parameter(self, parameter_id, target_value, duration=200):
        if parameter_id not in self._animated_parameters:
            initial_value = self._get_parameter_value_from_model(parameter_id)
            self._animated_parameters[parameter_id] = self.AnimatedParameter(initial_value)

        if parameter_id not in self.animations:
            self.animations[parameter_id] = self.SpeedSegmentAnimation(self._animated_parameters[parameter_id], b"value")

        animation = self.animations[parameter_id]
        animation.stop()
        animation.setDuration(duration)
        animation.setStartValue(self._animated_parameters[parameter_id].value)
        animation.setEndValue(target_value)
        animation.start()
        log.Debug('start animation', parameter_id, 'to', target_value)

    def initializeGL(self):
        live2d.init()
        live2d.glewInit()

        self.model = live2d.LAppModel()
        self.model.LoadModelJson(self.model_path)

        self.model.SetAutoBreathEnable(False)
        self.model.SetAutoBlinkEnable(False)

        self.startTimer(1000 // self.fps)

    def resizeGL(self, width, height):
        if self.model:
            self.model.Resize(width, height)

    def paintGL(self):
        live2d.clearBuffer(0.0, 0.0, 0.0, 0.0)
        if self.model:
            self.model.SetOffset(self.model_x, self.model_y)
            self.model.Update()

            current_time = time.time()
            if self.auto_blink_enabled:
                if not self.is_blinking and current_time - self.last_blink_time >= self.blink_interval:
                    self.is_blinking = True
                    self.blink_start_time = current_time

                if self.is_blinking:
                    blink_progress = (current_time - self.blink_start_time) / self.blink_duration
                    if blink_progress >= 1.0:
                        self.is_blinking = False
                        self.last_blink_time = current_time
                        self.blink_interval = 3.0 + random.random() * 2.0
                        eye_open_value = 1.0
                    else:
                        if blink_progress < 0.5:
                            eye_open_value = 1.0 - blink_progress / 0.5
                        else:
                            eye_open_value = (blink_progress - 0.5) / 0.5

                    self.model.SetParameterValue("ParamEyeLOpen", eye_open_value, 1)
                    self.model.SetParameterValue("ParamEyeROpen", eye_open_value, 1)
                else:
                    self.model.SetParameterValue("ParamEyeLOpen", 1, 1)
                    self.model.SetParameterValue("ParamEyeROpen", 1, 1)

            breath_speed = 0.2
            breath_progress = (current_time * breath_speed) % 1
            breath_value = (math.sin(breath_progress * math.pi * 2) + 1) / 2
            self.model.SetParameterValue("ParamBreath", breath_value, 1)

            if self.cursor_tracking_enabled:
                mouse_x, mouse_y = QCursor.pos().x() - self.x(), QCursor.pos().y() - self.y()
                widget_width, widget_height = self.width(), self.height() / 3

                eye_center_x = widget_width * (self.model_x + 1) / 2
                eye_center_y = widget_height * (1 - self.model_y) / 2

                # Положение курсора относительно "центра глаз"
                relative_mouse_x = mouse_x - eye_center_x
                relative_mouse_y = mouse_y - eye_center_y

                look_x = max(-1.0, min(relative_mouse_x / (widget_width / 2), 1.0))
                look_y = max(-1.0, min(-relative_mouse_y / (widget_height / 2), 1.0))

                body_angle_x = max(-10.0, min(relative_mouse_x / (widget_width / 2), 10.0))
                body_angle_y = max(-10.0, min(-relative_mouse_y / (widget_height / 2), 10.0))

                face_angle_x = max(-30.0, min(relative_mouse_x / (widget_width / 2), 30.0))
                face_angle_y = max(-30.0, min(-relative_mouse_y / (widget_height / 2), 30.0))

                if not self.talking:
                    self.model.SetParameterValue("ParamEyeBallX", look_x, 1)
                    self.model.SetParameterValue("ParamEyeBallY", look_y, 1)

                self.model.SetParameterValue("ParamBodyAngleX", body_angle_x, 1)
                self.model.SetParameterValue("ParamBodyAngleZ", body_angle_y, 1)

                self.model.SetParameterValue("ParamAngleX", face_angle_x, 1)
                self.model.SetParameterValue("ParamAngleY", face_angle_y, 1)
                self.model.SetParameterValue("ParamAngleZ", face_angle_x, 1)

            for param_id, animated_param in self._animated_parameters.items():
                self.model.SetParameterValue(param_id, animated_param.value, 1)

            if self.wavhandler.Update():
                self.model.AddParameterValue(
                    StandardParams.ParamMouthOpenY, self.wavhandler.GetRms() * self.lipSyncN
                )

            self.model.Draw()
        self.draw_movable_text(self.text_x, self.text_y)

    def draw_movable_text(self, x, y):
        painter = QPainter(self)
        font = QFont("Arial", 16)
        font.setPointSizeF(font.pointSizeF() * self.text_scale)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))

        parts = self.text_in_model_center.split('*')
        formatted_text_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                formatted_text_parts.append(f"<b>{part}</b>")
            else:
                formatted_text_parts.append(part)
        formatted_text = "".join(formatted_text_parts)

        parts = formatted_text.split('_')
        formatted_text_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                formatted_text_parts.append(f"<i>{part}</i>")
            else:
                formatted_text_parts.append(part)
        formatted_text = "".join(formatted_text_parts)

        formatted_text = formatted_text.replace("\n", "<br>")

        document = QTextDocument()
        document.setDefaultFont(font)
        document.setHtml(formatted_text)

        available_width = 200  # Задайте желаемую ширину для переноса
        document.setTextWidth(available_width)

        text_rect = document.size()
        adjusted_x = x - text_rect.width() / 2
        adjusted_y = y + text_rect.height() / 2

        painter.translate(adjusted_x, adjusted_y - text_rect.height())
        document.drawContents(painter)
        painter.translate(-adjusted_x, -(adjusted_y - text_rect.height()))

        self.text_rect = QRectF(adjusted_x, adjusted_y - text_rect.height(), text_rect.width(), text_rect.height())

    def timerEvent(self, a0: QTimerEvent | None) -> None:
        if not self.isVisible():
            return

        self.update()

    def isInL2DArea(self, click_x, click_y):
        h = self.height()
        if 0 <= click_x < self.width() and 0 <= click_y < self.height():
            alpha = gl.glReadPixels(int(click_x * self.systemScale), int((h - click_y) * self.systemScale), 1, 1, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)[3]
            return alpha > 0
        return False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.text_rect.contains(event.position()):
                self.is_dragging_text = True
                self.drag_start_pos_text = event.position()
                return

            if self.isInL2DArea(event.pos().x(), event.pos().y()):
                self.is_dragging_model = True
                self.drag_start_pos = event.scenePosition()
                self.drag_start_model_x = self.model_x
                self.drag_start_model_y = self.model_y
                return

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging_model = False
            self.is_dragging_text = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_dragging_text:
            delta = event.position() - self.drag_start_pos_text
            self.text_x += delta.x()
            self.text_y += delta.y()
            self.drag_start_pos_text = event.position()
            self.update()

            threshold = self.window_move_threshold
            text_center_x = self.text_x
            text_center_y = self.text_y
            move_step = 15

            window_x = self.x()
            window_y = self.y()

            if text_center_x < threshold:
                window_x -= move_step
            elif text_center_x > self.width() - threshold:
                window_x += move_step

            if text_center_y < threshold:
                window_y -= move_step
            elif text_center_y > self.height() - threshold:
                window_y += move_step

            if window_x != self.x() or window_y != self.y():
                self.move(window_x, window_y)

            return

        if self.is_dragging_model:
            x, y = event.scenePosition().x(), event.scenePosition().y()
            delta_x = x - self.drag_start_pos.x()
            delta_y = y - self.drag_start_pos.y()

            self.model_x = self.drag_start_model_x + (delta_x / self.width()) * 2
            self.model_y = self.drag_start_model_y - (delta_y / self.height()) * 2

            threshold = self.model_window_move_threshold
            model_center_x = self.width() * (self.model_x + 1) / 2
            model_center_y = self.height() * (1 - self.model_y) / 2
            move_step = 15

            window_x = self.x()
            window_y = self.y()

            if model_center_x < threshold:
                window_x -= move_step
            elif model_center_x > self.width() - threshold:
                window_x += move_step

            if model_center_y < threshold:
                window_y -= move_step
            elif model_center_y > self.height() - threshold:
                window_y += move_step

            if window_x != self.x() or window_y != self.y():
                self.move(window_x, window_y)
            self.update()

    def wheelEvent(self, event: QWheelEvent):
        if self.text_rect.contains(event.position()):
            angle_delta = event.angleDelta().y()
            scale_factor = 1.1 if angle_delta > 0 else 0.9
            self.text_scale *= scale_factor
            self.text_scale = max(0.5, min(self.text_scale, 5.0))
            self.update()
            return

        angle_delta = event.angleDelta().y()
        scale_factor = 1.05 if angle_delta > 0 else 0.95
        self.model_scale *= scale_factor
        self.model_scale = max(0.5, min(self.model_scale, 5.0))
        self.model.SetScale(self.model_scale)
        self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            current_geom = self.geometry()
            center_point = current_geom.center()

            if self.translucent:
                self.setWindowFlags(Qt.WindowType.Window | (
                    Qt.WindowType.WindowStaysOnTopHint if self.always_on_top else Qt.WindowType.Widget))
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            else:
                self.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint if self.always_on_top else Qt.WindowType.FramelessWindowHint)
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.translucent = not self.translucent
            self.close()
            self.show()

            new_geom = self.geometry()
            new_geom.moveCenter(center_point)
            self.setGeometry(new_geom)

            self.control_panel.setVisible(not self.translucent)

            live2d.clearBuffer(0.0, 0.0, 0.0, 0.0)

    def set_text_model_center(self, text):
        self.text_in_model_center = text

    def use_emote(self, emote_name):
        if self.emote_data.get(emote_name, {}):
            for param in self.emote_data[emote_name]:
                value = self.emote_data[emote_name][param]
                self.animate_parameter(param, value)
        else:
            log.Error('emote', emote_name, 'not found')

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    win = Win()
    win.show()

    app.exec()
else:
    trls = translations(getconfig("language", QLocale.system().name()))