{{ config(materialized='table') }}

WITH base AS (
    SELECT 
        channel_name,
        MIN(message_timestamp) as first_post_date, -- Required [cite: 2940]
        MAX(message_timestamp) as last_post_date, -- Required [cite: 2940]
        COUNT(message_id) as total_posts, -- Required [cite: 2941]
        AVG(views_count) as avg_views -- Required [cite: 2942]
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_name
)

SELECT
    MD5(channel_name) AS channel_key, -- Required [cite: 2937]
    channel_name, -- Required [cite: 2938]
    CASE 
        WHEN channel_name = 'CheMed18' THEN 'Medical'
        WHEN channel_name = 'Lobeliacosmetics' THEN 'Cosmetics'
        WHEN channel_name = 'Tikvahpharma' THEN 'Pharmaceutical'
        ELSE 'Medical'
    END AS channel_type, -- Required [cite: 2939]
    first_post_date,
    last_post_date,
    total_posts,
    ROUND(avg_views, 2) AS avg_views
FROM base