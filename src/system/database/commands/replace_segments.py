# src/system/database/commands/replace_segments.py


LIST_TRANSCRIPT_SEGMENTS_COMMAND = """
SELECT
    segment_index,
    start_ms,
    end_ms,
    text
FROM transcript_segments
WHERE video_id = ?
ORDER BY segment_index ASC, start_ms ASC
"""
