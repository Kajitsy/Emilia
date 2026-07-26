import os, hashlib, json, requests
import sys

from PyQt6.QtCore import QThread, pyqtSignal

class UpdaterThread(QThread):
    has_update_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)

    def __init__(self, remote_url="https://ru-emiupd.kajitsy.xyz/"):
        super().__init__()
        self.remote_url = remote_url
        self.local_manifest = {"files": {}}
        self.remote_manifest = {"files": {}}
        self.files_to_download = []
        self.files_to_removed = []

    def run(self):
        self.get_remote_manifest()
        self.generate_local_manifest()
        self.diff()

    def generate_local_manifest(self):
        if not os.path.exists('./manifest.json'):
            base_path = os.path.dirname(sys.executable)
            INCLUDE_FILES = [
                "emilia.exe",
                "icon.ico",
            ]

            INCLUDE_DIRS = [
                "_internal",
                "lang",
                "themes/Light",
                "themes/Dark",
                "data/default_qss"
            ]

            def get_hash(filepath):
                hasher = hashlib.sha256()
                try:
                    with open(filepath, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                    return hasher.hexdigest()
                except FileNotFoundError:
                    return None


            for filename in INCLUDE_FILES:
                full_path = os.path.join(base_path, filename)
                if os.path.exists(full_path):
                    file_hash = get_hash(full_path)
                    if file_hash:
                        self.local_manifest["files"][filename] = file_hash

            for directory in INCLUDE_DIRS:
                dir_full_path = os.path.join(base_path, directory)
                if not os.path.exists(dir_full_path):
                    continue

                for root, _, files in os.walk(dir_full_path):
                    for filename in files:
                        full_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")

                        file_hash = get_hash(full_path)
                        if file_hash:
                            self.local_manifest["files"][rel_path] = file_hash

            with open("manifest.json", "w", encoding="utf-8") as f:
                json.dump(self.local_manifest, f, indent=4)
        else:
            with open("manifest.json", "r", encoding="utf-8") as f:
                self.local_manifest = json.load(f)

    def get_remote_manifest(self):
        try:
            response = requests.get(f"{self.remote_url}manifest.json", timeout=5)
            response.raise_for_status()
            self.remote_manifest = response.json()
        except Exception as e:
            self.error_signal.emit(str(e))
            return

    def diff(self):
        for file_path, remote_hash in self.remote_manifest["files"].items():
            local_hash = self.local_manifest["files"].get(file_path)
            if local_hash != remote_hash:
                self.files_to_download.append(file_path)

        for local_path in self.local_manifest["files"]:
            if local_path not in self.remote_manifest["files"]:
                self.files_to_removed.append(local_path)

        if self.files_to_download or self.files_to_removed:
            self.has_update_signal.emit(True)
        else:
            self.has_update_signal.emit(False)
