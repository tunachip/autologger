from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from typing import Any, Callable
import threading
import subprocess

import time

from alog.config import IngesterConfig
from alog.service import IngesterService

from .constants import (
    DEFAULT_KEYBINDS,
    FONT,
    LAYOUT,
    POPUP_SIZES,
    THEME,
)
from .playback import PlaybackMixin
from .player_chrome import PlayerChromeMixin
from .popups import PopupMixin
from .root_chrome import RootChromeMixin
from .runtime_settings import RuntimeSettingsMixin
from .style_runtime import StyleRuntimeMixin
from .transcript import TranscriptMixin


class TranscriptPlayer(
    StyleRuntimeMixin,
    RuntimeSettingsMixin,
    RootChromeMixin,
    PlayerChromeMixin,
    TranscriptMixin,
    PlaybackMixin,
    PopupMixin,
):
    def __init__(
        self,
        transcript_json: Path | None = None,
        video_path: Path | None = None,
        audio_path: Path | None = None,
        skim_seconds: float = 5.0,
        start_sec: float = 0.0,
        workers: int = 0,
    ) -> None:
        self.transcript_json = transcript_json
        self.video_path = video_path
        self.audio_path = audio_path
        self.skim_seconds = skim_seconds
        self.start_sec = max(0.0, float(start_sec))
        self.workers = max(0, int(workers))

        self.segments = (
            self._load_segments(transcript_json)
            if transcript_json
            else []
        )
        self._segment_starts = [segment.start_sec for segment in self.segments]
        self.filtered_indexes = list(range(len(self.segments)))
        self.selected_filtered_pos = 0

        self._search_popup = None
        self._command_popup = None
        self._video_picker_popup = None
        self._queue_picker_popup = None
        self._ingest_popup = None
        self._ai_popup = None
        self._settings_popup = None
        self._goto_popup = None
        self._channel_popup = None
        self._subscriptions_popup = None
        self._jobs_popup = None
        self._jobs_text = None
        self._workers_cmd_list = None
        self._jobs_queue_list = None
        self._jobs_done_list = None
        self._jobs_dl_text = None
        self._jobs_tr_text = None
        self._jobs_agent_text = None
        self._jobs_after_id = None
        self._agent_activity: list[dict[str, str]] = []
        self._search_results: list[dict[str, Any]] = []
        self._video_picker_results: list[dict[str, Any]] = []
        self._channel_results: list[dict[str, Any]] = []
        self._channel_default_ref = ""
        self._browse_preview_cache: dict[str, dict[str, Any]] = {}
        self._browse_thumb_dir: Path | None = None
        self._video_thumb_dir: Path | None = None
        self._browse_temp_files: set[Path] = set()
        self._playback_rate = 1.0
        self._split_initialized = False
        self._transcript_hidden = False
        self._details_hidden = False
        self._split_x_before_hide: int | None = None
        self._active_popup_name: str | None = None
        self.current_video_id: str | None = None
        self._load_fail_count = 0
        self._startup_poll_count = 0
        self._proxy_attempted = False
        self._skim_mode = False
        self._skim_pre_ms = 300
        self._skim_post_ms = 500
        self._skim_cursor = 0
        self._skim_last_seek_at = 0.0
        self._worker_target_count = self.workers
        self._downloader_target_count = (
            self.workers
            if self.workers > 0
            else 1
        )
        self._transcriber_target_count = (
            self.workers
            if self.workers > 0
            else 1
        )
        self._summarizer_target_count = (
            self.workers
            if self.workers > 0
            else 1
        )
        self._workers_paused = False
        self._popup_paused_player = False
        self._popup_video_hidden = False
        self._workers_eta_remaining_sec: float | None = None
        self._workers_eta_next_recalc_at = 0.0
        self._workers_eta_last_tick_at = time.monotonic()
        self._workers_eta_recalc_interval_sec = 60.0
        self._worker_anim_tick = 0
        self._bound_shortcut_sequences: list[str] = []
        self._ollama_proc: subprocess.Popen[str] | None = None
        self._ollama_started_by_app = False
        self._ollama_bootstrap_thread: threading.Thread | None = None
        self._ollama_bootstrap_lock = threading.Lock()
        self._ollama_bootstrap_done = threading.Event()
        self._ollama_bootstrap_success = False
        self._ollama_bootstrap_error: str | None = None
        self._ollama_bootstrap_state = "idle"

        self.ingester_config = IngesterConfig.from_env()
        self.ingester = IngesterService(self.ingester_config)
        self.ingester.init()
        self._browse_thumb_dir = (
            self.ingester_config.db_path.parent / "browse_previews"
        )
        self._video_thumb_dir = (
            self.ingester_config.db_path.parent / "video_previews"
        )
        try:
            self._browse_thumb_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        try:
            self._video_thumb_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._gui_settings_path = (
            self.ingester_config.db_path.parent / "gui_settings.json"
        )
        self._ai_settings = self._load_gui_settings()
        if self.workers <= 0:
            self.workers = max(0, int(
                self._ai_settings.get("default_worker_count")
                or 0))
            self._worker_target_count = self.workers
        self._downloader_target_count = max(0, int(
            self._ai_settings.get("default_downloaders")
            or self._worker_target_count
            or 1))
        self._transcriber_target_count = max(0, int(
            self._ai_settings.get("default_transcribers")
            or self._worker_target_count
            or 1))
        self._summarizer_target_count = max(0, int(
            self._ai_settings.get("default_summarizers")
            or self._worker_target_count
            or 1))
        if self._worker_target_count <= 0:
            self._worker_target_count = max(
                self._downloader_target_count,
                self._transcriber_target_count,
                self._summarizer_target_count)
        self.ingester.set_runtime_options(
            auto_transcribe_default=bool(
                self._ai_settings.get("auto_transcribe_default", True)),
            subscription_db_max_videos=max(0, int(
                self._ai_settings.get("subscription_db_max_videos")
                or 0)),
            job_retry_limit=max(0, int(
                self._ai_settings.get("job_retry_limit")
                or 0)),
            ai_runtime_settings=self._build_ai_runtime_settings(),
        )
        if self.workers > 0:
            self.ingester.start_background_workers(
                max(self.workers,
                    self._downloader_target_count
                    + self._transcriber_target_count
                    + self._summarizer_target_count),
                downloader_count=self._downloader_target_count,
                transcriber_count=self._transcriber_target_count,
                summarizer_count=self._summarizer_target_count,
            )
        if str(self._ai_settings.get("ai_provider")
               or "ollama").lower() == "ollama":
            self._start_ollama_bootstrap(background=True)

        self.root = tk.Tk()
        self.root.title("Alogger Player")
        self.root.geometry(POPUP_SIZES["ROOT"])
        self.root.configure(bg=THEME["APP_BG"])
        self.root.option_add("*insertOffTime", 0)
        self.root.option_add("*Entry.insertOffTime", 0)
        self.root.option_add("*Text.insertOffTime", 0)
        self.root.option_add("*TEntry.insertOffTime", 0)

        self._text_font = tkfont.Font(
            family=FONT["STYLE"],
            size=FONT["SIZE"])
        self._text_font_bold = tkfont.Font(
            family=FONT["STYLE"],
            size=FONT["SIZE"],
            weight="bold")
        self._timestamp_prefix = "[00:00:00] "
        self._wrap_indent_px = self._text_font.measure(self._timestamp_prefix)
        self._progress_bar_width = LAYOUT["PROGRESS_BAR_WIDTH"]
        self._clock_prefix_len = len("[00:00:00] ")
        self._clock_last_length_sec = 0.0
        self._font_size_delta = 0
        self._drag_origin_x = 0
        self._drag_origin_y = 0
        self._window_origin_x = 0
        self._window_origin_y = 0
        self._shell_stacked = False
        self._shell_layout_mode = "horizontal"
        self._launch_buttons: list[tk.Widget] = []
        self._root_layout_after_id: str | None = None

        self._setup_styles()
        self._build_layout()
        self._apply_theme()
        self._apply_font_scale_tree(self.root, reset_base=True)
        if bool(self._ai_settings.get("default_details_hidden", False)):
            self.details_frame.grid_remove()
            self._details_hidden = True
        if bool(self._ai_settings.get("default_transcript_hidden", False)):
            self._on_toggle_transcript_log(None)
        self._bind_keys()
        self._build_vlc()
        self._refresh_caption_view()
        if not self.video_path:
            self.status_var.set(self._status_hint("startup"))
        self._tick_ui()

    def _display_to_tk_sequence(self, value: str) -> str | None:
        token = str(value or "").strip()
        if not token:
            return None
        if token.startswith("<") and token.endswith(">"):
            return token
        parts = [
            piece for piece in token.replace("+", "-").split("-")
            if piece
        ]
        if not parts:
            return None
        mods: list[str] = []
        key = parts[-1].lower()
        for raw in parts[:-1]:
            piece = raw.strip().lower()
            if piece in {"ctrl", "control"}:
                mods.append("Control")
            elif piece in {"alt", "meta"}:
                mods.append("Alt")
            elif piece == "shift":
                mods.append("Shift")
        key_map = {
            "space": "space",
            "left": "Left",
            "right": "Right",
            "up": "Up",
            "down": "Down",
            "pgup": "Prior",
            "pageup": "Prior",
            "pgdn": "Next",
            "pagedown": "Next",
            "enter": "Return",
            "return": "Return",
            "esc": "Escape",
            "escape": "Escape",
        }
        tk_key = key_map.get(key, key if len(key) == 1 else key)
        prefix = "-".join(mods)
        return f"<{prefix + '-' if prefix else ''}KeyPress-{tk_key}>"

    def _apply_shortcut_bindings(self) -> None:
        handlers: dict[str, Callable[[tk.Event[tk.Misc]], str]] = {
            "open_command": self._on_open_command_popup,
            "open_ingest": self._on_open_ingest_popup,
            "open_workers": self._on_toggle_jobs_popup,
            "open_video": self._on_open_video_picker_popup,
            "open_finder": self._on_open_search_popup,
            "open_ai": self._on_open_ai_popup,
            "open_goto": self._on_open_goto_popup,
            "toggle_skim": self._on_ctrl_s,
            "open_settings": self._on_open_settings_popup,
            "quit": self._on_quit,
            "play_pause": self._on_toggle_play,
            "seek_back": self._on_ctrl_left,
            "seek_forward": self._on_ctrl_right,
            "prev_match": self._on_ctrl_up,
            "next_match": self._on_ctrl_down,
            "vim_left": self._on_ctrl_left,
            "vim_down": self._on_ctrl_down,
            "vim_up": self._on_ctrl_up,
            "vim_right": self._on_ctrl_right,
            "clear_input": self._on_clear_filter,
            "toggle_transcript": self._on_toggle_transcript_log,
            "toggle_details": self._on_toggle_details,
        }
        for seq in self._bound_shortcut_sequences:
            try:
                self.root.unbind(seq)
            except Exception:
                pass
        self._bound_shortcut_sequences = []
        keybinds = self._ai_settings.get("keybinds")
        if not isinstance(keybinds, dict):
            keybinds = dict(DEFAULT_KEYBINDS)
            self._ai_settings["keybinds"] = keybinds
        for action, handler in handlers.items():
            raw = str(keybinds.get(action, DEFAULT_KEYBINDS.get(action, "")))
            seq = self._display_to_tk_sequence(raw)
            if not seq:
                continue
            try:
                def _wrapped(
                    event: tk.Event[tk.Misc],
                    handler: Callable[[tk.Event[tk.Misc]], str] = handler
                ) -> str:
                    if self._active_popup_name is not None:
                        return "break"
                    return handler(event)
                self.root.bind(seq, _wrapped)
                self._bound_shortcut_sequences.append(seq)
            except Exception:
                continue

    def _guard_key_handler(
        self,
        handler: Callable[[tk.Event[tk.Misc]], str]
    ) -> Callable[[tk.Event[tk.Misc]], str]:
        def _wrapped(
            event: tk.Event[tk.Misc]
        ) -> str:
            if self._active_popup_name is not None:
                return "break"
            return handler(event)
        return _wrapped

    def _bind_keys(self) -> None:
        self.filter_var.trace_add(
            "write",
            self._on_filter_change
        )
        self.root.bind(
            "<Up>",
            self._guard_key_handler(self._on_up)
        )
        self.root.bind(
            "<Down>",
            self._guard_key_handler(self._on_down)
        )
        self.root.bind(
            "<Return>",
            self._guard_key_handler(self._on_return)
        )
        self.root.bind(
            "<Left>",
            self._guard_key_handler(self._on_left)
        )
        self.root.bind(
            "<Right>",
            self._guard_key_handler(self._on_right)
        )
        self.root.bind(
            "<Prior>",
            self._guard_key_handler(self._on_page_up)
        )
        self.root.bind(
            "<Next>",
            self._guard_key_handler(self._on_page_down)
        )
        self.root.bind(
            "<Home>",
            self._guard_key_handler(self._on_home)
        )
        self.root.bind(
            "<End>",
            self._guard_key_handler(self._on_end)
        )
        self.root.bind(
            "<Control-Prior>",
            self._guard_key_handler(self._on_ctrl_page_up)
        )
        self.root.bind(
            "<Control-Next>",
            self._guard_key_handler(self._on_ctrl_page_down)
        )
        self.root.bind(
            "<Control-Home>",
            self._guard_key_handler(self._on_ctrl_home)
        )
        self.root.bind(
            "<Control-End>",
            self._guard_key_handler(self._on_ctrl_end)
        )
        self.root.bind(
            "<Control-minus>",
            self._guard_key_handler(self._on_font_smaller)
        )
        self.root.bind(
            "<Control-equal>",
            self._guard_key_handler(self._on_font_larger)
        )
        self.root.bind(
            "<Control-plus>",
            self._guard_key_handler(self._on_font_larger)
        )
        self.root.bind(
            "<Escape>",
            self._on_escape,
            add="+"
        )
        self.root.bind(
            "<KeyPress>",
            self._on_type_to_filter,
            add="+"
        )
        self._apply_shortcut_bindings()
        self._bind_ctrl_i_conflicts()
        self.caption_view.bind(
            "<Double-Button-1>",
            self._on_double_click
        )
        self.caption_view.bind(
            "<Button-1>",
            self._on_click_seek_transcript
        )
        self.video_panel.bind(
            "<Button-1>",
            self._on_click_video_toggle
        )
        self.root.after(
            50,
            lambda: self.filter_entry.focus_set()
        )


def run_player(
    transcript_json: Path | None = None,
    video_path: Path | None = None,
    *,
    audio_path: Path | None = None,
    skim_seconds: float = 5.0,
    start_sec: float = 0.0,
    workers: int = 0,
) -> None:
    app = TranscriptPlayer(
        transcript_json=transcript_json,
        video_path=video_path,
        audio_path=audio_path,
        skim_seconds=skim_seconds,
        start_sec=start_sec,
        workers=workers,
    )
    app.run()
