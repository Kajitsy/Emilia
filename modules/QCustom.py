from PyQt6.QtWidgets import (QPushButton,
                             QLabel,
                             QLineEdit,
                             QSizePolicy)

class ResizableButton(QPushButton):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.adjustFontSize()

    def adjustFontSize(self):
        button_width = self.width()
        button_height = self.height()

        base_size = min(button_width, button_height) // 5
        min_font_size = 10
        font_size = max(base_size, min_font_size)
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

class ResizableLabel(QLabel):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.adjustFontSize()

    def adjustFontSize(self):
        button_width = self.width()
        button_height = self.height()

        base_size = min(button_width, button_height) // 5
        min_font_size = 10
        font_size = max(base_size, min_font_size)
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

class ResizableLineEdit(QLineEdit):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.adjustFontSize()

    def adjustFontSize(self):
        button_width = self.width()
        button_height = self.height()

        base_size = min(button_width, button_height) // 5
        min_font_size = 10
        font_size = max(base_size, min_font_size)
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)