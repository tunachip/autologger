# src/system/transcribe/video.py

import os
import subprocess
from typing import Callable
from pathlib import Path
from ..shared.command import run_cmd
from ..shared.helpers import has_stream


def transcribe_video(
    path: Path,
    id: str,
    *,
    on_process: Callable[[subprocess.Popen[str]], None] | None = None,
    should_terminate: Callable[[], bool] | None = None,
) -> Path:
    output_dir = Path('./data/media/transcripts') / id
    output_dir.mkdir(parents=True, exist_ok=True)

    has_audio = has_stream(path, 'audio')
    if has_audio is False:
        raise RuntimeError(
            f"Input media has no audio stream: {path}. "
            "Use a merged A/V file or an audio-containing stream."
        )
    cmd = [
        os.getenv('whisper'),
        str(path),
        '--model base',
        '--language en',
        '--output-format json',
        f'--output_dir {str(output_dir)}',
        '--verbose False',
    ]
    run_cmd(
        cmd,
        on_process=on_process,
        should_terminate=should_terminate
    )
    return _resolve_whisper_output(output_dir, path)


def _resolve_whisper_output(output_dir: Path, filepath: Path) -> Path:
    primary = output_dir / f"{filepath.stem}.json"
    if primary.exists():
        return primary
    json_files = sorted([
        p for p in output_dir.glob("*.json")
        if p.is_file()
    ])
    if len(json_files) == 1:
        return json_files[0]
    if json_files:
        return sorted(
            json_files,
            key=lambda p: p.stat().st_mtime, reverse=True
        )[0]
    raise RuntimeError(
        f"Whisper Output Missing in {output_dir}. "
        "No JSON files were produced."
    )
