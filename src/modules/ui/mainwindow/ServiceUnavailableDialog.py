from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from modules.ui import TM
from modules.ui.Elements import PushButton


class ServiceUnavailableDialog(QDialog):
    def __init__(self, parent=None, allow_retry=False):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Service Unavailable"))
        self.setModal(False)
        self.setFixedWidth(440)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title_label = QLabel(self.tr("The service is experiencing heavy load"))
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        message_label = QLabel(
            self.tr(
                "All requests to the service are returning error 503. "
                "The service is currently not working. Please try again later."
            )
        )
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch(1)

        if allow_retry:
            retry_button = PushButton(self.tr("Retry"))
            retry_button.clicked.connect(self.accept)
            button_layout.addWidget(retry_button)

        close_button = PushButton(self.tr("Close"))
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)
        button_layout.addStretch(1)

        layout.addLayout(button_layout)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {TM.c("mw_back")};
            }}
            QLabel {{
                background-color: transparent;
                color: {TM.c("mw_color")};
            }}
        """)
