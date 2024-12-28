import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QFileDialog
)
from modules.vmodel import Win

class VTubeModelViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTube Model Viewer")
        self.setGeometry(100, 100, 600, 500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()

        self.select_folder_button = QPushButton("Select folder")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.main_layout.addWidget(self.select_folder_button)

        self.model_list_widget = QListWidget()
        self.model_list_widget.itemClicked.connect(self.show_model_path)
        self.main_layout.addWidget(self.model_list_widget)

        self.continue_button = QPushButton("Continue")
        self.continue_button.clicked.connect(self.continuee)
        self.main_layout.addWidget(self.continue_button)

        self.central_widget.setLayout(self.main_layout)

        self.selected_folder = None
        self.models_data = {}
        self.current_model_path = None

    def select_folder(self):
        folder_path = QFileDialog.getOpenFileName(self, "Select folder")
        if folder_path:
            self.selected_folder = folder_path
            self.update_model_list()
            self.current_model_path = None

    def update_model_list(self):
        self.model_list_widget.clear()
        self.models_data.clear()
        if self.selected_folder:
            for root, _, files in os.walk(self.selected_folder):
                vtube_file_path = None
                for file in files:
                    if file.endswith(".vtube.json"):
                        vtube_file_path = os.path.join(root, file)
                        break

                if vtube_file_path:
                    try:
                        with open(vtube_file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            model_name = data.get("Name", "No Name")
                            model_filename = data["FileReferences"].get("Model")

                            if model_filename and model_filename.endswith(".model3.json"):
                                model3_path = os.path.join(root, model_filename)
                                self.model_list_widget.addItem(model_name)
                                self.models_data[model_name] = model3_path

                    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                        print(f"Error {vtube_file_path}: {e}")

    def show_model_path(self):
        selected_item = self.model_list_widget.currentItem()
        if selected_item:
            model_name = selected_item.text()
            if model_name in self.models_data:
                self.current_model_path = self.models_data[model_name]
            else:
                self.current_model_path = None
        else:
            self.current_model_path = None

    def continuee(self):
        if self.current_model_path:
            vmodel = Win()
            vmodel.model_path = self.current_model_path
            vmodel.show()
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = VTubeModelViewer()
    viewer.show()
    sys.exit(app.exec())