import os
import json

from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QFileDialog
from PyQt6.QtCore import pyqtSignal

from modules.vmodel.vmodel import VModelWidget
from modules.style.Elements import PushButton, VerticalScrollPage
from modules.cards.VTubesCards import ListCard


class VTubeModelViewer(QWidget):
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
        self.models_data = {}

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
        self.model_list_widget.clear()
        self.models_data.clear()
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