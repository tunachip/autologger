from __future__ import annotations

from typing import Callable

import tkinter as tk

from .constants import FONT, FONT_SIZE_OFFSETS, LAYOUT, THEME


class RootChromeMixin:
    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=0)
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(3, weight=0)
        self._build_root_top_bars()
        self._build_shell_layout()
        self._build_player_chrome()
        self._build_transcript_layout()
        self._bind_window_controls()
        self.root.bind("<Configure>", self._on_root_configure, add="+")
        self._apply_root_chrome_settings()

    def _build_root_top_bars(self) -> None:
        self.title_bar = tk.Frame(
            self.root,
            bg=THEME["SURFACE_BG"],
            height=LAYOUT["TITLEBAR_HEIGHT"],
            highlightthickness=0,
            bd=0,
        )
        self.title_bar.grid(row=0, column=0, sticky="ew")
        self.title_bar.grid_propagate(False)
        self.title_bar.columnconfigure(0, weight=1)
        self.title_bar.columnconfigure(1, weight=0)
        self.title_label = tk.Label(
            self.title_bar,
            text="Alogger Player",
            anchor="w",
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG_SOFT"],
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["BODY"], "bold"),
            padx=LAYOUT["BAR_PAD_X"],
            pady=LAYOUT["BAR_PAD_Y"],
        )
        self.title_label.grid(row=0, column=0, sticky="ew")
        self.title_close = tk.Label(
            self.title_bar,
            text="x",
            anchor="center",
            bg=THEME["SURFACE_BG"],
            fg="#000000",
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["BODY"], "bold"),
            padx=LAYOUT["BAR_PAD_X"],
            pady=LAYOUT["BAR_PAD_Y"],
            cursor="hand2",
        )
        self.title_close.grid(row=0, column=1, sticky="e")
        self.launch_bar = tk.Frame(
            self.root,
            bg=THEME["SURFACE_BG"],
            height=LAYOUT["LAUNCHBAR_HEIGHT"],
            highlightthickness=0,
            bd=0,
        )
        self.launch_bar.grid(row=1, column=0, sticky="ew")
        self.launch_bar.grid_propagate(False)
        self.launch_bar.columnconfigure(99, weight=1)
        launchers: list[tuple[str, Callable[[], None]]] = [
            ("Cmd", lambda: self._toggle_popup("command", self._open_command_popup)),
            ("Ingest", lambda: self._toggle_popup("ingest", self._open_ingest_popup)),
            ("Workflows", lambda: self._toggle_popup("workers", self._open_jobs_popup)),
            ("Open", lambda: self._toggle_popup("open_video", self._open_video_picker_popup)),
            ("Find", lambda: self._toggle_popup("finder", self._open_search_popup)),
            ("AI", lambda: self._toggle_popup("ai", self._open_ai_popup)),
            ("Goto", self._open_goto_popup),
            ("Settings", lambda: self._toggle_popup("settings", self._open_settings_popup)),
            ("Browse", lambda: self._toggle_popup("channel", self._open_channel_popup)),
            ("Subs", lambda: self._toggle_popup("subscriptions", self._open_subscriptions_popup)),
        ]
        self._launch_buttons = []
        for idx, (label, command) in enumerate(launchers):
            button = tk.Label(
                self.launch_bar,
                text=label,
                anchor="center",
                bg=THEME["SURFACE_BG"],
                fg="#000000",
                font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["SMALL"]),
                padx=LAYOUT["BAR_PAD_X"],
                pady=LAYOUT["BAR_PAD_Y"],
                cursor="hand2",
            )
            button.grid(row=0, column=idx, sticky="w", padx=(0 if idx == 0 else 2, 0))
            button.bind("<Button-1>", lambda _e, fn=command: fn(), add="+")
            button.bind("<Enter>", lambda e: e.widget.configure(fg=self._theme_color("FG_ACCENT")), add="+")
            button.bind("<Leave>", lambda e: e.widget.configure(fg="#000000"), add="+")
            self._launch_buttons.append(button)
        self.title_close.bind("<Enter>", lambda e: e.widget.configure(fg=self._theme_color("FG_ACCENT")), add="+")
        self.title_close.bind("<Leave>", lambda e: e.widget.configure(fg="#000000"), add="+")

    def _build_shell_layout(self) -> None:
        self.shell = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            sashrelief=tk.FLAT,
            sashwidth=LAYOUT["SASH_WIDTH"],
            bg=THEME["APP_BG"],
            bd=0,
            relief="flat",
            showhandle=False,
        )
        self.shell.grid(row=2, column=0, sticky="nsew")
        self.left_panel = tk.Frame(self.shell, bg=THEME["PANEL_BG"])
        self.right_panel = tk.Frame(self.shell, bg=THEME["APP_BG"])
        self.shell.add(self.left_panel, minsize=0)
        self.shell.add(self.right_panel, minsize=0)
        self.shell.bind("<Configure>", self._on_shell_configure)
        self.root.after(0, self._set_initial_split_ratio)

    def _build_transcript_layout(self) -> None:
        self.status_var = tk.StringVar(value="Idle")
        self.root_status_box = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG_SOFT"],
            font=(FONT["STYLE"], FONT["SIZE"]),
            padx=10,
            pady=6,
        )
        self.root_status_box.grid(row=3, column=0, sticky="ew")
        self.right_panel.rowconfigure(1, weight=1)
        self.right_panel.columnconfigure(0, weight=1)
        self.filter_var = tk.StringVar()
        self.filter_entry = self._create_query_entry(self.right_panel, self.filter_var)
        self.filter_entry.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        self.caption_view = tk.Text(
            self.right_panel,
            bg=THEME["PANEL_BG"],
            fg=THEME["FG"],
            borderwidth=0,
            highlightthickness=0,
            font=self._text_font,
            wrap="word",
            padx=8,
            pady=8,
            insertbackground=THEME["FG"],
        )
        self.caption_view.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.caption_view.configure(state="disabled")
        self.caption_view.tag_configure("row", lmargin1=0, lmargin2=self._wrap_indent_px)
        self.caption_view.tag_configure("ts", foreground=THEME["FG_MUTED"])
        self.caption_view.tag_configure("txt", foreground=THEME["FG"])
        self.caption_view.tag_configure("match", foreground=THEME["FG_ACCENT"])
        self.caption_view.tag_configure("selected", background="#282828")
        self.caption_view.tag_configure("selected_txt", font=self._text_font_bold)
        self._row_ranges: list[tuple[str, str]] = []
        self._row_text_ranges: list[tuple[str, str]] = []

    def _bind_window_controls(self) -> None:
        for widget in (self.title_bar, self.title_label):
            widget.bind("<ButtonPress-1>", self._on_begin_window_drag, add="+")
            widget.bind("<B1-Motion>", self._on_window_drag, add="+")
            widget.bind("<Double-Button-1>", self._on_toggle_window_maximize, add="+")
        self.title_close.bind("<Button-1>", lambda _e: self.close(), add="+")

    def _bind_ctrl_i_conflicts(self) -> None:
        def _handle(event: tk.Event[tk.Misc]) -> str:
            state = int(getattr(event, "state", 0))
            if state & 0x4:
                return self._on_toggle_jobs_popup(event)
            return "break"

        for widget in (self.filter_entry, self.caption_view, self.details_description):
            widget.bind("<Control-i>", _handle, add="+")
            widget.bind("<Tab>", _handle, add="+")

    def _apply_root_chrome_settings(self) -> None:
        show_root_top_bar = bool(self._ai_settings.get("show_root_top_bar", True))
        show_launch_bar = bool(self._ai_settings.get("show_launch_bar", True))
        if hasattr(self, "title_bar"):
            if show_root_top_bar:
                self.title_bar.grid()
            else:
                self.title_bar.grid_remove()
        if hasattr(self, "launch_bar"):
            if show_launch_bar:
                self.launch_bar.grid()
            else:
                self.launch_bar.grid_remove()
        self._schedule_root_layout_refresh()

    def _on_root_configure(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is not self.root:
            return
        self._schedule_root_layout_refresh()

    def _schedule_root_layout_refresh(self) -> None:
        if self._root_layout_after_id is not None:
            try:
                self.root.after_cancel(self._root_layout_after_id)
            except Exception:
                pass
        self._root_layout_after_id = self.root.after(30, self._refresh_root_layout)

    def _refresh_root_layout(self) -> None:
        self._root_layout_after_id = None
        if not hasattr(self, "shell"):
            return
        try:
            self.root.update_idletasks()
            total_w = int(self.shell.winfo_width())
            total_h = int(self.shell.winfo_height())
        except Exception:
            return
        if total_w > 0 and total_h > 0:
            self._apply_shell_layout(total_w, total_h)
        self._position_video_overlay()

    def _on_begin_window_drag(self, event: tk.Event[tk.Misc]) -> str:
        self._drag_origin_x = int(getattr(event, "x_root", 0))
        self._drag_origin_y = int(getattr(event, "y_root", 0))
        self._window_origin_x = int(self.root.winfo_x())
        self._window_origin_y = int(self.root.winfo_y())
        return "break"

    def _on_window_drag(self, event: tk.Event[tk.Misc]) -> str:
        delta_x = int(getattr(event, "x_root", 0)) - self._drag_origin_x
        delta_y = int(getattr(event, "y_root", 0)) - self._drag_origin_y
        width = max(1, int(self.root.winfo_width()))
        height = max(1, int(self.root.winfo_height()))
        x = self._window_origin_x + delta_x
        y = self._window_origin_y + delta_y
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        return "break"

    def _on_toggle_window_maximize(self, _event: tk.Event[tk.Misc]) -> str:
        try:
            current = bool(self.root.wm_attributes("-zoomed"))
            self.root.wm_attributes("-zoomed", not current)
        except Exception:
            pass
        return "break"
