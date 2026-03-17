# src/system/player/video.py

import os
import subprocess
from typing import Callable
from pathlib import Path
from ..shared.command import run_cmd
from ..shared.helpers import has_stream, _select_primary, _fallback_paths


def merge_streams(
    *,
    id: str,
    on_process: Callable[[subprocess.Popen[str]], None] | None = None,
    should_terminate: Callable[[], bool] | None = None,
) -> Path | None:
    """ Merges Audio & Video Streams into a Single Player-Ready Video File """

    candidates = _fallback_paths(Path('./data/media/'), id)
    if not candidates:
        return None

    with_video = [p for p in candidates if has_stream(p, 'video') is True]
    with_audio = [p for p in candidates if has_stream(p, 'audio') is True]
    with_both = [p for p in with_video if has_stream(p, 'audio') is True]

    if with_both:
        return _select_primary('video', with_both)

    video_source = _pick_largest(with_video)
    audio_only = [p for p in with_audio
                  if p not in with_video
                  and has_stream(p, 'video') is False]
    audio_source = _pick_largest(audio_only)
    if not video_source or not audio_source:
        return None

    for format in ['mp4', 'aac_mp4', 'mkv', 'compat']:
        merged = _merge_by_filetype(
            format,
            audio_source,
            video_source,
            id,
            on_process=on_process,
            should_terminate=should_terminate
        )
        if merged is not None:
            return merged
    return None


def _merge_by_filetype(
    filetype: str,
    audio_source: Path,
    video_source: Path,
    video_id: str,
    *,
    on_process: Callable[[subprocess.Popen[str]], None] | None = None,
    should_terminate: Callable[[], bool] | None = None,
):
    if filetype == 'mp4':
        merged = Path('./data/media') / f'{video_id}.merged.mp4'
        cmd = [
            os.getenv('ffmpeg'),
            '-y',
            '-i', str(video_source),
            '-i', str(audio_source),
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-c', 'copy',
            str(merged),
        ]
    elif filetype == 'aac_mp4':
        merged = Path('./data/media') / f'{video_id}.merged.mp4'
        cmd = [
            os.getenv('ffmpeg'),
            '-y',
            '-i', str(video_source),
            '-i', str(audio_source),
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '160k',
            str(merged),
        ]
    elif filetype == 'mkv':
        merged = Path('./data/media') / f'{video_id}.merged.mkv'
        cmd = [
            os.getenv('ffmpeg'),
            '-y',
            '-i', str(video_source),
            '-i', str(audio_source),
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-c', 'copy',
            str(merged)
        ]
        run_cmd(
            cmd,
            on_process=on_process,
            should_terminate=should_terminate,
        )
    elif filetype == 'compat':
        merged = Path('./data/media') / f'{video_id}.playback.mp4'
        cmd = [
            os.getenv('ffmpeg'),
            "-y",
            "-i", str(video_source),
            "-i", str(audio_source),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.1",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-ac", "2",
            "-ar", "48000",
            "-b:a", "160k",
            "-movflags", "+faststart",
            str(merged),
        ]
        run_cmd(
            cmd,
            on_process=on_process,
            should_terminate=should_terminate,
        )
    else:
        return
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if (
        proc.returncode == 0 and
        merged.exists() and
        has_stream(merged, 'audio') is True and
        has_stream(merged, 'video') is True and
        _decode_smoke_test(merged)
    ):
        return merged
    return None


def _decode_smoke_test(path: Path) -> bool:
    cmd = [
        os.getenv('ffmpeg'),
        '-v', 'error',
        '-t', '2',
        '-i', str(path),
        '-f', 'null',
        '-'
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _pick_largest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return sorted(paths, key=lambda p: p.stat().st_size, reverse=True)[0]
