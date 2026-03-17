# src/gui/window.py

from .widgets.app import App
from .widgets.main import Main
from .widgets.top_bar import TopBar
from .widgets.bar_button import BarButton
from .widgets.status_line import StatusLine
from .widgets.description import Description
from .widgets.player import PlayerPanel
from .widgets.text_list import TextList
from .widgets.body import Body
from .widgets.float_window import FloatWindow
from .constants import (
    CLOSE_BUTTON_STYLE,
    ICONIFY_BUTTON_STYLE,
    FILL_SCREEN_BUTTON_STYLE,
    TRANSCRIPTS_STYLE,
    POPUP_STYLE,
)
from .keybinds.toggle import register_toggle, register_window_toggle


def start_app() -> None:
    app = App()
    window = Main(w=1400, h=1000)

    top_bar = TopBar(title='Autologger')
    min_button = BarButton(ICONIFY_BUTTON_STYLE, '-')
    min_button.clicked.connect(window.showMinimized)
    max_button = BarButton(FILL_SCREEN_BUTTON_STYLE, '+')
    max_button.clicked.connect(window.showMaximized)
    close_button = BarButton(CLOSE_BUTTON_STYLE, 'x')
    close_button.clicked.connect(app.quit)
    top_bar.add_control(min_button)
    top_bar.add_control(max_button)
    top_bar.add_control(close_button)

    body = Body()
    player = PlayerPanel()
    description = Description()
    player.panels.addWidget(description)

    transcripts = TextList(TRANSCRIPTS_STYLE)
    register_toggle("Ctrl+T", transcripts, window)

    body.panels.addWidget(player, 2)
    body.panels.addWidget(transcripts, 1)

    status_line = StatusLine("info", "Ready")

    settings = FloatWindow(POPUP_STYLE)
    register_window_toggle("Ctrl+M", settings, window)

    app.root.addWidget(top_bar)
    app.root.addWidget(body)
    app.root.addWidget(status_line)

    window.setCentralWidget(app.center)
    window.show()

    raise SystemExit(app.exec())


if __name__ == '__main__':
    start_app()
