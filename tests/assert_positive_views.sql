SELECT *
FROM {{ ref('stg_telegram_messages') }}
WHERE views_count < 0