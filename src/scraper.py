import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

# Load env variables
load_dotenv()

API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")

# Logging setup
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/scraping.log"),
        logging.StreamHandler()
    ]
)

# Target Ethiopian medical Telegram channels
CHANNELS = [
    "CheMed18",
    "Lobeliacosmetics",
    "Tikvahpharma"
]

async def scrape_channel(client, channel_username, limit=100):
    logging.info(f"Starting scraping for channel: @{channel_username}")
    channel_data = []
    
    # Establish dynamic data-lake structure
    today_str = datetime.now().strftime("%Y-%m-%d")
    messages_dir = f"data/raw/telegram_messages/{today_str}"
    images_dir = f"data/raw/images/{channel_username}"
    os.makedirs(messages_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    try:
        # Retrieve messages
        async for message in client.iter_messages(channel_username, limit=limit):
            has_media = message.media is not None
            image_path = None

            # Download photos safely if they exist
            if has_media and hasattr(message.media, 'photo') and message.media.photo:
                filename = f"{message.id}.jpg"
                dest_path = os.path.join(images_dir, filename)
                try:
                    await client.download_media(message.media, file=dest_path)
                    image_path = dest_path
                    logging.info(f"Downloaded image for msg_id {message.id} to {dest_path}")
                except Exception as media_err:
                    logging.error(f"Failed to download media for msg_id {message.id}: {media_err}")

            # Build metadata payload
            payload = {
                "message_id": message.id,
                "channel_name": channel_username,
                "message_date": message.date.isoformat() if message.date else None,
                "message_text": message.text or "",
                "has_media": has_media,
                "image_path": image_path,
                "views": message.views or 0,
                "forwards": message.forwards or 0
            }
            channel_data.append(payload)

        # Write clean partitioned JSON to data lake
        json_file_path = os.path.join(messages_dir, f"{channel_username}.json")
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(channel_data, f, ensure_ascii=False, indent=4)
            
        logging.info(f"Successfully scraped {len(channel_data)} messages from @{channel_username}")

    except Exception as e:
        logging.error(f"Error occurred while scraping @{channel_username}: {e}")

async def main():
    if not API_ID or not API_HASH:
        logging.critical("Missing Telegram credentials. Check your .env configuration.")
        return

    async with TelegramClient("session_name", int(API_ID), API_HASH) as client:
        for channel in CHANNELS:
            await scrape_channel(client, channel, limit=150)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())