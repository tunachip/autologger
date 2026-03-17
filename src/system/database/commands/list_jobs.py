# src/system/database/commands/list_jobs.py


LIST_ALL_JOBS_COMMAND = """
SELECT
    id,
    source_url,
    status,
    priority,
    error_text,
    queue_stage,
    auto_transcribe,
    auto_summarize,
    retries,
    media_id,
    created_at,
    started_at,
    finished_at
FROM ingest_jobs
ORDER BY id DESC
LIMIT ?
"""


LIST_DONE_JOBS_COMMAND = """
WITH lastest_done AS (
    SELECT
        media_id,
        MAX(id) AS max_id
    FROM ingest_jobs
    WHERE status = 'done' AND media_id IS NOT NULL
    GROUP BY media_id
)
SELECT
    j.id,
    j.media_id,
    j.local_media_path,
    j.transcript_path
FROM ingest_jobs j
JOIN latest_done ld
    ON ld.max_id = j.id
ORDER BY j.id DESC
"""
