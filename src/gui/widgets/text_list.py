# src/gui/widgets/text_list.py

from PySide6.QtWidgets import QListView

from ..constants import TEXT_LIST_STYLE


class TextList(QListView):
    def __init__(self, style=None, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(style if style is not None else TEXT_LIST_STYLE)
