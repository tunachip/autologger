# src/gui/widgets/app.py

from PySide6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QWidget,
)

import sys


class App(QApplication):
    def __init__(self) -> None:
        super().__init__(sys.argv)
        self.center = QWidget()
        root = QVBoxLayout(self.center)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.root = root
