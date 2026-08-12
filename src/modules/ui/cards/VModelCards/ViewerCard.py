import json
import logging
import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QFileDialog, QVBoxLayout, QWidget

from modules.ui.cards.VModelCards import ListCard, MainCard
from modules.ui.Elements import PushButton, VerticalScrollPage


class ViewerCard(QWidget):
    vmodel_widget = pyqtSignal(QOpenGLWidget)

    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.setGeometry(100, 100, 600, 500)
        self.default_vtube_folder = self.mw.settings.value(
            "vmodel/default_folder", "./vtubes"
        )

        self.main_layout = QVBoxLayout()

        self.select_folder_button = PushButton(self.tr("Select folder"))
        self.select_folder_button.clicked.connect(self.select_folder)
        self.main_layout.addWidget(self.select_folder_button)

        self.model_list_widget = VerticalScrollPage()
        self.model_list_layout = self.model_list_widget.layout
        self.main_layout.addWidget(self.model_list_widget)

        self.setLayout(self.main_layout)

        self.selected_folder = None

        if os.path.exists(self.default_vtube_folder):
            for root, _, files in os.walk(self.default_vtube_folder):
                for file in files:
                    if file.endswith(".vtube.json"):
                        vtube_file_path = os.path.join(root, file)
                        try:
                            with open(vtube_file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                model_name = data.get("Name", "Unnamed Model")
                                file_refs = data.get("FileReferences", {})
                                model_filename = file_refs.get("Model")
                                avatar_file_path = ""
                                idle_path = ""
                                if data.get("FileReferences", {}).get("Icon"):
                                    avatar_file_path = os.path.join(
                                        root, data.get("FileReferences", {}).get("Icon")
                                    )

                                if data.get("FileReferences", {}).get("Icon"):
                                    idle_path = os.path.join(
                                        root,
                                        f'animations/{data.get("FileReferences", {}).get("IdleAnimation")}',
                                    )

                                if model_filename and model_filename.endswith(
                                    ".model3.json"
                                ):
                                    model3_path = os.path.normpath(
                                        os.path.join(root, model_filename)
                                    )

                                    if os.path.exists(model3_path):
                                        widget = ListCard(
                                            self.mw, avatar_file_path, model_name
                                        )
                                        widget.mousePressEvent = lambda _, path=model3_path, idle=idle_path: self.continuee(
                                            path, idle
                                        )
                                        self.model_list_layout.addWidget(widget)

                        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                            logging.error(f"Error {vtube_file_path}: {e}")

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.tr("Select folder"))
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
                            with open(vtube_file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                model_name = data.get("Name", "Unnamed Model")
                                file_refs = data.get("FileReferences", {})
                                model_filename = file_refs.get("Model")
                                avatar_file_path = ""
                                idle_path = ""
                                if data.get("FileReferences", {}).get("Icon"):
                                    avatar_file_path = os.path.join(
                                        root, data.get("FileReferences", {}).get("Icon")
                                    )

                                if data.get("FileReferences", {}).get("IdleAnimation"):
                                    idle_path = os.path.join(
                                        root,
                                        f'animations/{data.get("FileReferences", {}).get("IdleAnimation")}',
                                    )

                                if model_filename and model_filename.endswith(
                                    ".model3.json"
                                ):
                                    model3_path = os.path.normpath(
                                        os.path.join(root, model_filename)
                                    )

                                    if os.path.exists(model3_path):
                                        widget = ListCard(
                                            self.mw, avatar_file_path, model_name
                                        )
                                        widget.mousePressEvent = lambda _, path=model3_path, idle=idle_path: self.continuee(
                                            path, idle
                                        )
                                        self.model_list_layout.addWidget(widget)

                        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                            logging.error(f"Error {vtube_file_path}: {e}")

    def continuee(self, path, idle):
        vmodel = MainCard()
        vmodel.fps = self.mw.settings.value("vmodel/fps", 60, type=int)
        vmodel.volume_smoothing = self.mw.settings.value(
            "vmodel/volume_smoothing", 0.6, type=float
        )
        vmodel.auto_blink = self.mw.settings.value("vmodel/auto_blink", True, type=bool)
        vmodel.cursor_tracking = self.mw.settings.value(
            "vmodel/cursor_tracking", True, type=bool
        )
        vmodel.model_path = path
        vmodel.idle_animation_path = idle
        self.vmodel_widget.emit(vmodel)
        self.close()
