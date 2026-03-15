from __future__ import annotations

import json
import time
from typing import Any

from ..constants import ICONS
from ..utils import format_hms as _fmt_hms


class JobsRenderMixin:
    def _recalculate_workers_eta(self) -> None:
        now = time.monotonic()
        self._workers_eta_last_tick_at = now
        self._workers_eta_next_recalc_at = now + self._workers_eta_recalc_interval_sec
        if self._workers_paused:
            self._workers_eta_remaining_sec = None
            return
        try:
            snapshot = self.ingester.dashboard_snapshot()
            counts = snapshot.get("counts", {})
            pending = (
                int(counts.get("queued", 0))
                + int(counts.get("downloading", 0))
                + int(counts.get("transcribing", 0))
                + int(counts.get("summarizing", 0))
            )
            if pending <= 0:
                self._workers_eta_remaining_sec = 0.0
                return
            avg = snapshot.get("median_duration_sec")
            if avg is None:
                avg = snapshot.get("avg_duration_sec")
            avg_sec = max(30.0, float(avg) if avg is not None else 300.0)
            workers = max(
                1,
                int(
                    (
                        self._downloader_target_count
                        + self._transcriber_target_count
                        + self._summarizer_target_count
                    )
                    or self._worker_target_count
                    or 1
                ),
            )
            self._workers_eta_remaining_sec = float(pending) * avg_sec / float(workers)
        except Exception:
            if self._workers_eta_remaining_sec is None:
                self._workers_eta_remaining_sec = 0.0

    def _tick_workers_eta_countdown(self) -> None:
        now = time.monotonic()
        elapsed = max(0.0, now - self._workers_eta_last_tick_at)
        self._workers_eta_last_tick_at = now
        if self._workers_eta_remaining_sec is None:
            return
        self._workers_eta_remaining_sec = max(0.0, self._workers_eta_remaining_sec - elapsed)

    def _workers_eta_line(self) -> str:
        now = time.monotonic()
        if now >= self._workers_eta_next_recalc_at:
            self._recalculate_workers_eta()
        self._tick_workers_eta_countdown()
        recalc_in = max(0, int(self._workers_eta_next_recalc_at - time.monotonic()))
        if self._workers_paused:
            return f"eta=paused  recalc={_fmt_hms(recalc_in)}"
        if self._workers_eta_remaining_sec is None:
            return f"eta=unknown  recalc={_fmt_hms(recalc_in)}"
        return f"eta~{_fmt_hms(self._workers_eta_remaining_sec)}  recalc={_fmt_hms(recalc_in)}"

    def _stage_progress_bar(self, fill_ratio: float, *, width: int = 10) -> str:
        clamped = max(0.0, min(1.0, fill_ratio))
        filled = min(width, max(0, int(round(clamped * width))))
        return "[" + ("#" * filled) + ("." * (width - filled)) + "]"

    def _workflow_label(self, row: dict[str, Any], *, prefer: tuple[str, ...], width: int = 28) -> str:
        text = ""
        for key in prefer:
            value = str(row.get(key) or "").strip()
            if value:
                text = value
                break
        if not text:
            text = str(row.get("id") or row.get("job_id") or row.get("video_id") or "-")
        text = text.replace("\n", " ").strip()
        if len(text) > width:
            text = text[: max(0, width - 1)] + "…"
        return text.ljust(width)

    def _metadata_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        raw = str(row.get("metadata_json") or "").strip()
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _summary_backlog_rows(self, limit: int = 8) -> list[dict[str, Any]]:
        try:
            rows = [dict(row) for row in self.ingester.search_video_metadata("", limit=max(20, limit * 3))]
        except Exception:
            return []
        pending: list[dict[str, Any]] = []
        for row in rows:
            if not str(row.get("transcript_json_path") or "").strip():
                continue
            payload = self._metadata_payload(row)
            if str(payload.get("summary") or "").strip():
                continue
            pending.append(row)
            if len(pending) >= limit:
                break
        return pending

    def _render_stage_text(
        self,
        widget,
        *,
        queue_rows: list[dict[str, Any]],
        worker_rows: list[dict[str, Any]],
        worker_count: int,
        state: str,
    ) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.tag_configure("queue_head", foreground=self._theme_color("FG_INFO"))
        widget.tag_configure("workers_head", foreground=self._theme_color("FG_ACCENT"))
        widget.tag_configure("progress_head", foreground=self._theme_color("FG_MUTED"))
        widget.tag_configure("meta", foreground=self._theme_color("FG_SOFT"))
        widget.tag_configure("idle", foreground=self._theme_color("FG_LOG"))
        widget.tag_configure("active", foreground=self._theme_color("FG_ACCENT"))
        widget.tag_configure("error", foreground=self._theme_color("FG_ERROR"))
        widget.tag_configure("done", foreground=self._theme_color("FG_INFO"))

        widget.insert("end", "queue".ljust(31), ("queue_head",))
        widget.insert("end", "workers".ljust(12), ("workers_head",))
        widget.insert("end", "progress\n", ("progress_head",))

        row_count = max(3, len(queue_rows), len(worker_rows))
        for idx in range(row_count):
            queue_label = (
                self._workflow_label(queue_rows[idx], prefer=("title", "video_id", "source_url"))
                if idx < len(queue_rows)
                else "".ljust(28)
            )
            widget.insert("end", f"{queue_label} ", ("meta",))
            if idx < len(worker_rows):
                worker = worker_rows[idx]
                tag = str(worker.get("tag") or "idle")
                widget.insert("end", f"{ICONS['WORKER']} ".ljust(12), (tag,))
                widget.insert("end", str(worker.get("progress") or self._stage_progress_bar(0.0)), (tag,))
                suffix = str(worker.get("suffix") or "")
                if suffix:
                    widget.insert("end", f" {suffix}", ("meta",))
            else:
                widget.insert("end", "".ljust(12), ("idle",))
                widget.insert("end", self._stage_progress_bar(0.0), ("idle",))
            widget.insert("end", "\n")
        widget.insert("end", f"\nworkers={worker_count}  {state}", ("meta",))
        widget.configure(state="disabled")
