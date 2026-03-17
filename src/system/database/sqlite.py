# src/system/database/sqlite.py

import sqlite3
import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from pathlib import Path
from collections.abc import Iterator

from .commands.init_schema import INIT_SCHEMA
from .commands.enqueue_download import ENQUEUE_DOWNLOAD
from .commands.reserve_job import RESERVE_JOB, UPDATE_STATUS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iso_to_epoch_sec(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


@dataclass(slots=True)
class Job:
    id: int
    url: str
    status: str
    priority: int
    queue_stage: str = "download"
    media_id: str | None = None
    local_media_path: str | None = None
    transcript_path: str | None = None
    auto_transcribe: int | None = None
    auto_summarize: int | None = None
    retries: int = 0


class DB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(INIT_SCHEMA)
            self._ensure_column(
                conn,
                "ingest_jobs",
                "auto_transcribe",
                "INTEGER"
            )
            self._ensure_column(
                conn,
                "ingest_jobs",
                "auto_summarize",
                "INTEGER"
            )
            self._ensure_column(
                conn,
                "ingest_jobs",
                "queue_stage",
                "TEXT NOT NULL DEFAULT 'download'"
            )
            self._ensure_column(
                conn,
                "channel_subscriptions",
                "auto_transcribe",
                "INTEGER"
            )
            self._ensure_column(
                conn,
                "channel_subscriptions",
                "auto_summarize",
                "INTEGER"
            )

    def _ensure_column(
        self,
        conn: sqlite3.Connection,
        table: str,
        column: str,
        column_type: str,
    ) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {str(row['name']) for row in rows}
        if column in existing:
            return
        conn.execute(str(
            f"ALTER TABLE {table} "
            + f"ADD COLUMN {column} "
            + f"{column_type}"
        ))

    def enqueue(
        self,
        urls: list[str],
        priority: int = 0,
        *,
        auto_transcribe: bool | None = None,
        auto_summarize: bool | None = None,
    ) -> list[int]:
        return self.enqueue_downloads(
            urls,
            priority=priority,
            auto_transcribe=auto_transcribe,
            auto_summarize=auto_summarize,
        )

    def enqueue_downloads(
        self,
        urls: list[str],
        priority: int = 0,
        *,
        auto_transcribe: bool | None = None,
        auto_summarize: bool | None = None,
    ) -> list[int]:
        now = utc_now_iso()
        ids: list[int] = []
        with self.connect() as conn:
            for url in urls:
                cur = conn.execute(
                    ENQUEUE_DOWNLOAD, (
                        url,
                        (None if auto_transcribe is None
                         else 1 if auto_transcribe
                         else 0),
                        (None if auto_summarize is None
                         else 1 if auto_summarize
                         else 0),
                        priority,
                        now
                    )
                )
                if cur.lastrowid is None:
                    raise RuntimeError("insert did not produce a row id")
                ids.append(int(cur.lastrowid))
        return ids

    def reserve_next_job(self, stage: str) -> Job | None:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(RESERVE_JOB, stage).fetchone()
            if not row:
                conn.execute("COMMIT")
                return None
            active_status = (
                "downloading" if stage == "download"
                else "transcribing"
            )
            conn.execute(
                UPDATE_STATUS, (
                    active_status,
                    utc_now_iso(),
                    row['id']
                )
            )
            conn.execute("COMMIT")
            return Job(
                id=int(row['id']),
                url=str(row['source_url']),
                status=active_status,
                queue_stage=str(row['queue_stage'] or stage),
                priority=int(row['priority']),
                media_id=(
                    None if row['media_id'] is None
                    else str(row['media_id'])
                ),
                local_media_path=(
                    None if row['local_media_path'] is None
                    else str(row['local_media_path'])
                ),
                transcript_path=(
                    None if row['transcript_path'] is None
                    else str(row['transcript_path'])
                ),
                auto_transcribe=(
                    None if row['auto_transcribe'] is None
                    else int(row['auto_transcribe'])
                ),
                auto_summarize=(
                    None if row['auto_summarize'] is None
                    else int(row['auto_summarize'])
                ),
                retries=int(row['retries'] or 0),
            )

    def update_job_status(
        self,
        job_id: int,
        status: str,
        *,
        error_text: str | None = None,
        queue_stage: str | None = None,
        media_id: str | None = None,
        local_media_path: str | None = None,
        transcript_path: str | None = None,
    ) -> None:
        finished_at = utc_now_iso() if status in {"done", "failed"} else None
        with self.connect() as conn:
            conn.execute(
                UPDATE_JOB_STATUS, (
                    status,
                    error_text,
                    queue_stage,
                    media_id,
                    local_media_path,
                    transcript_path,
                    finished_at,
                    job_id,
                )
            )

    def retry_job(self, job_id: int, *, error_text: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(RETRY_JOB, (error_text, job_id))

    def queue_job_stage(
        self,
        job_id: int,
        *,
        queue_stage: str,
        media_id: str | None = None,
        local_media_path: str | None = None,
        transcript_path: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                QUEUE_JOB_STAGE, (
                    queue_stage,
                    media_id,
                    local_media_path,
                    transcript_path,
                    job_id
                ),
            )

    def upsert_video(
        self,
        media_id: str,
        source_url: str,
        metadata: dict[str, Any],
    ) -> None:
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                UPSERT_VIDEO, (
                    media_id,
                    source_url,
                    metadata.get('title'),
                    metadata.get('channel') or metadata.get('uploader'),
                    metadata.get('uploader_id'),
                    metadata.get('duration'),
                    metadata.get('upload_date'),
                    metadata.get('webpage)url'),
                    metadata.get('thumbnail'),
                    metadata.get('view_count'),
                    metadata.get('like_count'),
                    json.dumps(metadata, separators=(",", ":")),
                    now,
                    now,
                )
            )

    def 
