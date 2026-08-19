import hashlib
import json
import os
import platform
import sys

from curl_cffi import requests
from PyQt6.QtCore import QThread, pyqtSignal


def get_app_base_path() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def get_file_hash(filepath: str) -> str | None:
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError):
        return None


class UpdaterThread(QThread):
    has_update_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)

    def __init__(self, remote_url="https://nl-emiupd.kajitsy.xyz/"):
        super().__init__()
        self.base_remote_url = ""
        self.remote_url = ""
        self.set_remote_url(remote_url)

        self.local_manifest = {"files": {}}
        self.remote_manifest = {"files": {}}
        self.files_to_download = []
        self.files_to_removed = []

    def set_remote_url(self, remote_url: str):
        self.base_remote_url = remote_url.rstrip("/") + "/"
        system = platform.system()
        if system == "Windows":
            self.remote_url = self.base_remote_url + "windows/"
        elif system == "Linux":
            self.remote_url = self.base_remote_url + "linux/"
        else:
            self.remote_url = self.base_remote_url

    def run(self):
        if not self.get_remote_manifest():
            return
        self.generate_local_manifest()
        self.diff()

    def generate_local_manifest(self):
        base_path = get_app_base_path()
        manifest_path = os.path.join(base_path, "manifest.json")

        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "files" in data and isinstance(data["files"], dict):
                        self.local_manifest = data
                        return
            except Exception:
                pass

        self.local_manifest = {"files": {}}
        ignored_names = {
            "manifest.json",
            "update_installer.bat",
            "emilia_update_installer.bat",
            ".git",
            ".idea",
            ".venv",
            "__pycache__",
        }
        ignored_extensions = {".log", ".tmp", ".bak"}

        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in ignored_names]
            for filename in files:
                if filename in ignored_names or any(filename.endswith(ext) for ext in ignored_extensions):
                    continue

                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")

                file_hash = get_file_hash(full_path)
                if file_hash:
                    self.local_manifest["files"][rel_path] = file_hash

        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.local_manifest, f, indent=4)
        except Exception:
            pass

    def get_remote_manifest(self) -> bool:
        urls_to_try = [f"{self.remote_url}manifest.json"]
        if self.remote_url != self.base_remote_url:
            urls_to_try.append(f"{self.base_remote_url}manifest.json")

        for url in urls_to_try:
            try:
                response = requests.get(url, impersonate="chrome120", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "files" in data and isinstance(data["files"], dict):
                        self.remote_manifest = data
                        if url == f"{self.base_remote_url}manifest.json":
                            self.remote_url = self.base_remote_url
                        return True
            except Exception:
                continue

        self.error_signal.emit(self.tr("Failed to fetch remote update manifest."))
        return False

    def diff(self):
        self.files_to_download.clear()
        self.files_to_removed.clear()

        remote_files = self.remote_manifest.get("files", {})
        local_files = self.local_manifest.get("files", {})

        if not remote_files:
            self.has_update_signal.emit(False)
            return

        for file_path, remote_hash in remote_files.items():
            local_hash = local_files.get(file_path)
            if local_hash != remote_hash:
                self.files_to_download.append(file_path)

        for local_path in local_files:
            if local_path not in remote_files:
                self.files_to_removed.append(local_path)

        if self.files_to_download or self.files_to_removed:
            self.has_update_signal.emit(True)
        else:
            self.has_update_signal.emit(False)
