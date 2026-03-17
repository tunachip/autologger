# src/gui/widgets/top_bar.py

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel
)

from ..constants import TOP_BAR_STYLE


class TopBar(QFrame):
    def __init__(self, parent=None, h=30, title="test") -> None:
        super().__init__(parent)
        self.setStyleSheet(TOP_BAR_STYLE)

        self.title = QLabel(title)
        self.root_layout = QHBoxLayout(self)
        self.root_layout.setContentsMargins(8, 0, 8, 0)
        self.root_layout.addWidget(self.title)
        self.root_layout.addStretch()
        self.setFixedHeight(h)

    def add_control(self, widget):
        self.root_layout.addWidget(widget)
