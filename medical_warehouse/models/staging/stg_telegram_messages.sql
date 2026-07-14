{{ config(materialized='view') }}

WITH raw_messages AS (
    SELECT
        message_id,
        channel_name,
        message_date,
        message_text,
        has_media,
        image_path,
        views,
        forwards,
        ROW_NUMBER() OVER (
            PARTITION BY channel_name, message_id 
            ORDER BY message_date DESC
        ) as rn
    FROM {{ source('raw', 'telegram_messages') }}
)

SELECT
    message_id,
    channel_name,
    CAST(message_date AS TIMESTAMP) AS message_timestamp,
    TRIM(message_text) AS cleaned_text,
    COALESCE(LENGTH(TRIM(message_text)), 0) AS message_length, -- Required [cite: 2932]
    COALESCE(has_media, FALSE) AS has_image, -- Required [cite: 2932]
    image_path,
    COALESCE(views, 0) AS views_count,
    COALESCE(forwards, 0) AS forwards_count
FROM raw_messages
WHERE rn = 1 AND message_id IS NOT NULL