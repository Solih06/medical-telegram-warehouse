{{ config(materialized='table') }}

WITH yolo_data AS (
    SELECT * FROM {{ ref('yolo_detections') }}
)

SELECT
    y.message_id, -- Required [cite: 3008]
    MD5(y.channel_name) AS channel_key, -- Required [cite: 3008]
    f.date_key, -- Required [cite: 3008]
    y.detected_class, -- Required [cite: 3008]
    y.confidence_score, -- Required [cite: 3008]
    y.image_category -- Required [cite: 3008]
FROM yolo_data y
LEFT JOIN {{ ref('fct_messages') }} f ON y.message_id = f.message_id AND MD5(y.channel_name) = f.channel_key
