from __future__ import annotations

from typing import Any

from ..constants import DEFAULT_KEYBINDS, FONT, THEME, THEME_SETTINGS_FIELDS

SETTINGS_TAB_NAMES = ["Ingest", "Theme", "Search", "Subscription", "AI", "Keybinds"]

SETTINGS_KEYBIND_DEFS: list[tuple[str, str]] = [
    ("Command menu", "open_command"),
    ("Ingest menu", "open_ingest"),
    ("Workflows", "open_workers"),
    ("Open video", "open_video"),
    ("Finder", "open_finder"),
    ("AI", "open_ai"),
    ("Goto", "open_goto"),
    ("Skim toggle", "toggle_skim"),
    ("Settings", "open_settings"),
    ("Quit", "quit"),
    ("Play/Pause", "play_pause"),
    ("Seek back", "seek_back"),
    ("Seek forward", "seek_forward"),
    ("Prev match", "prev_match"),
    ("Next match", "next_match"),
    ("Vim left", "vim_left"),
    ("Vim down", "vim_down"),
    ("Vim up", "vim_up"),
    ("Vim right", "vim_right"),
    ("Clear input", "clear_input"),
    ("Toggle transcript", "toggle_transcript"),
    ("Toggle details", "toggle_details"),
]


def normalize_hex_value(value: str) -> str | None:
    token = value.strip().lower()
    if not token.startswith("#"):
        token = "#" + token
    if len(token) != 7:
        return None
    try:
        int(token[1:], 16)
        return token
    except Exception:
        return None


def subscription_mode_text(row: dict[str, Any]) -> str:
    mode = row.get("auto_transcribe")
    if mode is None:
        return "default"
    return "on" if int(mode) == 1 else "off"


def build_settings_rows(owner: Any, tab_idx: int) -> list[dict[str, str]]:
    if tab_idx == 0:
        return [
            {
                "id": "default_downloaders",
                "key": "Downloaders",
                "value": str(owner._ai_settings.get("default_downloaders", 1)),
            },
            {
                "id": "default_transcribers",
                "key": "Transcribers",
                "value": str(owner._ai_settings.get("default_transcribers", 1)),
            },
            {
                "id": "default_summarizers",
                "key": "Summarizers",
                "value": str(owner._ai_settings.get("default_summarizers", 1)),
            },
            {
                "id": "auto_transcribe_default",
                "key": "Auto Transcribe",
                "value": "on" if owner._auto_transcribe_default() else "off",
            },
            {
                "id": "job_retry_limit",
                "key": "Retry Limit",
                "value": str(owner._ai_settings.get("job_retry_limit", 0)),
            },
            {
                "id": "skim_pre",
                "key": "Skim Pre (ms)",
                "value": str(owner._skim_pre_ms),
            },
            {
                "id": "skim_post",
                "key": "Skim Post (ms)",
                "value": str(owner._skim_post_ms),
            },
        ]
    if tab_idx == 1:
        rows: list[dict[str, str]] = [
            {
                "id": setting_id,
                "key": label,
                "value": str(owner._ai_settings.get(setting_id) or THEME[theme_key]).removeprefix("#"),
            }
            for setting_id, label, theme_key in THEME_SETTINGS_FIELDS
        ]
        rows.extend(
            [
                {
                    "id": "font_family",
                    "key": "Font Family",
                    "value": str(owner._ai_settings.get("font_family") or FONT["STYLE"]),
                },
                {
                    "id": "font_size",
                    "key": "Font Size",
                    "value": str(owner._ai_settings.get("font_size") or FONT["SIZE"]),
                },
                {
                    "id": "show_root_top_bar",
                    "key": "Root Top Bar",
                    "value": "on" if bool(owner._ai_settings.get("show_root_top_bar", True)) else "off",
                },
                {
                    "id": "show_launch_bar",
                    "key": "Launch Bar",
                    "value": "on" if bool(owner._ai_settings.get("show_launch_bar", True)) else "off",
                },
                {
                    "id": "show_popup_top_bar",
                    "key": "Popup Top Bars",
                    "value": "on" if bool(owner._ai_settings.get("show_popup_top_bar", True)) else "off",
                },
                {
                    "id": "default_transcript_hidden",
                    "key": "Default Transcript Hidden",
                    "value": "on" if bool(owner._ai_settings.get("default_transcript_hidden", False)) else "off",
                },
                {
                    "id": "default_details_hidden",
                    "key": "Default Details Hidden",
                    "value": "on" if bool(owner._ai_settings.get("default_details_hidden", False)) else "off",
                },
            ]
        )
        return rows
    if tab_idx == 2:
        return [
            {
                "id": "defer_local_picker_preview",
                "key": "Instant Local Preview",
                "value": "on" if bool(owner._ai_settings.get("defer_local_picker_preview", True)) else "off",
            },
            {
                "id": "defer_browse_preview",
                "key": "Instant Browse Preview",
                "value": "on" if bool(owner._ai_settings.get("defer_browse_preview", True)) else "off",
            },
            {
                "id": "video_picker_default_field",
                "key": "Open Default Field",
                "value": str(owner._ai_settings.get("video_picker_default_field") or "title"),
            },
            {
                "id": "finder_default_field",
                "key": "Finder Default Field",
                "value": str(owner._ai_settings.get("finder_default_field") or "ts"),
            },
        ]
    if tab_idx == 3:
        rows = [
            {
                "id": "subscription_db_max_videos",
                "key": "DB Max Videos",
                "value": str(owner._ai_settings.get("subscription_db_max_videos") or 0),
            }
        ]
        try:
            subs = owner.ingester.list_channel_subscriptions(active_only=False)
            for row in subs:
                key = str(row.get("channel_key") or "")
                title = str(row.get("channel_title") or key)
                active = "on" if int(row.get("active") or 0) == 1 else "off"
                mode = subscription_mode_text(dict(row))
                rows.append(
                    {
                        "id": f"sub:{key}",
                        "key": f"{title} ({key})",
                        "value": f"active={active} mode={mode}",
                    }
                )
        except Exception:
            pass
        return rows
    if tab_idx == 4:
        return [
            {
                "id": "ai_provider",
                "key": "Provider",
                "value": str(owner._ai_settings.get("ai_provider") or "ollama"),
            },
            {
                "id": "ollama_model",
                "key": "Ollama Model",
                "value": str(owner._ai_settings.get("ollama_model") or "llama3.2:3b"),
            },
            {
                "id": "ollama_base_url",
                "key": "Ollama Base URL",
                "value": str(owner._ai_settings.get("ollama_base_url") or "http://127.0.0.1:11434"),
            },
            {
                "id": "api_base_url",
                "key": "API Base URL",
                "value": str(owner._ai_settings.get("api_base_url") or "https://api.openai.com"),
            },
            {
                "id": "api_key_env",
                "key": "API Key Env",
                "value": str(owner._ai_settings.get("api_key_env") or "OPENAI_API_KEY"),
            },
            {
                "id": "api_model",
                "key": "API Model",
                "value": str(owner._ai_settings.get("api_model") or "gpt-4o-mini"),
            },
            {
                "id": "auto_summary_default",
                "key": "Auto Summary",
                "value": "on" if bool(owner._ai_settings.get("auto_summary_default", False)) else "off",
            },
            {
                "id": "summary_segment_limit",
                "key": "Summary Segments",
                "value": str(owner._ai_settings.get("summary_segment_limit") or 0),
            },
            {
                "id": "summary_instructions_path",
                "key": "Summary Instructions",
                "value": str(owner._ai_settings.get("summary_instructions_path") or ""),
            },
        ]
    rows: list[dict[str, str]] = []
    kb = owner._ai_settings.get("keybinds") or {}
    for label, key in SETTINGS_KEYBIND_DEFS:
        rows.append(
            {
                "id": f"kb:{key}",
                "key": label,
                "value": str(kb.get(key, DEFAULT_KEYBINDS.get(key, ""))),
            }
        )
    return rows
