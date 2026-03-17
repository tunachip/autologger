# src/system/database/commands/queue_job_stage.py


QUEUE_JOB_STAGE = """

UPDATE ingest_jobs
SET status='queued',
    queue_stage=?,
    error_text=NULL,
    media_id=COALESCE(?, video_id),
    local_media_path=COALESCE(?, local_media_path),
    transcript_path=COALESCE(?, transcript_path),
    started_at=NULL,
    finished_at=NULL
WHERE id=?
"""
