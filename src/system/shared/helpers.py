# src/system/shared/helpers.py

import subprocess
import json
from pathlib import Path


def has_stream(path: Path, stream_type: str) -> bool | None:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    streams = payload.get("streams", [])
    return any(str(s.get('codec_type')) == stream_type
               for s in streams if isinstance(s, dict))


def _select_primary(filetype: str, paths: list[Path]) -> Path | None:
    if filetype == 'video':
        ext_rank = {
            '.mkv': 5,
            '.mp4': 4,
            '.webm': 3,
            '.mov': 2,
            '.m4v': 2,
        }
    elif filetype == 'audio':
        ext_rank = {
            '.mp3': 3,
            '.wav': 2,
            '.flac': 1,
        }
    elif filetype == 'image':
        ext_rank = {
        }
    else:
        return None
    return sorted(
        paths,
        key=lambda p: (ext_rank.get(p.suffix.lower(), 0), p.stat().st_size),
        reverse=True,
    )[0]


def _fallback_paths(media_dir: Path, id: str | None) -> list[Path]:
    if not id:
        return []
    return sorted([
        path for path in media_dir.glob(f"{id}*")
        if path.is_file()
        and not path.name.endswith(".part")
    ])
