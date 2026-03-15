from __future__ import annotations

import io
import urllib.request
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except Exception:
    Image = None  # type: ignore[assignment]

from alog.pipeline import resolve_playback_media_path


class ChannelPreviewMixin:
    def _youtube_thumbnail_candidates(self, video_id: str) -> list[str]:
        token = str(video_id or "").strip()
        if not token:
            return []
        base = f"https://i.ytimg.com/vi/{token}"
        return [
            f"{base}/maxresdefault.jpg",
            f"{base}/sddefault.jpg",
            f"{base}/hqdefault.jpg",
            f"{base}/mqdefault.jpg",
            f"{base}/default.jpg",
        ]

    def _download_browse_thumbnail(
        self,
        video_id: str,
        thumbnail_url: str,
        *,
        cache_dir: Path | None = None,
        temporary: bool = True,
    ) -> Path | None:
        if not video_id or not thumbnail_url:
            return None
        target_dir = cache_dir or self._browse_thumb_dir
        if target_dir is None:
            return None
        out_path = target_dir / f"{video_id}.png"
        if out_path.exists():
            return out_path
        candidate_urls: list[str] = []
        seen: set[str] = set()
        for candidate in [*self._youtube_thumbnail_candidates(video_id), thumbnail_url]:
            token = str(candidate or "").strip()
            if not token or token in seen:
                continue
            seen.add(token)
            candidate_urls.append(token)
        for candidate_url in candidate_urls:
            try:
                req = urllib.request.Request(
                    candidate_url,
                    headers={"User-Agent": "alogger/1.0 (+https://localhost)"},
                )
                with urllib.request.urlopen(req, timeout=6.0) as resp:
                    raw = resp.read()
                if Image is not None:
                    with Image.open(io.BytesIO(raw)) as img:
                        img = img.convert("RGB")
                        img.save(out_path, format="PNG")
                    if temporary:
                        self._browse_temp_files.add(out_path)
                    return out_path
                raw_path = target_dir / f"{video_id}.img"
                raw_path.write_bytes(raw)
                if temporary:
                    self._browse_temp_files.add(raw_path)
                return raw_path
            except Exception:
                continue
        return None

    def _get_browse_preview(
        self,
        row: dict[str, Any],
        *,
        fetch_metadata: bool = True,
    ) -> dict[str, Any]:
        video_id = str(row.get("video_id") or "").strip()
        cache_key = video_id or str(row.get("url") or "").strip()
        if cache_key and cache_key in self._browse_preview_cache:
            cached = dict(self._browse_preview_cache[cache_key])
            has_image = bool(str(cached.get("image_path") or "").strip())
            if has_image:
                return cached

        title = str(row.get("title") or row.get("video_id") or "untitled").strip()
        creator = str(row.get("uploader") or row.get("channel") or "").strip()
        hashtags = self._hashtags_from_text(title)
        thumbnail_url = str(row.get("thumbnail") or "").strip()
        url = str(row.get("url") or "").strip()
        meta_ok = False

        if fetch_metadata and url:
            try:
                meta = dict(self.ingester.fetch_url_metadata(url))
                meta_ok = True
                title = str(meta.get("title") or title).strip()
                creator = str(meta.get("uploader") or meta.get("channel") or creator).strip()
                thumbnail_url = str(meta.get("thumbnail") or thumbnail_url).strip()
                if not hashtags:
                    hashtags = self._hashtags_from_text(str(meta.get("description") or ""))
                if not hashtags:
                    raw_tags = meta.get("tags") or []
                    if isinstance(raw_tags, list):
                        for tag in raw_tags:
                            token = str(tag or "").strip().replace(" ", "")
                            if not token:
                                continue
                            if token.startswith("#"):
                                hashtags.append(token.lower())
                            elif len(hashtags) < 8:
                                hashtags.append(f"#{token.lower()}")
                            if len(hashtags) >= 8:
                                break
            except Exception:
                pass

        if not thumbnail_url and video_id:
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/default.jpg"

        image_path = self._download_browse_thumbnail(video_id, thumbnail_url) if video_id else None
        preview = {
            "video_id": video_id,
            "title": title or "untitled",
            "creator": creator or "unknown",
            "hashtags": hashtags[:8],
            "thumbnail_url": thumbnail_url,
            "image_path": str(image_path) if image_path else "",
            "meta_ok": meta_ok,
        }
        if cache_key and (preview["image_path"] or preview["hashtags"] or preview["title"] or preview["creator"]):
            self._browse_preview_cache[cache_key] = dict(preview)
        return preview

    def _open_video_from_row(self, row: dict[str, Any], *, filter_text: str = "") -> tuple[bool, str]:
        video_id = str(row.get("video_id") or "").strip()
        if not video_id:
            return False, "row has no video_id"
        transcript_raw = str(row.get("transcript_json_path") or "").strip()
        transcript_path = Path(transcript_raw) if transcript_raw else None
        preferred = Path(str(row.get("local_video_path") or "")) if row.get("local_video_path") else None
        if transcript_path is not None and not transcript_path.exists():
            transcript_path = None
        try:
            video_path = resolve_playback_media_path(
                self.ingester_config,
                video_id=video_id,
                preferred_path=preferred,
            )
        except Exception as exc:
            return False, f"playback path error: {exc}"
        audio_path = self._find_audio_sidecar(video_id, video_path)
        self._load_session(
            video_id=video_id,
            transcript_json=transcript_path,
            video_path=video_path,
            audio_path=audio_path,
            start_sec=0.0,
            filter_text=filter_text,
        )
        return True, f"opened video {video_id}"
