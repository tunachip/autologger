# src/gui/widgets/float_window.py

from PySide6.QtWidgets import QWidget, QVBoxLayout


class FloatWindow(QWidget):
    def __init__(self, style, parent=None, w=500, h=400) -> None:
        super().__init__(parent)
        self.resize(w, h)
        self.setStyleSheet(style)
        self.panels = QVBoxLayout(self)
