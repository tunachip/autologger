# src/gui/widgets/status_line.py

from PySide6.QtWidgets import QLabel

from ..constants import STATUS_LINE_STYLE


class StatusLine(QLabel):
    def __init__(self, state, text, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(STATUS_LINE_STYLE)
        self.setText(text)
        self.setProperty("state", state)
