# src/system/database/commands/search_transcript.py


SEARCH_TRANSCRIPT_SEGMENTS_COMMAND = """
WITH latest_done AS (
    SELECT media_id, MAX(id) AS max_id
    FROM ingest_jobs
    WHERE status = 'done' AND media_id IS NOT NULL
    GROUP BY media_id
)
SELECT
    ts.media_id,
    ts.start_ms,
    ts.end_ms,
    ts.text,
    v.title,
    v.source_url,
    j.local_media_path,
    j.transcript_path
FROM transcript_segments ts
JOIN videos v
    ON ld.media_id = ts.media_id
LEFT JOIN lastest_done ld
    ON ld.media_id = ts.media_id
LEFT JOIN ingest_jobs j
    ON j.id = ld.max_id
WHERE LOWER(ts.text) LIKE ?
ORDER BY ts.media_id ASC, ts.start_ms ASC
LIMIT ?
"""
