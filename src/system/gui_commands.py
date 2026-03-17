# src/system/gui_commands.py


def show_gui(request: dict):
    ...


def hide_gui(request: dict):
    ...


def open_float(request: dict):
    ...


def hide_float(request: dict):
    ...


def show_panel(request: dict):
    ...


def hide_panel(request: dict):
    ...


GUI_COMMANDS = {
        "show_gui": show_gui,
        "hide_gui": hide_gui,
        "open_float": open_float,
        "hide_float": hide_float,
        "hide_panel": hide_panel,
        "show_panel": show_panel,
}
