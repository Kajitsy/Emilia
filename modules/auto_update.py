import requests, zipfile, os, sys

from packaging import version
from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtWidgets import (
    QApplication, QMessageBox, QProgressDialog
)

from modules.config import getconfig, writeconfig, exe_check
from modules.ets import translations

trls = translations(getconfig("language", QLocale.system().name()), "locales")

def check_for_updates(ver, target_filename, pre=False, parent=None):
    if not exe_check():
        return

    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(
            "https://api.github.com/repos/Kajitsy/Emilia/releases",
            headers=headers
        )
        response.raise_for_status()

        releases = response.json()

        latest_release = None
        latest_prerelease = None
        for release in releases:
            if not latest_release and not release["prerelease"]:
                latest_release = release
            elif not latest_prerelease and release["prerelease"]:
                latest_prerelease = release

        target_release = None
        if pre and latest_prerelease:
            target_release = latest_prerelease
        else:
            target_release = latest_release

        if target_release:
            latest_version = target_release["tag_name"]
            if version.parse(latest_version) > version.parse(ver):
                reply = QMessageBox.question(
                    parent, "An update is available",
                    f"{trls.tr('AutoUpdate', 'upgrade_to')} {latest_version}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    update(target_release, target_filename, parent)
                return

    except requests.exceptions.RequestException as e:
        QMessageBox.warning(
            parent, trls.tr("Errors", "Error"),
            f"{trls.tr('Errors', 'UpdateCheckError')} {e}"
        )
        writeconfig("autoupdate_enable", False)

def update(release, target_filename, parent=None):
    for asset in release["assets"]:
        if asset["name"] == target_filename:
            download_url = asset["browser_download_url"]

            try:
                response = requests.get(download_url, stream=True)
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                progress = QProgressDialog(
                    "Download", None, 0, total_size, parent
                )
                progress.setWindowTitle("Updating")
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()

                with open("update.zip", "wb") as f:
                    for chunk in response.iter_content(chunk_size=4096):
                        if progress.wasCanceled():
                            return

                        f.write(chunk)
                        downloaded += len(chunk)
                        progress.setValue(downloaded)
                        QApplication.processEvents()

                progress.setValue(total_size)

                with zipfile.ZipFile("update.zip", "r") as zip_ref:
                    zip_ref.extractall(".")

                os.remove("update.zip")

                QMessageBox.information(
                    parent, trls.tr("AutoUpdate", "UpdateCompleteTitle"),
                    trls.tr("AutoUpdate", "UpdateCompleteMessage")
                )
                sys.exit()

            except requests.exceptions.RequestException as e:
                QMessageBox.warning(
                    parent, trls.tr("Errors", "Error"),
                    f"{trls.tr('Errors', 'UpdateDownloadError')} {e}"
                )
                writeconfig("autoupdate_enable", False)
                return