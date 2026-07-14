{{ config(materialized='table') }}

WITH date_spine AS (
    SELECT DISTINCT
        CAST(message_timestamp AS DATE) AS message_date
    FROM {{ ref('stg_telegram_messages') }}
    WHERE message_timestamp IS NOT NULL
)

SELECT
    message_date AS date_key,
    EXTRACT(YEAR FROM message_date) AS calendar_year,
    EXTRACT(MONTH FROM message_date) AS calendar_month,
    TO_CHAR(message_date, 'Month') AS month_name,
    EXTRACT(DAY FROM message_date) AS calendar_day,
    EXTRACT(DOW FROM message_date) AS day_of_week,
    TO_CHAR(message_date, 'Day') AS day_name,
    EXTRACT(WEEK FROM message_date) AS calendar_week
FROM date_spine