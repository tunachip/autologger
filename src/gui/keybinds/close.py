# src/gui/keybinds/close.py

from typing import Callable


def make_close(window) -> Callable[[], None]:
    def close() -> None:
        window.close()
    return close
