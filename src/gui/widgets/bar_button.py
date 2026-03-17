# src/gui/widgets/bar_button.py

from PySide6.QtWidgets import QPushButton


class BarButton(QPushButton):
    def __init__(self, style, label='') -> None:
        super().__init__(label)
        self.setStyleSheet(style)
        self.setFixedSize(25, 25)
