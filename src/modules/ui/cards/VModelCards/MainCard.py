import logging
import os
import time

import live2d.v3 as live2d
import OpenGL.GL as gl
from live2d.utils import log
from live2d.utils.lipsync import WavHandler
from live2d.v3 import MotionPriority, StandardParams
from PyQt6.QtCore import (
    QObject,
    QPropertyAnimation,
    Qt,
    QTimer,
    QTimerEvent,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QCursor,
    QGuiApplication,
    QMouseEvent,
    QSurfaceFormat,
    QWheelEvent,
)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget


class MainCard(QOpenGLWidget):
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
        self.auto_blink = True
        self.cursor_tracking = True
        self.window_move_threshold = 1
        self.model_window_move_threshold = 1
        self.translucent = True
        self.systemScale = QGuiApplication.primaryScreen().devicePixelRatio()

        self.emote_data = {}
        self.talking = False
        self.model_path = ""
        self.lastUpdateTime = time.time()

        self.is_dragging_model = False
        self.setGeometry(500, 500, 500, 500)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, self.translucent)

        format_gl = QSurfaceFormat()
        format_gl.setAlphaBufferSize(8)
        self.setFormat(format_gl)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)

        self.model = None
        self.model_x = 0
        self.model_y = 0
        self.model_scale = 1
        self.stream_volume = 0.0
        self.volume_smoothing = 0.6
        self.idle_animation_path = ""
        self.idle_motion_group = "custom_idle"
        self.idle_motion_no = -1

        self.wavhandler = WavHandler()
        self.lipSyncN = 2.5
        self.audioPlayed = False

        self._animated_parameters = {}
        self.animations = {}

        self.setMouseTracking(True)

    def set_stream_volume(self, volume: float):
        self.stream_volume = (self.stream_volume * self.volume_smoothing) + (
            volume * (1.0 - self.volume_smoothing)
        )

    def set_window_stay_on_top(self, stay_on_top):
        flags = self.windowFlags()
        if stay_on_top:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

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
            self._animated_parameters[parameter_id] = self.AnimatedParameter(
                initial_value
            )

        if parameter_id not in self.animations:
            self.animations[parameter_id] = self.SpeedSegmentAnimation(
                self._animated_parameters[parameter_id], b"value"
            )

        animation = self.animations[parameter_id]
        animation.stop()
        animation.setDuration(duration)
        animation.setStartValue(self._animated_parameters[parameter_id].value)
        animation.setEndValue(target_value)
        animation.start()
        log.Debug("start animation", parameter_id, "to", target_value)

    def load_idle_animation(self, motion_path: str):
        if not os.path.exists(motion_path):
            logging.error(f"Error: Animation file not found at path: {motion_path}")
            return

        self.idle_animation_path = motion_path

        if self.model:
            self.idle_motion_no = self.model.LoadExtraMotion(
                self.idle_motion_group, self.idle_animation_path
            )

            if self.idle_motion_no != -1:
                self._play_idle_motion()
            else:
                logging.error(
                    "Error: The file was found, but Live2D was unable to load it. The file may be corrupted."
                )

    def _play_idle_motion(self, z=0, v=0):
        if self.model and self.idle_motion_no != -1:
            self.model.StartMotion(
                self.idle_motion_group,
                self.idle_motion_no,
                MotionPriority.FORCE,
                None,
                self._on_motion_finished,
            )

    def _on_motion_finished(self, z=None, v=None):
        delay_ms = 3000
        QTimer.singleShot(delay_ms, self._play_idle_motion)

    def initializeGL(self):
        live2d.init()
        live2d.glInit()

        self.model = live2d.Model()
        self.model.LoadModelJson(self.model_path)

        self.model.CreateRenderer(2)

        self.model.SetAutoBreath(False)
        self.model.SetAutoBlink(False)

        if self.idle_animation_path:
            self.load_idle_animation(self.idle_animation_path)

        self.startTimer(1000 // self.fps)

    def resizeGL(self, width, height):
        if self.model:
            self.model.Resize(width, height)

    def paintGL(self):
        live2d.clearBuffer(0.0, 0.0, 0.0, 0.0)

        if not self.model:
            return

        ct = time.time()
        deltaSecs = max(0.0001, ct - self.lastUpdateTime)
        self.lastUpdateTime = ct

        self.model.SetOffset(self.model_x, self.model_y)

        self.model.LoadParameters()
        motionUpdated = False

        if not self.model.IsMotionFinished():
            motionUpdated = self.model.UpdateMotion(deltaSecs)

        if self.cursor_tracking:
            local_mouse_pos = QCursor.pos()
            mouse_x = local_mouse_pos.x()
            mouse_y = local_mouse_pos.y()

            center_x = self.width() / 2.0
            center_y = self.height() / 2.0

            model_pixel_x = center_x + (self.model_x * min(center_x, center_y))
            model_pixel_y = center_y - (self.model_y * center_y)

            eye_center_x = model_pixel_x
            eye_center_y = model_pixel_y - (self.height() * 0.15 * self.model_scale)

            relative_mouse_x = mouse_x - eye_center_x
            relative_mouse_y = mouse_y - eye_center_y

            look_x = max(-1.0, min(relative_mouse_x / (center_x / 2), 1.0))
            look_y = max(-1.0, min(-relative_mouse_y / (center_y / 2), 1.0))

            body_angle_x = max(-10.0, min(relative_mouse_x / (center_x / 2), 10.0))
            body_angle_y = max(-10.0, min(-relative_mouse_y / (center_y / 2), 10.0))

            face_angle_x = max(-30.0, min(relative_mouse_x / (center_x / 2), 30.0))
            face_angle_y = max(-30.0, min(-relative_mouse_y / (center_y / 2), 30.0))

            if not self.talking:
                self.model.SetParameterValueById(
                    StandardParams.ParamEyeBallX, look_x, 1
                )
                self.model.SetParameterValueById(
                    StandardParams.ParamEyeBallY, look_y, 1
                )

            self.model.SetParameterValueById(
                StandardParams.ParamBodyAngleX, body_angle_x, 1
            )
            self.model.SetParameterValueById(
                StandardParams.ParamBodyAngleZ, body_angle_y, 1
            )

            self.model.SetParameterValueById(
                StandardParams.ParamAngleX, face_angle_x, 1
            )
            self.model.SetParameterValueById(
                StandardParams.ParamAngleY, face_angle_y, 1
            )
            self.model.SetParameterValueById(
                StandardParams.ParamAngleZ, face_angle_x, 1
            )

        for param_id, animated_param in self._animated_parameters.items():
            self.model.SetParameterValueById(param_id, animated_param.value, 1)

        if self.wavhandler.Update():
            self.model.SetParameterValueById(
                StandardParams.ParamMouthOpenY, self.wavhandler.GetRms() * self.lipSyncN
            )

        if self.stream_volume > 0.005:
            self.model.SetParameterValueById(
                StandardParams.ParamMouthOpenY, self.stream_volume * self.lipSyncN
            )

        self.model.SaveParameters()

        if not motionUpdated:
            if self.auto_blink:
                self.model.UpdateBlink(deltaSecs)

        self.model.UpdateExpression(deltaSecs)
        self.model.UpdateDrag(deltaSecs)
        self.model.UpdateBreath(deltaSecs)
        self.model.UpdatePhysics(deltaSecs)
        self.model.UpdatePose(deltaSecs)

        self.model.Draw()

    def timerEvent(self, a0: QTimerEvent | None) -> None:
        if not self.isVisible():
            return

        self.update()

    def isInL2DArea(self, click_x, click_y):
        h = self.height()
        if 0 <= click_x < self.width() and 0 <= click_y < self.height():
            alpha = gl.glReadPixels(
                int(click_x * self.systemScale),
                int((h - click_y) * self.systemScale),
                1,
                1,
                gl.GL_RGBA,
                gl.GL_UNSIGNED_BYTE,
            )[3]
            return alpha > 0
        return False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isInL2DArea(event.pos().x(), event.pos().y()):
                self.is_dragging_model = True
                self.drag_start_pos = event.scenePosition()
                self.drag_start_model_x = self.model_x
                self.drag_start_model_y = self.model_y
                return

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging_model = False
            return

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_dragging_model:
            x, y = event.scenePosition().x(), event.scenePosition().y()
            delta_x = x - self.drag_start_pos.x()
            delta_y = y - self.drag_start_pos.y()

            aspect_ratio = self.width() / self.height() if self.height() != 0 else 1.0

            new_model_x = (
                self.drag_start_model_x + (delta_x / self.width()) * 2.0 * aspect_ratio
            )
            new_model_y = self.drag_start_model_y - (delta_y / self.height()) * 2

            self.model_x = new_model_x
            self.model_y = new_model_y

            self.update()
            return

    def wheelEvent(self, event: QWheelEvent):
        if self.isInL2DArea(event.position().x(), event.position().y()):
            angle_delta = event.angleDelta().y()
            scale_factor = 1.05 if angle_delta > 0 else 0.95
            self.model_scale *= scale_factor
            self.model_scale = max(0.5, min(self.model_scale, 5))
            self.model.SetScale(self.model_scale)
            self.update()
            return

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.translucent:
                self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            else:
                self.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents, False
                )
            self.translucent = not self.translucent
            live2d.clearBuffer(0.0, 0.0, 0.0, 0.0)
