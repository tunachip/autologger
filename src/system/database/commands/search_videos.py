# src/system/database/commands/search_videos.py


SEARCH_VIDEOS_BY_TRANSCRIPT_COMMAND = """
WITH latest_done AS (
    SELECT media_id, MAX(id) AS max_id
    FROM ingest_jobs
    WHERE status = 'done' AND media_id IS NOT NULL
    GROUP BY media_id
)
SELECT
    ts.media_id,
    COALESCE(v.title, ts.media_id) AS title,
    COUNT(*) AS match_count,
    MIN(ts.start_ms) AS first_start_ms,
    j.local_media_path,
    j.transcript_path
FROM transcript_segments ts
JOIN videos v
    ON v.media_id = ts.media_id
LEFT JOIN latest_done ld
    ON ld.media_id = ts.media_id
LEFT JOIN ingest_jobs j
    ON j.id = ld.max_id
WHERE LOWER(ts.text) LIKE ?
GROUP BY ts.media_id, v.title, j.local_media_path, j.transcript_path
ORDER BY match_count DESC, first_start_ms ASC
LIMIT ?
"""


SEARCH_VIDEOS_BY_TITLE_COMMAND = """
WITH latest_playable AS (
    SELECT media_id, MAX(id) AS max_id
    FROM ingest_jobs
    WHERE
        media_id IS NOT NULL
        AND local_media_path IS NOT NULL
        AND status IN ('transcribing', 'done')
    GROUP BY media_id
)
SELECT
    v.media_id,
    COALESCE(v.title, v.media_id) AS title,
    j.local_media_path,
    j.transcript_path
FROM videos v
JOIN latest_playable ld
    ON ld.media_id = v.media_id
JOIN ingest_jobs j
    ON j.id = ld.max_id
{where_clause}
ORDER BY LOWER(COALESCE(v.title, v.media_id)) ASC
LIMIT ?
"""


SEARCH_VIDEOS_BY_METADATA_WHERE_CLAUSE = """
WHERE
    LOWER(COALESCE(v.title, '')) LIKE ?
    OR LOWER(COALESCE(v.channel, '')) LIKE ?
    OR LOWER(COALESCE(v.uploader_id, '')) LIKE ?
    OR LOWER(COALESCE(v.video_id, '')) LIKE ?
    OR LOWER(COALESCE(v.source_url, '')) LIKE ?
    OR LOWER(COALESCE(v.webpage_url, '')) LIKE ?
    OR LOWER(COALESCE(v.metadata_json, '')) LIKE ?
"""


SEARCH_VIDEOS_BY_METADATA_COMMAND = """
WITH latest_playable AS (
    SELECT media_id, MAX(id) AS max_id
    FROM ingest_jobs
    WHERE
        media_id IS NOT NULL
        AND local_media_path IS NOT NULL
        AND status IN ('transcribing', 'done')
    GROUP BY media_id
)
SELECT
    v.media_id,
COALESCE(v.title, v.media_id) AS title,
    v.channel,
    v.uploader_id,
    v.duration_sec,
    v.upload_date,
    v.source_url,
    v.webpage_url,
    v.metadata_json,
    j.local_media_path,
    j.transcript_path
FROM videos v
JOIN latest_playable ld
    ON ld.media_id = v.media_id
JOIN ingest_jobs j
    ON j.id = ld.max_id
{where_clause}
ORDER BY LOWER(COALESCE(v.title, v.media_id)) ASC
LIMIT ?
"""
