# src/gui/widgets/text_input.py

from PySide6.QtWidgets import QLineEdit

from ..constants import TEXT_INPUT_STYLE


class TextInput(QLineEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(TEXT_INPUT_STYLE)
