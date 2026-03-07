import os, shutil, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication

class UpdateThread(QThread):
    finished_signal = pyqtSignal(bool)
    progress_signal = pyqtSignal(int, int)
    error_signal = pyqtSignal(str)

    def __init__(self, main_window, remote_url, files_to_download, files_to_removed):
        super().__init__()
        self.mw = main_window
        self.remote_url = remote_url
        self.files_to_download = files_to_download
        self.files_to_removed = files_to_removed
        self.total_files_count = len(self.files_to_download)
        self.downloaded_files_count = 0
        self.update_cache_dir = "cache/update"

    def run(self):
        if self.total_files_count == 0:
            self.apply_update(self.update_cache_dir)
            self.finished_signal.emit(True)
        else:
            self.download_update()

    def download_update(self):
        if os.path.exists(self.update_cache_dir):
            shutil.rmtree(self.update_cache_dir)
        os.makedirs(self.update_cache_dir, exist_ok=True)

        def download_worker(rel_path):
            url = self.remote_url + rel_path
            local_temp_path = os.path.join(self.update_cache_dir, rel_path)

            try:
                os.makedirs(os.path.dirname(local_temp_path), exist_ok=True)

                r = requests.get(url, stream=True, timeout=10)
                if r.status_code == 200:
                    with open(local_temp_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                else:
                    self.error_signal.emit(f"HTTP error {r.status_code}: {rel_path}")
                    return False
            except Exception as e:
                self.error_signal.emit(f"Download error {e}: {rel_path}")
                return False

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(download_worker, f) for f in self.files_to_download]

            for future in as_completed(futures):
                success = future.result()
                if success:
                    self.downloaded_files_count += 1
                    self.progress_signal.emit(self.downloaded_files_count, self.total_files_count)
                else:
                    self.error_signal.emit(self.tr("File upload error. Check the internet."))
                    return

        if all(futures):
            self.apply_update(self.update_cache_dir)
        else:
            self.error_signal.emit(self.tr("Some files could not be downloaded. Cancel the update."))

    def apply_update(self, update_dir):
        deletion_commands = ""
        for file_path in self.files_to_removed:
            win_path = file_path.replace("/", "\\")
            deletion_commands += f'if exist "{win_path}" del /f /q "{win_path}"\n    '

        bat_script = f"""
        @echo off
        cd /d "%~dp0"
        echo Waiting for application to close...
        timeout /t 5 /nobreak > NUL

        echo Deleting obsolete files...
        if exist manifest.json del /f /q manifest.json
        {deletion_commands}

        echo Installing new files...
        xcopy "{update_dir}" "." /E /H /Y /Q

        echo Cleaning up...
        rmdir /s /q "{update_dir}"

        echo Starting application...
        start "" "emilia.exe"

        del "%~f0"
        """

        with open("update_installer.bat", "w") as f:
            f.write(bat_script)

        os.startfile("update_installer.bat")
        QApplication.instance().quit()
