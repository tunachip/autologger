from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk
import urllib.error

from ..constants import FONT_SIZE_OFFSETS, POPUP_SIZES
from .ai_actions import AIActionsMixin


class AIPopupMixin(AIActionsMixin):

    def _open_ai_popup(self) -> None:
        popup = self._create_popup_window(
            name="ai",
            title="Agent",
            size=POPUP_SIZES["AI"],
            attr_name="_ai_popup",
            row_weights={0: 1},
            column_weights={0: 1},
        )
        if popup is None:
            return
        content = self._popup_content(popup)

        shell = tk.Frame(
            content,
            bg=self._theme_color("APP_BG"),
            highlightthickness=0,
            bd=0,
        )
        shell.grid(row=0, column=0, sticky="nsew")
        shell.rowconfigure(1, weight=1)
        shell.columnconfigure(0, weight=1)
        header = tk.Frame(
            shell,
            bg=self._theme_color("SURFACE_BG"),
            highlightthickness=1,
            highlightbackground=self._theme_color("BORDER"),
            bd=0,
        )
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        header.columnconfigure(0, weight=1)
        tk.Label(
            header,
            text="Agent Console",
            anchor="w",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_SOFT"),
            font=self._ui_font(FONT_SIZE_OFFSETS["BODY"], bold=True),
            padx=10,
            pady=6,
        ).grid(row=0, column=0, sticky="ew")
        spinner_var = tk.StringVar(value="")
        tk.Label(
            header,
            textvariable=spinner_var,
            anchor="e",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_ACCENT"),
            font=self._ui_font(FONT_SIZE_OFFSETS["BODY"], bold=True),
            padx=10,
            pady=6,
        ).grid(row=0, column=1, sticky="e")

        feed_shell = tk.Frame(
            shell,
            bg=self._theme_color("PANEL_BG"),
            highlightthickness=1,
            highlightbackground=self._theme_color("BORDER"),
            bd=0,
        )
        feed_shell.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))
        feed_shell.rowconfigure(0, weight=1)
        feed_shell.columnconfigure(0, weight=1)
        feed = tk.Text(
            feed_shell,
            bg=self._theme_color("PANEL_BG"),
            fg=self._theme_color("FG"),
            borderwidth=0,
            highlightthickness=0,
            font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
            wrap="word",
            padx=10,
            pady=10,
            insertbackground=self._theme_color("FG"),
        )
        feed.grid(row=0, column=0, sticky="nsew")
        feed.configure(state="disabled")

        input_var = tk.StringVar(value="")
        prompt_row = tk.Frame(shell, bg=self._theme_color("APP_BG"))
        prompt_row.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))
        prompt_row.columnconfigure(0, weight=1)
        entry = ttk.Entry(prompt_row, textvariable=input_var, style="Filter.TEntry")
        entry.grid(row=0, column=0, sticky="ew")
        send_button = tk.Label(
            prompt_row,
            text="Send",
            anchor="center",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_SOFT"),
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"], bold=True),
            padx=10,
            pady=6,
            cursor="hand2",
        )
        send_button.grid(row=0, column=1, sticky="e", padx=(8, 0))
        send_button.bind("<Enter>", lambda e: e.widget.configure(fg=self._theme_color("FG_ACCENT")), add="+")
        send_button.bind("<Leave>", lambda e: e.widget.configure(fg=self._theme_color("FG_SOFT")), add="+")

        provider = str(self._ai_settings.get("ai_provider", "ollama"))
        if provider.lower() == "ollama":
            self._start_ollama_bootstrap(background=True)
        status_var = tk.StringVar(
            value=self._status_hint("ai", provider=provider)
        )
        status = tk.Label(
            shell,
            textvariable=status_var,
            anchor="w",
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG_MUTED"),
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
            padx=8,
            pady=6,
        )
        status.grid(row=3, column=0, sticky="ew")

        def append_line(prefix: str, text: str) -> None:
            feed.configure(state="normal")
            feed.insert(tk.END, f"[{prefix}] {text}\n\n")
            feed.see("end")
            feed.configure(state="disabled")

        append_line(
            "sys",
            "Agent initialized with app API context. Ask for ingest/search/subscription actions directly.",
        )

        busy_state = {"active": False, "tick": 0}

        def _set_busy(active: bool) -> None:
            busy_state["active"] = bool(active)
            if not active:
                spinner_var.set("")

        def _tick_spinner() -> None:
            if not popup.winfo_exists():
                return
            if busy_state["active"]:
                frames = ["⠁", "⠂", "⠄", "⠂"]
                spinner_var.set(frames[busy_state["tick"] % len(frames)])
                busy_state["tick"] += 1
            else:
                spinner_var.set("")
            popup.after(120, _tick_spinner)

        def send_prompt(_event: tk.Event[tk.Misc] | None = None) -> str:
            prompt = input_var.get().strip()
            if not prompt:
                return "break"
            input_var.set("")
            append_line("you", prompt)
            _set_busy(True)
            prompt_ast = self._prompt_intent_ast(prompt)
            direct_actions = self._infer_actions_from_prompt(prompt)
            if direct_actions:
                append_line("sys", f"AST resolved prompt directly ({
                            len(direct_actions)} action(s)); skipping model.")
                summary = self._execute_agent_actions(
                    direct_actions,
                    emit=lambda p, t: append_line(p, t),
                )
                append_line(
                    "sys",
                    f"Direct-action summary: executed={summary.get('executed', 0)} failed={
                        summary.get('failed', 0)}",
                )
                _set_busy(False)
                status_var.set("Ready")
                if bool(summary.get("close_ai")) and popup.winfo_exists():
                    popup.destroy()
                    self.filter_entry.focus_set()
                return "break"
            if (
                provider.lower() == "ollama"
                and
                not self._ollama_bootstrap_done.is_set()
            ):
                status_var.set(f"Ollama startup: {
                               self._ollama_bootstrap_state} ...")
            else:
                status_var.set("Running model (AST fallback)...")
            self.root.update_idletasks()
            try:
                reply = self._ask_ai(
                    f"User prompt: {prompt}\n"
                    f"Prompt AST: {json.dumps(
                        prompt_ast, ensure_ascii=False)}\n"
                    "Use AST as source of truth when translating to actions."
                )
                actions = self._parse_agent_actions(reply)
                actions = self._coerce_actions_with_prompt_ast(
                    prompt_ast, actions)
                if actions:
                    append_line("ai", f"Action plan received ({
                                len(actions)} action(s))")
                    append_line("sys", f"Executing {len(actions)} action(s)")
                    summary = self._execute_agent_actions(
                        actions,
                        emit=lambda p, t: append_line(p, t),
                    )
                    append_line(
                        "sys",
                        f"Action summary: executed={
                            summary.get('executed', 0)
                        } failed={
                            summary.get('failed', 0)
                        }",
                    )
                    if bool(summary.get("close_ai")) and popup.winfo_exists():
                        popup.destroy()
                        self.filter_entry.focus_set()
                        return "break"
                else:
                    append_line("ai", reply)
                    inferred = self._infer_actions_from_prompt(prompt)
                    if inferred:
                        append_line(
                            "sys",
                            f"No valid action JSON found; inferred {
                                len(inferred)
                            } action(s) from prompt."
                        )
                        summary = self._execute_agent_actions(
                            inferred,
                            emit=lambda p, t: append_line(p, t),
                        )
                        append_line(
                            "sys",
                            f"Inferred-action summary: executed={
                                summary.get('executed', 0)
                            } failed={
                                summary.get('failed', 0)
                            }",
                        )
                        if (
                            bool(summary.get("close_ai"))
                            and popup.winfo_exists()
                        ):
                            popup.destroy()
                            self.filter_entry.focus_set()
                            return "break"
                    else:
                        append_line(
                            "sys", "No structured actions found (expected JSON actions array).")
                        self._record_agent_activity(
                            "info", "AI reply had no structured actions")
                _set_busy(False)
                status_var.set("Ready")
            except urllib.error.URLError as exc:
                append_line("err", str(exc))
                _set_busy(False)
                status_var.set(f"AI error: {exc}")
            except Exception as exc:
                append_line("err", str(exc))
                _set_busy(False)
                status_var.set(f"AI error: {exc}")
            return "break"

        def _tick_status() -> None:
            if not popup.winfo_exists():
                return
            if provider.lower() == "ollama":
                if self._ollama_bootstrap_done.is_set():
                    if self._ollama_bootstrap_success:
                        model = self._ollama_model()
                        status_var.set(
                            f"Provider={provider} ready ({model})")
                    else:
                        status_var.set(
                            f"Ollama init failed: {
                                self._ollama_bootstrap_error
                                or 'unknown error'
                            }"
                        )
                else:
                    status_var.set(f"Ollama startup: {
                                   self._ollama_bootstrap_state} ...")
            popup.after(1000, _tick_status)

        popup.bind("<Escape>", lambda _e: popup.destroy())
        popup.bind("<Return>", send_prompt)
        entry.bind("<Return>", send_prompt)
        entry.bind("<KP_Enter>", send_prompt)
        send_button.bind("<Button-1>", send_prompt, add="+")
        self._focus_popup_entry(popup, entry)
        _tick_spinner()
        _tick_status()
