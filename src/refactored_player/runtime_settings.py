from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import urllib.request
from typing import Any

from .constants import DEFAULT_KEYBINDS, build_default_gui_settings


class RuntimeSettingsMixin:
    def _load_gui_settings(self) -> dict[str, Any]:
        settings = build_default_gui_settings()
        if not self._gui_settings_path:
            return settings
        try:
            if self._gui_settings_path.exists():
                payload = json.loads(self._gui_settings_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    settings.update(payload)
                    keybinds = payload.get("keybinds")
                    if isinstance(keybinds, dict):
                        merged = dict(DEFAULT_KEYBINDS)
                        for key, value in keybinds.items():
                            if isinstance(key, str) and isinstance(value, str):
                                merged[key] = value
                        settings["keybinds"] = merged
        except Exception:
            pass
        return settings

    def _save_gui_settings(self) -> None:
        try:
            self._gui_settings_path.parent.mkdir(parents=True, exist_ok=True)
            self._gui_settings_path.write_text(
                json.dumps(
                    self._ai_settings,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _ollama_base_url(self) -> str:
        return str(
            self._ai_settings.get("ollama_base_url")
            or "http://127.0.0.1:11434"
        ).rstrip("/")

    def _ollama_model(self) -> str:
        return str(
            self._ai_settings.get("ollama_model")
            or "llama3.2:3b"
        ).strip() or "llama3.2:3b"

    def _auto_transcribe_default(self) -> bool:
        return bool(self._ai_settings.get("auto_transcribe_default", True))

    def _build_ai_runtime_settings(self) -> dict[str, Any]:
        return {
            "ai_provider": str(self._ai_settings.get("ai_provider") or "ollama"),
            "ollama_model": str(self._ai_settings.get("ollama_model") or "llama3.2:3b"),
            "ollama_base_url": str(
                self._ai_settings.get("ollama_base_url")
                or "http://127.0.0.1:11434"
            ),
            "api_base_url": str(
                self._ai_settings.get("api_base_url")
                or "https://api.openai.com"
            ),
            "api_key_env": str(
                self._ai_settings.get("api_key_env")
                or "OPENAI_API_KEY"
            ),
            "api_model": str(self._ai_settings.get("api_model") or "gpt-4o-mini"),
            "auto_summary_default": bool(
                self._ai_settings.get("auto_summary_default", False)
            ),
            "summary_segment_limit": max(
                0,
                int(self._ai_settings.get("summary_segment_limit") or 0),
            ),
            "summary_instructions_path": str(
                self._ai_settings.get("summary_instructions_path") or ""
            ),
        }

    def _ollama_server_healthy(self) -> bool:
        try:
            req = urllib.request.Request(
                f"{self._ollama_base_url()}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                resp.read()
            return True
        except Exception:
            return False

    def _ollama_model_exists(self, model: str) -> bool:
        try:
            req = urllib.request.Request(
                f"{self._ollama_base_url()}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            models = payload.get("models") or []
            if not isinstance(models, list):
                return False
            aliases = {model, f"{model}:latest"} if ":" not in model else {model}
            for item in models:
                if (
                    isinstance(item, dict)
                    and str(item.get("name") or "").strip() in aliases
                ):
                    return True
            return False
        except Exception:
            return False

    def _start_ollama_server(self) -> None:
        if self._ollama_proc and self._ollama_proc.poll() is None:
            return
        kwargs: dict[str, Any] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "text": True,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        self._ollama_proc = subprocess.Popen(["ollama", "serve"], **kwargs)
        self._ollama_started_by_app = True

    def _reset_ollama_bootstrap(self) -> None:
        self._ollama_bootstrap_done.clear()
        self._ollama_bootstrap_success = False
        self._ollama_bootstrap_error = None
        self._ollama_bootstrap_state = "idle"

    def _bootstrap_ollama(self) -> None:
        with self._ollama_bootstrap_lock:
            if (
                self._ollama_bootstrap_done.is_set()
                and self._ollama_bootstrap_success
            ):
                return
            model = self._ollama_model()
            try:
                self._ollama_bootstrap_state = "checking_server"
                if not self._ollama_server_healthy():
                    self._ollama_bootstrap_state = "starting_server"
                    self._start_ollama_server()
                    deadline = time.time() + 25.0
                    while time.time() < deadline:
                        if self._ollama_server_healthy():
                            break
                        time.sleep(0.5)
                    if not self._ollama_server_healthy():
                        raise RuntimeError(
                            "ollama server did not become healthy on 127.0.0.1:11434"
                        )
                self._ollama_bootstrap_state = "checking_model"
                if not self._ollama_model_exists(model):
                    self._ollama_bootstrap_state = "pulling_model"
                    proc = subprocess.run(
                        ["ollama", "pull", model],
                        capture_output=True,
                        text=True,
                    )
                    if proc.returncode != 0:
                        raise RuntimeError(
                            f"failed to pull Ollama model '{model}': "
                            f"{proc.stderr.strip() or proc.stdout.strip()}"
                        )
                    if not self._ollama_model_exists(model):
                        raise RuntimeError(f"model '{model}' still missing after pull")
                self._ollama_bootstrap_success = True
                self._ollama_bootstrap_error = None
                self._ollama_bootstrap_state = "ready"
            except FileNotFoundError:
                self._ollama_bootstrap_success = False
                self._ollama_bootstrap_error = "ollama binary not found in PATH"
                self._ollama_bootstrap_state = "error"
            except Exception as exc:
                self._ollama_bootstrap_success = False
                self._ollama_bootstrap_error = str(exc)
                self._ollama_bootstrap_state = "error"
            finally:
                self._ollama_bootstrap_done.set()

    def _start_ollama_bootstrap(
        self,
        *,
        background: bool,
        force_reset: bool = False,
    ) -> None:
        if str(self._ai_settings.get("ai_provider") or "ollama").lower() != "ollama":
            return
        if force_reset:
            self._reset_ollama_bootstrap()
        if (
            self._ollama_bootstrap_done.is_set()
            and self._ollama_bootstrap_success
        ):
            return
        if background:
            if (
                self._ollama_bootstrap_thread
                and self._ollama_bootstrap_thread.is_alive()
            ):
                return
            self._ollama_bootstrap_thread = threading.Thread(
                target=self._bootstrap_ollama,
                daemon=True,
                name="alog-ollama-bootstrap",
            )
            self._ollama_bootstrap_thread.start()
            return
        self._bootstrap_ollama()

    def _ensure_ollama_ready(
        self,
        *,
        block: bool = True,
    ) -> None:
        if str(self._ai_settings.get("ai_provider") or "ollama").lower() != "ollama":
            return
        self._start_ollama_bootstrap(background=not block)
        if block:
            self._ollama_bootstrap_done.wait(timeout=600.0)
            if not self._ollama_bootstrap_done.is_set():
                raise RuntimeError("Timed out preparing Ollama")
            if not self._ollama_bootstrap_success:
                raise RuntimeError(
                    self._ollama_bootstrap_error
                    or "Ollama initialization failed"
                )
