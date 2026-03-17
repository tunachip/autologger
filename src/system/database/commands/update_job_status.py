# src/system/database/commands/update_job_status.py


UPDATE_JOB_STATUS = """
UPDATE ingest_jobs
SET status=?,
    error_text=COALESCE(?, error_text),
    queue_stage=COALESCE(?, queue_stage),
    media_id=COALESCE(?, media_id),
    local_media_path=COALESCE(?, local_media_path),
    transcript_path=COALESCE(?, transcript_path),
    finished_at=COALESCE(?, finished_at),
WHERE id=?
"""
