# src/gui/keybinds/toggle.py

from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence


def register_window_toggle(keybind, window, parent) -> None:
    def toggle():
        if window.isVisible():
            window.hide()
        else:
            window.show()
            window.raise_()
            window.activateWindow()

    command = QShortcut(QKeySequence(keybind), parent)
    command.setContext(Qt.ShortcutContext.ApplicationShortcut)
    command.activated.connect(toggle)


def register_toggle(keybind, panel, parent) -> None:
    def toggle():
        if panel.isVisible():
            panel.hide()
        else:
            panel.show()

    command = QShortcut(QKeySequence(keybind), parent)
    command.activated.connect(toggle)
