# src/system/shared/command.py

import subprocess
import threading
import shlex
import time
from typing import Callable, Any


def run_cmd(
    cmd: list[str],
    *,
    on_process: Callable[[subprocess.Popen[str]], None] | None,
    should_terminate: Callable[[], bool] | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if on_process:
        on_process(proc)

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def _drain_stream(
        stream: Any,
        chunks: list[str]
    ) -> None:
        try:
            while True:
                data = stream.read(4096)
                if not data:
                    break
                chunks.append(data)
        finally:
            try:
                stream.close()
            except Exception:
                pass

    stdout_thread = threading.Thread(
        target=_drain_stream,
        args=(proc.stdout, stdout_chunks),
        daemon=True
    )

    stderr_thread = threading.Thread(
        target=_drain_stream,
        args=(proc.stderr, stdout_chunks),
        daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()

    while proc.poll() is None:
        if should_terminate and should_terminate():
            proc.kill()
            break
        time.sleep(0.1)

    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)
    completed = subprocess.CompletedProcess(
        cmd,
        proc.returncode,
        stdout,
        stderr
    )
    if completed.returncode != 0:
        command = " ".join(shlex.quote(c) for c in cmd)
        raise RuntimeError(
            f"Command Failed ({completed.returncode}): {command}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed
