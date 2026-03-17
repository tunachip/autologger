# src/system/database/commands/list_videos.py


LIST_PLAYABLE_VIDEOS_COMMAND = """
WITH latest_playable AS (
    SELECT video_id, MAX(id) AS max_id
    FROM ingest_jobs
    WHERE
        video_id IS NOT NULL
        AND local_video_path IS NOT NULL
        AND status IN ('transcribing', 'done')
    GROUP BY video_id
)
SELECT
    v.video_id,
    COALESCE(v.title, v.video_id) AS title,
    v.channel,
    v.uploader_id,
    v.source_url,
    v.webpage_url,
    j.local_video_path,
    j.transcript_json_path
FROM videos v
JOIN latest_playable ld
    ON ld.video_id = v.video_id
JOIN ingest_jobs j
    ON j.id = ld.max_id
ORDER BY j.id DESC
LIMIT ?
"""
