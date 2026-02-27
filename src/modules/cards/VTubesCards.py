import os, json, time, math, random

import OpenGL.GL as gl
from PyQt6.QtCore import QTimerEvent, Qt, QRectF, QPropertyAnimation, pyqtProperty, QObject, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QCursor, QFont, QPainter, QColor, QWheelEvent, QGuiApplication, QTextDocument, QSurfaceFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QLabel, QFileDialog

import live2d.v3 as live2d
from live2d.v3 import StandardParams
from live2d.utils import log
from live2d.utils.lipsync import WavHandler

from modules.style.Elements import PushButton, CardFrame, VerticalScrollPage
from modules.style.Utils import color_avatar

class ListCard(CardFrame):
    def __init__(self, main_window, icon_path, name):
        super().__init__()
        self.mw = main_window
        self.image_loader = self.mw.image_loader
        self.icon_path = icon_path
        self.name = name

        self.avatar_label_w = 70
        self.avatar_label_h = 70

        self.initUI()

    def initUI(self):
        card_layout = QHBoxLayout()
        self.setLayout(card_layout)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.avatar_label_w, self.avatar_label_h)
        card_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        if self.icon_path:
            self.image_loader.load(self.icon_path, self.avatar_label_w, self.avatar_label_h, 4,
                label=self.avatar_label,
                error_cb=lambda _: color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name))
        else:
            color_avatar(self.avatar_label, self.avatar_label_w, self.avatar_label_h, self.name, 4)

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(text_layout, 1)

        title_label = QLabel(self.name)
        title_label.setWordWrap(True)
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        title_label.setFont(font)
        text_layout.addWidget(title_label)

class VModelWidget(QOpenGLWidget):
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
        self.auto_blink_enabled = True
        self.cursor_tracking_enabled = True
        self.window_move_threshold = 1
        self.model_window_move_threshold = 1
        self.translucent = True
        self.systemScale = QGuiApplication.primaryScreen().devicePixelRatio()

        self.emote_data = {}
        self.talking = False
        self.model_path = ""

        self.is_dragging_model = False
        self.is_dragging_text = False

        self.setGeometry(500,500,500,500)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, self.translucent)

        format_gl = QSurfaceFormat()
        format_gl.setAlphaBufferSize(8)
        self.setFormat(format_gl)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)

        self.model: live2d.LAppModel | None = None
        self.model_x = 0
        self.model_y = 0
        self.model_scale = 1
        self.stream_volume = 0.0
        self.volume_smoothing = 0.6
        self.idle_animation = ""

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

        self.on = 'on'
        self.off = 'off'

        self.control_panel = QWidget()
        self.blink_button = PushButton(f"blink_button: {self.on}")
        self.blink_button.clicked.connect(self.toggle_blinking)
        self.cursor_button = PushButton(f"cursor_button: {self.on}")
        self.cursor_button.clicked.connect(self.toggle_cursor_tracking)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.blink_button)
        controls_layout.addWidget(self.cursor_button)
        self.control_panel.setLayout(controls_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.control_panel)
        self.control_panel.setVisible(not self.translucent)
        self.setLayout(main_layout)
        self.setMouseTracking(True)

    def set_stream_volume(self, volume: float):
        self.stream_volume = (self.stream_volume * self.volume_smoothing) + (volume * (1.0 - self.volume_smoothing))

    def set_window_stay_on_top(self, stay_on_top):
        flags = self.windowFlags()
        if stay_on_top:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def toggle_blinking(self):
        self.auto_blink_enabled = not self.auto_blink_enabled
        self.blink_button.setText(f"blink_button: {self.on if self.auto_blink_enabled else self.off}")

    def toggle_cursor_tracking(self):
        self.cursor_tracking_enabled = not self.cursor_tracking_enabled
        self.cursor_button.setText(f"cursor_button: {self.on if self.cursor_tracking_enabled else self.off}")

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
        live2d.glInit()

        self.model = live2d.LAppModel()
        self.model.LoadModelJson(self.model_path)
        #self.model.StartMotion("Idle", 0, MotionPriority.IDLE)
        self.model.SetRandomExpression()

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
                local_mouse_pos =  QCursor.pos()
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
                self.model.SetParameterValue(
                    StandardParams.ParamMouthOpenY, self.wavhandler.GetRms() * self.lipSyncN
                )

            if self.stream_volume > 0.005:
                self.model.SetParameterValue(
                    StandardParams.ParamMouthOpenY, self.stream_volume * self.lipSyncN
                )

            self.model.Draw()
        #self.draw_movable_text(self.text_x, self.text_y)

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

        available_width = 200
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
            return

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_dragging_text:
            delta = event.position() - self.drag_start_pos_text
            new_text_x = self.text_x + delta.x()
            new_text_y = self.text_y + delta.y()

            self.text_x = max(0.0, min(float(self.width()), new_text_x))
            self.text_y = max(0.0, min(float(self.height()), new_text_y))

            self.drag_start_pos_text = event.position()
            self.update()
            return

        if self.is_dragging_model:
            x, y = event.scenePosition().x(), event.scenePosition().y()
            delta_x = x - self.drag_start_pos.x()
            delta_y = y - self.drag_start_pos.y()

            aspect_ratio = self.width() / self.height() if self.height() != 0 else 1.0

            new_model_x = self.drag_start_model_x + (delta_x / self.width()) * 2.0 * aspect_ratio
            new_model_y = self.drag_start_model_y - (delta_y / self.height()) * 2

            self.model_x = new_model_x
            self.model_y = new_model_y

            self.update()
            return

    def wheelEvent(self, event: QWheelEvent):
        if self.text_rect.contains(event.position()):
            angle_delta = event.angleDelta().y()
            scale_factor = 1.1 if angle_delta > 0 else 0.9
            self.text_scale *= scale_factor
            self.text_scale = max(0.5, min(self.text_scale, 5.0))
            self.update()

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
                self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.translucent = not self.translucent

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

class VModelViewer(QWidget):
    vmodel_widget = pyqtSignal(QOpenGLWidget)
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.setWindowTitle("VTube Model Viewer")
        self.setGeometry(100, 100, 600, 500)
        self.default_vtube_folder = self.mw.settings.value("vmodel/default_folder", "./vtubes")

        self.main_layout = QVBoxLayout()

        self.select_folder_button = PushButton("Select folder")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.main_layout.addWidget(self.select_folder_button)

        self.model_list_widget = VerticalScrollPage()
        self.model_list_layout = self.model_list_widget.layout
        self.main_layout.addWidget(self.model_list_widget)

        self.continue_button = PushButton("Continue")
        self.continue_button.clicked.connect(self.continuee)
        self.main_layout.addWidget(self.continue_button)

        self.setLayout(self.main_layout)

        self.selected_folder = None

        if os.path.exists(self.default_vtube_folder):
            for root, _, files in os.walk(self.default_vtube_folder):
                for file in files:
                    if file.endswith(".vtube.json"):
                        vtube_file_path = os.path.join(root, file)
                        try:
                            with open(vtube_file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                model_name = data.get("Name", "Unnamed Model")
                                file_refs = data.get("FileReferences", {})
                                model_filename = file_refs.get("Model")
                                avatar_file_path = ""
                                if data.get("FileReferences", {}).get("Icon"):
                                    avatar_file_path = os.path.join(root, data.get("FileReferences", {}).get("Icon"))

                                if model_filename and model_filename.endswith(".model3.json"):
                                    model3_path = os.path.normpath(os.path.join(root, model_filename))

                                    if os.path.exists(model3_path):
                                        widget = ListCard(self.mw, avatar_file_path, model_name)
                                        widget.mousePressEvent = lambda _, path=model3_path: self.continuee(path)
                                        self.model_list_layout.addWidget(widget)

                        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                            print(f"Error {vtube_file_path}: {e}")

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder_path:
            self.selected_folder = folder_path
            self.update_model_list()

    def update_model_list(self):
        if os.path.exists(self.selected_folder):
            for root, _, files in os.walk(self.selected_folder):
                for file in files:
                    if file.endswith(".vtube.json"):
                        vtube_file_path = os.path.join(root, file)
                        try:
                            with open(vtube_file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                model_name = data.get("Name", "Unnamed Model")
                                file_refs = data.get("FileReferences", {})
                                model_filename = file_refs.get("Model")
                                avatar_file_path = ""
                                if data.get("FileReferences", {}).get("Icon"):
                                    avatar_file_path = os.path.join(root, data.get("FileReferences", {}).get("Icon"))

                                if model_filename and model_filename.endswith(".model3.json"):
                                    model3_path = os.path.normpath(os.path.join(root, model_filename))

                                    if os.path.exists(model3_path):
                                        widget = ListCard(self.mw, avatar_file_path, model_name)
                                        widget.mousePressEvent = lambda _, path=model3_path: self.continuee(path)
                                        self.model_list_layout.addWidget(widget)

                        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                            print(f"Error {vtube_file_path}: {e}")

    def continuee(self, path):
        vmodel = VModelWidget()
        vmodel.model_path = path
        self.vmodel_widget.emit(vmodel)
        self.close()