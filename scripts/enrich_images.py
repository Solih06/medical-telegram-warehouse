import os
import logging
import psycopg2
from dotenv import load_dotenv
from ultralytics import YOLO

# Load configurations
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "medical_dwh"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )

def setup_detection_table():
    """Ensures the destination table for our enriched image data exists."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS raw.image_detections (
        detection_id SERIAL PRIMARY KEY,
        channel_name VARCHAR(100),
        image_path TEXT UNIQUE,
        detected_class VARCHAR(100),
        confidence_score FLOAT,
        box_coordinates TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cur.execute(create_table_query)
    conn.commit()
    cur.close()
    conn.close()
    logging.info("raw.image_detections table verified/created.")

def process_and_enrich_images():
    # Initialize the pre-trained YOLOv8 Nano model (lightweight, highly efficient)
    logging.info("Loading pre-trained YOLOv8 nano model...")
    model = YOLO("yolov8n.pt") 

    conn = get_db_connection()
    cur = conn.cursor()

    image_base_dir = "data/raw/images"
    if not os.path.exists(image_base_dir):
        logging.warning(f"No image folder found at {image_base_dir}. Skipping vision enrichment.")
        return

    # Iterate through each channel's image directory
    for channel_name in os.listdir(image_base_dir):
        channel_path = os.path.join(image_base_dir, channel_name)
        if not os.path.isdir(channel_path):
            continue

        logging.info(f"Processing images from channel: @{channel_name}")
        for image_file in os.listdir(channel_path):
            if not image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            image_path = os.path.join(channel_path, image_file)
            
            # Check if this image has already been processed to avoid redundant computation
            cur.execute("SELECT 1 FROM raw.image_detections WHERE image_path = %s LIMIT 1;", (image_path,))
            if cur.fetchone():
                continue

            logging.info(f"Running object detection on: {image_path}")
            try:
                # Run YOLOv8 inference
                results = model(image_path, verbose=False)
                
                # Parse output detections
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        class_id = int(box.cls[0])
                        class_name = model.names[class_id] # Convert ID to label (e.g., 'bottle', 'bowl', etc.)
                        confidence = float(box.conf[0])
                        xyxy_coords = box.xyxy[0].tolist() # Bounding box [x1, y1, x2, y2]

                        # Store detections directly in our PostgreSQL Data Warehouse
                        insert_query = """
                        INSERT INTO raw.image_detections (
                            channel_name, image_path, detected_class, confidence_score, box_coordinates
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (image_path) DO NOTHING;
                        """
                        cur.execute(insert_query, (
                            channel_name,
                            image_path,
                            class_name,
                            confidence,
                            str(xyxy_coords)
                        ))
                conn.commit()
                
            except Exception as e:
                logging.error(f"Failed to process image {image_path}: {e}")
                conn.rollback()

    cur.close()
    conn.close()
    logging.info("Image detection pipeline completed successfully!")

if __name__ == "__main__":
    setup_detection_table()
    process_and_enrich_images()