import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from curl_cffi import requests
from modules.api.base_client import IMPERSONATE_TARGET
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
                impersonate=IMPERSONATE_TARGET,
                timeout=10,
            )
            if r.status_code == 200:
                manifest_path = os.path.join(self.update_cache_dir, "manifest.json")
                with open(manifest_path, "wb") as f:
                    f.write(r.content)
        except Exception:
            pass

    def _validate_rel_path(self, rel_path, base_dir):
        """Validate that a relative path resolves within base_dir (path traversal protection)."""
        try:
            rel_str = str(rel_path).replace("\\", "/").strip()
            if not rel_str or rel_str.startswith("/") or os.path.isabs(rel_str):
                return False
            if len(rel_str) >= 2 and rel_str[1] == ":":
                return False
            p = Path(rel_str)
            if any(part in ("..", ".") for part in p.parts):
                return False
            base_resolved = Path(base_dir).resolve()
            resolved = (base_resolved / p).resolve()
            return resolved.is_relative_to(base_resolved) and resolved != base_resolved
        except Exception:
            return False

    def download_update(self):
        if os.path.exists(self.update_cache_dir):
            shutil.rmtree(self.update_cache_dir, ignore_errors=True)
        os.makedirs(self.update_cache_dir, exist_ok=True)

        self.download_manifest()

        if self.total_files_count == 0:
            self.apply_update(self.update_cache_dir)
            return

        def download_worker(rel_path):
            # Fix 1.3: Validate path before downloading
            if not self._validate_rel_path(rel_path, self.update_cache_dir):
                self.error_signal.emit(f"Invalid path rejected: {rel_path}")
                return False

            clean_rel_path = str(rel_path).replace("\\", "/").lstrip("/")
            url = self.remote_url + clean_rel_path
            local_temp_path = os.path.normpath(os.path.join(str(self.update_cache_dir), clean_rel_path))

            try:
                os.makedirs(os.path.dirname(local_temp_path), exist_ok=True)

                r = requests.get(
                    url,
                    impersonate=IMPERSONATE_TARGET,
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

        # Fix 1.5: Cancel remaining futures on first error and avoid hanging shutdown
        error_occurred = False
        executor = ThreadPoolExecutor(max_workers=4)
        try:
            futures = [
                executor.submit(download_worker, f) for f in self.files_to_download
            ]

            for future in as_completed(futures):
                try:
                    success = future.result()
                except Exception as e:  # noqa: BLE001
                    self.error_signal.emit(f"Download exception: {e}")
                    success = False

                if success:
                    self.downloaded_files_count += 1
                    self.progress_signal.emit(
                        self.downloaded_files_count, self.total_files_count
                    )
                else:
                    error_occurred = True
                    for f in futures:
                        f.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    self.error_signal.emit(
                        self.tr("File upload error. Check the internet.")
                    )
                    return
        except Exception as e:  # noqa: BLE001
            error_occurred = True
            for f in futures:
                f.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            self.error_signal.emit(str(e))
            return
        finally:
            if not error_occurred:
                executor.shutdown(wait=True)

        if self.downloaded_files_count == self.total_files_count:
            self.apply_update(self.update_cache_dir)
        else:
            self.error_signal.emit(
                self.tr("Some files could not be downloaded. Cancel the update.")
            )

    def apply_update(self, update_dir):
        app_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
        current_pid = os.getpid()
        app_dir_resolved = Path(app_dir).resolve()

        if sys.platform == "win32":
            self._apply_update_windows(update_dir, app_dir_resolved, current_pid)
        else:
            self._apply_update_linux(update_dir, app_dir_resolved, current_pid)

        os._exit(0)

    def _apply_update_windows(self, update_dir, app_dir_resolved, current_pid):
        app_dir_win = str(app_dir_resolved).replace("/", "\\")
        update_dir_win = str(Path(update_dir).resolve()).replace("/", "\\")

        deletion_commands = ""
        protected_files = {"emilia.exe", "manifest.json", "icon.ico", ".", "..", ""}
        for file_path in self.files_to_removed:
            clean_rel_path = file_path.replace("/", "\\").strip("\\")
            # Fix 1.3: Validate path traversal for deletion targets
            if clean_rel_path.lower() in protected_files:
                continue
            if not self._validate_rel_path(clean_rel_path, app_dir_resolved):
                continue
            deletion_commands += f'if exist "{clean_rel_path}" del /f /q "{clean_rel_path}"\n'

        # Fix 1.1: Ensure labels start at column 0 with no indentation
        # Fix 1.2: Replace `timeout` with `ping` for headless (no stdin) processes
        bat_script = f"""@echo off
setlocal
cd /d "{app_dir_win}"

echo Waiting for application to exit...
taskkill /F /PID {current_pid} >nul 2>&1
taskkill /F /IM emilia.exe >nul 2>&1
ping 127.0.0.1 -n 3 > NUL

:CHECK_LOCK
tasklist /FI "PID eq {current_pid}" 2>NUL | find /I /N "{current_pid}">NUL
if "%ERRORLEVEL%"=="0" (
    echo Process {current_pid} is still running, waiting...
    taskkill /F /PID {current_pid} >nul 2>&1
    ping 127.0.0.1 -n 2 > NUL
    goto CHECK_LOCK
)

echo Cleaning old temporary files...
if exist "emilia.exe.old" del /f /q "emilia.exe.old" >nul 2>&1

echo Deleting obsolete files...
{deletion_commands}echo Preparing executable replacement...
if exist "{os.path.join(update_dir_win, 'emilia.exe')}" (
    if exist "emilia.exe" (
        del /f /q "emilia.exe" >nul 2>&1
        if exist "emilia.exe" (
            move /y "emilia.exe" "emilia.exe.old" >nul 2>&1
        )
    )
)

echo Installing new files...
:RETRY_COPY
xcopy "{update_dir_win}" "{app_dir_win}" /E /H /Y /Q /I >nul 2>&1
if errorlevel 1 (
    ping 127.0.0.1 -n 2 > NUL
    goto RETRY_COPY
)

echo Cleaning up...
rmdir /s /q "{update_dir_win}" >nul 2>&1
if exist "emilia.exe.old" del /f /q "emilia.exe.old" >nul 2>&1

echo Starting application...
start "" "{os.path.join(app_dir_win, 'emilia.exe')}"

echo Update complete.
(goto) 2>nul & del "%~f0"
"""

        script_dir = tempfile.gettempdir()
        script_name = os.path.join(script_dir, "emilia_update_installer.bat")
        with open(script_name, "w", encoding="utf-8") as f:
            f.write(bat_script)

        creation_flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            | getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        )
        popen_kwargs = {
            "close_fds": True,
            "stdin": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = creation_flags

        subprocess.Popen(
            ["cmd", "/c", script_name],
            **popen_kwargs,
        )

    def _apply_update_linux(self, update_dir, app_dir_resolved, current_pid):
        app_dir_linux = str(app_dir_resolved)
        update_dir_linux = str(Path(update_dir).resolve())

        deletion_commands = ""
        protected_files = {"emilia", "emilia.exe", "manifest.json", "icon.ico", ".", "..", ""}
        for file_path in self.files_to_removed:
            clean_rel_path = file_path.replace("\\", "/").strip("/")
            if clean_rel_path.lower() in protected_files:
                continue
            if not self._validate_rel_path(clean_rel_path, app_dir_resolved):
                continue
            deletion_commands += f'[ -e "{clean_rel_path}" ] && rm -rf "{clean_rel_path}"\n'

        # Fix 1.4: Separate bash script (updater.sh) for Linux
        sh_script = f"""#!/bin/bash
cd "{app_dir_linux}" || exit 1

echo "Waiting for application to exit..."
kill -9 {current_pid} 2>/dev/null
sleep 2

# Wait for process to fully exit
while kill -0 {current_pid} 2>/dev/null; do
    echo "Process {current_pid} is still running, waiting..."
    kill -9 {current_pid} 2>/dev/null
    sleep 1
done

echo "Deleting obsolete files..."
{deletion_commands}echo "Installing new files..."
cp -rf "{update_dir_linux}"/. "{app_dir_linux}/"

echo "Cleaning up..."
rm -rf "{update_dir_linux}"

echo "Starting application..."
if [ -f "{app_dir_linux}/emilia" ]; then
    chmod +x "{app_dir_linux}/emilia"
    nohup "{app_dir_linux}/emilia" > /dev/null 2>&1 &
fi

echo "Update complete."
rm -f "$0"
"""

        script_dir = tempfile.gettempdir()
        script_name = os.path.join(script_dir, "updater.sh")
        with open(script_name, "w", encoding="utf-8") as f:
            f.write(sh_script)
        os.chmod(script_name, 0o755)

        subprocess.Popen(
            ["bash", script_name],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
