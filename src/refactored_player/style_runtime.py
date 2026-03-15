from __future__ import annotations

from typing import Any

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from .constants import DEFAULT_KEYBINDS, FONT, FONT_SIZE_OFFSETS, STATUS_HINTS, THEME, THEME_SETTING_IDS


class StyleRuntimeMixin:
    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Filter.TEntry",
            fieldbackground=THEME["SURFACE_ALT_BG"],
            foreground="#f0f0f0",
        )
        style.configure(
            "Terminal.TNotebook",
            background=THEME["APP_BG"],
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "Terminal.TNotebook.Tab",
            background=THEME["SURFACE_BG"],
            foreground=THEME["FG_MUTED"],
            borderwidth=0,
            padding=(8, 4),
        )
        style.configure(
            "Vertical.TScrollbar",
            background=THEME["SURFACE_BG"],
            troughcolor=THEME["PANEL_BG"],
            arrowcolor=THEME["FG_MUTED"],
            bordercolor=THEME["BORDER"],
            lightcolor=THEME["SURFACE_BG"],
            darkcolor=THEME["SURFACE_BG"],
            gripcount=0,
        )
        style.map(
            "Vertical.TScrollbar",
            background=[
                ("active", THEME["SELECT_BG"]),
                ("pressed", THEME["FG_ACCENT"]),
            ],
            arrowcolor=[
                ("active", THEME["FG_SOFT"]),
                ("pressed", THEME["FG"]),
            ],
        )
        style.map(
            "Terminal.TNotebook.Tab",
            background=[
                ("selected", THEME["PANEL_BG"]),
                ("active", THEME["SELECT_BG"]),
            ],
            foreground=[
                ("selected", THEME["FG"]),
                ("active", THEME["FG_SOFT"]),
            ],
        )

    def _theme_color(self, key: str) -> str:
        setting_id = THEME_SETTING_IDS.get(key)
        if setting_id:
            return str(self._ai_settings.get(setting_id) or THEME[key])
        return str(THEME.get(key, ""))

    def _ui_font(
        self,
        delta: int = 0,
        *,
        bold: bool = False,
    ) -> tuple[str, int] | tuple[str, int, str]:
        family = str(
            getattr(self, "_ui_font_family", None)
            or self._ai_settings.get("font_family")
            or FONT["STYLE"]
        )
        size = max(
            8,
            int(getattr(self, "_ui_font_size", FONT["SIZE"])) + int(delta),
        )
        if bold:
            return (family, size, "bold")
        return (family, size)

    def _shortcut_label(self, action: str) -> str:
        keybinds = self._ai_settings.get("keybinds")
        if not isinstance(keybinds, dict):
            keybinds = DEFAULT_KEYBINDS
        token = str(
            keybinds.get(action, DEFAULT_KEYBINDS.get(action, ""))
        ).strip()
        return token or DEFAULT_KEYBINDS.get(action, "")

    def _status_hint(self, name: str, **values: str) -> str:
        template = STATUS_HINTS.get(name, "")
        context = {
            action: self._shortcut_label(action)
            for action in DEFAULT_KEYBINDS
        }
        context.update(values)
        try:
            return template.format(**context)
        except Exception:
            return template

    def _apply_theme(self) -> None:
        bg = self._theme_color("APP_BG")
        panel_bg = self._theme_color("PANEL_BG")
        surface_bg = self._theme_color("SURFACE_BG")
        surface_alt_bg = self._theme_color("SURFACE_ALT_BG")
        fg = self._theme_color("FG")
        muted = self._theme_color("FG_MUTED")
        accent = self._theme_color("FG_ACCENT")
        soft = self._theme_color("FG_SOFT")
        border = self._theme_color("BORDER")
        try:
            family = str(self._ai_settings.get("font_family") or FONT["STYLE"])
            base_size = max(8, int(self._ai_settings.get("font_size") or FONT["SIZE"]))
        except Exception:
            family = FONT["STYLE"]
            base_size = FONT["SIZE"]
        size = max(8, min(64, base_size + int(self._font_size_delta)))
        self._ui_font_family = family
        self._ui_font_size = size
        self._text_font.configure(family=family, size=size)
        self._text_font_bold.configure(family=family, size=size)
        self.root.configure(bg=bg)
        if hasattr(self, "title_bar"):
            self.title_bar.configure(bg=surface_bg)
        if hasattr(self, "launch_bar"):
            self.launch_bar.configure(bg=surface_bg)
        self.left_panel.configure(bg=panel_bg)
        self.right_panel.configure(bg=bg)
        self.video_panel.configure(bg=panel_bg)
        self.clock_row.configure(bg=surface_bg)
        self.clock_view.configure(
            bg=surface_bg,
            fg=fg,
            insertbackground=fg,
            font=(family, max(8, size + FONT_SIZE_OFFSETS["BODY"]), "bold"),
        )
        self.play_pause_button.configure(
            bg=surface_bg,
            fg=fg,
            activebackground=self._theme_color("SELECT_BG"),
            activeforeground=fg,
            font=(family, max(8, size + FONT_SIZE_OFFSETS["BODY"]), "bold"),
        )
        self.playback_rate_button.configure(
            bg=surface_bg,
            fg=fg,
            activebackground=self._theme_color("SELECT_BG"),
            activeforeground=fg,
            font=(family, max(8, size + FONT_SIZE_OFFSETS["BODY"]), "bold"),
        )
        self.playback_rate_menu.configure(
            bg=surface_bg,
            fg=fg,
            activebackground=self._theme_color("SELECT_BG"),
            activeforeground=fg,
        )
        self.caption_now_box.configure(
            bg=surface_bg,
            fg=fg,
            font=(family, size + FONT_SIZE_OFFSETS["BODY"]),
        )
        self.details_frame.configure(bg=surface_bg)
        self.details_title.configure(
            bg=surface_bg,
            fg=fg,
            font=(family, max(8, size + FONT_SIZE_OFFSETS["BODY"]), "bold"),
        )
        self.details_meta.configure(
            bg=surface_bg,
            fg=soft,
            font=(family, max(8, size + FONT_SIZE_OFFSETS["SMALL"])),
        )
        self.details_genre.configure(
            bg=surface_bg,
            fg=self._theme_color("FG_INFO"),
            font=(family, max(8, size + FONT_SIZE_OFFSETS["SMALL"])),
        )
        self.details_description.configure(
            bg=surface_bg,
            fg=soft,
            insertbackground=fg,
            font=(family, max(8, size + FONT_SIZE_OFFSETS["SMALL"])),
        )
        self.root_status_box.configure(bg=surface_bg, fg=fg, font=(family, size))
        self.caption_view.configure(
            bg=panel_bg,
            fg=fg,
            insertbackground=fg,
            font=self._text_font,
        )
        self.caption_view.tag_configure("ts", foreground=muted)
        self.caption_view.tag_configure("txt", foreground=fg)
        self.caption_view.tag_configure("match", foreground=accent)
        self.caption_view.tag_configure("selected", background=self._theme_color("SELECTED_ROW_BG"))
        self.caption_view.tag_configure("selected_txt", font=self._text_font_bold)
        style = ttk.Style(self.root)
        style.configure(
            "Filter.TEntry",
            fieldbackground=surface_alt_bg,
            foreground=fg,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            insertcolor=fg,
            font=(family, max(8, size - 1)),
        )
        style.configure("Terminal.TNotebook", background=bg)
        style.configure(
            "Terminal.TNotebook.Tab",
            background=surface_bg,
            foreground=muted,
            font=(family, max(8, size + FONT_SIZE_OFFSETS["SMALL"])),
        )
        style.map(
            "Terminal.TNotebook.Tab",
            background=[
                ("selected", panel_bg),
                ("active", self._theme_color("SELECT_BG")),
            ],
            foreground=[
                ("selected", fg),
                ("active", soft),
            ],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=surface_bg,
            troughcolor=panel_bg,
            arrowcolor=muted,
            bordercolor=border,
            lightcolor=surface_bg,
            darkcolor=surface_bg,
            gripcount=0,
        )
        style.map(
            "Vertical.TScrollbar",
            background=[
                ("active", self._theme_color("SELECT_BG")),
                ("pressed", accent),
            ],
            arrowcolor=[
                ("active", soft),
                ("pressed", fg),
            ],
        )
        if hasattr(self, "title_label"):
            self.title_label.configure(
                bg=surface_bg,
                fg=soft,
                font=(family, max(8, size + FONT_SIZE_OFFSETS["BODY"]), "bold"),
            )
        if hasattr(self, "title_close"):
            self.title_close.configure(
                bg=surface_bg,
                fg="#000000",
                font=(family, max(8, size + FONT_SIZE_OFFSETS["BODY"]), "bold"),
            )
        if hasattr(self, "video_pause_overlay"):
            self.video_pause_overlay.configure(
                bg=self._theme_color("VIDEO_OVERLAY_BG"),
                fg=self._theme_color("VIDEO_OVERLAY_FG"),
                font=(family, max(18, size + 18), "bold"),
            )
        if hasattr(self, "filter_entry") and hasattr(self.filter_entry, "configure_colors"):
            try:
                self.filter_entry.configure_colors(
                    bg=surface_alt_bg,
                    fg=fg,
                    accent_fg=accent,
                    border=border,
                    font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
                )
            except Exception:
                pass
        for button in getattr(self, "_launch_buttons", []):
            try:
                button.configure(
                    bg=surface_bg,
                    fg="#000000",
                    font=(family, max(8, size + FONT_SIZE_OFFSETS["SMALL"])),
                )
            except Exception:
                pass
        self._apply_root_chrome_settings()
        self._refresh_clock_now()
        self._refresh_transport_controls()
        self._refresh_details_pane()

    def _apply_font_scale_tree(
        self,
        root_widget: tk.Misc | None = None,
        *,
        reset_base: bool = False,
    ) -> None:
        root = root_widget or self.root
        if not root:
            return

        def _visit(widget: tk.Misc) -> None:
            try:
                keys = set(widget.keys())
            except Exception:
                keys = set()
            if "font" in keys:
                try:
                    if reset_base and hasattr(widget, "_alog_base_font"):
                        delattr(widget, "_alog_base_font")
                    base = getattr(widget, "_alog_base_font", None)
                    if base is None:
                        font_obj = tkfont.Font(root=self.root, font=widget.cget("font"))
                        actual = font_obj.actual()
                        base = {
                            "family": str(actual.get("family") or FONT["STYLE"]),
                            "size": int(actual.get("size") or FONT["SIZE"]) - int(self._font_size_delta),
                            "weight": str(actual.get("weight") or "normal"),
                            "slant": str(actual.get("slant") or "roman"),
                            "underline": int(actual.get("underline") or 0),
                            "overstrike": int(actual.get("overstrike") or 0),
                        }
                        setattr(widget, "_alog_base_font", base)
                    new_size = max(8, min(64, int(base["size"]) + int(self._font_size_delta)))
                    desired_family = str(self._ai_settings.get("font_family") or FONT["STYLE"])
                    parts: list[Any] = [desired_family, new_size]
                    if str(base.get("weight")) == "bold":
                        parts.append("bold")
                    if str(base.get("slant")) == "italic":
                        parts.append("italic")
                    if int(base.get("underline") or 0):
                        parts.append("underline")
                    if int(base.get("overstrike") or 0):
                        parts.append("overstrike")
                    widget.configure(font=tuple(parts))
                except Exception:
                    pass
            for child in widget.winfo_children():
                _visit(child)

        _visit(root)
