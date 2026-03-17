# src/gui/widgets/body.py

from PySide6.QtWidgets import QWidget, QHBoxLayout


class Body(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.panels = QHBoxLayout(self)
        self.panels.setContentsMargins(0, 0, 0, 0)
