# src/system/database/commands/get_video.py


GET_VIDEO_COMMAND = """
SELECT (
    media_id,
    source_url,
    title,
    channel,
    uploader_id,
    duration_sec,
    upload_date,
    webpage_url,
    thumbnail,
    metadata_json
)
FROM videos
WHERE media_id=?
LIMIT 1
"""
