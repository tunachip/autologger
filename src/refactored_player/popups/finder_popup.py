from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from alog.pipeline import resolve_playback_media_path

from ..constants import FONT_SIZE_OFFSETS, POPUP_SIZES


class FinderPopupMixin:
    def _open_search_popup(self) -> None:
        popup = self._create_popup_window(
            name="finder",
            title="Search DB",
            size=POPUP_SIZES["PICKER"],
            attr_name="_search_popup",
            reuse_existing=True,
            row_weights={2: 1},
            column_weights={0: 1},
        )
        if popup is None:
            return
        content = self._popup_content(popup)

        query_var = tk.StringVar(
            value=self.filter_var.get().strip()
            or self._default_query_text("finder_default_field", "ts")
        )
        query_row = tk.Frame(content, bg=self._theme_color("SURFACE_BG"))
        query_row.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        query_row.columnconfigure(0, weight=1)
        query_entry = self._create_query_entry(
            query_row,
            query_var,
            enable_field_completion=True,
        )
        query_entry.grid(row=0, column=0, sticky="ew")
        fields_button = tk.Menubutton(
            query_row,
            text="⚙",
            direction="below",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_SOFT"),
            activebackground=self._theme_color("SELECT_BG"),
            activeforeground=self._theme_color("FG"),
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=8,
            pady=4,
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
        )
        fields_button.grid(row=0, column=1, sticky="e", padx=(8, 0))

        body = tk.Frame(content, bg=self._theme_color("APP_BG"))
        body.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=0, minsize=360)
        body.columnconfigure(1, weight=1)

        preview = self._build_video_preview_pane(body)
        preview["frame"].grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_shell = tk.Frame(
            body,
            bg=self._theme_color("PANEL_BG"),
            highlightthickness=1,
            highlightbackground=self._theme_color("BORDER"),
            bd=0,
        )
        list_shell.grid(row=0, column=1, sticky="nsew")
        list_shell.columnconfigure(0, weight=1)
        list_shell.rowconfigure(0, weight=1)
        pane_strip = tk.PanedWindow(
            list_shell,
            orient="horizontal",
            sashwidth=8,
            sashrelief="flat",
            showhandle=False,
            bg=self._theme_color("PANEL_BG"),
            bd=0,
            relief="flat",
            opaqueresize=True,
        )
        pane_strip.grid(row=0, column=0, sticky="nsew")
        title_scroll = ttk.Scrollbar(list_shell, orient="vertical")
        title_scroll.grid(row=0, column=1, sticky="ns")

        hint = tk.Label(
            content,
            text=self._status_hint("search"),
            anchor="w",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_MUTED"),
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
            padx=8,
            pady=6,
        )
        hint.grid(row=3, column=0, sticky="ew")
        field_layout_signature = {"value": ()}
        row_ids: list[str] = []
        selected_index = {"value": 0}
        field_texts: dict[str, tk.Text] = {}
        field_frames: dict[str, tk.Frame] = {}
        ysync = {"active": False}

        def _selected_video_id() -> str:
            if 0 <= selected_index["value"] < len(row_ids):
                return row_ids[selected_index["value"]]
            return ""

        def _sync_scroll_from(source: str, first: str, last: str) -> None:
            if ysync["active"]:
                return
            ysync["active"] = True
            try:
                title_scroll.set(first, last)
                frac = float(first)
                for field, widget in field_texts.items():
                    if field != source:
                        widget.yview_moveto(frac)
            finally:
                ysync["active"] = False

        def _scroll_all(*args: object) -> None:
            for widget in field_texts.values():
                widget.yview(*args)

        def _scroll_units(units: int) -> str:
            if not units:
                return "break"
            for widget in field_texts.values():
                widget.yview_scroll(units, "units")
            return "break"

        def _mousewheel_units(event: tk.Event[tk.Misc]) -> int:
            delta = int(getattr(event, "delta", 0))
            if delta:
                return -1 if delta > 0 else 1
            num = int(getattr(event, "num", 0))
            if num == 4:
                return -1
            if num == 5:
                return 1
            return 0

        title_scroll.configure(command=_scroll_all)

        def _search_field_value(row: dict[str, object], field: str) -> str:
            token = str(field or "").strip().lower()
            if token == "matches":
                return str(int(row.get("match_count") or 0))
            return self._picker_field_value(row, token)

        def _finder_columns() -> list[tuple[str, str, int]]:
            widths = self._picker_field_widths_for("finder")
            columns: list[tuple[str, str, int]] = [("matches", "Matches", int(widths.get("matches") or 130))]
            for field, label, width in self._picker_columns_for("finder"):
                columns.append((field, label.rsplit(" ", 1)[0] if " " in label else label, int(width)))
            return columns

        def _store_finder_widths() -> None:
            widths = dict(self._picker_field_widths_for("finder"))
            changed = False
            for field, frame in field_frames.items():
                width = int(frame.winfo_width())
                if width > 0 and widths.get(field) != width:
                    widths[field] = width
                    changed = True
            if changed:
                self._set_picker_field_widths("finder", widths)

        def _rebuild_field_panes() -> None:
            columns = _finder_columns()
            layout_signature = tuple((field, label) for field, label, _width in columns)
            if field_texts and layout_signature == field_layout_signature["value"]:
                return
            field_layout_signature["value"] = layout_signature
            field_texts.clear()
            field_frames.clear()
            for pane in pane_strip.panes():
                pane_strip.forget(pane)
            saved_widths = self._picker_field_widths_for("finder")
            for field, label, width in columns:
                frame = tk.Frame(pane_strip, bg=self._theme_color("PANEL_BG"), bd=0, highlightthickness=0)
                frame.rowconfigure(1, weight=1)
                frame.columnconfigure(0, weight=1)
                header = tk.Frame(
                    frame,
                    bg=self._theme_color("PANEL_BG"),
                    highlightthickness=1,
                    highlightbackground=self._theme_color("BORDER"),
                    bd=0,
                )
                header.grid(row=0, column=0, sticky="ew")
                tk.Label(
                    header,
                    text=label,
                    anchor="w",
                    bg=self._theme_color("PANEL_BG"),
                    fg=self._theme_color("FG_MUTED"),
                    font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
                    padx=8,
                    pady=4,
                ).pack(fill="x")
                field_text = tk.Text(
                    frame,
                    bg=self._theme_color("PANEL_BG"),
                    fg=self._theme_color("FG_ACCENT") if field == "matches" else self._theme_color("FG"),
                    insertbackground=self._theme_color("FG"),
                    borderwidth=0,
                    highlightthickness=0,
                    wrap="none",
                    state="disabled",
                    cursor="arrow",
                    padx=8,
                    pady=4,
                    font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
                )
                field_text.grid(row=1, column=0, sticky="nsew")
                field_text.configure(yscrollcommand=lambda first, last, name=field: _sync_scroll_from(name, first, last))
                field_text.bind(
                    "<ButtonRelease-1>",
                    lambda event, widget=field_text: _set_selection(
                        max(0, int(str(widget.index(f"@0,{event.y}")).split(".", 1)[0]) - 1)
                    ),
                    add="+",
                )
                field_text.bind("<Double-Button-1>", open_selected, add="+")
                field_text.bind("<Return>", open_selected, add="+")
                field_text.bind("<Up>", lambda _e: move_sel(-1), add="+")
                field_text.bind("<Down>", lambda _e: move_sel(1), add="+")
                field_text.bind("<Home>", lambda _e: move_sel(-10_000), add="+")
                field_text.bind("<End>", lambda _e: move_sel(10_000), add="+")
                field_text.bind("<Prior>", lambda _e: move_sel(-10), add="+")
                field_text.bind("<Next>", lambda _e: move_sel(10), add="+")
                field_text.bind("<MouseWheel>", lambda event: _scroll_units(_mousewheel_units(event)), add="+")
                field_text.bind("<Button-4>", lambda event: _scroll_units(_mousewheel_units(event)), add="+")
                field_text.bind("<Button-5>", lambda event: _scroll_units(_mousewheel_units(event)), add="+")
                pane_strip.add(
                    frame,
                    minsize=0,
                    width=max(1, int(saved_widths.get(field, width))),
                    stretch="always",
                )
                field_frames[field] = frame
                field_texts[field] = field_text
            pane_strip.bind("<ButtonRelease-1>", lambda _e: _store_finder_widths(), add="+")
            self.root.after_idle(_store_finder_widths)

        def _set_selection(idx: int) -> None:
            if not row_ids:
                return
            idx = max(0, min(idx, len(row_ids) - 1))
            selected_index["value"] = idx
            specs = self._picker_highlight_specs(query_var.get().strip(), ["title", "creator", "length"])
            for widget in field_texts.values():
                widget.configure(state="normal")
                widget.tag_remove("selected_row", "1.0", tk.END)
                widget.tag_add("selected_row", f"{idx + 1}.0", f"{idx + 1}.end")
                widget.tag_lower("selected_row")
                for spec_idx, _spec in enumerate(specs):
                    widget.tag_raise(f"match_{spec_idx}")
                widget.configure(state="disabled")
                widget.see(f"{idx + 1}.0")
            row = next(
                (item for item in self._search_results if str(item.get("video_id") or "") == _selected_video_id()),
                None,
            )
            if row is not None:
                self._render_video_preview(
                    row,
                    image_box=preview["image_box"],
                    image_label=preview["image_label"],
                    title_var=preview["title_var"],
                    creator_var=preview["creator_var"],
                    genre_var=preview["genre_var"],
                    description_widget=preview["description"],
                    photo_ref=preview["photo_ref"],
                    image_size=preview["image_size"],
                )

        def refresh_results(*_args: object) -> None:
            query = query_var.get().strip()
            selected_video_id = _selected_video_id()
            _rebuild_field_panes()
            specs = self._picker_highlight_specs(query, ["title", "creator", "length"])
            for field, widget in field_texts.items():
                widget.configure(state="normal")
                widget.delete("1.0", tk.END)
                widget.tag_configure(
                    "selected_row",
                    background=self._theme_color("SELECTED_ROW_BG"),
                    foreground=self._theme_color("FG_ACCENT") if field == "matches" else self._theme_color("FG"),
                )
                for idx, (_targets, _terms, color) in enumerate(specs):
                    widget.tag_configure(f"match_{idx}", foreground=color)
            self._search_results = []
            row_ids.clear()
            if not query:
                return
            rows = self._search_videos_with_query(query, limit=200)
            self._search_results = [dict(r) for r in rows]
            selected_idx = 0
            for row_idx, row in enumerate(self._search_results):
                row_ids.append(str(row.get("video_id") or ""))
                for field in field_texts:
                    widget = field_texts[field]
                    cell_text = " ".join(str(_search_field_value(row, field) or "").split())
                    line_no = int(widget.index("end-1c").split(".", 1)[0])
                    widget.insert(tk.END, cell_text + "\n")
                    if field in {"title", "creator", "length"}:
                        cell_lower = cell_text.lower()
                        for spec_idx, (target_fields, terms, _color) in enumerate(specs):
                            if field not in target_fields:
                                continue
                            for term in terms:
                                token = str(term or "").strip().lower()
                                if not token:
                                    continue
                                start_at = 0
                                while True:
                                    found = cell_lower.find(token, start_at)
                                    if found < 0:
                                        break
                                    widget.tag_add(
                                        f"match_{spec_idx}",
                                        f"{line_no}.{found}",
                                        f"{line_no}.{found + len(token)}",
                                    )
                                    start_at = found + len(token)
                if selected_video_id and str(row.get("video_id") or "").strip() == selected_video_id:
                    selected_idx = row_idx
            if self._search_results:
                for field, widget in field_texts.items():
                    for idx, _spec in enumerate(specs):
                        widget.tag_raise(f"match_{idx}")
                    widget.configure(state="disabled")
                _set_selection(selected_idx)

        def open_selected(_event: tk.Event[tk.Misc] | None = None) -> str:
            if not row_ids:
                return "break"
            idx = int(selected_index["value"])
            if idx < 0 or idx >= len(self._search_results):
                return "break"
            row = self._search_results[idx]
            query = query_var.get().strip()
            video_id = str(row.get("video_id") or "")
            transcript_path = Path(str(row.get("transcript_json_path") or ""))
            preferred = Path(str(row.get("local_video_path") or "")) if row.get("local_video_path") else None
            if not transcript_path.exists():
                self.status_var.set(f"Missing transcript for {video_id}")
                return "break"
            try:
                video_path = resolve_playback_media_path(
                    self.ingester_config,
                    video_id=video_id,
                    preferred_path=preferred,
                )
            except Exception as exc:
                self.status_var.set(f"Playback path error: {exc}")
                return "break"
            audio_path = self._find_audio_sidecar(video_id, video_path)
            start_sec = float(int(row.get("first_start_ms") or 0)) / 1000.0
            self._load_session(
                video_id=video_id,
                transcript_json=transcript_path,
                video_path=video_path,
                audio_path=audio_path,
                start_sec=start_sec,
                filter_text=query,
            )
            popup.destroy()
            self._search_popup = None
            self.filter_entry.focus_set()
            return "break"

        def move_sel(delta: int) -> str:
            _set_selection(selected_index["value"] + delta)
            return "break"

        query_var.trace_add("write", refresh_results)
        self._attach_picker_fields_menu(
            fields_button,
            picker_name="finder",
            on_change=refresh_results,
        )
        self._bind_popup_close(
            popup,
            after_close=lambda: setattr(self, "_search_popup", None),
        )
        self._bind_fzf_like_keys(
            popup,
            entry=query_entry,
            capture_widgets=[query_entry],
            on_enter=lambda: open_selected(),
            on_up=lambda: move_sel(-1),
            on_down=lambda: move_sel(1),
            on_home=lambda: move_sel(-10_000),
            on_end=lambda: move_sel(10_000),
            on_page_up=lambda: move_sel(-10),
            on_page_down=lambda: move_sel(10),
        )
        try:
            popup.update_idletasks()
            preview["frame"].update_idletasks()
            preview["image_box"].update_idletasks()
        except Exception:
            pass
        refresh_results()
        self._focus_popup_entry(popup, query_entry)
