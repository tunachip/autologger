from __future__ import annotations

import tkinter as tk

import vlc

from .constants import FONT, FONT_SIZE_OFFSETS, ICONS, PLAYBACK_SPEEDS, THEME


class PlayerChromeMixin:
    def _build_player_chrome(self) -> None:
        self.left_panel.rowconfigure(0, weight=1)
        self.left_panel.columnconfigure(0, weight=1)
        self.video_panel = tk.Frame(
            self.left_panel,
            bg=THEME["PANEL_BG"],
            highlightthickness=0,
            bd=0,
        )
        self.video_panel.grid(row=0, column=0, sticky="nsew")
        self.video_pause_overlay = tk.Label(
            self.left_panel,
            text=ICONS["PAUSE"],
            anchor="center",
            justify="center",
            bg=self._theme_color("VIDEO_OVERLAY_BG"),
            fg=self._theme_color("VIDEO_OVERLAY_FG"),
            font=self._ui_font(18, bold=True),
            padx=18,
            pady=8,
        )
        self.video_pause_overlay.place_forget()
        self._build_transport_row()
        self._build_caption_now_box()
        self._build_details_pane()
        self.left_panel.bind("<Configure>", self._on_left_resize)

    def _build_transport_row(self) -> None:
        self.clock_row = tk.Frame(
            self.left_panel,
            bg=THEME["SURFACE_BG"],
            highlightthickness=0,
            bd=0,
        )
        self.clock_row.grid(row=2, column=0, sticky="ew")
        self.clock_row.columnconfigure(1, weight=1)
        self.play_pause_button = tk.Button(
            self.clock_row,
            text=ICONS["PLAY"],
            command=lambda: self._on_toggle_play(None),
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG"],
            activebackground=THEME["SELECT_BG"],
            activeforeground=THEME["FG"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=10,
            pady=6,
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["BODY"], "bold"),
            cursor="hand2",
        )
        self.play_pause_button.grid(row=0, column=0, sticky="w")
        self.clock_view = tk.Text(
            self.clock_row,
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG_ACCENT"],
            borderwidth=0,
            highlightthickness=0,
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["BODY"], "bold"),
            wrap="none",
            height=1,
            padx=10,
            pady=6,
            cursor="hand2",
            insertbackground=THEME["FG_ACCENT"],
        )
        self.clock_view.grid(row=0, column=1, sticky="ew")
        self.clock_view.configure(state="disabled")
        self.clock_view.bind("<Button-1>", self._on_click_clock_progress)
        self.playback_rate_var = tk.StringVar(value="1.00x")
        self.playback_rate_button = tk.Menubutton(
            self.clock_row,
            textvariable=self.playback_rate_var,
            direction="below",
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG"],
            activebackground=THEME["SELECT_BG"],
            activeforeground=THEME["FG"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=10,
            pady=6,
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["BODY"], "bold"),
            cursor="hand2",
        )
        self.playback_rate_button.grid(row=0, column=2, sticky="e")
        self.playback_rate_menu = tk.Menu(
            self.playback_rate_button,
            tearoff=False,
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG"],
            activebackground=THEME["SELECT_BG"],
            activeforeground=THEME["FG"],
            bd=0,
        )
        self.playback_rate_button.configure(menu=self.playback_rate_menu)
        for speed in PLAYBACK_SPEEDS:
            self.playback_rate_menu.add_command(
                label=f"{speed:.2f}x",
                command=lambda value=speed: self._set_playback_rate(value),
            )

    def _build_caption_now_box(self) -> None:
        self.caption_now_var = tk.StringVar(value="")
        self.caption_now_box = tk.Label(
            self.left_panel,
            textvariable=self.caption_now_var,
            anchor="w",
            justify="left",
            bg=THEME["PANEL_BG"],
            fg=THEME["FG"],
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["BODY"]),
            padx=10,
            pady=8,
            wraplength=400,
        )
        self.caption_now_box.grid(row=1, column=0, sticky="ew")

    def _build_details_pane(self) -> None:
        self.details_frame = tk.Frame(
            self.left_panel,
            bg=THEME["SURFACE_BG"],
            highlightthickness=0,
            bd=0,
        )
        self.details_frame.grid(row=3, column=0, sticky="ew")
        self.details_frame.columnconfigure(0, weight=1)
        self.details_title_var = tk.StringVar(value="")
        self.details_meta_var = tk.StringVar(value="")
        self.details_genre_var = tk.StringVar(value="")
        self.details_title = tk.Label(
            self.details_frame,
            textvariable=self.details_title_var,
            anchor="w",
            justify="left",
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG"],
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["BODY"], "bold"),
            padx=10,
            pady=4,
            wraplength=400,
        )
        self.details_title.grid(row=0, column=0, sticky="ew")
        self.details_meta = tk.Label(
            self.details_frame,
            textvariable=self.details_meta_var,
            anchor="w",
            justify="left",
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG_SOFT"],
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["SMALL"]),
            padx=10,
            pady=2,
            wraplength=400,
        )
        self.details_meta.grid(row=1, column=0, sticky="ew")
        self.details_genre = tk.Label(
            self.details_frame,
            textvariable=self.details_genre_var,
            anchor="w",
            justify="left",
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG_INFO"],
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["SMALL"]),
            padx=10,
            pady=2,
            wraplength=400,
        )
        self.details_genre.grid(row=2, column=0, sticky="ew")
        self.details_description = tk.Text(
            self.details_frame,
            bg=THEME["SURFACE_BG"],
            fg=THEME["FG_SOFT"],
            borderwidth=0,
            highlightthickness=0,
            font=(FONT["STYLE"], FONT["SIZE"] + FONT_SIZE_OFFSETS["SMALL"]),
            wrap="word",
            padx=10,
            pady=6,
            height=6,
        )
        self.details_description.grid(row=3, column=0, sticky="ew")
        self.details_description.configure(state="disabled")

    def _position_video_overlay(self) -> None:
        if not hasattr(self, "video_pause_overlay") or not hasattr(self, "video_panel"):
            return
        try:
            panel_x = int(self.video_panel.winfo_x())
            panel_y = int(self.video_panel.winfo_y())
            panel_w = int(self.video_panel.winfo_width())
            panel_h = int(self.video_panel.winfo_height())
        except Exception:
            return
        if panel_w <= 0 or panel_h <= 0:
            self.video_pause_overlay.place_forget()
            return
        self.video_pause_overlay.place(
            x=panel_x + (panel_w // 2),
            y=panel_y + (panel_h // 2),
            anchor="center",
        )

    def _refresh_pause_overlay(self, state: vlc.State | None = None) -> None:
        if not hasattr(self, "video_pause_overlay"):
            return
        if not self.video_path:
            self.video_pause_overlay.place_forget()
            return
        try:
            current = state if state is not None else self.player.get_state()
        except Exception:
            current = None
        if current in {vlc.State.Paused, vlc.State.Stopped}:
            self._position_video_overlay()
            self.video_pause_overlay.lift()
            return
        self.video_pause_overlay.place_forget()

    def _refresh_transport_controls(self) -> None:
        if not hasattr(self, "play_pause_button"):
            return
        icon = ICONS["PLAY"]
        try:
            state = self.player.get_state()
        except Exception:
            state = None
        if state == vlc.State.Playing:
            icon = ICONS["PAUSE"]
        self.play_pause_button.configure(text=icon)
        self.playback_rate_var.set(f"{float(getattr(self, '_playback_rate', 1.0)):.2f}x")

    def _set_playback_rate(self, value: float) -> None:
        rate = max(0.25, min(4.0, float(value)))
        self._playback_rate = rate
        try:
            self.player.set_rate(rate)
        except Exception:
            pass
        self._refresh_transport_controls()
        self.status_var.set(f"Speed {rate:.2f}x")

    def _refresh_details_pane(self) -> None:
        if not hasattr(self, "details_frame"):
            return
        title = ""
        meta = ""
        genre_text = ""
        description = ""
        video_id = str(getattr(self, "current_video_id", None) or "").strip()
        if video_id:
            try:
                row = self.ingester.db.get_video(video_id) or {}
            except Exception:
                row = {}
            payload = self._row_metadata_payload(row)
            title = str(row.get("title") or video_id).strip()
            creator = str(row.get("channel") or row.get("uploader_id") or "unknown").strip().lstrip("@")
            length = self._metadata_text_for_field(row, "LENGTH").split(" ", 1)[-1].strip() or "--:--"
            meta = f"{creator} | {length}"
            genre_value = self._display_genre_text(row)
            genre_text = f"genre: {genre_value}" if genre_value else "genre: (none)"
            summary = str(payload.get("summary") or "").strip()
            raw_description = str(payload.get("description") or "").strip()
            clean_description = "\n".join(
                line for line in raw_description.splitlines()
                if line.strip("- ").strip()
            ).strip()
            description = summary or clean_description
        self.details_title_var.set(title)
        self.details_meta_var.set(meta)
        self.details_genre_var.set(genre_text)
        self.details_description.configure(state="normal")
        self.details_description.delete("1.0", tk.END)
        self.details_description.insert("1.0", description or "(no details)")
        self.details_description.configure(state="disabled")
