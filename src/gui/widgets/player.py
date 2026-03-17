# src/gui/widgets/player.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame


class PlayerPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.panels = QVBoxLayout(self)
        self.panels.setContentsMargins(0, 0, 0, 0)


class PlayerFrame(QFrame):
    def __init__(self, vlcInstance) -> None:
        super().__init__()
