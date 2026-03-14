import os
import shutil

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame

from modules.ui import TM
from modules.ui.Elements import CardFrame, PushButton

class MainCard(QFrame):
    def __init__(self, main_window, theme_id):
        self.mw = main_window
        self.theme_id = theme_id
        self.name = None

        self.initUI()
        self.mw.chat_thread.get_theme_signal.connect(self._getTheme)
        self.mw.chat_thread.get_theme(self.theme_id)

    def initUI(self):
        self.card_layout = QVBoxLayout()

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(12)
        self.title_label.setFont(font)
        self.card_layout.addWidget(self.title_label)

        self.author_label = QLabel()
        font = self.author_label.font()
        font.setPointSize(10)
        self.author_label.setFont(font)
        self.card_layout.addWidget(self.author_label)

        self.button_layout = QHBoxLayout()

        self.install_sel_button = PushButton(self.tr("Install and Select"))
        self.install_sel_button.clicked.connect(self.installSelectTheme)

        self.install_button = PushButton(self.tr("Install"))
        self.install_button.clicked.connect(self.downloadSelectTheme)

        self.sel_button = PushButton(self.tr("Select"))
        self.sel_button.clicked.connect(self.selectTheme)

        self.uninstall_button = PushButton(self.tr("Uninstall"))
        self.uninstall_button.clicked.connect(self.uninstallTheme)

        self.card_layout.addLayout(self.button_layout)

        super().__init__()
        self.setLayout(self.card_layout)

    def _getTheme(self, data):
        self.data = data
        self.name = self.data.get("name")
        self.title_label.setText(self.name)
        self.author_label.setText(self.tr("Author: @") + self.data.get("author"))
        self.author_label.mousePressEvent = lambda _: self.mw.openUserPage(self.data.get("author"))
        self.author_label.setCursor(Qt.CursorShape.PointingHandCursor)

        if TM.check_theme(self.theme_id):
            self.button_layout.addWidget(self.sel_button, alignment=Qt.AlignmentFlag.AlignRight)
            self.button_layout.addWidget(self.uninstall_button, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            self.button_layout.addWidget(self.install_button, alignment=Qt.AlignmentFlag.AlignRight)
            self.button_layout.addWidget(self.install_sel_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.mw.hide_overlay = True

    def uninstallTheme(self):
        self.uninstall_button.setEnabled(False)
        shutil.rmtree(os.path.join("themes/", self.name), ignore_errors=True)
        self.mw.hideOverlay()
        if self.mw.theme == self.name:
            TM.set_theme("Dark")
            self.mw.theme = self.name
            self.mw.settings.setValue("theme", self.name)

    def selectTheme(self):
        self.mw.hideOverlay()
        TM.set_theme(self.name)
        self.mw.theme = self.name
        self.mw.settings.setValue("theme", self.name)

    def downloadSelectTheme(self):
        self.mw.hideOverlay()
        self.mw.chat_thread.download_theme(self.name, self.theme_id)

    def installSelectTheme(self):
        self.install_sel_button.setEnabled(False)
        self.install_button.setEnabled(False)
        self.mw.chat_thread.download_theme_signal.connect(self._installSelectTheme)
        self.mw.chat_thread.download_theme(self.name, self.theme_id)

    def _installSelectTheme(self, path):
        self.mw.chat_thread.download_theme_signal.disconnect(self._installSelectTheme)
        self.mw.hideOverlay()
        TM.set_theme(self.name)
        self.mw.theme = self.name
        self.mw.settings.setValue("theme", self.name)