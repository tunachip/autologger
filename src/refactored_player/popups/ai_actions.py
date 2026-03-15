from __future__ import annotations

import ast
import json
import re
from typing import Any, Callable

from log.ai import ask_ai_text

from ..utils import format_hms as _fmt_hms


class AIActionsMixin:
    def _ask_ai(self, prompt: str) -> str:
        api_context = self._agent_api_context()
        if api_context:
            prompt = (
                f"{api_context}\n\nUser request:\n{prompt}\n\n"
                "Return ONLY JSON with top-level key `actions` (array)."
            )
        return ask_ai_text(
            prompt,
            self._ai_settings,
            ensure_ollama_ready=lambda: self._ensure_ollama_ready(block=True),
        )

    def _agent_api_context(self) -> str:
        return (
            "You are the in-app ALogger agent. Use this API surface:\n"
            "- list_channel_videos(channel_ref, limit:int<=100) -> channel metadata + entries[{title, video_id, url}]\n"
            "- enqueue_with_dedupe(urls:list[str], allow_overwrite:bool=False, auto_transcribe:bool|None)\n"
            "- add_channel_subscription(channel_ref, seed_with_latest:bool=True, auto_transcribe:bool|None)\n"
            "- list_channel_subscriptions(active_only:bool=False)\n"
            "- update_channel_subscription(channel_key, active:bool|None, auto_transcribe:bool|None, clear_auto_transcribe:bool=False)\n"
            "- poll_subscriptions_once()\n"
            "- search_video_titles(query, limit)\n"
            "- search_video_metadata(query, limit)  # matches title/channel/uploader/video_id/url with fuzzy fallback\n"
            "- search_videos(query, limit) and search_segments(query, limit)\n"
            "- jobs_summary(limit), dashboard_snapshot()\n"
            "- delete_video_and_assets(video_id)\n"
            "Preferred action schema (JSON only):\n"
            "{ \"actions\": [ {\"action\": \"<name>\", ...args } ] }\n"
            "Supported actions you can emit:\n"
            "- ingest_recent_matching_channel(channel_ref, query, count, fetch_limit=50, auto_transcribe=true)\n"
            "- enqueue_urls(urls, auto_transcribe=true)\n"
            "- list_channel_videos(channel_ref, limit=30)\n"
            "- subscribe_channel(channel_ref, auto_transcribe=null)\n"
            "- poll_subscriptions()\n"
            "- clear_queue()\n"
            "- kill_jobs()\n"
            "- open_video(video_id=<id>) OR open_video(query=<title query>)\n"
            "Rules:\n"
            "1) Prefer deterministic, minimal API calls.\n"
            "2) When asked to ingest N recent channel videos matching a title phrase:\n"
            "   call list_channel_videos(channel, limit=30-100), filter title case-insensitively, sort by listing order as newest-first, take N, enqueue URLs.\n"
            "3) Return concise action steps and the exact API calls/arguments."
        )

    def _parse_agent_actions(self, text: str) -> list[dict[str, Any]]:
        src = text.strip()
        if not src:
            return []
        for payload in self._agent_action_candidates(src):
            data = self._decode_agent_action_payload(payload)
            if data is None:
                continue
            actions = self._extract_agent_actions(data)
            if actions:
                return actions
        return []

    def _agent_action_candidates(self, src: str) -> list[str]:
        candidates: list[str] = []
        fenced = re.findall(
            r"```(?:json)?\s*(.*?)```",
            src,
            flags=re.IGNORECASE | re.DOTALL,
        )
        candidates.extend(candidate.strip() for candidate in fenced if candidate.strip())
        for pattern in (r"(\{[\s\S]*\})", r"(\[[\s\S]*\])"):
            match = re.search(pattern, src)
            if match:
                candidates.append(match.group(1).strip())
        candidates.append(src)
        return candidates

    def _decode_agent_action_payload(self, payload: str) -> Any | None:
        data = self._load_agent_action_data(payload)
        if data is None:
            return None
        if isinstance(data, str):
            inner = data.strip()
            if inner.startswith("{") or inner.startswith("["):
                return self._load_agent_action_data(inner)
        return data

    def _load_agent_action_data(self, payload: str) -> Any | None:
        try:
            return json.loads(payload)
        except Exception:
            try:
                return ast.literal_eval(payload)
            except Exception:
                return None

    def _extract_agent_actions(self, data: Any) -> list[dict[str, Any]]:
        if isinstance(data, dict):
            actions = data.get("actions")
            if isinstance(actions, list):
                return [item for item in actions if isinstance(item, dict)]
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _normalize_agent_action_name(self, name: str) -> str:
        key = str(name or "").strip().lower()
        alias_map = {
            "download_most_recent_video": "ingest_recent_matching_channel",
            "download_recent_video": "ingest_recent_matching_channel",
            "ingest_recent_video": "ingest_recent_matching_channel",
            "enqueue_video_urls": "enqueue_urls",
            "play_video": "open_video",
            "launch_video": "open_video",
        }
        return alias_map.get(key, key)

    def _prompt_intent_ast(self, prompt: str) -> dict[str, Any]:
        raw = prompt.strip()
        low = raw.lower()
        wants_download = any(k in low for k in ("download", "ingest", "queue", "enqueue"))
        wants_play = any(k in low for k in ("play", "open", "watch"))
        wants_recent = any(k in low for k in ("most recent", "latest", "newest", "recent"))
        m_from = re.search(r"(?:from|by)\s+([a-z0-9_@.\-]+)", low)
        channel_ref = m_from.group(1).strip() if m_from else ""
        count = 1
        m_count = re.search(r"\b(\d+)\b", low)
        if m_count:
            count = max(1, int(m_count.group(1)))
        else:
            word_to_num = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            }
            for w, n in word_to_num.items():
                if re.search(rf"\b{w}\b", low):
                    count = n
                    break
        query = ""
        m_title_phrase = re.search(
            r"(?:with|containing)\s+['\"]?(.+?)['\"]?\s+in\s+(?:the\s+)?title\b",
            raw,
            flags=re.IGNORECASE,
        )
        if m_title_phrase:
            query = m_title_phrase.group(1).strip()
        m_contains = re.search(r"(?:containing|contains|with)\s+['\"]?([^'\"]+)['\"]?", raw, flags=re.IGNORECASE)
        if m_contains and not query:
            query = m_contains.group(1).strip()
        if not channel_ref and wants_download:
            m_recent_channel = re.search(r"(?:most\s+recent|latest|newest|recent)\s+([a-z0-9_@.\-]+)\s+video[s]?\b", low)
            if m_recent_channel:
                channel_ref = m_recent_channel.group(1).strip()
        if not channel_ref and wants_download:
            m_download_channel = re.search(
                r"\bdownload\s+(?:the\s+)?(?:most\s+recent|latest|newest|recent\s+)?([a-z0-9_@.\-]+)\s+video[s]?\b",
                low,
            )
            if m_download_channel:
                channel_ref = m_download_channel.group(1).strip()
        if not channel_ref and wants_download:
            scrub = re.sub(r"[^a-z0-9_@.\-\s]", " ", low)
            tokens = [t for t in scrub.split() if t]
            stop = {
                "download", "ingest", "queue", "enqueue", "the", "a", "an",
                "most", "recent", "latest", "newest", "video", "videos",
                "from", "by", "please", "and", "of", "to", "for", "me",
                "with", "containing", "contains",
            }
            candidates = [t for t in tokens if t not in stop and not t.isdigit()]
            if candidates:
                candidates.sort(key=lambda t: (any(ch in t for ch in "_-.@"), len(t)), reverse=True)
                channel_ref = candidates[0]
        return {
            "wants_download": wants_download,
            "wants_play": wants_play,
            "wants_recent": wants_recent,
            "channel_ref": channel_ref,
            "query": query,
            "count": count,
            "raw_prompt": raw,
        }

    def _coerce_actions_with_prompt_ast(
        self,
        prompt_ast: dict[str, Any],
        actions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not actions:
            return actions
        wants_download = bool(prompt_ast.get("wants_download"))
        wants_play = bool(prompt_ast.get("wants_play"))
        channel_ref = str(prompt_ast.get("channel_ref") or "").strip()
        query = str(prompt_ast.get("query") or "").strip()
        count = max(1, int(prompt_ast.get("count") or 1))
        normalized: list[dict[str, Any]] = []
        for act in actions:
            item = dict(act)
            item["action"] = self._normalize_agent_action_name(str(item.get("action") or ""))
            normalized.append(item)
        if wants_download:
            if not channel_ref:
                for a in normalized:
                    maybe = str(
                        a.get("channel_ref")
                        or a.get("channel")
                        or a.get("creator")
                        or a.get("uploader")
                        or ""
                    ).strip()
                    if maybe:
                        channel_ref = maybe
                        break
                if not channel_ref:
                    for a in normalized:
                        if str(a.get("action")) == "open_video":
                            maybe = str(a.get("query") or "").strip()
                            if maybe and " " not in maybe:
                                channel_ref = maybe
                                break
            if channel_ref:
                return [{
                    "action": "ingest_recent_matching_channel",
                    "channel_ref": channel_ref,
                    "query": query,
                    "count": count,
                    "fetch_limit": max(30, min(100, count * 10)),
                    "auto_transcribe": True,
                }]
            return [a for a in normalized if str(a.get("action")) in {"ingest_recent_matching_channel", "enqueue_urls", "list_channel_videos"}]
        if wants_play:
            has_open = any(str(a.get("action")) == "open_video" for a in normalized)
            if not has_open:
                q = query or channel_ref or ""
                if q:
                    normalized.insert(0, {"action": "open_video", "query": q})
        return normalized

    def _infer_actions_from_prompt(self, prompt: str) -> list[dict[str, Any]]:
        text = prompt.strip()
        low = text.lower()
        prompt_ast = self._prompt_intent_ast(text)
        actions: list[dict[str, Any]] = []
        ref = str(prompt_ast.get("channel_ref") or "").strip(" .,!?:;\"'")
        count = max(1, int(prompt_ast.get("count") or 1))
        query = str(prompt_ast.get("query") or "")
        if bool(prompt_ast.get("wants_download")) and ref:
            actions.append({
                "action": "ingest_recent_matching_channel",
                "channel_ref": ref,
                "query": query,
                "count": count,
                "fetch_limit": max(30, min(100, count * 10)),
                "auto_transcribe": True,
            })
            return actions
        is_phrase_request = bool(re.search(r"\b(most\s+recent|latest|newest|recent)\b", low)) and "video" in low
        has_explicit_non_ingest_intent = any(k in low for k in ("play", "open", "watch", "subscribe"))
        if ref and is_phrase_request and not has_explicit_non_ingest_intent:
            actions.append({
                "action": "ingest_recent_matching_channel",
                "channel_ref": ref,
                "query": query,
                "count": count,
                "fetch_limit": max(30, min(100, count * 10)),
                "auto_transcribe": True,
            })
            return actions
        if bool(prompt_ast.get("wants_play")):
            q = re.sub(r"^(play|open|watch)\s+", "", text, flags=re.IGNORECASE).strip()
            q = re.sub(r"\s+video[s]?\s*$", "", q, flags=re.IGNORECASE).strip()
            if q:
                actions.append({"action": "open_video", "query": q})
                return actions
        return actions

    def _hashtags_from_text(self, text: str) -> list[str]:
        tags = re.findall(r"#([a-z0-9_]+)", str(text or ""), flags=re.IGNORECASE)
        out: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            token = f"#{tag.lower()}"
            if token in seen:
                continue
            seen.add(token)
            out.append(token)
        return out

    def _record_agent_activity(self, kind: str, message: str) -> None:
        stamp = _fmt_hms(max(0, self.player.get_time()) / 1000.0) if hasattr(self, "player") else "00:00:00"
        self._agent_activity.append({
            "time": stamp,
            "kind": str(kind).strip() or "info",
            "message": str(message).strip(),
        })
        if len(self._agent_activity) > 300:
            self._agent_activity = self._agent_activity[-300:]

    def _execute_agent_actions(
        self,
        actions: list[dict[str, Any]],
        *,
        emit: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        should_close_ai = False
        executed = 0
        failed = 0
        events: list[dict[str, str]] = []
        if not actions:
            return {"close_ai": False, "executed": 0, "failed": 0, "events": events}
        for i, act in enumerate(actions, start=1):
            name = str(act.get("action") or "").strip().lower()
            if not name:
                if emit:
                    emit("err", f"action #{i}: missing `action`")
                failed += 1
                continue
            name = self._normalize_agent_action_name(name)
            try:
                if name == "ingest_recent_matching_channel":
                    channel_ref = str(
                        act.get("channel_ref")
                        or act.get("channel")
                        or act.get("creator")
                        or act.get("uploader")
                        or ""
                    ).strip()
                    query = str(act.get("query") or "").strip().lower()
                    count = max(1, int(act.get("count") or 1))
                    fetch_limit = max(count, min(100, int(act.get("fetch_limit") or 50)))
                    auto_transcribe = bool(act.get("auto_transcribe", True))
                    data = self.ingester.list_channel_videos(channel_ref, limit=fetch_limit)
                    entries = [dict(r) for r in (data.get("entries") or [])]
                    matched: list[dict[str, Any]] = []
                    for row in entries:
                        title = str(row.get("title") or "").lower()
                        if query and query not in title:
                            continue
                        matched.append(row)
                        if len(matched) >= count:
                            break
                    urls = [str(r.get("url") or "").strip() for r in matched if str(r.get("url") or "").strip()]
                    result = self.ingester.enqueue_with_dedupe(urls, allow_overwrite=False, auto_transcribe=auto_transcribe)
                    ids = list(result.get("queued_ids") or [])
                    self.status_var.set(f"Agent queued {len(ids)} ingest jobs")
                    message = f"{name}: matched={len(matched)} queued={len(ids)}"
                    if emit:
                        emit("act", message)
                    executed += 1
                    events.append({"kind": "act", "message": message})
                    continue
                if name == "enqueue_urls":
                    raw_urls = act.get("urls") or []
                    urls = [str(u).strip() for u in raw_urls if str(u).strip()]
                    auto_transcribe = bool(act.get("auto_transcribe", True))
                    result = self.ingester.enqueue_with_dedupe(urls, allow_overwrite=False, auto_transcribe=auto_transcribe)
                    ids = list(result.get("queued_ids") or [])
                    message = f"{name}: queued={len(ids)}"
                    self.status_var.set(f"Agent queued {len(ids)} ingest jobs")
                    if emit:
                        emit("act", message)
                    executed += 1
                    events.append({"kind": "act", "message": message})
                    continue
                if name == "list_channel_videos":
                    channel_ref = str(act.get("channel_ref") or "").strip()
                    limit = max(1, min(100, int(act.get("limit") or 30)))
                    data = self.ingester.list_channel_videos(channel_ref, limit=limit)
                    message = f"{name}: channel={data.get('channel')} entries={len(data.get('entries') or [])}"
                    if emit:
                        emit("act", message)
                    executed += 1
                    events.append({"kind": "act", "message": message})
                    continue
                if name == "search_video_metadata":
                    query = str(act.get("query") or "").strip()
                    limit = max(1, min(200, int(act.get("limit") or 30)))
                    rows = self.ingester.search_video_metadata(query, limit=limit)
                    message = f"{name}: query={query!r} matches={len(rows)}"
                    if emit:
                        emit("act", message)
                    executed += 1
                    events.append({"kind": "act", "message": message})
                    continue
                if name == "subscribe_channel":
                    channel_ref = str(act.get("channel_ref") or "").strip()
                    auto_mode = act.get("auto_transcribe", None)
                    auto_transcribe = None if auto_mode is None else bool(auto_mode)
                    sub = self.ingester.add_channel_subscription(channel_ref, seed_with_latest=True, auto_transcribe=auto_transcribe)
                    message = f"{name}: {sub.get('channel_title')} ({sub.get('channel_key')})"
                    if emit:
                        emit("act", message)
                    executed += 1
                    events.append({"kind": "act", "message": message})
                    continue
                if name == "poll_subscriptions":
                    summary = self.ingester.poll_subscriptions_once()
                    message = f"{name}: scanned={summary.get('scanned', 0)} queued={summary.get('queued', 0)}"
                    if emit:
                        emit("act", message)
                    executed += 1
                    events.append({"kind": "act", "message": message})
                    continue
                if name == "clear_queue":
                    n = int(self.ingester.clear_queue())
                    message = f"{name}: cleaned={n}"
                    if emit:
                        emit("act", message)
                    executed += 1
                    events.append({"kind": "act", "message": message})
                    continue
                if name == "kill_jobs":
                    n = int(self.ingester.kill_active_jobs())
                    if emit:
                        emit("act", f"{name}: killed={n}")
                    executed += 1
                    events.append({"kind": "act", "message": f"{name}: killed={n}"})
                    continue
                if name == "open_video":
                    video_id = str(act.get("video_id") or "").strip()
                    query = str(act.get("query") or "").strip()
                    row: dict[str, Any] | None = None
                    if video_id:
                        done = self.ingester.db.get_latest_done_job_for_video(video_id)  # type: ignore[attr-defined]
                        if done:
                            row = dict(done)
                    if row is None and query:
                        rows = self.ingester.search_video_metadata(query, limit=50)
                        if not rows:
                            rows = self.ingester.search_video_titles(query, limit=50)
                        if rows:
                            row = dict(rows[0])
                    if row is None:
                        if emit:
                            emit("err", f"{name}: no matching playable video")
                        continue
                    ok, msg = self._open_video_from_row(row, filter_text=query)
                    if emit:
                        emit("act" if ok else "err", f"{name}: {msg}")
                    if ok:
                        executed += 1
                        events.append({"kind": "act", "message": f"{name}: {msg}"})
                        should_close_ai = True
                    else:
                        failed += 1
                        events.append({"kind": "err", "message": f"{name}: {msg}"})
                    continue
                if emit:
                    emit("err", f"unsupported action: {name}")
                failed += 1
                events.append({"kind": "err", "message": f"unsupported action: {name}"})
            except Exception as exc:
                if emit:
                    emit("err", f"{name} failed: {exc}")
                failed += 1
                events.append({"kind": "err", "message": f"{name} failed: {exc}"})
        summary = {"close_ai": should_close_ai, "executed": executed, "failed": failed, "events": events}
        self._record_agent_activity("summary", f"actions={len(actions)} executed={executed} failed={failed}")
        for ev in events:
            self._record_agent_activity(str(ev.get("kind") or "act"), str(ev.get("message") or ""))
        return summary
