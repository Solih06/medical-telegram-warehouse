import os
import json
import logging
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "medical_dwh"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )

def load_data_to_warehouse():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
    except Exception as e:
        logging.critical(f"Database connection failed: {e}")
        return

    # Create the landing schema and table
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    create_table_query = """
    CREATE TABLE IF NOT EXISTS raw.telegram_messages (
        message_id INT,
        channel_name VARCHAR(100),
        message_date TIMESTAMP,
        message_text TEXT,
        has_media BOOLEAN,
        image_path TEXT,
        views INT,
        forwards INT,
        PRIMARY KEY (channel_name, message_id)
    );
    """
    cur.execute(create_table_query)
    conn.commit()

    # Locate current date partitions
    today_str = datetime.now().strftime("%Y-%m-%d")
    target_dir = f"data/raw/telegram_messages/{today_str}"

    if not os.path.exists(target_dir):
        logging.warning(f"No scraped data found for date: {today_str}. Make sure to run 'src/scraper.py' first!")
        cur.close()
        conn.close()
        return

    for filename in os.listdir(target_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(target_dir, filename)
            logging.info(f"Loading {filename} metadata into raw.telegram_messages table...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                records = json.load(f)

            for record in records:
                insert_query = """
                INSERT INTO raw.telegram_messages (
                    message_id, channel_name, message_date, message_text, has_media, image_path, views, forwards
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (channel_name, message_id) DO UPDATE SET
                    message_date = EXCLUDED.message_date,
                    message_text = EXCLUDED.message_text,
                    has_media = EXCLUDED.has_media,
                    image_path = EXCLUDED.image_path,
                    views = EXCLUDED.views,
                    forwards = EXCLUDED.forwards;
                """
                cur.execute(insert_query, (
                    record["message_id"],
                    record["channel_name"],
                    record["message_date"],
                    record["message_text"],
                    record["has_media"],
                    record["image_path"],
                    record["views"],
                    record["forwards"]
                ))
            conn.commit()
            
    logging.info("Load process successfully completed!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    load_data_to_warehouse()