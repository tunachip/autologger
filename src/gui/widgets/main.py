# src/gui/widgets/main.py

from PySide6.QtWidgets import QMainWindow

from ..constants import MAIN_STYLE


class Main(QMainWindow):
    def __init__(self, parent=None, w=800, h=600) -> None:
        super().__init__(parent)
        self.setStyleSheet(MAIN_STYLE)
        self.resize(w, h)
