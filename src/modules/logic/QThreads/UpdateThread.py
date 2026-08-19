import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from curl_cffi import requests
from platformdirs import user_data_dir
from PyQt6.QtCore import QThread, pyqtSignal


class UpdateThread(QThread):
    finished_signal = pyqtSignal(bool)
    progress_signal = pyqtSignal(int, int)
    error_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__()
        # Support both (remote_url, files_to_download, files_to_removed)
        # and (main_window, remote_url, files_to_download, files_to_removed)
        if len(args) == 4:
            self.mw = args[0]
            self.remote_url = args[1]
            self.files_to_download = args[2]
            self.files_to_removed = args[3]
        elif len(args) >= 3:
            self.mw = None
            self.remote_url = args[0]
            self.files_to_download = args[1]
            self.files_to_removed = args[2]
        else:
            self.mw = kwargs.get("main_window", None)
            self.remote_url = kwargs.get("remote_url", "")
            self.files_to_download = kwargs.get("files_to_download", [])
            self.files_to_removed = kwargs.get("files_to_removed", [])

        self.total_files_count = len(self.files_to_download)
        self.downloaded_files_count = 0
        self.update_cache_dir = Path(user_data_dir("Emilia", False), "cache", "update")

    def run(self):
        if self.total_files_count == 0 and not self.files_to_removed:
            self.finished_signal.emit(True)
            return

        self.download_update()

    def download_manifest(self):
        try:
            r = requests.get(
                f"{self.remote_url}manifest.json",
                impersonate="chrome120",
                timeout=10,
            )
            if r.status_code == 200:
                manifest_path = os.path.join(self.update_cache_dir, "manifest.json")
                with open(manifest_path, "wb") as f:
                    f.write(r.content)
        except Exception:
            pass

    def download_update(self):
        if os.path.exists(self.update_cache_dir):
            shutil.rmtree(self.update_cache_dir, ignore_errors=True)
        os.makedirs(self.update_cache_dir, exist_ok=True)

        self.download_manifest()

        if self.total_files_count == 0:
            self.apply_update(self.update_cache_dir)
            return

        def download_worker(rel_path):
            url = self.remote_url + rel_path
            local_temp_path = os.path.join(self.update_cache_dir, rel_path)

            try:
                os.makedirs(os.path.dirname(local_temp_path), exist_ok=True)

                r = requests.get(
                    url,
                    impersonate="chrome120",
                    stream=True,
                    timeout=30,
                )
                if r.status_code == 200:
                    with open(local_temp_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                else:
                    self.error_signal.emit(f"HTTP error {r.status_code}: {rel_path}")
                    return False
            except Exception as e:  # noqa: BLE001
                self.error_signal.emit(f"Download error {e}: {rel_path}")
                return False

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(download_worker, f) for f in self.files_to_download
            ]

            for future in as_completed(futures):
                success = future.result()
                if success:
                    self.downloaded_files_count += 1
                    self.progress_signal.emit(
                        self.downloaded_files_count, self.total_files_count
                    )
                else:
                    self.error_signal.emit(
                        self.tr("File upload error. Check the internet.")
                    )
                    return

        if all(f.result() for f in futures):
            self.apply_update(self.update_cache_dir)
        else:
            self.error_signal.emit(
                self.tr("Some files could not be downloaded. Cancel the update.")
            )

    def apply_update(self, update_dir):
        app_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
        app_dir_win = str(Path(app_dir).resolve()).replace("/", "\\")
        update_dir_win = str(Path(update_dir).resolve()).replace("/", "\\")

        deletion_commands = ""
        protected_files = {"emilia.exe", "manifest.json", "icon.ico", ".", "..", ""}
        for file_path in self.files_to_removed:
            clean_rel_path = file_path.replace("/", "\\").strip("\\")
            if clean_rel_path.lower() in protected_files or ".." in clean_rel_path:
                continue
            deletion_commands += f'if exist "{clean_rel_path}" del /f /q "{clean_rel_path}"\n        '

        bat_script = f"""@echo off
        setlocal
        cd /d "{app_dir_win}"

        echo Waiting for process to terminate...
        timeout /t 3 /nobreak > NUL

        :CHECK_LOCK
        tasklist /FI "IMAGENAME eq emilia.exe" 2>NUL | find /I /N "emilia.exe">NUL
        if "%ERRORLEVEL%"=="0" (
            echo Application is still running, waiting...
            timeout /t 2 /nobreak > NUL
            goto CHECK_LOCK
        )

        echo Deleting obsolete files...
        {deletion_commands}

        echo Installing new files...
        xcopy "{update_dir_win}" "{app_dir_win}" /E /H /Y /Q /I

        echo Cleaning up...
        rmdir /s /q "{update_dir_win}"

        echo Starting application...
        start "" "{os.path.join(app_dir_win, 'emilia.exe')}"

        echo Update complete.
        (goto) 2>nul & del "%~f0"
        """

        script_dir = tempfile.gettempdir()
        script_name = os.path.join(script_dir, "emilia_update_installer.bat")
        with open(script_name, "w", encoding="utf-8") as f:
            f.write(bat_script)

        subprocess.Popen(
            ["cmd", "/c", script_name], creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        os._exit(0)
