from __future__ import annotations

import tkinter as tk
from typing import Any

from ..constants import FONT_SIZE_OFFSETS, LISTBOX, POPUP_SIZES
from .jobs_commands import JobsCommandMixin
from .jobs_render import JobsRenderMixin


class JobsPopupMixin(JobsRenderMixin, JobsCommandMixin):

    def _open_jobs_popup(self) -> None:
        self._workflow_command_state = "root"
        popup = self._create_popup_window(
            name="workers",
            title="Workflows",
            size=POPUP_SIZES["WORKERS"],
            attr_name="_jobs_popup",
            row_weights={0: 1, 1: 0},
            column_weights={0: 1},
        )
        if popup is None:
            return
        content = self._popup_content(popup)
        content.columnconfigure(0, weight=4)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=self._theme_color("APP_BG"))
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=(8, 6))
        left.columnconfigure(0, weight=1)
        left.columnconfigure(1, weight=1)
        for idx in range(4):
            left.rowconfigure(idx * 2 + 1, weight=1)

        panels: dict[str, tk.Text] = {}
        panel_heads: dict[str, tk.Label] = {}
        for idx, title in enumerate(("DOWNLOAD", "TRANSCRIBE", "SUMMARIZE", "FINISHED")):
            head = tk.Label(
                left,
                text=title,
                anchor="w",
                bg=self._theme_color("SURFACE_BG"),
                fg=self._theme_color("FG_MUTED"),
                font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
                padx=8,
                pady=4,
            )
            body = tk.Text(
                left,
                bg=self._theme_color("PANEL_BG"),
                fg=self._theme_color("FG"),
                borderwidth=0,
                highlightthickness=0,
                font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
                wrap="none",
                padx=8,
                pady=8,
            )
            body.configure(state="disabled")
            panels[title.lower()] = body
            panel_heads[title.lower()] = head

        def _layout_workflow_panels(_event: tk.Event[tk.Misc] | None = None) -> None:
            try:
                wide_mode = int(left.winfo_width()) >= 760
            except Exception:
                wide_mode = False
            rows = [
                ("download", 0, 0),
                ("transcribe", 0, 1 if wide_mode else 0),
                ("summarize", 2 if wide_mode else 4, 0),
                ("finished", 2 if wide_mode else 6, 1 if wide_mode else 0),
            ]
            if wide_mode:
                for row in range(4):
                    left.rowconfigure(row, weight=1 if row in {1, 3} else 0)
            else:
                for row in range(8):
                    left.rowconfigure(row, weight=1 if row in {1, 3, 5, 7} else 0)
            for name, head_row, column in rows:
                head_widget = panel_heads[name]
                body_widget = panels[name]
                head_widget.grid_configure(row=head_row, column=column, sticky="ew", pady=(0 if head_row == 0 else 4, 2), padx=(0, 4) if column == 0 and wide_mode else (4, 0) if wide_mode else 0)
                body_widget.grid_configure(row=head_row + 1, column=column, sticky="nsew", pady=(0, 4), padx=(0, 4) if column == 0 and wide_mode else (4, 0) if wide_mode else 0)

        for name, head in panel_heads.items():
            body = panels[name]
            head.grid(row=0, column=0, sticky="ew")
            body.grid(row=1, column=0, sticky="nsew")
        left.bind("<Configure>", _layout_workflow_panels, add="+")
        left.after(0, _layout_workflow_panels)

        right = tk.Frame(content, bg=self._theme_color("APP_BG"))
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=(8, 6))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self._jobs_queue_list = tk.Label(
            right,
            text=self._workflow_command_label(),
            anchor="w",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_MUTED"),
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
            padx=8,
            pady=4,
        )
        self._jobs_queue_list.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        cmd_list = self._create_listbox(right, font_delta=FONT_SIZE_OFFSETS["BODY"])
        cmd_list.configure(height=LISTBOX["COMMAND_HEIGHT"])
        cmd_list.grid(row=1, column=0, sticky="nsew")
        self._workers_cmd_list = cmd_list

        self._jobs_dl_text = panels["download"]
        self._jobs_tr_text = panels["transcribe"]
        self._jobs_text = panels["summarize"]
        self._jobs_done_list = panels["finished"]

        status_var = tk.StringVar(value=self._status_hint("jobs"))
        status_lbl = self._create_status_label(
            content,
            status_var,
            font_delta=FONT_SIZE_OFFSETS["SMALL"],
        )
        status_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))

        def render_commands() -> None:
            commands = self._workflow_command_menu()
            if self._jobs_queue_list and self._jobs_queue_list.winfo_exists():
                self._jobs_queue_list.configure(text=self._workflow_command_label())
            cmd_list.delete(0, tk.END)
            for cmd in commands:
                cmd_list.insert(tk.END, cmd)
            if commands:
                cmd_list.selection_set(0)
                cmd_list.activate(0)

        def run_selected(_event: tk.Event[tk.Misc] | None = None) -> str:
            sel = cmd_list.curselection()
            if not sel:
                return "break"
            label = str(cmd_list.get(sel[0]))
            status_var.set(self._run_worker_command(label))
            render_commands()
            self._refresh_jobs_popup()
            return "break"

        def move(delta: int) -> str:
            commands = self._workflow_command_menu()
            self._move_listbox_selection(
                [cmd_list],
                delta=delta,
                item_count=max(0, len(commands)),
            )
            return "break"

        render_commands()
        self._bind_popup_close(popup, after_close=self._close_jobs_popup, focus_filter=False)
        popup.bind("<Up>", lambda _e: move(-1))
        popup.bind("<Down>", lambda _e: move(1))
        popup.bind("<Return>", run_selected)
        cmd_list.bind("<Double-Button-1>", run_selected)
        self._refresh_jobs_popup()

    def _close_jobs_popup(self) -> None:
        if self._jobs_after_id:
            try:
                self.root.after_cancel(self._jobs_after_id)
            except Exception:
                pass
            self._jobs_after_id = None
        if self._jobs_popup and self._jobs_popup.winfo_exists():
            self._jobs_popup.destroy()
        self._jobs_popup = None
        self._jobs_text = None
        self._workers_cmd_list = None
        self._jobs_queue_list = None
        self._jobs_done_list = None
        self._jobs_dl_text = None
        self._jobs_tr_text = None
        self._jobs_agent_text = None
        self._workflow_command_state = "root"
        self.filter_entry.focus_set()

    def _refresh_jobs_popup(self) -> None:
        if not self._jobs_popup or not self._jobs_popup.winfo_exists():
            return
        try:
            snapshot = self.ingester.jobs_summary(limit=30)
            dash = self.ingester.dashboard_snapshot()
            counts = dict(snapshot.get("counts", {}) or {})
            stage_counts = dict(dash.get("stage_counts", {}) or {})
            jobs = [dict(row) for row in (snapshot.get("jobs", []) or [])]
            active_jobs = [dict(row) for row in (dash.get("active_jobs", []) or [])]
            active_summary = [dict(row) for row in (dash.get("active_summary_jobs", []) or [])]

            download_queue = [
                row for row in jobs
                if str(row.get("status")) == "queued"
                and str(row.get("queue_stage") or "download") == "download"
            ]
            transcribe_queue = [
                row for row in jobs
                if str(row.get("status")) == "queued"
                and str(row.get("queue_stage") or "download") == "transcribe"
            ]
            summary_queue = [
                row for row in jobs
                if str(row.get("status")) == "queued"
                and str(row.get("queue_stage") or "download") == "summarize"
            ]
            finished_jobs = [row for row in jobs if str(row.get("status")) in {"done", "failed"}]
            download_active = [
                row for row in active_jobs
                if str(row.get("status")) == "downloading"
                and str(row.get("queue_stage") or "download") == "download"
            ]
            transcribe_active = [
                row for row in active_jobs
                if str(row.get("status")) == "transcribing"
                and str(row.get("queue_stage") or "download") == "transcribe"
            ]

            download_workers: list[dict[str, Any]] = []
            for idx in range(max(1, self._downloader_target_count)):
                if idx < len(download_active):
                    row = download_active[idx]
                    elapsed = float(row.get("elapsed_sec") or 0.0)
                    download_workers.append(
                        {"tag": "active", "progress": self._stage_progress_bar(min(1.0, elapsed / 120.0)), "suffix": ""}
                    )
                else:
                    download_workers.append(
                        {"tag": "idle", "progress": self._stage_progress_bar(0.0), "suffix": ""}
                    )

            transcribe_workers: list[dict[str, Any]] = []
            for idx in range(max(1, self._transcriber_target_count)):
                if idx < len(transcribe_active):
                    row = transcribe_active[idx]
                    elapsed = float(row.get("elapsed_sec") or 0.0)
                    transcribe_workers.append(
                        {"tag": "active", "progress": self._stage_progress_bar(min(1.0, elapsed / 300.0)), "suffix": ""}
                    )
                else:
                    transcribe_workers.append(
                        {"tag": "idle", "progress": self._stage_progress_bar(0.0), "suffix": ""}
                    )

            summary_enabled = bool(self._ai_settings.get("auto_summary_default", False))
            summary_lane_active = (
                summary_enabled
                or bool(summary_queue)
                or bool(active_summary)
                or self._summarizer_target_count > 0
            )
            summary_backlog = self._summary_backlog_rows(limit=8) if summary_lane_active else []
            summary_workers: list[dict[str, Any]] = []
            summary_slots = max(1, self._summarizer_target_count if summary_lane_active else 1)
            for idx in range(summary_slots):
                if idx < len(active_summary):
                    row = active_summary[idx]
                    elapsed = float(row.get("elapsed_sec") or 0.0)
                    summary_workers.append(
                        {"tag": "active", "progress": self._stage_progress_bar(min(1.0, elapsed / 90.0)), "suffix": ""}
                    )
                else:
                    summary_workers.append(
                        {
                            "tag": "idle" if summary_lane_active else "error",
                            "progress": self._stage_progress_bar(0.0),
                            "suffix": "" if summary_lane_active else "disabled",
                        }
                    )

            if self._jobs_dl_text and self._jobs_dl_text.winfo_exists():
                self._render_stage_text(
                    self._jobs_dl_text,
                    queue_rows=download_queue[:8],
                    worker_rows=download_workers,
                    worker_count=self._downloader_target_count,
                    state=f"{self._workers_eta_line()} queued={stage_counts.get('download_queued', 0)}",
                )
            if self._jobs_tr_text and self._jobs_tr_text.winfo_exists():
                self._render_stage_text(
                    self._jobs_tr_text,
                    queue_rows=transcribe_queue[:8],
                    worker_rows=transcribe_workers,
                    worker_count=self._transcriber_target_count,
                    state=f"queued={stage_counts.get('transcribe_queued', 0)} active={len(transcribe_active)}",
                )
            if self._jobs_text and self._jobs_text.winfo_exists():
                self._render_stage_text(
                    self._jobs_text,
                    queue_rows=summary_queue[:8] if summary_queue else summary_backlog,
                    worker_rows=summary_workers,
                    worker_count=(self._summarizer_target_count if summary_lane_active else 0),
                    state=(
                        f"queued={stage_counts.get('summarize_queued', 0)}"
                        if summary_lane_active else "disabled"
                    ),
                )
            if self._jobs_done_list and self._jobs_done_list.winfo_exists():
                self._jobs_done_list.configure(state="normal")
                self._jobs_done_list.delete("1.0", tk.END)
                self._jobs_done_list.tag_configure("file_head", foreground=self._theme_color("FG_INFO"))
                self._jobs_done_list.tag_configure("result_head", foreground=self._theme_color("FG_ACCENT"))
                self._jobs_done_list.tag_configure("meta", foreground=self._theme_color("FG_SOFT"))
                self._jobs_done_list.tag_configure("done", foreground=self._theme_color("FG_INFO"))
                self._jobs_done_list.tag_configure("error", foreground=self._theme_color("FG_ERROR"))
                self._jobs_done_list.insert(tk.END, "file".ljust(31), ("file_head",))
                self._jobs_done_list.insert(tk.END, "result\n", ("result_head",))
                rows = finished_jobs[:8]
                for row in rows:
                    label = self._workflow_label(row, prefer=("video_id", "source_url"))
                    status = str(row.get("status") or "")
                    self._jobs_done_list.insert(tk.END, f"{label} ", ("meta",))
                    self._jobs_done_list.insert(tk.END, ("success" if status == "done" else "failed"), ("done" if status == "done" else "error",))
                    self._jobs_done_list.insert(tk.END, "\n")
                for _ in range(max(0, 3 - len(rows))):
                    self._jobs_done_list.insert(tk.END, "".ljust(31), ("meta",))
                    self._jobs_done_list.insert(tk.END, "\n")
                self._jobs_done_list.insert(
                    tk.END,
                    f"\nfinished={counts.get('done', 0)} failed={counts.get('failed', 0)}",
                    ("meta",),
                )
                self._jobs_done_list.configure(state="disabled")
        except Exception as exc:
            if self._jobs_dl_text and self._jobs_dl_text.winfo_exists():
                self._jobs_dl_text.configure(state="normal")
                self._jobs_dl_text.delete("1.0", tk.END)
                self._jobs_dl_text.insert("1.0", f"Failed to load workflows: {exc}")
                self._jobs_dl_text.configure(state="disabled")
        self._jobs_after_id = self.root.after(1000, self._refresh_jobs_popup)
