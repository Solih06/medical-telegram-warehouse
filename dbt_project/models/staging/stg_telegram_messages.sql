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
    has_media,
    image_path,
    COALESCE(views, 0) AS views_count,
    COALESCE(forwards, 0) AS forwards_count,
    -- Simple extraction check to see if it's a visual product focus
    CASE 
        WHEN LOWER(message_text) LIKE '%pills%' OR LOWER(message_text) LIKE '%tablets%' THEN 'Pill'
        WHEN LOWER(message_text) LIKE '%cream%' OR LOWER(message_text) LIKE '%ointment%' THEN 'Cream'
        ELSE 'Other/Unspecified'
    END AS visual_product_type
FROM raw_messages
WHERE rn = 1
  AND message_id IS NOT NULL