# src/gui/widgets/panel.py

from PySide6.QtWidgets import QFrame

from ..constants import PANEL_STYLE


class Panel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(PANEL_STYLE)
