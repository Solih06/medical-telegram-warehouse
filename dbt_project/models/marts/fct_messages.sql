{{ config(materialized='table') }}

SELECT
    -- Surrogate and Foreign Keys
    MD5(channel_name) AS channel_key,
    CAST(message_timestamp AS DATE) AS date_key,
    message_id,
    
    -- Cleaned attributes
    cleaned_text,
    has_media,
    image_path,
    visual_product_type,

    -- Numerical metrics
    views_count,
    forwards_count
FROM {{ ref('stg_telegram_messages') }}