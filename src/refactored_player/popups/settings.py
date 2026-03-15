from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import simpledialog
from tkinter import ttk

from ..constants import (
    DEFAULT_KEYBINDS,
    FONT,
    FONT_SIZE_OFFSETS,
    POPUP_SIZES,
    THEME,
    THEME_PRESETS,
    THEME_SETTINGS_FIELDS,
)
from .settings_data import (
    SETTINGS_TAB_NAMES,
    build_settings_rows,
    normalize_hex_value,
)


class SettingsPopupMixin:
    def _open_settings_popup(self) -> None:
        popup = self._create_popup_window(
            name="settings",
            title="Settings",
            size=POPUP_SIZES["SETTINGS"],
            attr_name="_settings_popup",
            row_weights={0: 1, 1: 0, 2: 0},
            column_weights={0: 1},
        )
        if popup is None:
            return
        content = self._popup_content(popup)

        tabs = ttk.Notebook(content, style="Terminal.TNotebook")
        tabs.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 6))

        tab_names = list(SETTINGS_TAB_NAMES)
        tab_frames: list[tk.Frame] = []
        key_lists: list[tk.Listbox] = []
        val_lists: list[tk.Listbox] = []
        preview_lists: list[tk.Listbox | None] = []
        theme_preset_var = tk.StringVar(value=str(self._ai_settings.get("theme_preset") or "dark"))
        theme_preset_box: ttk.Combobox | None = None
        theme_export_button: tk.Label | None = None
        for name in tab_names:
            frame = tk.Frame(tabs, bg=THEME["APP_BG"])
            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=0)
            tabs.add(frame, text=name)
            tab_frames.append(frame)
            head_row = 0
            list_row = 1

            if name == "Theme":
                frame.rowconfigure(2, weight=1)
                controls = tk.Frame(frame, bg=THEME["APP_BG"])
                controls.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))
                controls.columnconfigure(1, weight=1)
                tk.Label(
                    controls,
                    text="Preset",
                    anchor="w",
                    bg=self._theme_color("APP_BG"),
                    fg=self._theme_color("FG_MUTED"),
                    font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
                ).grid(row=0, column=0, sticky="w", padx=(0, 8))
                theme_preset_box = ttk.Combobox(
                    controls,
                    textvariable=theme_preset_var,
                    values=[*sorted(THEME_PRESETS), "custom"],
                    state="readonly",
                    style="Filter.TCombobox",
                )
                theme_preset_box.grid(row=0, column=1, sticky="ew")
                theme_export_button = tk.Label(
                    controls,
                    text="Export YAML",
                    anchor="center",
                    bg=self._theme_color("SURFACE_BG"),
                    fg=self._theme_color("FG"),
                    font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
                    padx=10,
                    pady=4,
                    cursor="hand2",
                )
                theme_export_button.grid(row=0, column=2, sticky="e", padx=(8, 0))
                theme_export_button.bind(
                    "<Enter>",
                    lambda e: e.widget.configure(fg=self._theme_color("FG_ACCENT")),
                    add="+",
                )
                theme_export_button.bind(
                    "<Leave>",
                    lambda e: e.widget.configure(fg=self._theme_color("FG")),
                    add="+",
                )
                head_row = 1
                list_row = 2
            else:
                frame.rowconfigure(1, weight=1)

            tk.Label(
                frame,
                text="Key",
                anchor="w",
                bg=self._theme_color("SURFACE_BG"),
                fg=self._theme_color("FG_MUTED"),
                font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
                padx=8,
                pady=4,
            ).grid(row=head_row, column=0, sticky="ew", padx=(8, 4), pady=(8 if head_row == 0 else 0, 4))
            tk.Label(
                frame,
                text="Value",
                anchor="w",
                bg=self._theme_color("SURFACE_BG"),
                fg=self._theme_color("FG_MUTED"),
                font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
                padx=8,
                pady=4,
            ).grid(row=head_row, column=1, sticky="ew", padx=(4, 8), pady=(8 if head_row == 0 else 0, 4))
            preview_label = tk.Label(
                frame,
                text="",
                anchor="center",
                bg=self._theme_color("SURFACE_BG"),
                fg=self._theme_color("FG_MUTED"),
                font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
                padx=8,
                pady=4,
            )
            preview_list: tk.Listbox | None = None
            if name == "Theme":
                preview_label.configure(text="Preview")
                preview_label.grid(row=head_row, column=2, sticky="ew", padx=(0, 8), pady=(0, 4))
                preview_list = tk.Listbox(
                    frame,
                    bg=self._theme_color("PANEL_BG"),
                    fg=self._theme_color("FG"),
                    selectbackground=self._theme_color("SELECT_BG"),
                    selectforeground=self._theme_color("FG"),
                    activestyle="none",
                    borderwidth=0,
                    highlightthickness=0,
                    exportselection=False,
                    width=10,
                    font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
                )
                preview_list.grid(row=list_row, column=2, sticky="ns", padx=(0, 8), pady=(0, 8))

            k_list = tk.Listbox(
                frame,
                bg=self._theme_color("PANEL_BG"),
                fg=self._theme_color("FG_SOFT"),
                selectbackground=self._theme_color("SELECT_BG"),
                selectforeground=self._theme_color("FG"),
                activestyle="none",
                borderwidth=0,
                highlightthickness=0,
                exportselection=False,
                font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
            )
            v_list = tk.Listbox(
                frame,
                bg=self._theme_color("PANEL_BG"),
                fg=self._theme_color("FG"),
                selectbackground=self._theme_color("SELECT_BG"),
                selectforeground=self._theme_color("FG"),
                activestyle="none",
                borderwidth=0,
                highlightthickness=0,
                exportselection=False,
                font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
            )
            k_list.grid(row=list_row, column=0, sticky="nsew",
                        padx=(8, 4), pady=(0, 8))
            v_list.grid(row=list_row, column=1, sticky="nsew",
                        padx=(4, 8), pady=(0, 8))
            key_lists.append(k_list)
            val_lists.append(v_list)
            preview_lists.append(preview_list)

        edit_var = tk.StringVar(value="")
        edit_entry = ttk.Entry(
            content, textvariable=edit_var, style="Filter.TEntry")
        edit_entry.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        edit_entry.grid_remove()

        status_var = tk.StringVar(
            value=self._status_hint("settings"))
        tk.Label(
            content,
            textvariable=status_var,
            anchor="w",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_MUTED"),
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
            padx=8,
            pady=6,
        ).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))

        def _rows_for_tab(tab_idx: int) -> list[dict[str, str]]:
            return build_settings_rows(self, tab_idx)

        selected_idx = [0 for _ in tab_names]
        tab_rows: list[list[dict[str, str]]] = [[] for _ in tab_names]
        editing = {
            "active": False,
            "tab": 0,
            "row": 0,
            "orig": ""
        }

        def _sync_selection(tab_idx: int) -> None:
            rows = tab_rows[tab_idx]
            if not rows:
                return
            idx = max(0, min(selected_idx[tab_idx], len(rows) - 1))
            selected_idx[tab_idx] = idx
            k = key_lists[tab_idx]
            v = val_lists[tab_idx]
            p = preview_lists[tab_idx]
            k.selection_clear(0, tk.END)
            v.selection_clear(0, tk.END)
            k.selection_set(idx)
            v.selection_set(idx)
            if p is not None:
                p.selection_clear(0, tk.END)
                p.selection_set(idx)
            k.activate(idx)
            v.activate(idx)
            k.see(idx)
            v.see(idx)
            if p is not None:
                p.activate(idx)
                p.see(idx)

        def _render_tab(tab_idx: int) -> None:
            tab_rows[tab_idx] = _rows_for_tab(tab_idx)
            if tab_idx == 1:
                theme_preset_var.set(str(self._ai_settings.get("theme_preset") or "dark"))
            k = key_lists[tab_idx]
            v = val_lists[tab_idx]
            p = preview_lists[tab_idx]
            k.delete(0, tk.END)
            v.delete(0, tk.END)
            if p is not None:
                p.delete(0, tk.END)
            for row in tab_rows[tab_idx]:
                k.insert(tk.END, row["key"])
                v.insert(tk.END, row["value"])
                if p is not None:
                    if row["id"] in {field[0] for field in THEME_SETTINGS_FIELDS}:
                        color = normalize_hex_value(row["value"]) or "#000000"
                        p.insert(tk.END, "      ")
                        idx = p.size() - 1
                        p.itemconfig(idx, {"bg": color, "fg": color, "selectbackground": color, "selectforeground": color})
                    else:
                        p.insert(tk.END, "")
            _sync_selection(tab_idx)

        def _render_current() -> None:
            _render_tab(int(tabs.index("current")))

        def _export_theme_yaml() -> None:
            name = simpledialog.askstring("Export Theme", "Theme file name:", parent=popup)
            if not name:
                status_var.set("Theme export canceled")
                return
            slug = "".join(ch.lower() if ch.isalnum() or ch in {"-", "_"} else "-" for ch in name).strip("-_")
            if not slug:
                status_var.set("Theme name must contain letters or numbers")
                return
            theme_dir = Path(__file__).resolve().parent.parent / "themes"
            theme_dir.mkdir(parents=True, exist_ok=True)
            target = theme_dir / f"{slug}.yaml"
            lines = [
                f"{theme_key}: \"{str(self._ai_settings.get(setting_id) or THEME[theme_key])}\""
                for setting_id, _label, theme_key in THEME_SETTINGS_FIELDS
            ]
            try:
                target.write_text("\n".join(lines) + "\n", encoding="utf-8")
                THEME_PRESETS[slug] = {
                    theme_key: str(self._ai_settings.get(setting_id) or THEME[theme_key])
                    for setting_id, _label, theme_key in THEME_SETTINGS_FIELDS
                }
                if theme_preset_box is not None:
                    theme_preset_box.configure(values=[*sorted(THEME_PRESETS), "custom"])
                status_var.set(f"Saved theme preset: {slug}")
            except Exception as exc:
                status_var.set(f"Theme export failed: {exc}")

        def _apply_row_value(row_id: str, value: str) -> str | None:
            prev_provider = str(self._ai_settings.get(
                "ai_provider") or "ollama")
            prev_model = str(self._ai_settings.get(
                "ollama_model") or "llama3.2:3b")
            prev_base = str(self._ai_settings.get(
                "ollama_base_url") or "http://127.0.0.1:11434")
            token = value.strip()
            try:
                if row_id == "default_downloaders":
                    self._ai_settings["default_downloaders"] = max(
                        0, int(token or "0"))
                elif row_id == "default_transcribers":
                    self._ai_settings["default_transcribers"] = max(
                        0, int(token or "0"))
                elif row_id == "default_summarizers":
                    self._ai_settings["default_summarizers"] = max(
                        0, int(token or "0"))
                elif row_id == "job_retry_limit":
                    self._ai_settings["job_retry_limit"] = max(
                        0, int(token or "0"))
                elif row_id == "auto_transcribe_default":
                    self._ai_settings["auto_transcribe_default"] = token.lower() in {
                        "1", "true", "yes", "on"}
                elif row_id == "skim_pre":
                    self._skim_pre_ms = max(0, int(token or "0"))
                elif row_id == "skim_post":
                    self._skim_post_ms = max(0, int(token or "0"))
                elif row_id in {field[0] for field in THEME_SETTINGS_FIELDS}:
                    color = normalize_hex_value(token)
                    if not color:
                        return "Invalid hex color; use #RRGGBB"
                    self._ai_settings[row_id] = color
                    self._ai_settings["theme_preset"] = "custom"
                elif row_id == "theme_preset":
                    preset_key = token.strip().lower()
                    if preset_key not in THEME_PRESETS:
                        return f"Unknown preset: {preset_key}"
                    for setting_id, _label, theme_key in THEME_SETTINGS_FIELDS:
                        self._ai_settings[setting_id] = THEME_PRESETS[preset_key][theme_key]
                    self._ai_settings["theme_preset"] = preset_key
                elif row_id == "font_family":
                    self._ai_settings["font_family"] = token or FONT["STYLE"]
                elif row_id == "font_size":
                    self._ai_settings["font_size"] = max(8, int(token or "12"))
                elif row_id in {
                    "show_root_top_bar",
                    "show_launch_bar",
                    "show_popup_top_bar",
                    "default_transcript_hidden",
                    "default_details_hidden",
                    "defer_local_picker_preview",
                    "defer_browse_preview",
                }:
                    self._ai_settings[row_id] = token.lower() in {"1", "true", "yes", "on"}
                elif row_id in {"video_picker_default_field", "finder_default_field"}:
                    cleaned = token.strip().lower().removeprefix("$") or ("title" if row_id == "video_picker_default_field" else "ts")
                    self._ai_settings[row_id] = cleaned
                elif row_id == "subscription_db_max_videos":
                    self._ai_settings["subscription_db_max_videos"] = max(
                        0, int(token or "0"))
                elif row_id.startswith("sub:"):
                    channel_key = row_id.split(":", 1)[1]
                    if token.lower() in {"remove", "rm", "delete"}:
                        self.ingester.remove_channel_subscription(channel_key)
                    else:
                        parts = token.replace(",", " ").split()
                        active_val: bool | None = None
                        mode_val: str | None = None
                        for part in parts:
                            if "=" not in part:
                                continue
                            k, v = part.split("=", 1)
                            kl = k.strip().lower()
                            vl = v.strip().lower()
                            if kl == "active":
                                active_val = vl in {"on", "1", "true", "yes"}
                            if kl in {"mode", "transcribe"}:
                                mode_val = vl
                        if active_val is not None:
                            self.ingester.update_channel_subscription(
                                channel_key, active=active_val)
                        if mode_val is not None:
                            if mode_val == "default":
                                self.ingester.update_channel_subscription(
                                    channel_key, clear_auto_transcribe=True)
                            elif mode_val in {"on", "true", "1", "yes"}:
                                self.ingester.update_channel_subscription(
                                    channel_key, auto_transcribe=True)
                            elif mode_val in {"off", "false", "0", "no"}:
                                self.ingester.update_channel_subscription(
                                    channel_key, auto_transcribe=False)
                elif row_id in {
                    "ai_provider",
                    "ollama_model",
                    "ollama_base_url",
                    "api_base_url",
                    "api_key_env",
                    "api_model",
                    "summary_instructions_path",
                }:
                    self._ai_settings[row_id] = token
                    if row_id == "ai_provider" and not token:
                        self._ai_settings[row_id] = "ollama"
                elif row_id == "auto_summary_default":
                    self._ai_settings["auto_summary_default"] = token.lower() in {
                        "1", "true", "yes", "on"}
                elif row_id == "summary_segment_limit":
                    self._ai_settings["summary_segment_limit"] = max(
                        0, int(token or "0"))
                elif row_id.startswith("kb:"):
                    action = row_id.split(":", 1)[1]
                    kb = self._ai_settings.get("keybinds")
                    if not isinstance(kb, dict):
                        kb = dict(DEFAULT_KEYBINDS)
                    kb[action] = token or DEFAULT_KEYBINDS.get(action, "")
                    self._ai_settings["keybinds"] = kb
                else:
                    return "Unknown setting"

                self._ai_settings["default_worker_count"] = max(
                    int(self._ai_settings.get("default_downloaders") or 0),
                    int(self._ai_settings.get("default_transcribers") or 0),
                    int(self._ai_settings.get("default_summarizers") or 0),
                )
                self.ingester.set_runtime_options(
                    auto_transcribe_default=bool(self._ai_settings.get(
                        "auto_transcribe_default",
                        True
                    )),
                    subscription_db_max_videos=int(self._ai_settings.get(
                        "subscription_db_max_videos"
                    ) or 0),
                    job_retry_limit=int(self._ai_settings.get(
                        "job_retry_limit"
                    ) or 0),
                    ai_runtime_settings=self._build_ai_runtime_settings(),
                )
                target_downloaders = max(0, int(self._ai_settings.get(
                    "default_downloaders"
                ) or 0))
                target_transcribers = max(0, int(self._ai_settings.get(
                    "default_transcribers"
                ) or 0))
                target_summarizers = max(0, int(self._ai_settings.get(
                    "default_summarizers"
                ) or 0))
                target_workers = max(
                    target_downloaders,
                    target_transcribers,
                    target_summarizers,
                )
                if (
                    self._worker_target_count != target_workers
                    or self._downloader_target_count != target_downloaders
                    or self._transcriber_target_count != target_transcribers
                    or self._summarizer_target_count != target_summarizers
                ):
                    self._restart_workers(
                        target_workers,
                        target_downloaders,
                        target_transcribers,
                        target_summarizers,
                    )

                self._apply_theme()
                self._apply_font_scale_tree(self.root, reset_base=True)
                self._apply_root_chrome_settings()
                self._refresh_caption_view()
                self._apply_shortcut_bindings()
                self._save_gui_settings()

                new_provider = str(self._ai_settings.get(
                    "ai_provider") or "ollama")
                if new_provider.lower() == "ollama":
                    if (
                        prev_provider.lower() != "ollama"
                        or prev_model != str(self._ai_settings.get(
                            "ollama_model"
                        ))
                        or prev_base != str(self._ai_settings.get(
                            "ollama_base_url"
                        ))
                    ):
                        self._start_ollama_bootstrap(
                            background=True, force_reset=True)
                self.status_var.set("Settings saved")
                return None
            except Exception as exc:
                return str(exc)

        for i in range(len(tab_names)):
            _render_tab(i)

        def _start_edit() -> None:
            tab = int(tabs.index("current"))
            rows = tab_rows[tab]
            if not rows:
                return
            row = max(0, min(selected_idx[tab], len(rows) - 1))
            editing["active"] = True
            editing["tab"] = tab
            editing["row"] = row
            editing["orig"] = rows[row]["value"]
            edit_var.set(rows[row]["value"])
            edit_entry.grid()
            edit_entry.focus_set()
            edit_entry.selection_range(0, tk.END)
            status_var.set(
                f"Editing `{rows[row]['key']}` | Enter commit | Esc revert")

        def _stop_edit(*, revert: bool) -> None:
            if not editing["active"]:
                return
            tab = int(editing["tab"])
            row = int(editing["row"])
            rows = tab_rows[tab]
            if not revert and rows and row < len(rows):
                err = _apply_row_value(rows[row]["id"], edit_var.get())
                if err:
                    status_var.set(f"Apply failed: {err}")
                    return
                status_var.set("Saved")
            if revert:
                status_var.set("Edit canceled")
            editing["active"] = False
            edit_entry.grid_remove()
            _render_current()
            key_lists[int(tabs.index("current"))].focus_set()

        def _move_row(delta: int) -> None:
            tab = int(tabs.index("current"))
            rows = tab_rows[tab]
            if not rows:
                return
            selected_idx[tab] = max(
                0, min(selected_idx[tab] + delta, len(rows) - 1))
            _sync_selection(tab)

        def _switch_tab(delta: int) -> None:
            cur = int(tabs.index("current"))
            nxt = max(0, min(cur + delta, len(tab_names) - 1))
            tabs.select(nxt)
            _render_tab(nxt)
            key_lists[nxt].focus_set()

        def _on_key(event: tk.Event[tk.Misc]) -> str | None:
            keysym = str(getattr(event, "keysym", ""))
            if editing["active"]:
                if keysym == "Return":
                    _stop_edit(revert=False)
                    return "break"
                if keysym == "Escape":
                    _stop_edit(revert=True)
                    return "break"
                return None

            if keysym == "Escape":
                popup.destroy()
                return "break"
            if keysym in {"Left", "h", "H"}:
                _switch_tab(-1)
                return "break"
            if keysym in {"Right", "l", "L"}:
                _switch_tab(1)
                return "break"
            if keysym in {"Up", "k", "K"}:
                _move_row(-1)
                return "break"
            if keysym in {"Down", "j", "J"}:
                _move_row(1)
                return "break"
            if keysym == "Prior":
                _move_row(-10)
                return "break"
            if keysym == "Next":
                _move_row(10)
                return "break"
            if keysym == "Home":
                tab = int(tabs.index("current"))
                selected_idx[tab] = 0
                _sync_selection(tab)
                return "break"
            if keysym == "End":
                tab = int(tabs.index("current"))
                rows = tab_rows[tab]
                if rows:
                    selected_idx[tab] = len(rows) - 1
                    _sync_selection(tab)
                return "break"
            if keysym == "Return":
                _start_edit()
                return "break"
            return "break"

        for lb in [*key_lists, *val_lists]:
            lb.bind("<KeyPress>", _on_key, add="+")
            lb.bind("<Button-1>", lambda _e: "break")
        edit_entry.bind("<KeyPress>", _on_key, add="+")
        popup.bind("<KeyPress>", _on_key, add="+")
        if theme_preset_box is not None:
            theme_preset_box.bind(
                "<<ComboboxSelected>>",
                lambda _e: (
                    status_var.set(_apply_row_value("theme_preset", theme_preset_var.get()) or f"Theme preset: {theme_preset_var.get()}"),
                    _render_tab(1),
                ),
                add="+",
            )
        if theme_export_button is not None:
            theme_export_button.bind("<Button-1>", lambda _e: _export_theme_yaml(), add="+")
        tabs.bind(
            "<<NotebookTabChanged>>",
            lambda _e: (
                _render_current(),
                key_lists[int(tabs.index("current"))].focus_set()
            ),
            add="+"
        )
        key_lists[0].focus_set()
