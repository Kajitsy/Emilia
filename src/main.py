import asyncio
import ctypes
import datetime
import logging
import os
import platform
import sys
from pathlib import Path

from platformdirs import user_log_dir

log_dir = Path(user_log_dir("Emilia", False))
log_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join(log_dir, f"{timestamp}.log")
latest_log_filename = os.path.join(log_dir, "latest.log")

logger = logging.getLogger("Emilia")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

latest_file_handler = logging.FileHandler(
    latest_log_filename, encoding="utf-8", mode="w"
)
latest_file_handler.setFormatter(formatter)
logger.addHandler(latest_file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logging.getLogger("qasync").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class LoggerWriter:
    def __init__(self, level, stream):
        self.level = level
        self.stream = stream

    def write(self, message):
        if message.strip():
            self.level(message.strip())

    def flush(self):
        self.stream.flush()


from version import __version__

logger.info(
    f"""
Emilia:       {__version__}
OS:           {platform.system()} {platform.release()} {platform.version()} ({platform.architecture()[0]})
Script Path:  {os.path.abspath(sys.argv[0])}
Started at:   {datetime.datetime.now(datetime.timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S')}
Python:       {sys.version.split()[0]} ({platform.architecture()[0]})
Frozen EXE:   {getattr(sys, 'frozen', False)}
Python Path:  {sys.executable}
Process ID:   {os.getpid()}"""
)

from PyQt6.QtCore import QLocale, QSettings, QTranslator, Qt
from PyQt6.QtGui import QAction, QGuiApplication, QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QDialog, QSplashScreen, QSystemTrayIcon
from qasync import QEventLoop

from modules.api.service_status import is_service_unavailable
from modules.ui import TM
from modules.ui.Elements import Menu
from modules.ui.mainwindow import MainPage, ServiceUnavailableDialog

if platform.system() == "Windows":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Emilia")
    logger.debug("ctypes SetCurrentProcessExplicitAppUserModelID")

app = QApplication(sys.argv)
app.setWindowIcon(QIcon("icon.ico"))

settings = QSettings(
    QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Emilia", "settings"
)
translator = QTranslator()
translator.load(
    f"lang/{settings.value('emilia_language', QLocale.system().name())}.qm"
)
app.installTranslator(translator)

theme = settings.value("app_theme", "Dark", type=str)
if settings.value("app_theme_system_sync", False, type=bool):
    theme = (
        "Dark"
        if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        else "Light"
    )
TM.use_system_accent = settings.value("app_use_system_accent", False, type=bool)
TM.set_theme(theme)

loop = QEventLoop(app)
asyncio.set_event_loop(loop)

mw_show = True


async def main(splash=None):
    while await is_service_unavailable(
        settings.value("cai_auth/token", "", type=str),
        settings.value("cai_auth/cookie", "", type=str),
    ):
        if splash:
            splash.hide()
        dialog = ServiceUnavailableDialog(allow_retry=True)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            app.quit()
            return

    def actions_toggle():
        global mw_show
        mw_show = not mw_show
        show_action.setVisible(not mw_show)
        hide_action.setVisible(mw_show)

    tray_icon = QSystemTrayIcon()
    tray_menu = Menu()
    main_window = MainPage()
    main_window.mw_hide_signal.connect(actions_toggle)
    main_window.mw_show_signal.connect(actions_toggle)

    tray_icon.activated.connect(
        lambda reason: (
            main_window.show() or main_window.raise_() or main_window.activateWindow()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )
    )
    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Emilia")
    tray_icon.setIcon(QIcon("icon.ico"))

    show_action = QAction(tray_icon.tr("Show"))
    show_action.triggered.connect(
        lambda: (
            main_window.showMaximized()
            if main_window.isMaximized()
            else main_window.show()
        )
    )
    tray_menu.addAction(show_action)

    hide_action = QAction(tray_icon.tr("Hide"))
    hide_action.triggered.connect(lambda: main_window.hide())
    tray_menu.addAction(hide_action)

    quit_action = QAction(tray_icon.tr("Quit"))
    quit_action.triggered.connect(lambda: app.quit())
    tray_menu.addAction(quit_action)

    await asyncio.sleep(2.5)

    if main_window.settings.value("main_window/maximized", False, type=bool):
        main_window.showMaximized()
    else:
        main_window.show()

    if splash:
        splash.finish(main_window)

    tray_icon.show()


if __name__ == "__main__":
    pixmap = QPixmap("icon.ico")
    splash = QSplashScreen(pixmap)
    splash.show()

    with loop:
        loop.create_task(main(splash))
        loop.run_forever()
