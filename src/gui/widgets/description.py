# src/gui/widgets/description.py

from PySide6.QtWidgets import QLabel

from ..constants import DESCRIPTION_STYLE


class Description(QLabel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(DESCRIPTION_STYLE)
