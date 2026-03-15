from __future__ import annotations

import tkinter as tk

from ..constants import FONT_SIZE_OFFSETS, POPUP_SIZES
from ..models import PickerTable


class QueuePickerPopupMixin:
    def _open_queue_picker_popup(self, queue_stage: str) -> None:
        stage = str(queue_stage or "transcribe").strip().lower()
        if stage not in {"transcribe", "summarize"}:
            stage = "transcribe"
        if self._jobs_popup and self._jobs_popup.winfo_exists():
            self._close_jobs_popup()
        popup = self._create_popup_window(
            name="queue_picker",
            title=f"Queue Videos: {stage.title()}",
            size=POPUP_SIZES["PICKER"],
            attr_name="_queue_picker_popup",
            reuse_existing=True,
            row_weights={2: 1},
            column_weights={0: 1},
        )
        if popup is None:
            return
        content = self._popup_content(popup)

        query_var = tk.StringVar(value="")
        query_entry = self._create_query_entry(
            content,
            query_var,
            enable_field_completion=True,
        )
        query_entry.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))

        header_row = tk.Frame(content, bg=self._theme_color("SURFACE_BG"))
        header_row.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        header_row.columnconfigure(0, weight=1)
        header = tk.Label(
            header_row,
            text=f"Queue {stage.title()}",
            anchor="w",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_MUTED"),
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
            padx=8,
            pady=4,
        )
        header.grid(row=0, column=0, sticky="ew")
        fields_button = tk.Menubutton(
            header_row,
            text="Fields",
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
        fields_button.grid(row=0, column=1, sticky="e")

        body = tk.Frame(content, bg=self._theme_color("APP_BG"))
        body.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=0, minsize=360)
        body.columnconfigure(1, weight=1)

        preview = self._build_video_preview_pane(body)
        preview["frame"].grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        title_list = PickerTable(
            body,
            columns=self._picker_columns_for("queue_picker"),
            bg=self._theme_color("PANEL_BG"),
            fg=self._theme_color("FG"),
            muted_fg=self._theme_color("FG_MUTED"),
            border=self._theme_color("BORDER"),
            select_bg=self._theme_color("SELECTED_ROW_BG"),
            select_fg=self._theme_color("FG"),
            retained_bg=self._darken_hex_color(self._theme_color("SELECTED_ROW_BG")),
            retained_fg=self._theme_color("FG"),
            font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
            heading_font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
            on_widths_changed=lambda widths: self._set_picker_field_widths("queue_picker", widths),
            on_heading_click=lambda field: (self._cycle_picker_sort_field("queue_picker", field, reverse=False), refresh_results()),
            on_heading_right_click=lambda field: (self._cycle_picker_sort_field("queue_picker", field, reverse=True), refresh_results()),
        )
        title_list.grid(row=0, column=1, sticky="nsew")

        status_var = tk.StringVar(value=self._status_hint("queue_picker"))
        self._create_status_label(
            content,
            status_var,
            fg=self._theme_color("FG_SOFT"),
            font_delta=-3,
        ).grid(row=3, column=0, sticky="ew")

        selected_indexes: set[int] = set()
        current_index = {"value": 0}
        rows_state: list[dict[str, object]] = []

        def _apply_state() -> None:
            if rows_state:
                idx = max(0, min(current_index["value"], len(rows_state) - 1))
                current_index["value"] = idx
                current_video_id = str(rows_state[idx].get("video_id") or "")
                title_list.select_item_id(current_video_id)
                title_list.set_retained(
                    {
                        str(rows_state[row_idx].get("video_id") or "")
                        for row_idx in selected_indexes
                        if 0 <= row_idx < len(rows_state)
                    }
                )
                self._render_video_preview(
                    rows_state[idx],
                    image_box=preview["image_box"],
                    image_label=preview["image_label"],
                    title_var=preview["title_var"],
                    creator_var=preview["creator_var"],
                    genre_var=preview["genre_var"],
                    description_widget=preview["description"],
                    photo_ref=preview["photo_ref"],
                    image_size=preview["image_size"],
                )

        def _move_cursor(delta: int, *, add_current: bool = False) -> str:
            if not rows_state:
                return "break"
            cur = current_index["value"]
            if add_current:
                selected_indexes.add(cur)
            nxt = max(0, min(cur + delta, len(rows_state) - 1))
            current_index["value"] = nxt
            _apply_state()
            return "break"

        def _queue_selected(_event: tk.Event[tk.Misc] | None = None) -> str:
            if not rows_state:
                status_var.set("No rows available")
                return "break"
            targets = set(selected_indexes)
            targets.add(current_index["value"])
            queued = 0
            skipped = 0
            for idx in sorted(targets):
                if idx < 0 or idx >= len(rows_state):
                    continue
                video_id = str(rows_state[idx].get("video_id") or "").strip()
                if not video_id:
                    skipped += 1
                    continue
                try:
                    if stage == "transcribe":
                        result = self.ingester.enqueue_video_for_transcription(video_id)
                    else:
                        result = self.ingester.enqueue_video_for_summary(video_id)
                    if bool(result.get("queued", False)):
                        queued += 1
                    else:
                        skipped += 1
                except Exception:
                    skipped += 1
            status_var.set(f"Queued {queued} to {stage}; skipped {skipped}")
            return "break"

        def refresh_results(*_args: object) -> None:
            query = query_var.get().strip()
            previous_video_id = title_list.selected_item_id()
            title_list.configure_columns(self._picker_columns_for("queue_picker"))
            rows_state.clear()
            rows_state.extend(
                self._sort_picker_rows(
                    [dict(r) for r in self._search_video_titles_with_query(query, limit=300)],
                    "queue_picker",
                )
            )
            selected_indexes.clear()
            current_index["value"] = 0
            title_list.replace_rows(
                [
                    self._picker_row_values(row, "queue_picker")
                    for row in rows_state
                ]
            )
            for row_idx, row in enumerate(rows_state):
                if previous_video_id and str(row.get("video_id") or "") == previous_video_id:
                    current_index["value"] = row_idx
            _apply_state()
            status_var.set(f"{len(rows_state)} rows | stage={stage}")

        def _select_clicked(event: tk.Event[tk.Misc]) -> str:
            item_id = title_list.item_id_at_y(int(event.y))
            if not item_id:
                return "break"
            current_index["value"] = next(
                (
                    idx
                    for idx, row in enumerate(rows_state)
                    if str(row.get("video_id") or "") == item_id
                ),
                0,
            )
            if current_index["value"] in selected_indexes:
                selected_indexes.remove(current_index["value"])
            _apply_state()
            return "break"

        query_var.trace_add("write", refresh_results)
        self._attach_picker_fields_menu(
            fields_button,
            picker_name="queue_picker",
            on_change=refresh_results,
        )
        self._bind_popup_close(
            popup,
            after_close=lambda: setattr(self, "_queue_picker_popup", None),
        )
        title_list.bind("<Button-1>", _select_clicked)
        popup.bind("<Return>", _queue_selected)
        title_list.bind("<Return>", _queue_selected)
        popup.bind("<Control-Up>", lambda _e: _move_cursor(-1, add_current=True))
        popup.bind("<Control-Down>", lambda _e: _move_cursor(1, add_current=True))
        popup.bind("<Control-Prior>", lambda _e: _move_cursor(-10, add_current=True))
        popup.bind("<Control-Next>", lambda _e: _move_cursor(10, add_current=True))
        popup.bind("<Control-Home>", lambda _e: _move_cursor(-10_000, add_current=True))
        popup.bind("<Control-End>", lambda _e: _move_cursor(10_000, add_current=True))
        popup.bind("<Shift-Up>", lambda _e: _move_cursor(-1, add_current=False))
        popup.bind("<Shift-Down>", lambda _e: _move_cursor(1, add_current=False))
        popup.bind("<Shift-Prior>", lambda _e: _move_cursor(-10, add_current=False))
        popup.bind("<Shift-Next>", lambda _e: _move_cursor(10, add_current=False))
        popup.bind("<Shift-Home>", lambda _e: _move_cursor(-10_000, add_current=False))
        popup.bind("<Shift-End>", lambda _e: _move_cursor(10_000, add_current=False))
        self._bind_fzf_like_keys(
            popup,
            entry=query_entry,
            capture_widgets=[query_entry, title_list],
            on_enter=lambda: _queue_selected(),
            on_up=lambda: _move_cursor(-1),
            on_down=lambda: _move_cursor(1),
            on_home=lambda: _move_cursor(-10_000),
            on_end=lambda: _move_cursor(10_000),
            on_page_up=lambda: _move_cursor(-10),
            on_page_down=lambda: _move_cursor(10),
        )
        refresh_results()
        self._focus_popup_entry(popup, query_entry)
