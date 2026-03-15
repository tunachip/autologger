from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from ..constants import FONT_SIZE_OFFSETS

try:
    from PIL import Image, ImageOps, ImageTk
except Exception:
    Image = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]
    ImageTk = None  # type: ignore[assignment]


class SearchPreviewMixin:
    def _normalize_display_list(self, value: Any) -> str:
        if isinstance(value, list):
            parts = [str(item).strip() for item in value if str(item).strip()]
            return ", ".join(parts)
        token = str(value or "").strip()
        if not token:
            return ""
        if token.startswith("[") and token.endswith("]"):
            try:
                parsed = json.loads(token.replace("'", '"'))
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                parts = [str(item).strip() for item in parsed if str(item).strip()]
                return ", ".join(parts)
        return token

    def _display_genre_text(self, row: dict[str, Any]) -> str:
        payload = self._row_metadata_payload(row)
        for key in ("genre", "genres", "categories", "category", "tags"):
            rendered = self._normalize_display_list(payload.get(key))
            if rendered:
                return rendered
        return self._normalize_display_list(
            self._metadata_text_for_field(row, "GENRE").replace("\n", " ").strip()
        )

    def _video_preview_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        payload = self._row_metadata_payload(row)
        title = str(row.get("title") or row.get("video_id") or "untitled").strip()
        creator = " ".join(
            part for part in [
                str(row.get("channel") or ""),
                str(row.get("uploader_id") or ""),
            ] if part
        ).strip() or "unknown"
        genre = self._display_genre_text(row)
        description = " ".join(
            str(part).strip()
            for part in [
                payload.get("description"),
                payload.get("summary"),
            ]
            if str(part or "").strip()
        ).strip()
        thumbnail_url = str(
            payload.get("thumbnail")
            or row.get("thumbnail")
            or row.get("webpage_url")
            or ""
        ).strip()
        video_id = str(row.get("video_id") or "").strip()
        if thumbnail_url and "youtube.com/watch" in thumbnail_url:
            thumbnail_url = ""
        image_path = None
        if video_id and not bool(row.get("_skip_thumbnail_download")):
            image_path = self._download_browse_thumbnail(
                video_id,
                thumbnail_url or f"https://i.ytimg.com/vi/{video_id}/default.jpg",
                cache_dir=self._video_thumb_dir,
                temporary=False,
            )
        return {
            "title": title,
            "creator": creator,
            "genre": genre,
            "description": description or "(no description)",
            "image_path": str(image_path) if image_path else "",
        }

    def _render_video_preview(
        self,
        row: dict[str, Any],
        *,
        image_box: tk.Frame,
        image_label: tk.Label,
        title_var: tk.StringVar,
        creator_var: tk.StringVar,
        genre_var: tk.StringVar,
        description_widget: tk.Text,
        photo_ref: dict[str, Any],
        image_size: tuple[int, int] | Callable[[], tuple[int, int]],
    ) -> None:
        preview = self._video_preview_payload(row)
        title_var.set(str(preview.get("title") or "untitled"))
        creator_var.set(f"creator: {preview.get('creator') or 'unknown'}")
        genre_value = str(preview.get("genre") or "").strip()
        genre_var.set(f"genre: {genre_value}" if genre_value else "genre: (none)")
        description_widget.configure(state="normal")
        description_widget.delete("1.0", tk.END)
        description_widget.insert(
            "1.0",
            "\n\n".join(
                part for part in (
                    f"genre: {genre_value}" if genre_value else "genre: (none)",
                    str(preview.get("description") or "(no description)").strip(),
                )
                if part
            ),
        )
        description_widget.configure(state="disabled")
        try:
            description_widget.yview_moveto(0.0)
        except Exception:
            pass
        image_path = str(preview.get("image_path") or "").strip()
        if image_path and Image is not None and ImageTk is not None:
            try:
                with Image.open(image_path) as img:
                    img = img.convert("RGB")
                    try:
                        box_width = max(1, int(image_box.winfo_width()) - 2)
                    except Exception:
                        box_width = 1
                    if box_width <= 1:
                        fallback_size = image_size() if callable(image_size) else image_size
                        box_width = max(1, int(fallback_size[0]))
                    target_height = max(1, int(round(box_width * 9 / 16)))
                    try:
                        current_height = int(image_box.cget("height"))
                    except Exception:
                        current_height = 0
                    if current_height != target_height:
                        try:
                            image_box.configure(height=target_height)
                            image_box.update_idletasks()
                        except Exception:
                            pass
                    if ImageOps is not None:
                        img = ImageOps.fit(img, (box_width, target_height), method=Image.Resampling.LANCZOS)
                    else:
                        img = img.resize((box_width, target_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                photo_ref["image"] = photo
                image_label.configure(image=photo, text="")
                return
            except Exception:
                pass
        photo_ref["image"] = None
        image_label.configure(image="", text="Preview unavailable")

    def _render_video_preview_placeholder(
        self,
        row: dict[str, Any],
        *,
        image_box: tk.Frame,
        image_label: tk.Label,
        title_var: tk.StringVar,
        creator_var: tk.StringVar,
        genre_var: tk.StringVar,
        description_widget: tk.Text,
        photo_ref: dict[str, Any],
        loading: bool,
    ) -> None:
        preview = self._video_preview_payload({**row, "_skip_thumbnail_download": True})
        title_var.set(str(preview.get("title") or "untitled"))
        creator_var.set(f"creator: {preview.get('creator') or 'unknown'}")
        genre_value = str(preview.get("genre") or "").strip()
        genre_var.set(f"genre: {genre_value}" if genre_value else "genre: (none)")
        description_widget.configure(state="normal")
        description_widget.delete("1.0", tk.END)
        description_widget.insert(
            "1.0",
            "\n\n".join(
                part for part in (
                    f"genre: {genre_value}" if genre_value else "genre: (none)",
                    str(preview.get("description") or "(no description)").strip(),
                )
                if part
            ),
        )
        description_widget.configure(state="disabled")
        try:
            description_widget.yview_moveto(0.0)
        except Exception:
            pass
        photo_ref["image"] = None
        image_label.configure(image="", text="Loading preview..." if loading else "Preview unavailable")

    def _build_video_preview_pane(
        self,
        parent: tk.Misc,
        *,
        image_width: int = 344,
        image_height: int = 194,
    ) -> dict[str, Any]:
        frame = tk.Frame(
            parent,
            bg=self._theme_color("PANEL_BG"),
            highlightthickness=1,
            highlightbackground=self._theme_color("BORDER"),
            bd=0,
        )
        frame.rowconfigure(4, weight=1)
        frame.columnconfigure(0, weight=1)
        image_box = tk.Frame(
            frame,
            bg=self._theme_color("PANEL_BG"),
            height=image_height,
            highlightthickness=0,
            bd=0,
        )
        image_box.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        image_box.grid_propagate(False)
        image_box.rowconfigure(0, weight=1)
        image_box.columnconfigure(0, weight=1)
        image_label = tk.Label(
            image_box,
            bg=self._theme_color("PANEL_BG"),
            fg=self._theme_color("FG_MUTED"),
            text="No preview",
            anchor="center",
            justify="center",
            font=self._ui_font(FONT_SIZE_OFFSETS["BODY"]),
        )
        image_label.grid(row=0, column=0, sticky="nsew")
        title_var = tk.StringVar(value="")
        creator_var = tk.StringVar(value="")
        genre_var = tk.StringVar(value="")
        tk.Label(
            frame,
            textvariable=title_var,
            anchor="w",
            justify="left",
            bg=self._theme_color("PANEL_BG"),
            fg=self._theme_color("FG"),
            font=self._ui_font(FONT_SIZE_OFFSETS["BODY"], bold=True),
            wraplength=image_width,
        ).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        tk.Label(
            frame,
            textvariable=creator_var,
            anchor="w",
            justify="left",
            bg=self._theme_color("PANEL_BG"),
            fg=self._theme_color("FG_SOFT"),
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
            wraplength=image_width,
        ).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 2))
        description = tk.Text(
            frame,
            bg=self._theme_color("PANEL_BG"),
            fg=self._theme_color("FG_SOFT"),
            borderwidth=0,
            highlightthickness=0,
            font=self._ui_font(FONT_SIZE_OFFSETS["SMALL"]),
            wrap="word",
            padx=8,
            pady=6,
            height=8,
        )
        description_scroll = ttk.Scrollbar(frame, orient="vertical", command=description.yview)
        description.configure(yscrollcommand=description_scroll.set)
        description.grid(row=4, column=0, sticky="nsew", padx=(8, 0), pady=(0, 8))
        description_scroll.grid(row=4, column=1, sticky="ns", padx=(4, 8), pady=(0, 8))
        description.configure(state="disabled")

        def _preview_image_size() -> tuple[int, int]:
            try:
                width = max(image_width, int(image_box.winfo_width()) - 2)
            except Exception:
                width = image_width
            try:
                height = max(image_height, int(image_box.winfo_height()) - 2)
            except Exception:
                height = image_height
            return (width, height)

        def _refresh_wrap(_event: tk.Event[tk.Misc] | None = None) -> None:
            try:
                wrap = max(160, int(frame.winfo_width()) - 24)
            except Exception:
                wrap = image_width
            for widget in frame.grid_slaves(column=0):
                if isinstance(widget, tk.Label):
                    try:
                        widget.configure(wraplength=wrap)
                    except Exception:
                        pass

        frame.after(0, _refresh_wrap)
        return {
            "frame": frame,
            "image_box": image_box,
            "image_label": image_label,
            "title_var": title_var,
            "creator_var": creator_var,
            "genre_var": genre_var,
            "description": description,
            "photo_ref": {"image": None},
            "image_size": _preview_image_size,
        }

    def _row_metadata_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        cached = row.get("_metadata_payload")
        if isinstance(cached, dict):
            return cached
        raw = str(row.get("metadata_json") or "").strip()
        if not raw:
            payload: dict[str, Any] = {}
        else:
            try:
                loaded = json.loads(raw)
                payload = dict(loaded) if isinstance(loaded, dict) else {}
            except Exception:
                payload = {}
        row["_metadata_payload"] = payload
        return payload
