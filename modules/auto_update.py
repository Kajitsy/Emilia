import requests, zipfile, os
from modules.config import getconfig, writeconfig, resource_path 
from modules.translations import translations
from modules.other import MessageBox
from PyQt6.QtCore import QLocale

trls = translations(getconfig('language', QLocale.system().name()), resource_path('locales'))

class AutoUpdate():
    def __init__(self, build, type = 'full', pre = False) -> None:
        self.build = build
        self.type = type
        self.pre = pre

    def check_for_updates(self):
        response = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/autoupdate.json")
        response.raise_for_status()
        updates = response.json()
        try:
            if self.pre:
                if self.type == 'full':
                    if "latest_prerealease" in updates:
                        latest_prerealease = updates["latest_prerealease"]
                        if int(latest_prerealease["build"]) > int(self.build):
                            if resource_path("autoupdate") != "autoupdate":
                                if latest_prerealease.get('exe', '') != '':
                                    self.download_and_update_script(latest_prerealease["exe"], latest_prerealease["build"])
                                return
                            self.download_and_update_script(latest_prerealease["url"], latest_prerealease["build"])
                            return
                elif self.type == 'charai':
                    if "charai_latest_prerealease" in updates:
                        latest_prerealease = updates["charai_latest_prerealease"]
                        if int(latest_prerealease["build"]) > int(self.build):
                            if resource_path("autoupdate") != "autoupdate":
                                if latest_prerealease.get('exe', '') != '':
                                    self.download_and_update_script(latest_prerealease["exe"], latest_prerealease["build"])
                                return
                            self.download_and_update_script(latest_prerealease["url"], latest_prerealease["build"])
                            return
            else:
                if self.type == 'full':
                    if "latest_realease" in updates:
                        latest_realease = updates["latest_realease"]
                        if int(latest_realease["build"]) > int(self.build):
                            if resource_path("autoupdate") != "autoupdate":
                                if latest_realease.get('exe', '') != '':
                                    self.download_and_update_script(latest_realease["exe"], latest_realease["build"])
                                return
                            self.download_and_update_script(latest_realease["url"], latest_realease["build"])
                            return
                elif self.type == 'charai':
                    if "latest_realease" in updates:
                        latest_realease = updates["latest_realease"]
                        if int(latest_realease["build"]) > int(self.build):
                            if resource_path("autoupdate") != "autoupdate":
                                if latest_realease.get('exe', '') != '':
                                    self.download_and_update_script(latest_realease["exe"], latest_realease["build"])
                                return
                            self.download_and_update_script(latest_realease["url"], latest_realease["build"])
                            return
        except Exception as e:
            print(f"{trls.tr('Errors', 'UpdateCheckError')} {e}")
            writeconfig('autoupdate_enable', 'False')

    def download_and_update_script(self, url, build):
        print(f"{trls.tr('AutoUpdate', 'upgrade_to')} {build}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"{trls.tr('Errors', 'UpdateDownloadError')} {e}")
            writeconfig('autoupdate_enable', 'False')
            return
        with open(f"Emilia_{build}.zip", "wb") as f:
            f.write(response.content)

        with zipfile.ZipFile(f"Emilia_{build}.zip", "r") as zip_ref:
            zip_ref.extractall(".")

        os.remove(f"Emilia_{build}.zip")

        MessageBox("Update!", f"{trls.tr('AutoUpdate', 'emilia_updated')} {build}!")