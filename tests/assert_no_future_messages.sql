SELECT *
FROM {{ ref('stg_telegram_messages') }}
WHERE message_timestamp > CURRENT_TIMESTAMP