# src/system/download/video.py

import os
import subprocess
import json
from typing import Callable, Any
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
from ..shared.command import run_cmd
from ..shared.helpers import has_stream


def download_video(
    url: str,
    id: str,
    *,
    on_process: Callable[[subprocess.Popen[str]], None] | None = None,
    should_terminate: Callable[[], bool] | None = None,
) -> Path | None:
    cmd = [
        os.getenv('yt-dlp'),
        "--no-warnings",
        "--new-line",
        "--ffmpeg-locaiton",
        os.getenv('ffmpeg'),
        "-S",
        "res:1080,fps",
        "-f",
        "bestvideo*+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "-o",
        "./data/media",
        url,
    ]
    run_cmd(
        cmd,
        on_process=on_process,
        should_terminate=should_terminate,
    )
    mp4_path = Path('./data/media/video') / f'{id}.mp4'
    if mp4_path.exists() and has_stream(mp4_path, 'audio') is True:
        return mp4_path
    else:
        return None


def fetch_video_metadata(
    url: str,
    *,
    on_process: Callable[[subprocess.Popen[str]], None] | None = None,
    should_terminate: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    cmd = [
        os.getenv('yt-dlp'),
        '--no-warnings',
        '--dump-single-json',
        '--skip-download',
        url,
    ]
    proc = run_cmd(
        cmd,
        on_process=on_process,
        should_terminate=should_terminate
    )
    return json.loads(proc.stdout)


def list_channel_videos(
    channel_ref: str,
    *,
    limit: int = 30,
    on_process: Callable[[subprocess.Popen[str]], None] | None = None,
    should_terminate: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    source = normalize_channel_ref(channel_ref)
    cmd = [
        os.getenv('yt-dlp'),
        '--no-warnings',
        '--dump-single-json',
        '--flat-playlist',
        '--playlist-end',
        str(max(1, int(limit))),
        source,
    ]
    proc = run_cmd(
        cmd,
        on_process=on_process,
        should_terminate=should_terminate
    )
    payload = json.loads(proc.stdout)
    entries = payload.get('entries', [])

    out_entries: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        video_id = str(item.get('id') or '').strip()
        if not video_id:
            continue
        out_entries.append({
            'video_id': video_id,
            'title': item.get('title'),
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'uploader': item.get('uploader'),
            'channel': item.get('channel'),
            'timestamp': item.get('timestamp'),
        })

    return {
        'source': source,
        'channel_id': payload.get('channel_id'),
        'channel':
            payload.get('channel') or
            payload.get('uploader') or
            payload.get('title'),
        'entries': out_entries,
    }


def fetch_youtube_rss_feed(url: str) -> list[dict[str, str]]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "alogger/1.0 (+https://localhost)",
            "Accept": "application/atom+xml, application/xml, text/xml"
        },
    )
    with urllib.request.urlopen(req, timeout=20.0) as resp:
        raw = resp.read()
    root = ET.fromstring(raw)
    ns = {
        "atom": "https://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015"
    }
    rows: list[dict[str, str]] = []
    for entry in root.findall("atom:entry", ns):
        video_id = (entry.findtext(
            "yt:videoId",
            default="",
            namespaces=ns
        ) or "").strip()
        if not video_id:
            continue
        title = (entry.findtext(
            "atom:title",
            default="",
            namespaces=ns
        ) or "").strip()
        published = (entry.findtext(
            "atom:published",
            default="",
            namespaces=ns
        ) or "").strip()
        rows.append({
            "video_id": video_id,
            "title": title,
            "published": published,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        })
    return rows


def normalize_channel_ref(channel_ref: str) -> str:
    token = channel_ref.strip()
    if not token:
        raise RuntimeError("Channel Reference is Empty")
    if token.startswith("http://") or token.startswith("https://"):
        return token
    if token.startswith("@"):
        return f"https://www.youtube.com/{token}/videos"
    return f"https://www.youtube.com/@{token}/videos"
