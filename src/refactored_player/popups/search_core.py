from __future__ import annotations

import colorsys
import tkinter as tk
from pathlib import Path
from typing import Any

from ..constants import PICKER_FIELDS
from ..utils import (
    SearchClause,
    format_hms as _fmt_hms,
    matches_search_query,
    parse_advanced_search_query,
    parse_search_query,
    search_terms,
)
from .search_preview import SearchPreviewMixin


class SearchCoreMixin(SearchPreviewMixin):
    def _default_query_text(self, setting_key: str, fallback_field: str) -> str:
        field = str(self._ai_settings.get(setting_key) or fallback_field).strip().lower().removeprefix("$")
        return f"${field} " if field else ""

    def _picker_sort_setting_key(self, picker_name: str) -> str:
        if picker_name == "queue_picker":
            return "queue_picker_sort_fields"
        if picker_name == "finder":
            return "finder_sort_fields"
        return "video_picker_sort_fields"

    def _picker_fields_setting_key(self, picker_name: str) -> str:
        if picker_name == "queue_picker":
            return "queue_picker_fields"
        if picker_name == "finder":
            return "finder_fields"
        return "video_picker_fields"

    def _picker_fields_for(self, picker_name: str) -> list[str]:
        setting_key = self._picker_fields_setting_key(picker_name)
        raw = self._ai_settings.get(setting_key)
        values = raw if isinstance(raw, list) else []
        fields = [
            str(value).strip().lower()
            for value in values
            if str(value).strip().lower() in PICKER_FIELDS
        ]
        if not fields:
            fields = ["title", "creator", "length"]
        return fields

    def _set_picker_fields(self, picker_name: str, fields: list[str]) -> None:
        normalized = [
            str(field).strip().lower()
            for field in fields
            if str(field).strip().lower() in PICKER_FIELDS
        ]
        if not normalized:
            normalized = ["title", "creator", "length"]
        self._ai_settings[self._picker_fields_setting_key(picker_name)] = normalized
        self._save_gui_settings()

    def _picker_sort_fields_for(self, picker_name: str) -> list[str]:
        raw = self._ai_settings.get(self._picker_sort_setting_key(picker_name))
        values = raw if isinstance(raw, list) else []
        return [
            str(value).strip().lower()
            for value in values
            if str(value).strip().lower() in self._picker_fields_for(picker_name)
        ]

    def _set_picker_sort_fields(self, picker_name: str, fields: list[str]) -> None:
        visible = set(self._picker_fields_for(picker_name))
        normalized = []
        for field in fields:
            token = str(field).strip().lower()
            if token in visible and token not in normalized:
                normalized.append(token)
        self._ai_settings[self._picker_sort_setting_key(picker_name)] = normalized
        self._save_gui_settings()

    def _picker_widths_setting_key(self, picker_name: str) -> str:
        if picker_name == "queue_picker":
            return "queue_picker_field_widths"
        if picker_name == "finder":
            return "finder_field_widths"
        return "video_picker_field_widths"

    def _picker_field_widths_for(self, picker_name: str) -> dict[str, int]:
        raw = self._ai_settings.get(self._picker_widths_setting_key(picker_name))
        if not isinstance(raw, dict):
            return {}
        widths: dict[str, int] = {}
        allowed = set(PICKER_FIELDS)
        if picker_name == "finder":
            allowed.add("matches")
        for key, value in raw.items():
            token = str(key).strip().lower()
            if token not in allowed:
                continue
            try:
                widths[token] = max(48, int(value))
            except Exception:
                continue
        return widths

    def _set_picker_field_widths(self, picker_name: str, widths: dict[str, int]) -> None:
        allowed = set(PICKER_FIELDS)
        if picker_name == "finder":
            allowed.add("matches")
        normalized = {
            str(key).strip().lower(): max(48, int(value))
            for key, value in widths.items()
            if str(key).strip().lower() in allowed
        }
        self._ai_settings[self._picker_widths_setting_key(picker_name)] = normalized
        self._save_gui_settings()

    def _picker_columns_for(self, picker_name: str) -> list[tuple[str, str, int]]:
        widths = self._picker_field_widths_for(picker_name)
        sort_fields = self._picker_sort_fields_for(picker_name)
        columns: list[tuple[str, str, int]] = []
        for field in self._picker_fields_for(picker_name):
            spec = PICKER_FIELDS.get(field, {})
            numeral = "-"
            if field in sort_fields:
                idx = sort_fields.index(field)
                numerals = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ"]
                numeral = numerals[idx] if idx < len(numerals) else str(idx + 1)
            columns.append(
                (
                    field,
                    f"{str(spec.get('label') or field.title())} {numeral}",
                    int(widths.get(field) or spec.get("width") or 120),
                )
            )
        return columns

    def _cycle_picker_sort_field(
        self,
        picker_name: str,
        field_name: str,
        *,
        reverse: bool = False,
    ) -> None:
        field = str(field_name or "").strip().lower()
        visible_fields = self._picker_fields_for(picker_name)
        if field not in visible_fields:
            return
        sort_fields = self._picker_sort_fields_for(picker_name)
        if reverse:
            if field not in sort_fields:
                sort_fields.insert(0, field)
            else:
                idx = sort_fields.index(field)
                if idx >= len(sort_fields) - 1:
                    sort_fields.pop(idx)
                else:
                    sort_fields[idx], sort_fields[idx + 1] = sort_fields[idx + 1], sort_fields[idx]
        else:
            if field not in sort_fields:
                sort_fields.append(field)
            else:
                idx = sort_fields.index(field)
                if idx == 0:
                    sort_fields.pop(idx)
                else:
                    sort_fields[idx], sort_fields[idx - 1] = sort_fields[idx - 1], sort_fields[idx]
        self._set_picker_sort_fields(picker_name, sort_fields)

    def _move_picker_field(
        self,
        picker_name: str,
        field_name: str,
        *,
        delta: int,
    ) -> None:
        field = str(field_name or "").strip().lower()
        fields = self._picker_fields_for(picker_name)
        if field not in fields:
            return
        idx = fields.index(field)
        nxt = max(0, min(len(fields) - 1, idx + int(delta)))
        if idx == nxt:
            return
        fields[idx], fields[nxt] = fields[nxt], fields[idx]
        self._set_picker_fields(picker_name, fields)

    def _picker_field_value(self, row: dict[str, Any], field: str) -> str:
        token = str(field or "").strip().lower()
        if token == "title":
            return str(row.get("title") or row.get("video_id") or "untitled").replace("\n", " ").strip()
        if token == "creator":
            channel = str(row.get("channel") or "").strip()
            uploader = str(row.get("uploader_id") or "").strip()
            if channel:
                return channel.lstrip("@").strip()
            if uploader:
                return uploader.lstrip("@").strip()
            return "unknown"
        if token == "length":
            return self._metadata_text_for_field(row, "LENGTH").split(" ", 1)[-1].strip() or "--:--"
        if token == "genre":
            return self._display_genre_text(row)
        if token == "summary":
            return self._metadata_text_for_field(row, "SUMMARY").replace("\n", " ").strip()
        if token == "date":
            return str(row.get("upload_date") or "").strip()
        if token == "video_id":
            return str(row.get("video_id") or "").strip()
        return ""

    def _picker_row_values(self, row: dict[str, Any], picker_name: str) -> dict[str, str]:
        values = {
            field: self._picker_field_value(row, field)
            for field in self._picker_fields_for(picker_name)
        }
        values["id"] = str(row.get("video_id") or "")
        return values

    def _picker_sort_key(self, row: dict[str, Any], field: str) -> tuple[int, Any]:
        token = str(field or "").strip().lower()
        if token == "length":
            try:
                return (0, int(row.get("duration_sec") or 0))
            except Exception:
                return (1, 0)
        if token == "date":
            return (0, str(row.get("upload_date") or "").strip().lower())
        return (0, self._picker_field_value(row, token).lower())

    def _sort_picker_rows(self, rows: list[dict[str, Any]], picker_name: str) -> list[dict[str, Any]]:
        sort_fields = self._picker_sort_fields_for(picker_name)
        if not sort_fields:
            return rows
        ordered = list(rows)
        for field in reversed(sort_fields):
            ordered.sort(key=lambda row, token=field: self._picker_sort_key(row, token))
        return ordered

    def _picker_clause_colors(self, count: int) -> list[str]:
        accent = str(self._theme_color("FG_ACCENT") or "").strip()
        if not accent.startswith("#") or len(accent) != 7:
            return [accent for _ in range(max(1, count))]
        try:
            r = int(accent[1:3], 16) / 255.0
            g = int(accent[3:5], 16) / 255.0
            b = int(accent[5:7], 16) / 255.0
        except Exception:
            return [accent for _ in range(max(1, count))]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        total = 10
        order = [0, 5, 2, 7, 1, 6, 3, 8, 4, 9]
        palette: list[str] = []
        for idx in range(total):
            nr, ng, nb = colorsys.hls_to_rgb((h + (idx / float(total))) % 1.0, l, max(0.15, s))
            palette.append(
                "#{:02x}{:02x}{:02x}".format(
                    int(max(0, min(255, round(nr * 255.0)))),
                    int(max(0, min(255, round(ng * 255.0)))),
                    int(max(0, min(255, round(nb * 255.0)))),
                )
            )
        arranged = [palette[idx] for idx in order]
        return [arranged[idx % total] for idx in range(max(1, count))]

    def _picker_highlight_specs(
        self,
        query_text: str,
        visible_fields: list[str],
    ) -> list[tuple[set[str], list[str], str]]:
        query = str(query_text or "").strip()
        if not query:
            return []
        specs: list[tuple[set[str], list[str], str]] = []
        if "$" in query or ";" in query or "!" in query or "*" in query:
            clauses = parse_advanced_search_query(query)
            colors = self._picker_clause_colors(len(clauses))
            field_map = {
                "TITLE": {"title"},
                "CREATOR": {"creator"},
                "GENRE": {"genre"},
                "SUMMARY": {"summary"},
                "LENGTH": {"length"},
                "ANY": set(visible_fields),
            }
            for idx, clause in enumerate(clauses):
                if clause.negated or clause.expression.strip() == "*" or clause.field == "TS":
                    continue
                terms = search_terms(clause.expression)
                if not terms:
                    continue
                targets = field_map.get(clause.field, {clause.field.lower()})
                targets = {field for field in targets if field in visible_fields}
                if targets:
                    specs.append((targets, terms, colors[idx]))
            return specs
        clauses = parse_search_query(query)
        colors = self._picker_clause_colors(len(clauses))
        for idx, clause in enumerate(clauses):
            terms = [term for term in clause if term]
            if terms:
                specs.append((set(visible_fields), terms, colors[idx]))
        return specs

    def _attach_picker_fields_menu(
        self,
        button: tk.Menubutton,
        *,
        picker_name: str,
        on_change,
    ) -> dict[str, Any]:
        field_vars: dict[str, Any] = {}
        menu = tk.Menu(
            button,
            tearoff=False,
            bg=self._theme_color("SURFACE_BG"),
            fg=self._theme_color("FG"),
            activebackground=self._theme_color("SELECT_BG"),
            activeforeground=self._theme_color("FG"),
            bd=0,
        )
        button.configure(menu=menu)

        def _toggle(field_name: str) -> None:
            fields = self._picker_fields_for(picker_name)
            enabled = bool(field_vars[field_name].get())
            if enabled and field_name not in fields:
                fields.append(field_name)
            elif not enabled and field_name in fields:
                fields = [field for field in fields if field != field_name]
            self._set_picker_fields(picker_name, fields)
            for token, var in field_vars.items():
                var.set(token in self._picker_fields_for(picker_name))
            on_change()

        for field_name, spec in PICKER_FIELDS.items():
            var = tk.BooleanVar(value=field_name in self._picker_fields_for(picker_name))
            field_vars[field_name] = var
            menu.add_checkbutton(
                label=str(spec.get("label") or field_name.title()),
                variable=var,
                command=lambda name=field_name: _toggle(name),
            )
        return field_vars

    def _darken_hex_color(self, color: str, factor: float = 0.82) -> str:
        token = str(color or "").strip()
        if not token.startswith("#") or len(token) != 7:
            return color
        try:
            r = int(token[1:3], 16)
            g = int(token[3:5], 16)
            b = int(token[5:7], 16)
        except Exception:
            return color
        if r == 0 and g == 0 and b == 0:
            return "#000000"
        return "#{:02x}{:02x}{:02x}".format(
            max(0, min(255, int(r * factor))),
            max(0, min(255, int(g * factor))),
            max(0, min(255, int(b * factor))),
        )

    def _load_transcript_text_for_row(self, row: dict[str, Any]) -> str:
        cached = row.get("_transcript_text")
        if isinstance(cached, str):
            return cached
        transcript_raw = str(row.get("transcript_json_path") or "").strip()
        if not transcript_raw:
            row["_transcript_text"] = ""
            return ""
        transcript_path = Path(transcript_raw)
        if not transcript_path.exists():
            row["_transcript_text"] = ""
            return ""
        try:
            payload = transcript_path.read_text(encoding="utf-8")
        except Exception:
            row["_transcript_text"] = ""
            return ""
        row["_transcript_text"] = payload.lower()
        return row["_transcript_text"]

    def _load_transcript_segments_for_row(self, row: dict[str, Any]) -> list[dict[str, Any]]:
        cached = row.get("_transcript_segments")
        if isinstance(cached, list):
            return cached
        video_id = str(row.get("video_id") or "").strip()
        if not video_id:
            row["_transcript_segments"] = []
            return []
        try:
            segments = [
                dict(segment)
                for segment in self.ingester.db.list_transcript_segments(video_id)
            ]
        except Exception:
            segments = []
        row["_transcript_segments"] = segments
        return segments

    def _metadata_text_for_field(self, row: dict[str, Any], field: str) -> str:
        payload = self._row_metadata_payload(row)
        title = str(row.get("title") or row.get("video_id") or "")
        creator = " ".join(
            part for part in [
                str(row.get("channel") or ""),
                str(row.get("uploader_id") or ""),
            ] if part
        )
        genre = " ".join(
            str(part)
            for part in (
                payload.get("genre"),
                payload.get("categories"),
                payload.get("category"),
                payload.get("tags"),
            )
            if part
        )
        if field == "TITLE":
            return title
        if field == "CREATOR":
            return creator
        if field == "GENRE":
            return genre
        if field == "LENGTH":
            duration = row.get("duration_sec")
            if duration is None:
                return ""
            try:
                seconds = int(duration)
            except Exception:
                return str(duration)
            return f"{seconds} {_fmt_hms(float(seconds))}"
        if field == "SUMMARY":
            return " ".join(
                str(part)
                for part in [
                    payload.get("summary"),
                    payload.get("description"),
                    payload.get("fulltitle"),
                ]
                if part
            )
        if field == "ANY":
            return " ".join(
                part for part in [
                    title,
                    creator,
                    genre,
                    self._metadata_text_for_field(row, "SUMMARY"),
                    self._metadata_text_for_field(row, "LENGTH"),
                    str(row.get("video_id") or ""),
                    str(row.get("source_url") or ""),
                    str(row.get("webpage_url") or ""),
                    str(row.get("upload_date") or ""),
                ] if part
            )
        direct = row.get(field.lower())
        if direct is not None:
            return str(direct)
        meta_value = payload.get(field.lower())
        if meta_value is None:
            meta_value = payload.get(field)
        if isinstance(meta_value, list):
            return " ".join(str(item) for item in meta_value if item is not None)
        if meta_value is not None:
            return str(meta_value)
        return ""

    def _clause_matches_row(self, row: dict[str, Any], clause: SearchClause) -> bool:
        expression = clause.expression.strip()
        if clause.field == "TS":
            haystack = self._load_transcript_text_for_row(row)
        elif clause.field == "ANY":
            haystack = self._metadata_text_for_field(row, "ANY")
            if expression != "*":
                transcript_text = self._load_transcript_text_for_row(row)
                if transcript_text:
                    haystack = f"{haystack} {transcript_text}"
        else:
            haystack = self._metadata_text_for_field(row, clause.field)
        if expression == "*":
            matched = bool(str(haystack).strip())
        else:
            matched = matches_search_query(haystack, expression)
        return (not matched) if clause.negated else matched

    def _score_search_row(self, row: dict[str, Any], clauses: list[SearchClause]) -> int:
        score = 0
        for clause in clauses:
            if clause.negated:
                continue
            if clause.field == "TS":
                haystack = self._load_transcript_text_for_row(row)
            elif clause.field == "ANY":
                haystack = self._metadata_text_for_field(row, "ANY")
            else:
                haystack = self._metadata_text_for_field(row, clause.field)
            if clause.expression == "*":
                score += 1
                continue
            score += sum(haystack.lower().count(term) for term in search_terms(clause.expression))
        return max(1, score)

    def _segment_match_count_for_query(self, row: dict[str, Any], query_text: str) -> int:
        query = str(query_text or "").strip()
        if not query:
            return 0
        segments = self._load_transcript_segments_for_row(row)
        if not segments:
            return 0
        matched: set[int | tuple[int, int, str]] = set()
        for segment in segments:
            text = str(segment.get("text") or "").strip()
            if not text or not matches_search_query(text, query):
                continue
            segment_index = segment.get("segment_index")
            if segment_index is None:
                matched.add(
                    (
                        int(segment.get("start_ms") or 0),
                        int(segment.get("end_ms") or 0),
                        text,
                    )
                )
                continue
            matched.add(int(segment_index))
        return len(matched)

    def _segment_match_count_for_advanced_query(
        self,
        row: dict[str, Any],
        clauses: list[SearchClause],
    ) -> int:
        transcript_clauses = [
            clause
            for clause in clauses
            if not clause.negated and clause.field == "TS" and clause.expression.strip()
        ]
        if not transcript_clauses:
            return 0
        segments = self._load_transcript_segments_for_row(row)
        if not segments:
            return 0
        matched: set[int | tuple[int, int, str]] = set()
        for segment in segments:
            text = str(segment.get("text") or "").strip()
            if not text:
                continue
            if not all(matches_search_query(text, clause.expression) for clause in transcript_clauses):
                continue
            segment_index = segment.get("segment_index")
            if segment_index is None:
                matched.add(
                    (
                        int(segment.get("start_ms") or 0),
                        int(segment.get("end_ms") or 0),
                        text,
                    )
                )
                continue
            matched.add(int(segment_index))
        return len(matched)

    def _candidate_ids_for_clause(self, clause: SearchClause, *, limit: int) -> set[str] | None:
        if clause.negated or clause.expression.strip() == "*":
            return None
        if clause.field == "TS":
            clause_rows: set[str] | None = None
            for term_group in parse_search_query(clause.expression):
                group_rows = {
                    str(row.get("video_id") or "").strip()
                    for term in term_group
                    for row in self.ingester.search_videos(term, limit=max(limit * 4, 120))
                    if str(row.get("video_id") or "").strip()
                }
                clause_rows = group_rows if clause_rows is None else clause_rows.intersection(group_rows)
            return clause_rows or set()
        if clause.field in {"TITLE", "CREATOR", "GENRE", "ANY"}:
            return None
        return None

    def _search_rows_with_advanced_query(self, query_text: str, *, limit: int) -> list[dict[str, Any]]:
        clauses = parse_advanced_search_query(query_text)
        if not clauses:
            return []
        candidate_ids: set[str] | None = None
        for clause in clauses:
            clause_ids = self._candidate_ids_for_clause(clause, limit=limit)
            if clause_ids is None:
                continue
            candidate_ids = clause_ids if candidate_ids is None else candidate_ids.intersection(clause_ids)
            if not candidate_ids:
                return []
        rows = [
            dict(row)
            for row in self.ingester.db.list_playable_videos(limit=max(limit * 8, 1200))
        ]
        if candidate_ids is not None:
            rows = [
                row
                for row in rows
                if str(row.get("video_id") or "").strip() in candidate_ids
            ]
        matches = [
            row
            for row in rows
            if all(self._clause_matches_row(row, clause) for clause in clauses)
        ]
        for row in matches:
            row["match_count"] = (
                self._segment_match_count_for_advanced_query(row, clauses)
                or self._score_search_row(row, clauses)
            )
        matches.sort(
            key=lambda row: (
                -int(row.get("match_count") or 0),
                str(row.get("title") or row.get("video_id") or "").lower(),
            )
        )
        return matches[:limit]

    def _search_videos_with_query(self, query_text: str, *, limit: int) -> list[dict[str, Any]]:
        if "$" in query_text or ";" in query_text or "!" in query_text or "*" in query_text:
            return self._search_rows_with_advanced_query(query_text, limit=limit)
        clauses = parse_search_query(query_text)
        if not clauses:
            return []
        candidate_ids: set[str] | None = None
        first_start_by_id: dict[str, int] = {}
        for clause in clauses:
            clause_ids: set[str] | None = None
            for term in clause:
                rows = [
                    dict(row)
                    for row in self.ingester.search_videos(term, limit=max(limit * 4, 100))
                ]
                term_ids = {
                    str(row.get("video_id") or "").strip()
                    for row in rows
                    if str(row.get("video_id") or "").strip()
                }
                for row in rows:
                    video_id = str(row.get("video_id") or "").strip()
                    if not video_id:
                        continue
                    start_ms = int(row.get("first_start_ms") or 0)
                    if video_id not in first_start_by_id:
                        first_start_by_id[video_id] = start_ms
                    else:
                        first_start_by_id[video_id] = min(first_start_by_id[video_id], start_ms)
                clause_ids = term_ids if clause_ids is None else clause_ids.intersection(term_ids)
            if clause_ids is None:
                continue
            candidate_ids = clause_ids if candidate_ids is None else candidate_ids.union(clause_ids)
        if not candidate_ids:
            return []
        rows = [
            dict(row)
            for row in self.ingester.db.list_playable_videos(limit=max(limit * 8, 1200))
            if str(row.get("video_id") or "").strip() in candidate_ids
        ]
        for row in rows:
            row["match_count"] = self._segment_match_count_for_query(row, query_text)
            row["first_start_ms"] = first_start_by_id.get(
                str(row.get("video_id") or "").strip(),
                int(row.get("first_start_ms") or 0),
            )
        rows.sort(
            key=lambda row: (
                -int(row.get("match_count") or 0),
                int(row.get("first_start_ms") or 0),
            )
        )
        return rows[:limit]

    def _search_video_titles_with_query(self, query_text: str, *, limit: int) -> list[dict[str, Any]]:
        if "$" in query_text or ";" in query_text or "!" in query_text or "*" in query_text:
            return self._search_rows_with_advanced_query(query_text, limit=limit)
        rows = [
            dict(row)
            for row in self.ingester.search_video_titles("", limit=max(limit * 4, 300))
        ]
        if not query_text.strip():
            return rows[:limit]
        filtered = [
            row
            for row in rows
            if matches_search_query(
                str(row.get("title") or row.get("video_id") or ""),
                query_text,
            )
        ]
        filtered.sort(
            key=lambda row: str(row.get("title") or row.get("video_id") or "").lower()
        )
        return filtered[:limit]
