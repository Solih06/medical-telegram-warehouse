{{ config(materialized='table') }}

WITH unique_channels AS (
    SELECT DISTINCT
        channel_name
    FROM {{ ref('stg_telegram_messages') }}
)

SELECT
    -- Generate a clean, unique surrogate key for each channel
    MD5(channel_name) AS channel_key,
    channel_name,
    CASE 
        WHEN channel_name = 'CheMed18' THEN 'CheMed Medicine and Health'
        WHEN channel_name = 'Lobeliacosmetics' THEN 'Lobelia Cosmetics & Beauty'
        WHEN channel_name = 'Tikvahpharma' THEN 'Tikvah Pharmaceutical'
        ELSE 'Other Medical Channel'
    END AS channel_friendly_name,
    CASE
        WHEN channel_name = 'Lobeliacosmetics' THEN 'Cosmetics & Aesthetics'
        ELSE 'Pharma & Medicine'
    END AS channel_category
FROM unique_channels