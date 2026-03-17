# src/system/database/commands/get_job.py


GET_JOB_COMMAND = """
SELECT
    id,
    source_url,
    status,
    priority,
    error_text,
    queue_stage,
    retries,
    auto_transcribe,
    auto_summarize,
    media_id,
    local_media_path,
    transcript_path,
    created_at,
    started_at,
    finished_at
FROM ingest_jobs
WHERE id=?
LIMIT 1
"""


GET_LATEST_DONE_JOB_FOR_VIDEO_COMMAND = """
SELECT
    id,
    media_id,
    local_media_path,
    transcript_path,
    finished_at
FROM ingest_jobs
WHERE media_id=? AND status='done'
ORDER BY id DESC
LIMIT 1
"""


GET_LATEST_PLAYABLE_JOB_FOR_VIDEO = """
SELECT
    id,
    media_id,
    source_url,
    local_media_path,
    transcript_path,
    status,
    queue_stage
FROM ingest_jobs
WHERE media_id=?
    AND local_media_path IS NOT NULL
    AND status IN ('transcribing', 'summarizing', 'done')
ORDER BY id DESC
LIMIT 1
"""
