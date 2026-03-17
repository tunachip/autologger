from __future__ import annotations

from enum import StrEnum
from pathlib import Path


class StatusState(StrEnum):
    INFO = "info"
    DONE = "done"
    WARN = "warn"
    FAIL = "fail"


COLORS = {
    "black": "#000000",
    "white": "#eeeeee",
    "dim_gray": "#333333",
    "gray": "#999999",
    "red": "#bb0000",
    "green": "#00bb00",
    "blue": "#0000bb",
    "yellow": "#bbbb00",
    "cyan": "#00bbbb",
    "magenta": "#bb00bb",
    "dim_red": "#330000",
    "dim_green": "#003300",
    "dim_blue": "#000033",
    "dim_yellow": "#333300",
    "dim_cyan": "#003333",
    "dim_magenta": "#330033",
}


DEFAULT_THEME = {
    "main": {
        "fg": COLORS["gray"],
        "bg": COLORS["black"],
    },
    "top_bar": {
        "fg": COLORS["white"],
        "bg": COLORS["dim_gray"],
    },
    "panel": {
        "fg": COLORS["black"],
        "bg": COLORS["white"],
        "border_width": "1px",
        "border_style": "solid",
        "border_color": COLORS["black"],
    },
    "transcripts": {
        "fg": COLORS["black"],
        "bg": COLORS["dim_red"],
        "bg_image": "assets/red_velvet.png",
        "border_width": "1px",
        "border_style": "solid",
        "border_color": COLORS["black"],
    },
    "description": {
        "fg": COLORS["white"],
        "bg": COLORS["dim_blue"],
        "bg_image": "assets/blue_velvet.png",
        "border_width": "1px",
        "border_style": "solid",
        "border_color": COLORS["black"],
    },
    "popup": {
        "fg": COLORS["black"],
        "bg": COLORS["white"],
        "border_width": "1px",
        "border_style": "solid",
        "border_color": COLORS["black"],
    },
    "text_input": {
        "fg": COLORS["black"],
        "bg": COLORS["white"],
        "border_width": "1px",
        "border_style": "solid",
        "border_color": COLORS["black"],
        "padding": "2px 6px",
    },
    "text_list": {
        "fg": COLORS["black"],
        "bg": COLORS["white"],
        "selected_fg": COLORS["white"],
        "selected_bg": COLORS["blue"],
    },
    "iconify_button": {
        "fg": COLORS["white"],
        "bg": COLORS["black"],
        "border-radius": "10px",
        "border_width": "1px",
        "border_style": "solid",
        "border_color": COLORS["black"],
        "hover": {
            "fg": COLORS["white"],
            "bg": COLORS["dim_green"]
        },
        "pressed": {
            "fg": COLORS["white"],
            "bg": COLORS["dim_gray"],
        }
    },
    "fill_screen_button": {
        "fg": COLORS["white"],
        "bg": COLORS["black"],
        "border-radius": "10px",
        "border_width": "1px",
        "border_style": "solid",
        "border_color": COLORS["black"],
        "hover": {
            "fg": COLORS["white"],
            "bg": COLORS["dim_yellow"]
        },
        "pressed": {
            "fg": COLORS["white"],
            "bg": COLORS["dim_gray"],
        }
    },
    "close_button": {
        "fg": COLORS["white"],
        "bg": COLORS["black"],
        "border-radius": "10px",
        "border_width": "1px",
        "border_style": "solid",
        "border_color": COLORS["black"],
        "hover": {
            "fg": COLORS["white"],
            "bg": COLORS["dim_red"]
        },
        "pressed": {
            "fg": COLORS["white"],
            "bg": COLORS["dim_gray"],
        }
    },
    "status_line": {
        "base": {
            "fg": COLORS["white"],
            "bg": COLORS["black"],
            "padding": "2px 6px",
            "border_width": "1px",
            "border_style": "solid",
            "border_color": COLORS["black"],
        },
        "states": {
            StatusState.INFO.value: {
                "fg": COLORS["white"],
                "bg": COLORS["dim_cyan"],
            },
            StatusState.DONE.value: {
                "fg": COLORS["white"],
                "bg": COLORS["green"],
            },
            StatusState.WARN.value: {
                "fg": COLORS["black"],
                "bg": COLORS["yellow"],
            },
            StatusState.FAIL.value: {
                "fg": COLORS["white"],
                "bg": COLORS["red"],
            },
        },
    },
}


def image_path(rel_path: str) -> str:
    GUI_DIR = Path(__file__).resolve().parent
    return f"url({str((GUI_DIR / rel_path).as_posix())})"


def build_main_style(theme: dict) -> str:
    main = theme["main"]
    return f"""
QWidget {{
    background-color: {main["bg"]};
    color: {main["fg"]};
}}
""".strip()


def build_transcripts_style(theme: dict) -> str:
    transcripts = theme["transcripts"]
    return f"""
QWidget {{
    background-color: {transcripts['bg']};
    color: {transcripts['fg']};
}}
"""


def build_description_style(theme: dict) -> str:
    description = theme["description"]
    return f"""
QWidget {{
    background-color: {description['bg']};
    color: {description['fg']};
}}
"""


def build_top_bar_style(theme: dict) -> str:
    main = theme["top_bar"]
    return f"""
QFrame {{
    background-color: {main["bg"]};
    color: {main["fg"]};
}}
""".strip()


def build_fill_screen_button_style(theme: dict) -> str:
    main = theme['fill_screen_button']
    border = f"{main['border_width']} " + \
             f"{main['border_style']} " + \
             f"{main['border_color']}"
    hover = main["hover"]
    pressed = main["pressed"]
    return f"""
QPushButton {{
    background-color: {main['bg']};
    color: {main['fg']};
    border-radius: {main['border-radius']};
    border: {border};
    text-align: center;
}}
QPushButton:hover {{
    background-color: {hover['bg']};
    color: {hover['fg']};
}}
QPushButton:pressed {{
    background-color: {pressed['bg']};
    color: {pressed['fg']};
}}
""".strip()


def build_iconify_button_style(theme: dict) -> str:
    main = theme['iconify_button']
    border = f"{main['border_width']} " + \
             f"{main['border_style']} " + \
             f"{main['border_color']}"
    hover = main["hover"]
    pressed = main["pressed"]
    return f"""
QPushButton {{
    background-color: {main['bg']};
    color: {main['fg']};
    border-radius: {main['border-radius']};
    border: {border};
    text-align: center;
}}
QPushButton:hover {{
    background-color: {hover['bg']};
    color: {hover['fg']};
}}
QPushButton:pressed {{
    background-color: {pressed['bg']};
    color: {pressed['fg']};
}}
""".strip()


def build_close_button_style(theme: dict) -> str:
    main = theme['close_button']
    border = f"{main['border_width']} " + \
             f"{main['border_style']} " + \
             f"{main['border_color']}"
    hover = main["hover"]
    pressed = main["pressed"]
    return f"""
QPushButton {{
    background-color: {main['bg']};
    color: {main['fg']};
    border-radius: {main['border-radius']};
    border: {border};
    text-align: center;
}}
QPushButton:hover {{
    background-color: {hover['bg']};
    color: {hover['fg']};
}}
QPushButton:pressed {{
    background-color: {pressed['bg']};
    color: {pressed['fg']};
}}
""".strip()


def build_panel_style(theme: dict) -> str:
    panel = theme["panel"]
    border = f"{panel['border_width']} " + \
             f"{panel['border_style']} " + \
             f"{panel['border_color']}"
    return f"""
QFrame {{
    background-color: {panel["bg"]};
    color: {panel["fg"]};
    border: {border};
}}
""".strip()


def build_popup_style(theme: dict) -> str:
    popup = theme["popup"]
    border = f"{popup['border_width']} " + \
             f"{popup['border_style']}" + \
             f"{popup['border_color']}"
    return f"""
QFrame {{
    background-color: {popup["bg"]};
    color: {popup["fg"]};
    border: {border};
}}
""".strip()


def build_text_input_style(theme: dict) -> str:
    text_input = theme["text_input"]
    border = f"{text_input['border_width']} " + \
             f"{text_input['border_style']} " + \
             f"{text_input['border_color']}"
    return f"""
QLineEdit {{
    background-color: {text_input["bg"]};
    color: {text_input["fg"]};
    border: {border};
    padding: {text_input["padding"]};
}}
""".strip()


def build_text_list_style(theme: dict) -> str:
    text_list = theme["text_list"]
    return f"""
QListView {{
    background-color: {text_list["bg"]};
    color: {text_list["fg"]};
}}

QListView::item:selected {{
    background-color: {text_list["selected_bg"]};
    color: {text_list["selected_fg"]};
}}
""".strip()


def build_status_line_style(theme: dict) -> str:
    status_line = theme["status_line"]
    base = status_line["base"]
    border = f"{base['border_width']} " + \
             f"{base['border_style']}" + \
             f"{base['border_color']}"
    states = status_line["states"]

    parts = [f"""
QLabel {{
    color: {base["fg"]};
    background-color: {base["bg"]};
    border: {border};
    padding: {base["padding"]};
}}
""".strip()]

    for name, colors in states.items():
        parts.append(f"""
QLabel[state="{name}"] {{
    color: {colors["fg"]};
    background-color: {colors["bg"]};
}}
""".strip())

    return "\n\n".join(parts)


MAIN_STYLE = build_main_style(DEFAULT_THEME)
TOP_BAR_STYLE = build_top_bar_style(DEFAULT_THEME)
PANEL_STYLE = build_panel_style(DEFAULT_THEME)
POPUP_STYLE = build_popup_style(DEFAULT_THEME)
TEXT_INPUT_STYLE = build_text_input_style(DEFAULT_THEME)
TEXT_LIST_STYLE = build_text_list_style(DEFAULT_THEME)
STATUS_LINE_STYLE = build_status_line_style(DEFAULT_THEME)
ICONIFY_BUTTON_STYLE = build_iconify_button_style(DEFAULT_THEME)
FILL_SCREEN_BUTTON_STYLE = build_fill_screen_button_style(DEFAULT_THEME)
CLOSE_BUTTON_STYLE = build_close_button_style(DEFAULT_THEME)
DESCRIPTION_STYLE = build_description_style(DEFAULT_THEME)
TRANSCRIPTS_STYLE = build_transcripts_style(DEFAULT_THEME)
