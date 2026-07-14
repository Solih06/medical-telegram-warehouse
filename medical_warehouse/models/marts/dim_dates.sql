{{ config(materialized='table') }}

WITH date_spine AS (
    SELECT DISTINCT
        CAST(message_timestamp AS DATE) AS full_date
    FROM {{ ref('stg_telegram_messages') }}
    WHERE message_timestamp IS NOT NULL
)

SELECT
    full_date AS date_key, -- Required [cite: 2944]
    full_date, -- Required [cite: 2945]
    EXTRACT(DOW FROM full_date) AS day_of_week, -- Required [cite: 2946]
    TO_CHAR(full_date, 'Day') AS day_name, -- Required [cite: 2947]
    EXTRACT(WEEK FROM full_date) AS week_of_year, -- Required [cite: 2948]
    EXTRACT(MONTH FROM full_date) AS month, -- Required [cite: 2949]
    TO_CHAR(full_date, 'Month') AS month_name, -- Required [cite: 2950]
    EXTRACT(QUARTER FROM full_date) AS quarter, -- Required [cite: 2951]
    EXTRACT(YEAR FROM full_date) AS year, -- Required [cite: 2952]
    CASE WHEN EXTRACT(DOW FROM full_date) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend -- Required [cite: 2953]
FROM date_spine