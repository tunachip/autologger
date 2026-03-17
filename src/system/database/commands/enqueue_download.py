# src/system/database/commands/enqueue_download.py


ENQUEUE_DOWNLOAD = """
INSERT INTO ingest_jobs(
    source_url,
    status,
    queue_stage,
    auto_transcribe,
    auto_summarize,
    priority,
    created_at
)
VALUES (?, 'queued', 'download', ?, ?, ?, ?)
"""
