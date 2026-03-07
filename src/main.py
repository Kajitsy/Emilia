import sys, ctypes, platform, datetime, os, logging, asyncio

os.makedirs("logs", exist_ok=True)

timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = os.path.join("logs", f"{timestamp}.log")
latest_log_filename = os.path.join("logs", "latest.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

latest_file_handler = logging.FileHandler(latest_log_filename, encoding="utf-8", mode="w")
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

logging.info(f"""
OS:           {platform.system()} {platform.release()} {platform.version()} ({platform.architecture()[0]})
Script Path:  {os.path.abspath(sys.argv[0])}
Started at:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python:       {sys.version.split()[0]} ({platform.architecture()[0]})
Frozen EXE:   {getattr(sys, 'frozen', False)}
Python Path:  {sys.executable}
Process ID:   {os.getpid()}""")

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QSettings, QTranslator, QLocale
from qasync import QEventLoop

from modules.ui.Elements import Menu
from modules.ui.mainwindow import MainPage

if platform.system() == 'Windows':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Emilia Next")
    logging.debug("ctypes SetCurrentProcessExplicitAppUserModelID")

app = QApplication(sys.argv)

translator = QTranslator()
translator.load(f"lang/{QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, 'Emilia', 'settings').value('emilia_language', QLocale.system().name())}.qm")
app.installTranslator(translator)

loop = QEventLoop(app)
asyncio.set_event_loop(loop)


async def main():
    tray_icon = QSystemTrayIcon()
    tray_menu = Menu()
    main_window = MainPage()

    if platform.system() == 'Windows':
        from modules.logic.WinDarkTheme import ChangeDWMAttrib, detect

        ChangeDWMAttrib(detect(main_window), 19, ctypes.c_int(1))
        ChangeDWMAttrib(detect(main_window), 20, ctypes.c_int(1))

    tray_icon.activated.connect(
        lambda reason: main_window.show() or main_window.raise_() or main_window.activateWindow()
        if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )
    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Emilia")
    app.setWindowIcon(QIcon("icon.ico"))
    tray_icon.setIcon(QIcon("icon.ico"))

    show_action = QAction(tray_icon.tr("Show"))
    show_action.triggered.connect(
        lambda: main_window.showMaximized() if main_window.isMaximized() else main_window.show())
    tray_menu.addAction(show_action)

    hide_action = QAction(tray_icon.tr("Hide"))
    hide_action.triggered.connect(lambda: main_window.hide())
    tray_menu.addAction(hide_action)

    quit_action = QAction(tray_icon.tr("Quit"))
    quit_action.triggered.connect(lambda: app.quit())
    tray_menu.addAction(quit_action)

    if main_window.settings.value("main_window/maximized", False, type=bool):
        main_window.showMaximized()
    else:
        main_window.show()

    tray_icon.show()

if __name__ == "__main__":
    with loop:
        loop.create_task(main())
        loop.run_forever()