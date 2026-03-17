# src/system/database/commands/reserve_job.py


RESERVE_JOB = """
SELECT
    id,
    source_url,
    status,
    queue_stage,
    priority,
    media_id,
    local_media_path,
    transcript_path,
    auto_transcribe,
    auto_summarize,
    retries
FROM ingest_jobs
WHERE status = 'queued'
    AND queue_stage = ?
ORDER BY priority DESC, created at ASC
LIMIT 1
"""

UPDATE_STATUS = """
UPDATE ingest_jobs
SET status=?, started_at=?, error_text=NULL
WHERE id=?, status='queued'
"""
